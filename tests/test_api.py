"""Integration and contract tests for the FastAPI backend API."""

import pytest
from fastapi.testclient import TestClient

from src.api.app import app, settings, triage_graph

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_graph_and_openai(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "sk-mock-test-key")

    def fake_invoke(state):
        return {
            "ticket_id": state["ticket_id"],
            "messages": [],
            "tool_call_count": 0,
            "triage_result": {
                "urgency": "high",
                "next_action": "route_to_specialist",
                "routing_target": "Billing Operations",
                "product": "Pro Subscription",
                "issue_type": "billing_payment",
                "customer_sentiment": "frustrated_angry",
                "draft_response": "We are looking into your billing concern.",
                "reasoning": "Mocked triage decision for API integration testing.",
            },
        }

    monkeypatch.setattr(triage_graph, "invoke", fake_invoke)


def test_health_check_endpoint():
    """Verifies that the /health endpoint returns 200 with registered tools and model info."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "tools_available" in data
    assert "lookup_knowledge_base" in data["tools_available"]
    assert "check_system_status" in data["tools_available"]
    assert "check_billing_records" in data["tools_available"]
    assert "check_ticket_history" in data["tools_available"]


def test_audit_logs_by_ticket_endpoint():
    """Verifies that the /api/v1/audit/logs/{ticket_id} endpoint returns records scoped to ticket_id."""
    from src.utils.audit_logger import log_triage_event
    # Seed a hermetic audit record for TICKET-001
    log_triage_event({
        "ticket_id": "TICKET-001",
        "customer_info": "Free plan user",
        "language": "en",
        "messages": [],
        "tool_call_count": 0,
        "triage_result": {"urgency": "high", "next_action": "route_to_specialist"},
    })

    response = client.get("/api/v1/audit/logs/TICKET-001")
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == "TICKET-001"
    assert "total_records" in data
    assert data["total_records"] >= 1
    assert isinstance(data["logs"], list)



def test_audit_logs_not_found_endpoint():
    """Verifies that querying a non-existent ticket_id returns a 404."""
    response = client.get("/api/v1/audit/logs/NON-EXISTENT-999")
    assert response.status_code == 404



def test_triage_endpoint_validation_error():
    """Verifies that submitting an empty payload missing ticket_id triggers a 422 Unprocessable Entity."""
    response = client.post("/api/v1/triage", json={})
    assert response.status_code == 422


def test_triage_endpoint_not_found():
    """Verifies that requesting an unknown ticket_id returns a 404 Not Found."""
    response = client.post("/api/v1/triage", json={"ticket_id": "NON-EXISTENT-TICKET-999"})
    assert response.status_code == 404


def test_root_redirects_to_docs():
    """Verifies that GET / redirects to /docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in [307, 302]
    assert response.headers["location"] == "/docs"


def test_triage_endpoint_success():
    """Verifies that POST /api/v1/triage triages an existing stored ticket by ID."""
    response = client.post("/api/v1/triage", json={"ticket_id": "TICKET-001"})
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == "TICKET-001"
    assert data["urgency"] in ["critical", "high", "medium", "low"]
    assert data["next_action"] in ["auto-respond", "route_to_specialist", "escalate_to_human"]
    assert "draft_response" in data
    assert len(data["draft_response"]) > 0
    assert "latency_ms" in data
    assert data["latency_ms"] > 0


def test_realtime_triage_endpoint_existing_ticket_continuity():
    """Verifies that messaging with an existing ticket_id attaches to that ticket and preserves context."""
    payload = {
        "ticket_id": "TICKET-001",
        "message": "Following up on my charges - please expedite this!",
    }
    response = client.post("/api/v1/triage/realtime", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Confirms it preserved existing ticket ID and did not overwrite with a random ID
    assert data["ticket_id"] == "TICKET-001"
    assert data["urgency"] in ["critical", "high", "medium", "low"]
    assert "draft_response" in data


def test_realtime_triage_endpoint_new_customer():
    """Verifies that a brand new customer without prior tickets gets a fresh TICKET- ID."""
    payload = {
        "message": "Hello, I am asking a brand new question about your pricing plans.",
    }
    response = client.post("/api/v1/triage/realtime", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"].startswith("TICKET-")
    assert "draft_response" in data




