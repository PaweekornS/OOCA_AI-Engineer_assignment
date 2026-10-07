"""Tests for LangGraph state machine assembly, edges, and domain contracts."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from src.graph.edges import check_next_step
from src.graph.workflow import create_triage_graph
from src.models.domain import SupportTicket, TicketMessage
from src.models.triage import NextAction, TriageDecision, UrgencyLevel


def test_domain_model_formatting():
    """Verifies that SupportTicket correctly structures the prompt thread block."""
    ticket = SupportTicket(
        ticket_id="TICKET-TEST",
        customer_info="Enterprise tier, Thailand, 45 seats",
        messages=[
            TicketMessage(message_id="M1", timestamp_relative="2h ago", sender="customer", text="System error 500"),
            TicketMessage(message_id="M2", timestamp_relative="just now", sender="customer", text="Still broken"),
        ],
    )
    formatted = ticket.format_thread_for_prompt()
    assert "Ticket ID: TICKET-TEST" in formatted
    assert "Enterprise tier" in formatted
    assert "[2h ago] CUSTOMER: System error 500" in formatted
    assert "[just now] CUSTOMER: Still broken" in formatted


def test_edge_routing_with_tool_calls():
    """Verifies that check_next_step routes to exec_tools when tool calls exist under limit."""
    ai_msg_with_tool = AIMessage(
        content="",
        tool_calls=[{"name": "lookup_knowledge_base", "args": {"query": "test"}, "id": "call_1"}],
    )
    state = {
        "messages": [ai_msg_with_tool],
        "tool_call_count": 0,
    }
    assert check_next_step(state) == "exec_tools"


def test_edge_routing_loop_limit():
    """Verifies that check_next_step bails out to finalize_triage when tool limit reached."""
    ai_msg_with_tool = AIMessage(
        content="",
        tool_calls=[{"name": "lookup_knowledge_base", "args": {"query": "test"}, "id": "call_1"}],
    )
    state = {
        "messages": [ai_msg_with_tool],
        "tool_call_count": 3,  # Reached max limit
    }
    assert check_next_step(state) == "finalize_triage"


def test_edge_routing_no_tools():
    """Verifies that check_next_step routes directly to finalize_triage when no tool calls made."""
    ai_msg_clean = AIMessage(content="I have diagnosed the issue.")
    state = {
        "messages": [ai_msg_clean],
        "tool_call_count": 1,
    }
    assert check_next_step(state) == "finalize_triage"


def test_graph_compilation():
    """Verifies that the LangGraph workflow compiles successfully into an executable runnable."""
    app = create_triage_graph()
    assert app is not None
    assert hasattr(app, "invoke")
