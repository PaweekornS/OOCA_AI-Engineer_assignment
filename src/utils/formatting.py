import sys
from typing import Any, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(legacy_windows=False)



def print_banner():
    """Prints the application banner."""
    console.print(
        Panel(
            "[bold cyan]OOCA AI Support Ticket Triage Agent[/bold cyan]\n"
            "[dim]LangGraph State Machine • OpenAI GPT • Pydantic v2 Architecture[/dim]",
            border_style="cyan",
            expand=False,
        )
    )


def print_ticket_overview(ticket_dict: Dict[str, Any]):
    """Renders a structured card displaying the inbound ticket and message thread."""
    ticket_id = ticket_dict.get("ticket_id", "N/A")
    cust_info = ticket_dict.get("customer_info", "N/A")
    messages = ticket_dict.get("messages", [])

    table = Table(title=f"Inbound Ticket: {ticket_id}", border_style="blue", show_lines=True)
    table.add_column("Turn", style="cyan", width=12)
    table.add_column("Timestamp", style="magenta", width=22)
    table.add_column("Sender", style="green", width=10)
    table.add_column("Message Content", style="white")

    for i, msg in enumerate(messages, start=1):
        table.add_row(
            f"Message {i}",
            msg.get("timestamp_relative", "N/A"),
            msg.get("sender", "customer").upper(),
            msg.get("text", ""),
        )

    console.print(Panel(f"[bold]Customer Context:[/bold] {cust_info}", border_style="dim"))
    console.print(table)


def print_triage_decision(decision: Dict[str, Any], state: Any = None):
    """Renders the final triage decision as a formatted Rich table and response card."""
    urgency = decision.get("urgency", "low").lower()
    urgency_color = {
        "critical": "bold red",
        "high": "bold yellow",
        "medium": "bold blue",
        "low": "bold green",
    }.get(urgency, "white")

    action = decision.get("next_action", "auto-respond")
    action_color = {
        "escalate_to_human": "bold red",
        "route_to_specialist": "bold yellow",
        "auto-respond": "bold green",
    }.get(action, "white")

    summary_table = Table(title="Triage Evaluation Summary", border_style="cyan", show_lines=True)
    summary_table.add_column("Attribute", style="bold cyan", width=20)
    summary_table.add_column("Evaluation Output", width=65)

    summary_table.add_row("Urgency", Text(urgency.upper(), style=urgency_color))
    summary_table.add_row("Next Action", Text(action, style=action_color))
    summary_table.add_row("Routing Target", str(decision.get("routing_target") or "N/A"))
    summary_table.add_row("Product / Module", str(decision.get("product", "N/A")))
    summary_table.add_row("Issue Type", str(decision.get("issue_type", "N/A")))
    summary_table.add_row("Customer Sentiment", str(decision.get("customer_sentiment", "N/A")))

    if state and isinstance(state, dict):
        from langchain_core.messages import ToolMessage
        tools_called = [
            getattr(m, "name", "tool")
            for m in state.get("messages", [])
            if isinstance(m, ToolMessage)
        ]
        tools_display = (
            f"{', '.join(tools_called)} ({len(tools_called)} call{'s' if len(tools_called) > 1 else ''})"
            if tools_called
            else "None (Resolved via prompt context)"
        )
        summary_table.add_row("Tools Invoked", Text(tools_display, style="bold magenta"))

    console.print(summary_table)

    # Reasoning card
    console.print(
        Panel(
            decision.get("reasoning", "N/A"),
            title="[bold yellow]Diagnostic Reasoning[/bold yellow]",
            border_style="yellow",
        )
    )

    # Draft response card
    draft = decision.get("draft_response")
    if draft:
        console.print(
            Panel(
                draft,
                title="[bold green]Customer Draft Response[/bold green]",
                border_style="green",
            )
        )

    console.print("[dim]  📄 Audit Log: Record appended to logs/triage_audit.jsonl[/dim]\n")

