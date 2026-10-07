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

    initial_prompt = (
        f"--- INBOUND SUPPORT TICKET ---\n"
        f"Ticket ID: {ticket_id}\n"
        f"Customer Context: {clean_customer_info}\n\n"
        f"Conversation History:\n{clean_thread}\n"
        f"-------------------------------\n"
        f"Please analyze this ticket. Determine if any tools are needed to verify internal policies or system health."
    )

    return {
        "customer_info": clean_customer_info,
        "thread_text": clean_thread,
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
    """Node: Synthesizes diagnostic findings and produces the final structured TriageDecision."""
    llm = _get_llm()
    structured_llm = llm.with_structured_output(TriageDecision)

    # Compile synthesis context including system instructions and diagnostic history
    synthesis_messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(
            content=(
                "Please finalize the triage decision now. Output the structured TriageDecision "
                "with urgency, product, issue_type, customer_sentiment, next_action, routing_target, "
                "reasoning, and draft_response."
            )
        ),
    ]

    try:
        decision: TriageDecision = structured_llm.invoke(synthesis_messages)
        result_dict = decision.model_dump()
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
            "draft_response": "Thank you for contacting support. A representative is reviewing your ticket.",
        }

    return {"triage_result": result_dict}
