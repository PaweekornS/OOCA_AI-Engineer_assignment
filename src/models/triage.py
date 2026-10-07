"""Structured output models for the triage decision."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class UrgencyLevel(str, Enum):
    """Urgency classification levels for incoming tickets."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NextAction(str, Enum):
    """Operational next action to take for the ticket."""

    AUTO_RESPOND = "auto-respond"
    ROUTE_TO_SPECIALIST = "route_to_specialist"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class IssueType(str, Enum):
    """Domain issue classification."""

    BILLING_PAYMENT = "billing_payment"
    SYSTEM_OUTAGE = "system_outage"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    ACCOUNT_ACCESS = "account_access"
    GENERAL_INQUIRY = "general_inquiry"


class CustomerSentiment(str, Enum):
    """Customer emotional state inferred from thread progression."""

    FRUSTRATED_ANGRY = "frustrated_angry"
    URGENT_ANXIOUS = "urgent_anxious"
    NEUTRAL = "neutral"
    SATISFIED_POSITIVE = "satisfied_positive"


class TriageDecision(BaseModel):
    """Final structured triage evaluation and action decision."""

    urgency: UrgencyLevel = Field(
        ...,
        description=(
            "Calculated priority tier: 'critical', 'high', 'medium', or 'low'. "
            "Enterprise outages and imminent dispute/deadline risks must receive critical or high."
        ),
    )
    product: str = Field(
        ...,
        description="The product, module, or feature involved (e.g. 'Pro Export', 'Core Platform', 'Appearance/Settings')",
    )
    issue_type: IssueType = Field(
        ...,
        description="Categorical technical or domain classification",
    )
    customer_sentiment: CustomerSentiment = Field(
        ...,
        description="Customer emotional state evaluated across the entire thread progression",
    )
    next_action: NextAction = Field(
        ...,
        description=(
            "Operational next step: 'auto-respond', 'route_to_specialist', or 'escalate_to_human'. "
            "Financial disputes and outages must NOT be auto-respond."
        ),
    )
    routing_target: Optional[str] = Field(
        None,
        description="Department or team target if routed (e.g. 'Billing Operations', 'DevOps On-Call', 'Product Team')",
    )
    reasoning: str = Field(
        ...,
        description="Internal justification synthesizing customer tier, issue severity, KB findings, and guardrails",
    )
    draft_response: Optional[str] = Field(
        None,
        description=(
            "Draft response to the customer. "
            "Must mirror customer language (polite Thai with ครับ/ค่ะ for Thai tickets). "
            "Must NEVER promise monetary refunds or instant financial reversals autonomously."
        ),
    )
