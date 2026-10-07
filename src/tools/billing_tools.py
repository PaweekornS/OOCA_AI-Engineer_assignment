"""Billing records and payment gateway ledger inspection tool."""

from typing import Optional
from langchain_core.tools import tool


@tool
def check_billing_records(customer_id: Optional[str] = None, query: Optional[str] = None) -> str:
    """Queries payment gateway (e.g. Stripe) transaction logs, billing ledger,
    and subscription invoice status.

    Args:
        customer_id: Customer or Account ID (e.g., 'CUST-001', 'Free User', 'Pro User', or ticket reference).
        query: Optional specific search parameter (e.g. 'pending charges', 'subscription tier', 'refunds').

    Returns:
        Payment gateway ledger summary with transaction states, auth holds, and settled charges.
    """
    param = f"{customer_id or ''} {query or ''}".lower()

    if any(k in param for k in ["001", "free", "upgrade", "charge", "pending", "29.99", "dispute", "hold"]):
        return (
            "--- Payment Gateway (Stripe) Ledger Report ---\n"
            "Account: CUST-FREE-8821 (Free Tier User)\n"
            "Current Plan: Free Tier (Active, tenure: 4 months)\n"
            "Recent Payment Attempts (Last 4 Hours):\n"
            "  * Txn #ch_3N19a (1st attempt): $29.99 USD - FAILED / DECLINED\n"
            "    - Reason: Card declined by issuing bank (insufficient funds / security block)\n"
            "  * Txn #ch_3N19b (2nd attempt): $29.99 USD - PENDING AUTHORIZATION HOLD\n"
            "    - Status: uncaptured_authorization (issuer hold, expires in 48-72h, $0 captured by merchant)\n"
            "  * Txn #ch_3N19c (3rd attempt): $29.99 USD - PENDING AUTHORIZATION HOLD\n"
            "    - Status: uncaptured_authorization (duplicate click hold, expires in 48-72h, $0 captured by merchant)\n"
            "Total Settled/Captured Revenue: $0.00 USD\n"
            "Gateway Summary: No successful subscription upgrade processed. The three $29.99 entries on customer's statement are temporary issuer authorization holds, not debited merchant funds."
        )

    if any(k in param for k in ["002", "ent", "enterprise", "thai"]):
        return (
            "--- Payment Gateway Ledger Report ---\n"
            "Account: CUST-ENT-4501 (Enterprise Thailand)\n"
            "Current Plan: Enterprise (45 Seats, Annual Contract, Invoice Net-30)\n"
            "Billing Status: Good Standing (All invoices settled via wire transfer)\n"
            "Payment Gateway Failures: 0 (No active payment or billing issues)"
        )

    if any(k in param for k in ["003", "pro", "dark"]):
        return (
            "--- Payment Gateway Ledger Report ---\n"
            "Account: CUST-PRO-1092 (Pro User)\n"
            "Current Plan: Pro Tier ($19.99/month, auto-renews monthly)\n"
            "Billing Status: Active & Paid\n"
            "Payment Gateway Failures: 0"
        )

    return (
        f"--- Payment Gateway Ledger for '{param.strip() or 'Default'}' ---\n"
        "Account Status: Active\n"
        "No failed or pending transactions found for this account in the last 30 days."
    )
