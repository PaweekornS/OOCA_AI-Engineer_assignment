"""Unit tests for safety guardrails and PII scrubbing."""

import re
import pytest
from src.utils.pii_sanitizer import sanitize_pii


def test_pii_sanitizer_credit_cards():
    """Verifies that credit card numbers in various formats are properly masked."""
    sample_text = (
        "Customer card 4111-2222-3333-4444 was charged. "
        "Also tried card 5500 0000 0000 0004 and 4000000000000002."
    )
    sanitized = sanitize_pii(sample_text)
    assert "4111-2222-3333-4444" not in sanitized
    assert "5500 0000 0000 0004" not in sanitized
    assert "4000000000000002" not in sanitized
    assert "[MASKED_CARD_NUMBER]" in sanitized


def test_pii_sanitizer_cvv_and_email():
    """Verifies CVV and email masking."""
    text = "Send receipt to user@example.com with cvv: 123"
    sanitized = sanitize_pii(text)
    assert "user@example.com" not in sanitized
    assert "[MASKED_EMAIL]" in sanitized
    assert "[MASKED_CVV]" in sanitized


def test_zero_financial_promise_policy_checker():
    """Helper test checking that draft responses cannot promise monetary refunds."""
    bad_responses = [
        "We have refunded $89.97 to your card account immediately.",
        "I have reversed the 3 charges of 29.99 for you.",
        "Your refund has been approved and processed.",
    ]
    good_responses = [
        "These pending charges are temporary bank pre-authorization holds that automatically expire.",
        "I have escalated your ticket to our Billing Operations team to verify the transactions.",
    ]

    violation_pattern = r"\b(?:have refunded|refund has been (?:approved|processed)|reversed\s+(?:the\s+)?(?:\d+\s+)?(?:charges|\$\d+))\b"

    for r in bad_responses:
        assert re.search(violation_pattern, r, flags=re.IGNORECASE) is not None

    for r in good_responses:
        assert re.search(violation_pattern, r, flags=re.IGNORECASE) is None


def test_fixed_escalation_response_templates():
    """Verifies that escalate_to_human produces standardized deterministic templates."""
    from src.utils.response_templates import get_fixed_escalation_response

    thai_thread = "ระบบเข้าไม่ได้ครับ ขึ้น error 500 เช็ค status ให้หน่อย"
    thai_resp = get_fixed_escalation_response(thai_thread)
    assert "On-Call / Incident Management" in thai_resp
    assert "ครับ" in thai_resp

    en_thread = "Server 500 error across all systems"
    en_resp = get_fixed_escalation_response(en_thread)
    assert "On-Call Engineering / Incident Management" in en_resp


def test_slot_filled_route_to_specialist_response():
    """Verifies slot-filling template generation for routed tickets."""
    from src.utils.response_templates import build_route_to_specialist_response

    resp = build_route_to_specialist_response(
        routing_target="Billing Operations",
        issue_summary="disputed duplicate charges of $29.99",
        policy_note="Pending authorization holds typically expire in 3-5 business days.",
        is_thai=False,
    )
    assert "[Billing Operations]" in resp
    assert "disputed duplicate charges of $29.99" in resp
    assert "Pending authorization holds" in resp


def test_clean_email_artifacts():
    """Verifies that email subject lines, Dear salutations, and letter sign-offs are stripped."""
    from src.utils.response_templates import clean_email_artifacts

    raw_email_text = (
        "Subject: [TICKET-001] Re: Payment Failure\n\n"
        "Dear Alex Miller,\n\n"
        "We understand your frustration regarding the pending charges.\n\n"
        "Sincerely,\n"
        "Customer Support Team"
    )
    cleaned = clean_email_artifacts(raw_email_text)
    assert "Subject:" not in cleaned
    assert "Dear Alex Miller" not in cleaned
    assert "Sincerely" not in cleaned
    assert "Customer Support Team" not in cleaned
    assert "We understand your frustration regarding the pending charges." in cleaned


