"""Standard response templates and slot-filling generators for triage actions."""

import re
from typing import Optional


def is_thai_text(text: str) -> bool:
    """Detects whether text contains Thai characters."""
    return bool(re.search(r"[\u0e00-\u0e7f]", text))


# Fixed templates for Sev-1 human escalation
FIXED_ESCALATE_TEMPLATE_THAI = (
    "ทางเราได้รับเรื่องเหตุขัดข้องเร่งด่วนนี้แล้ว และได้ทำการส่งต่อเรื่องให้กับทีมวิศวกร On-Call / Incident Management "
    "เข้าดำเนินการตรวจสอบและแก้ไขปัญหาของท่านทันทีครับ เจ้าหน้าที่จะรีบอัปเดตสถานะความคืบหน้าให้ท่านทราบโดยเร็วที่สุด"
)

FIXED_ESCALATE_TEMPLATE_EN = (
    "We have received your critical incident report and have immediately escalated this ticket to our "
    "On-Call Engineering / Incident Management team for urgent investigation. Our engineers are actively "
    "looking into this and we will provide an update as soon as possible."
)


def get_fixed_escalation_response(language_or_text: str) -> str:
    """Returns the standardized, fixed template response for escalate_to_human cases."""
    if str(language_or_text).lower() in ("th", "thai") or is_thai_text(str(language_or_text)):
        return FIXED_ESCALATE_TEMPLATE_THAI
    return FIXED_ESCALATE_TEMPLATE_EN


def build_route_to_specialist_response(
    routing_target: str,
    issue_summary: str,
    policy_note: Optional[str] = None,
    is_thai: bool = False,
) -> str:
    """Builds a slot-filled template response for tickets routed to domain specialists.

    Slots:
    - {routing_target}: Department routed to (e.g. 'Billing Operations')
    - {issue_summary}: Specific issue being routed (e.g. 'multiple pending charges and Pro feature access')
    - {policy_note}: Policy explanation or preliminary guidance without financial commitments
    """
    target = routing_target or ("Billing Operations" if not is_thai else "ฝ่ายตรวจสอบการชำระเงิน")
    summary = issue_summary or ("your inquiry" if not is_thai else "เรื่องที่ท่านแจ้งเข้ามา")
    note = f" {policy_note.strip()}" if policy_note else ""

    if is_thai:
        return (
            f"ขอบคุณที่ติดต่อฝ่ายสนับสนุนครับ ทางเราเข้าใจถึงความเร่งด่วนในประเด็น {summary} "
            f"ขณะนี้เราได้ส่งต่อเคสของท่านไปยังทีม [{target}] เพื่อเข้าตรวจสอบเป็นกรณีเร่งด่วนแล้วครับ{note} "
            f"เจ้าหน้าที่ผู้เชี่ยวชาญจะเร่งตรวจสอบและติดต่อกลับโดยเร็วที่สุดครับ"
        )

    return (
        f"Thank you for contacting support. We understand the urgency regarding {summary}. "
        f"Your ticket has been prioritized and routed directly to our [{target}] team for specialized investigation.{note} "
        f"A specialist will follow up with you directly as an expedited priority."
    )


def clean_email_artifacts(text: str) -> str:
    """Strips email-style headers, formal salutations, and letter sign-offs from in-ticket responses."""
    if not text:
        return text

    cleaned = text.strip()

    # Remove subject lines (e.g. Subject: [Ticket-001] Urgent Billing Issue)
    cleaned = re.sub(r"^(?:Subject|Re|Fwd)\s*:[^\n]*\n+", "", cleaned, flags=re.IGNORECASE)

    # Remove formal letter salutations (e.g. Dear Alex Miller, / Dear Customer,)
    cleaned = re.sub(r"^Dear\s+[^,\n]+,\s*\n*", "", cleaned, flags=re.IGNORECASE)

    # Remove email sign-offs at the end
    sign_off_patterns = [
        r"\n+(?:Sincerely|Best regards|Warm regards|Regards|Yours truly|Kind regards)\s*,?\s*(\n+[^\n]+)?$",
        r"\n+(?:ทีมงานฝ่ายบริการลูกค้า|ฝ่ายบริการลูกค้า|Customer Support Team|The Support Team)\s*$",
    ]
    for pattern in sign_off_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()
