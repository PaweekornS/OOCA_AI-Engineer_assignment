"""FastAPI Backend Application for the Support Ticket Triage Agent."""

import json
import time
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from langchain_core.messages import ToolMessage

from src.api.schemas import (
    AuditLogResponse,
    HealthResponse,
    RealtimeTriageRequest,
    TriageRequest,
    TriageResponse,
)

from src.config import settings
from src.graph.workflow import create_triage_graph
from src.models.domain import SupportTicket, TicketMessage
from src.tools.base import get_triage_tools
from src.utils.audit_logger import AUDIT_LOG_FILE

# Initialize FastAPI application
app = FastAPI(
    title="Support Ticket Triage Agent API",
    description=(
        "Autonomous AI agent API designed to classify ticket urgency, extract domain metadata, "
        "verify policies/telemetry via internal tools, and determine operational routing next actions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for external dashboards and integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize compiled LangGraph state machine singleton
triage_graph = create_triage_graph()


@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Calculates and attaches execution latency to HTTP response headers."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


@app.get("/", include_in_schema=False)
def root():
    """Redirects root URL directly to interactive Swagger API documentation."""
    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check & readiness probe",
)
def health_check():
    """Verifies service readiness, model configuration, and registered tool connectivity."""
    tools = [t.name for t in get_triage_tools()]
    has_key = bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here")

    return HealthResponse(
        status="ok",
        model=settings.openai_model_name,
        tools_available=tools,
        api_key_configured=has_key,
    )


def _find_existing_ticket(ticket_id: Optional[str]) -> Optional[dict]:
    """Looks up active ticket records from sample_tickets.json by ticket_id."""
    if not ticket_id:
        return None
    sample_file = settings.sample_tickets_path
    if not sample_file.exists():
        return None

    try:
        with open(sample_file, "r", encoding="utf-8") as f:
            tickets = json.load(f)
    except Exception:
        return None

    target = ticket_id.strip().lower()
    for t in tickets:
        t_id = t.get("ticket_id", "").lower()
        if t_id == target or target in t_id or t_id.replace("ticket-", "").lstrip("0") == target:
            return t

    return None


@app.post(
    "/api/v1/triage",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    tags=["Triage"],
    summary="Triage an existing stored support ticket by ID",
)
def triage_ticket(request: TriageRequest):
    """Retrieves an existing support ticket from the repository by ticket_id
    and executes the autonomous LangGraph triage pipeline.
    """
    existing = _find_existing_ticket(request.ticket_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{request.ticket_id}' not found in active repository. Try 'TICKET-001', 'TICKET-002', or 'TICKET-003'.",
        )

    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY environment variable is not configured.",
        )

    start_time = time.perf_counter()

    ticket_id = existing["ticket_id"]
    customer_info = existing.get("customer_info", "")
    domain_messages = [
        TicketMessage(
            message_id=m.get("message_id", f"msg-{i+1}"),
            timestamp_relative=m.get("timestamp_relative", "recently"),
            sender=m.get("sender", "customer"),
            text=m.get("text", ""),
        )
        for i, m in enumerate(existing.get("messages", []))
    ]

    ticket_obj = SupportTicket(
        ticket_id=ticket_id,
        customer_info=customer_info,
        messages=domain_messages,
    )
    thread_text = ticket_obj.format_thread_for_prompt()

    initial_state = {
        "ticket_id": ticket_id,
        "customer_info": customer_info,
        "thread_text": thread_text,
        "language": "en",
        "messages": [],
        "tool_call_count": 0,
        "triage_result": None,
    }

    try:
        final_state = triage_graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph triage execution error: {str(exc)}",
        ) from exc

    decision = final_state.get("triage_result")
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Triage state machine completed without producing a decision.",
        )

    tools_invoked = [
        getattr(m, "name", "tool")
        for m in final_state.get("messages", [])
        if isinstance(m, ToolMessage)
    ]
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    return TriageResponse(
        ticket_id=ticket_id,
        urgency=decision.get("urgency", "medium"),
        next_action=decision.get("next_action", "auto-respond"),
        routing_target=decision.get("routing_target"),
        product=decision.get("product"),
        issue_type=decision.get("issue_type"),
        customer_sentiment=decision.get("customer_sentiment"),
        draft_response=decision.get("draft_response", ""),
        reasoning=decision.get("reasoning", ""),
        tools_invoked=tools_invoked,
        tool_call_count=len(tools_invoked),
        latency_ms=round(latency_ms, 2),
    )


@app.post(
    "/api/v1/triage/realtime",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    tags=["Triage"],
    summary="Real-time live customer chat triage",
)
def triage_realtime_message(request: RealtimeTriageRequest):
    """Triages a real-time live customer message. If an existing ticket_id is supplied,
    the new message is appended to the ongoing ticket thread to preserve context.
    If no ticket_id is supplied, a new ticket session is created.
    """
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENAI_API_KEY environment variable is not configured.",
        )

    start_time = time.perf_counter()

    # Look for existing ticket if ticket_id was specified
    existing = _find_existing_ticket(request.ticket_id) if request.ticket_id else None

    if existing:
        ticket_id = existing["ticket_id"]
        customer_info = existing.get("customer_info", "")
        domain_messages = [
            TicketMessage(
                message_id=m.get("message_id", f"msg-{i+1}"),
                timestamp_relative=m.get("timestamp_relative", "earlier"),
                sender=m.get("sender", "customer"),
                text=m.get("text", ""),
            )
            for i, m in enumerate(existing.get("messages", []))
        ]
        new_turn_idx = len(domain_messages) + 1
        domain_messages.append(
            TicketMessage(
                message_id=f"RT-M{new_turn_idx}",
                timestamp_relative="just now",
                sender="customer",
                text=request.message,
            )
        )
        ticket_obj = SupportTicket(
            ticket_id=ticket_id,
            customer_info=customer_info,
            messages=domain_messages,
        )
        thread_text = ticket_obj.format_thread_for_prompt()
    else:
        import uuid
        ticket_id = request.ticket_id or f"TICKET-{uuid.uuid4().hex[:6].upper()}"
        customer_info = "Inbound Live Support Inquiry"
        thread_text = f"Message 1 (just now) [CUSTOMER]:\n{request.message}"

    initial_state = {
        "ticket_id": ticket_id,
        "customer_info": customer_info,
        "thread_text": thread_text,
        "language": "en",
        "messages": [],
        "tool_call_count": 0,
        "triage_result": None,
    }



    try:
        final_state = triage_graph.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LangGraph triage execution error: {str(exc)}",
        ) from exc

    decision = final_state.get("triage_result")
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Triage state machine completed without producing a decision.",
        )

    tools_invoked = [
        getattr(m, "name", "tool")
        for m in final_state.get("messages", [])
        if isinstance(m, ToolMessage)
    ]
    latency_ms = (time.perf_counter() - start_time) * 1000.0

    return TriageResponse(
        ticket_id=ticket_id,
        urgency=decision.get("urgency", "medium"),
        next_action=decision.get("next_action", "auto-respond"),
        routing_target=decision.get("routing_target"),
        product=decision.get("product"),
        issue_type=decision.get("issue_type"),
        customer_sentiment=decision.get("customer_sentiment"),
        draft_response=decision.get("draft_response", ""),
        reasoning=decision.get("reasoning", ""),
        tools_invoked=tools_invoked,
        tool_call_count=len(tools_invoked),
        latency_ms=round(latency_ms, 2),
    )


@app.get(
    "/api/v1/audit/logs/{ticket_id}",
    response_model=AuditLogResponse,
    tags=["Observability"],
    summary="Retrieve audit logs scoped to a specific ticket ID (Tenant-Safe)",
)
def get_audit_logs_by_ticket(ticket_id: str):
    """Retrieves chronological audit records strictly for the specified ticket ID.
    Enforces tenant privacy and prevents cross-tenant data leakage.
    """
    if not AUDIT_LOG_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit log records found for ticket '{ticket_id}'.",
        )

    matched_records = []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    try:
                        record = json.loads(stripped)
                        if record.get("ticket_id") == ticket_id:
                            matched_records.append(record)
                    except json.JSONDecodeError:
                        continue
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read audit log: {str(exc)}",
        ) from exc

    if not matched_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit logs found for ticket '{ticket_id}'.",
        )

    matched_records.reverse()  # Newest first

    return AuditLogResponse(
        ticket_id=ticket_id,
        total_records=len(matched_records),
        logs=matched_records,
    )

