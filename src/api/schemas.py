"""Pydantic schemas for the Support Ticket Triage Backend API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.models.triage import CustomerSentiment, IssueType, NextAction, UrgencyLevel


class TicketMessageInput(BaseModel):
    """An individual message turn within the support ticket."""

    message_id: Optional[str] = Field(None, description="Optional unique identifier for the message")
    timestamp_relative: Optional[str] = Field(None, description="Relative timestamp (e.g. '2 hours ago', 'just now')")
    sender: str = Field("customer", description="Sender of the message: 'customer' or 'agent'")
    text: str = Field(..., description="Message text content")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message_id": "M-1",
                "timestamp_relative": "2 hours ago",
                "sender": "customer",
                "text": "My payment failed when I tried to upgrade to Pro. Can you check what's wrong?",
            }
        }
    }


class TriageRequest(BaseModel):
    """Inbound request payload to triage an existing stored support ticket."""

    ticket_id: str = Field(..., description="Ticket tracking ID to triage (e.g. 'TICKET-001', 'TICKET-002')", min_length=1)

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticket_id": "TICKET-001",
            }
        }
    }


class TriageResponse(BaseModel):
    """Structured decision output produced by the AI Triage Agent."""

    ticket_id: str = Field(..., description="Ticket ID that was triaged")
    urgency: UrgencyLevel = Field(..., description="Assessed ticket urgency priority")
    next_action: NextAction = Field(..., description="Operational triage routing action")
    routing_target: Optional[str] = Field(None, description="Target team or specialist")
    product: Optional[str] = Field(None, description="Identified product or functional module")
    issue_type: Optional[IssueType] = Field(None, description="Domain category classification")
    customer_sentiment: Optional[CustomerSentiment] = Field(None, description="Customer emotional state")
    draft_response: str = Field(..., description="Automated in-ticket draft response for the customer")
    reasoning: str = Field(..., description="Internal diagnostic justification for the triage decision")
    tools_invoked: List[str] = Field(default_factory=list, description="List of internal tools executed")
    tool_call_count: int = Field(0, description="Number of tool calls executed")
    latency_ms: float = Field(..., description="Total execution time in milliseconds")


class HealthResponse(BaseModel):
    """Health check diagnostic response."""

    status: str = Field("ok", description="API health status")
    model: str = Field(..., description="Configured OpenAI GPT model")
    tools_available: List[str] = Field(..., description="Registered agent tools")
    api_key_configured: bool = Field(..., description="Whether OPENAI_API_KEY is present")


class RealtimeTriageRequest(BaseModel):
    """Real-time inbound customer message from live chat or mobile app."""

    message: str = Field(..., description="Real-time message text submitted by the customer", min_length=1)
    ticket_id: Optional[str] = Field(None, description="Optional existing ticket ID to append to (e.g. 'TICKET-001')")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ticket_id": "TICKET-001",
                "message": "ตามเรื่องให้หน่อยครับ ใกล้ถึงเวลาพรีเซนต์แล้ว!",
            }
        }
    }



class AuditLogResponse(BaseModel):
    """Audit log inspection response scoped to a specific ticket."""

    ticket_id: str = Field(..., description="Target ticket ID")
    total_records: int = Field(..., description="Number of audit records found for this ticket")
    logs: List[Dict[str, Any]] = Field(..., description="Chronological audit log records for the ticket")

