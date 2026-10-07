"""Conditional routing edges for the LangGraph state machine."""

from typing import Literal
from src.config import settings
from src.state import TriageState


def check_next_step(state: TriageState) -> Literal["exec_tools", "finalize_triage"]:
    """Determines whether the agent needs to execute tools or transition to final triage.

    Routing logic:
    - If the last agent message contains tool_calls AND tool limit has not been exceeded -> 'exec_tools'
    - Otherwise -> 'finalize_triage'
    """
    messages = state.get("messages", [])
    if not messages:
        return "finalize_triage"

    last_message = messages[-1]
    has_tool_calls = bool(getattr(last_message, "tool_calls", None))
    current_count = state.get("tool_call_count", 0)

    if has_tool_calls and current_count < settings.max_tool_calls:
        return "exec_tools"

    return "finalize_triage"
