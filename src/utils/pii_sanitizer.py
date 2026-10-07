"""PII data sanitization utilities to comply with privacy frameworks (PDPA/GDPR)."""

import re


def sanitize_pii(text: str) -> str:
    """Masks sensitive Personal Identifiable Information (PII) such as credit card numbers

    and credentials from customer conversation threads prior to LLM processing.
    """
    if not text:
        return text

    # Mask credit card numbers (13-19 digits with optional hyphens or spaces)
    card_pattern = r"\b(?:\d[ -]*?){13,19}\b"
    sanitized = re.sub(card_pattern, "[MASKED_CARD_NUMBER]", text)

    # Mask CVV / CVC patterns (e.g. CVV: 123, CVC 456)
    cvv_pattern = r"\b(?:cvv|cvc)\s*[:=]?\s*\d{3,4}\b"
    sanitized = re.sub(cvv_pattern, "[MASKED_CVV]", sanitized, flags=re.IGNORECASE)

    # Mask email addresses if present in body
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    sanitized = re.sub(email_pattern, "[MASKED_EMAIL]", sanitized)

    return sanitized
