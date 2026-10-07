"""Unit tests for the audit logger."""

import json
from pathlib import Path
from langchain_core.messages import AIMessage, ToolMessage

from src.utils.audit_logger import _extract_tool_invocations, log_triage_event


def test_extract_tool_invocations_pairing():
    """Verifies that AIMessage tool calls correctly match with ToolMessage results."""
    ai_msg = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_123",
                "name": "check_billing_records",
                "args": {"customer_id": "TICKET-001"},
            }
        ],
    )
    tool_msg = ToolMessage(
        content="Payment Gateway: 3 pending auth holds",
        name="check_billing_records",
        tool_call_id="call_123",
    )

    invocations = _extract_tool_invocations([ai_msg, tool_msg])
    assert len(invocations) == 1
    assert invocations[0]["tool_name"] == "check_billing_records"
    assert invocations[0]["args"]["customer_id"] == "TICKET-001"
    assert "3 pending auth holds" in invocations[0]["output"]


def test_log_triage_event_writes_jsonl(tmp_path: Path):
    """Verifies that log_triage_event serializes state into a valid JSON Lines record."""
    dummy_log_file = tmp_path / "test_audit.jsonl"

    state = {
        "ticket_id": "TICKET-TEST-99",
        "customer_info": "Enterprise User",
        "language": "th",
        "thread_text": "ระบบล่ม error 500",
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call_999", "name": "check_system_status", "args": {"region": "Asia"}}
                ],
            ),
            ToolMessage(
                content="BKK-AP1: 16.4% error rate",
                name="check_system_status",
                tool_call_id="call_999",
            ),
        ],
        "tool_call_count": 1,
        "triage_result": {
            "urgency": "critical",
            "next_action": "escalate_to_human",
            "routing_target": "DevOps Incident Commander",
        },
    }

    entry = log_triage_event(state, log_file=dummy_log_file)
    assert entry["ticket_id"] == "TICKET-TEST-99"
    assert entry["language"] == "th"
    assert len(entry["tools_called"]) == 1
    assert entry["tools_called"][0]["tool"] == "check_system_status"
    assert entry["tool_call_count"] == 1

    # Verify physical file written
    assert dummy_log_file.exists()
    with open(dummy_log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["ticket_id"] == "TICKET-TEST-99"
        assert record["triage_decision"]["urgency"] == "critical"
