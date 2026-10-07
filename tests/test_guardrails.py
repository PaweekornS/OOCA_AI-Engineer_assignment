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

    violation_pattern = r"\b(?:have refunded|refund has been (?:approved|processed)|reversed the (?:charges|\$\d+))\b"

    for r in bad_responses:
        assert re.search(violation_pattern, r, flags=re.IGNORECASE) is not None

    for r in good_responses:
        assert re.search(violation_pattern, r, flags=re.IGNORECASE) is None
