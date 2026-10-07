"""Unit tests for knowledge base lookup and system telemetry tools."""

import pytest
from src.tools.knowledge_tools import lookup_knowledge_base
from src.tools.system_tools import check_system_status


def test_kb_lookup_billing_hold():
    """Verifies that billing hold queries surface the billing refund policy."""
    result = lookup_knowledge_base.invoke({"query": "pending authorization hold duplicate card charges"})
    assert "billing_refund_policy.md" in result
    assert "Pending" in result or "Hold" in result
    assert "Zero Financial Promises" in result or "strictly prohibited" in result


def test_kb_lookup_sev1_outage():
    """Verifies that outage queries surface the Sev-1 incident runbook."""
    result = lookup_knowledge_base.invoke({"query": "HTTP 500 regional outage status page delay"})
    assert "incident_sev1_runbook.md" in result
    assert "Status Page Discrepancy Rule" in result or "500" in result


def test_kb_lookup_macos_dark_mode():
    """Verifies that macOS theme bug queries surface the known issues guide."""
    result = lookup_knowledge_base.invoke({"query": "macOS dark mode system default theme sync bug"})
    assert "macos_desktop_known_issues.md" in result
    assert "KB-2048" in result
    assert "Workaround" in result


def test_kb_lookup_deliberate_knowledge_gap():
    """Verifies that completely out-of-domain queries return a 'No documentation found' notice."""
    result = lookup_knowledge_base.invoke({"query": "cryptocurrency bitcoin mining blockchain token"})
    assert "No relevant documentation found" in result


def test_kb_lookup_unreleased_feature_scheduling():
    """Verifies that querying scheduled dark mode confirms it is an unreleased feature request."""
    result = lookup_knowledge_base.invoke({"query": "time-based theme scheduling auto switch"})
    assert "Unreleased Features" in result or "not currently supported" in result



def test_system_status_asia_telemetry():
    """Verifies that system status tool surfaces edge errors for Asia/Thailand."""
    result = check_system_status.invoke({"region": "Thailand"})
    assert "Asia / Thailand" in result
    assert "DEGRADED" in result or "500" in result
    assert "status.company.com" in result


def test_system_status_us_healthy():
    """Verifies healthy telemetry for US-East."""
    result = check_system_status.invoke({"region": "US-East"})
    assert "US-East" in result
    assert "HEALTHY" in result


def test_check_billing_records_pending_hold():
    """Verifies billing tool detects uncaptured authorization holds for Scenario 1."""
    from src.tools.billing_tools import check_billing_records
    result = check_billing_records.invoke({"customer_id": "TICKET-001", "query": "pending charges"})
    assert "Payment Gateway" in result
    assert "uncaptured_authorization" in result
    assert "29.99" in result


def test_check_ticket_history_enterprise_sla():
    """Verifies ticket history tool returns enterprise SLA commitments for Scenario 2."""
    from src.tools.ticket_tools import check_ticket_history
    result = check_ticket_history.invoke({"customer_id": "Enterprise Thailand"})
    assert "CRM Customer Interaction History" in result
    assert "Enterprise" in result
    assert "99.99%" in result

