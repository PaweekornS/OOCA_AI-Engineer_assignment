"""LangGraph agent state schema."""

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class TriageState(TypedDict):
    """The working execution state passed across LangGraph nodes."""

    # Ticket inputs
    ticket_id: str
    customer_info: str
    thread_text: str
    language: str  # "th" or "en"

    # Agent conversation history & tool messages
    messages: Annotated[List[BaseMessage], add_messages]

    # Loop control counter
    tool_call_count: int

    # Final structured triage output
    triage_result: Optional[Dict[str, Any]]
