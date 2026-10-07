"""Audit logger for tracking AI agent tool invocations and triage decisions."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from langchain_core.messages import AIMessage, ToolMessage

from src.state import TriageState

# Project root logs directory
LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
AUDIT_LOG_FILE = LOGS_DIR / "triage_audit.jsonl"


def _extract_tool_invocations(messages: List[Any]) -> List[Dict[str, Any]]:
    """Extracts paired tool calls and tool responses from message history."""
    tool_calls_map: Dict[str, Dict[str, Any]] = {}

    # 1. Collect tool calls proposed by the AI
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for call in msg.tool_calls:
                call_id = call.get("id")
                if call_id:
                    tool_calls_map[call_id] = {
                        "tool_name": call.get("name"),
                        "args": call.get("args", {}),
                        "output": None,
                    }

    # 2. Match with actual ToolMessage execution results
    invocations = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            call_id = getattr(msg, "tool_call_id", None)
            tool_name = getattr(msg, "name", "tool") or "tool"
            content = str(msg.content)

            if call_id and call_id in tool_calls_map:
                entry = tool_calls_map[call_id]
                entry["output"] = content
                invocations.append(entry)
            else:
                invocations.append({
                    "tool_name": tool_name,
                    "args": {},
                    "output": content,
                })

    return invocations


def log_triage_event(state: TriageState, log_file: Optional[Path] = None) -> Dict[str, Any]:
    """Records an immutable audit trace of an inbound query, tools called, and final decision.

    Args:
        state: The LangGraph execution state.
        log_file: Optional target file path (defaults to logs/triage_audit.jsonl).

    Returns:
        The structured audit log entry.
    """
    target_file = log_file or AUDIT_LOG_FILE
    target_file.parent.mkdir(parents=True, exist_ok=True)

    messages = state.get("messages", [])
    tool_invocations = _extract_tool_invocations(messages)

    audit_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": state.get("ticket_id", "UNKNOWN"),
        "customer_info": state.get("customer_info", ""),
        "language": state.get("language", "en"),
        "tools_called": [
            {
                "tool": inv["tool_name"],
                "args": inv["args"],
                "output_preview": (inv["output"][:300] + "...") if inv["output"] and len(inv["output"]) > 300 else inv["output"],
            }
            for inv in tool_invocations
        ],
        "tool_call_count": len(tool_invocations),
        "triage_decision": state.get("triage_result"),
    }

    # Append single-line JSON record for streaming / SIEM log ingestion
    with open(target_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_entry, ensure_ascii=False) + "\n")

    return audit_entry
