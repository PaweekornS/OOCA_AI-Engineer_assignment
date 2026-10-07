"""CRM support ticket history and SLA interaction inspection tool."""

from typing import Optional
from langchain_core.tools import tool


@tool
def check_ticket_history(customer_id: Optional[str] = None, query: Optional[str] = None) -> str:
    """Queries CRM customer support history, prior tickets, SLA contract tier,
    and historical escalation records.

    Args:
        customer_id: Customer or Account ID (e.g., 'CUST-001', 'Enterprise', 'Pro User', or ticket reference).
        query: Optional search keyword (e.g., 'past tickets', 'escalations', 'sla').

    Returns:
        CRM customer support interaction summary and historical ticket log.
    """
    param = f"{customer_id or ''} {query or ''}".lower()

    if any(k in param for k in ["001", "free", "upgrade"]):
        return (
            "--- CRM Customer Interaction History ---\n"
            "Customer ID: CUST-FREE-8821\n"
            "Tenure: 4 months on Free Tier\n"
            "Total Prior Support Tickets (Past 12 Months): 0 (First-time support contact)\n"
            "Prior Escalations / Disputes: 0\n"
            "Account Standing: Good standing, high churn risk due to recent failed checkout."
        )

    if any(k in param for k in ["002", "ent", "enterprise", "thai"]):
        return (
            "--- CRM Customer Interaction History ---\n"
            "Customer ID: CUST-ENT-4501 (Enterprise Asia / Thailand)\n"
            "Contract Tier: Enterprise (45 Seats, 8 months tenure)\n"
            "Contract SLA Commitment: 99.99% Uptime, Sev-1 Response < 15 minutes\n"
            "Dedicated Account Manager: APAC Enterprise Success Desk\n"
            "Total Prior Support Tickets: 2 (both routine onboarding inquiries, resolved successfully)\n"
            "Prior Critical Incidents: 0 (This is their first critical outage ticket)"
        )

    if any(k in param for k in ["003", "pro", "dark"]):
        return (
            "--- CRM Customer Interaction History ---\n"
            "Customer ID: CUST-PRO-1092\n"
            "Contract Tier: Pro Plan (5 months tenure, daily active user)\n"
            "Total Prior Support Tickets: 0 (First support contact)\n"
            "Feature Voting History: Upvoted 'Desktop Dark Theme' on public roadmap (Vote ID #4182)\n"
            "Client App Version: Desktop macOS v2.4.1 (Build 890)"
        )

    return (
        f"--- CRM Interaction History for '{param.strip() or 'Default'}' ---\n"
        "Prior Tickets Found: 0\n"
        "SLA Tier: Standard Support (24-hour response target)\n"
        "Account Standing: Normal"
    )
