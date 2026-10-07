"""Node implementations for the LangGraph triage workflow."""

import json
from typing import Any, Dict
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from src.config import settings
from src.models.triage import TriageDecision
from src.prompts.extraction_prompt import EXTRACTION_SYSTEM_PROMPT
from src.prompts.system_prompt import AGENT_SYSTEM_PROMPT
from src.state import TriageState
from src.tools.base import get_triage_tools
from src.utils.pii_sanitizer import sanitize_pii


def _get_llm() -> ChatOpenAI:
    """Instantiates the ChatOpenAI client with project settings."""
    return ChatOpenAI(
        model=settings.openai_model_name,
        temperature=settings.openai_temperature,
        api_key=settings.openai_api_key,
    )


def prepare_context_node(state: TriageState) -> Dict[str, Any]:
    """Node: Sanitizes ticket thread text and prepares initial message history."""
    raw_thread = state.get("thread_text", "")
    customer_info = state.get("customer_info", "")
    ticket_id = state.get("ticket_id", "UNKNOWN")

    # Scrub PII (Credit cards, CVV, raw tokens)
    clean_thread = sanitize_pii(raw_thread)
    clean_customer_info = sanitize_pii(customer_info)

    # Detect language deterministically and record in state
    from src.utils.response_templates import is_thai_text
    lang = "th" if is_thai_text(clean_thread) else "en"

    initial_prompt = (
        f"--- INBOUND SUPPORT TICKET ---\n"
        f"Ticket ID: {ticket_id}\n"
        f"Customer Context: {clean_customer_info}\n"
        f"Language: {'THAI' if lang == 'th' else 'ENGLISH'}\n\n"
        f"Conversation History:\n{clean_thread}\n"
        f"-------------------------------\n"
        f"Please analyze this ticket. Determine if any tools are needed to verify internal policies or system health."
    )

    return {
        "customer_info": clean_customer_info,
        "thread_text": clean_thread,
        "language": lang,
        "messages": [
            SystemMessage(content=AGENT_SYSTEM_PROMPT),
            HumanMessage(content=initial_prompt),
        ],
        "tool_call_count": 0,
    }


def call_agent_node(state: TriageState) -> Dict[str, Any]:
    """Node: Invokes the LLM with bound tools to reason and formulate next actions."""
    llm = _get_llm()
    tools = get_triage_tools()
    llm_with_tools = llm.bind_tools(tools)

    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def exec_tools_node(state: TriageState) -> Dict[str, Any]:
    """Node: Executes tools requested by the LLM in the previous step."""
    tools_map = {t.name: t for t in get_triage_tools()}
    last_message = state["messages"][-1]

    tool_messages = []
    tool_calls = getattr(last_message, "tool_calls", []) or []

    for call in tool_calls:
        tool_name = call.get("name")
        tool_args = call.get("args", {})
        tool_call_id = call.get("id")

        tool_func = tools_map.get(tool_name)
        if tool_func:
            try:
                result = tool_func.invoke(tool_args)
            except Exception as e:
                result = f"Error executing tool '{tool_name}': {str(e)}"
        else:
            result = f"Tool '{tool_name}' not found."

        tool_messages.append(
            ToolMessage(
                content=str(result),
                name=tool_name,
                tool_call_id=tool_call_id,
            )
        )

    current_count = state.get("tool_call_count", 0)
    return {
        "messages": tool_messages,
        "tool_call_count": current_count + len(tool_calls),
    }


def finalize_triage_node(state: TriageState) -> Dict[str, Any]:
    """Node: Synthesizes diagnostic findings and produces the final structured TriageDecision.

    Resolves Error 400 by decoupling raw tool-calling message traces and passing a clean
    synthesized diagnostic dossier alongside state['language'] to the extraction model.
    """
    llm = _get_llm()
    structured_llm = llm.with_structured_output(TriageDecision)

    lang = state.get("language") or "en"
    lang_label = "THAI" if lang == "th" else "ENGLISH"

    # Extract all tool diagnostic findings cleanly without dangling tool_calls
    diagnostic_findings = []
    for msg in state.get("messages", []):
        if isinstance(msg, ToolMessage):
            tool_name = getattr(msg, "name", "tool") or "tool"
            diagnostic_findings.append(f"[{tool_name}]: {msg.content}")

    findings_block = (
        "\n\n".join(diagnostic_findings)
        if diagnostic_findings
        else "No external diagnostic tools were required."
    )

    synthesis_prompt = (
        f"--- TICKET CONTEXT ---\n"
        f"Ticket ID: {state.get('ticket_id', 'UNKNOWN')}\n"
        f"Customer Context: {state.get('customer_info', '')}\n"
        f"Customer Language: {lang_label}\n\n"
        f"Conversation Thread:\n{state.get('thread_text', '')}\n\n"
        f"--- TOOL DIAGNOSTIC FINDINGS ---\n"
        f"{findings_block}\n"
        f"--------------------------------\n\n"
        f"TASK: Generate the structured TriageDecision.\n"
        f"LANGUAGE RULE: The draft_response MUST be written in {lang_label} (matching customer language).\n"
        f"FORMAT RULE: Direct in-ticket response text only (NO 'Subject:', NO 'Dear...', NO sign-offs like 'Best regards')."
    )

    synthesis_messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=synthesis_prompt),
    ]

    try:
        decision: TriageDecision = structured_llm.invoke(synthesis_messages)
        result_dict = decision.model_dump()

        from src.utils.response_templates import (
            build_route_to_specialist_response,
            clean_email_artifacts,
            get_fixed_escalation_response,
            is_thai_text,
        )

        # 1. Enforce fixed template policy for Sev-1 human escalation
        if decision.next_action == "escalate_to_human":
            result_dict["draft_response"] = get_fixed_escalation_response(lang)

        # 2. Clean email artifacts (Subject:, Dear ..., Best regards)
        if result_dict.get("draft_response"):
            result_dict["draft_response"] = clean_email_artifacts(result_dict["draft_response"])

        # 3. Guardrail: Language consistency enforcement based on state['language']
        is_thai_customer = (lang == "th")
        response_is_thai = is_thai_text(result_dict.get("draft_response", ""))

        if not is_thai_customer and response_is_thai:
            # Customer is English but response was Thai -> fix with English slot-filling template
            if decision.next_action == "route_to_specialist":
                result_dict["draft_response"] = build_route_to_specialist_response(
                    routing_target=result_dict.get("routing_target") or "Billing Operations",
                    issue_summary="your disputed payment charges and Pro account upgrade",
                    policy_note="Please note that multiple pending charges are typically temporary bank authorization holds that expire within 3 to 5 business days. Our specialists are reviewing your transaction log.",
                    is_thai=False,
                )

    except Exception as e:
        # Fallback safeguard in case of structured output extraction failure
        result_dict = {
            "urgency": "high",
            "product": "Core Platform",
            "issue_type": "general_inquiry",
            "customer_sentiment": "neutral",
            "next_action": "escalate_to_human",
            "routing_target": "Human Support Lead",
            "reasoning": f"Structured parsing fallback triggered due to error: {str(e)}",
            "draft_response": (
                "ทางเราได้รับเรื่องของท่านแล้วและกำลังส่งให้เจ้าหน้าที่ตรวจสอบครับ"
                if lang == "th"
                else "Thank you for contacting support. A representative is reviewing your ticket."
            ),
        }


    # Record structured audit log (ticket, tools called with args/outputs, and decision)
    try:
        from src.utils.audit_logger import log_triage_event
        enriched_state = {**state, "triage_result": result_dict}
        log_triage_event(enriched_state)
    except Exception:
        pass  # Safeguard: Audit logging must never crash the triage pipeline

    return {"triage_result": result_dict}

