"""Assembles and compiles the LangGraph state machine for ticket triage."""

from langgraph.graph import END, START, StateGraph
from src.graph.edges import check_next_step
from src.graph.nodes import (
    call_agent_node,
    exec_tools_node,
    finalize_triage_node,
    prepare_context_node,
)
from src.state import TriageState


def create_triage_graph():
    """Builds and compiles the cyclic Support Ticket Triage LangGraph workflow.

    Workflow topology:
        START -> prepare_context -> call_agent -> [check_next_step]
                                      ^               |       \
                                      |               |        \
                                      +-- exec_tools -+         +-> finalize_triage -> END
    """
    workflow = StateGraph(TriageState)

    # Add workflow nodes
    workflow.add_node("prepare_context", prepare_context_node)
    workflow.add_node("call_agent", call_agent_node)
    workflow.add_node("exec_tools", exec_tools_node)
    workflow.add_node("finalize_triage", finalize_triage_node)

    # Add edges
    workflow.add_edge(START, "prepare_context")
    workflow.add_edge("prepare_context", "call_agent")

    # Conditional branching out of call_agent
    workflow.add_conditional_edges(
        "call_agent",
        check_next_step,
        {
            "exec_tools": "exec_tools",
            "finalize_triage": "finalize_triage",
        },
    )

    # Loop back from exec_tools to call_agent
    workflow.add_edge("exec_tools", "call_agent")

    # Finalize triage completes the graph
    workflow.add_edge("finalize_triage", END)

    return workflow.compile()
