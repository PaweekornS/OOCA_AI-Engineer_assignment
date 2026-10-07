"""Domain models for incoming customer support tickets."""

from typing import List, Literal
from pydantic import BaseModel, Field


class TicketMessage(BaseModel):
    """An individual message in a multi-turn support thread."""

    message_id: str = Field(..., description="Unique message identifier, e.g. 'T1-M1'")
    timestamp_relative: str = Field(
        ..., description="Relative timestamp, e.g. '3 hours ago', 'just now'"
    )
    sender: Literal["customer", "agent", "system"] = Field(
        "customer", description="Sender role of the message"
    )
    text: str = Field(..., description="The message content text")


class SupportTicket(BaseModel):
    """A customer support ticket with account context and multi-turn message history."""

    ticket_id: str = Field(..., description="Unique ticket identifier, e.g. 'TICKET-001'")
    customer_info: str = Field(
        ...,
        description=(
            "Account context and subscription tier, e.g. "
            "'Enterprise plan, Thailand region, 45 seats, 8 months customer, first critical issue'"
        ),
    )
    messages: List[TicketMessage] = Field(
        ..., description="Chronologically ordered list of conversation messages"
    )

    def format_thread_for_prompt(self) -> str:
        """Formats the ticket conversation thread into a readable prompt block."""
        header = f"Ticket ID: {self.ticket_id}\nCustomer Context: {self.customer_info}\n\nConversation Thread:"
        thread_lines = [
            f"[{msg.timestamp_relative}] {msg.sender.upper()}: {msg.text}"
            for msg in self.messages
        ]
        return f"{header}\n" + "\n".join(thread_lines)
