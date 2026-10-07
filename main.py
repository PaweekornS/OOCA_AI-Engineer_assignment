import argparse
import json
import sys
from pathlib import Path
from rich.console import Console

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.config import settings
from src.graph.workflow import create_triage_graph
from src.models.domain import SupportTicket, TicketMessage
from src.utils.formatting import (
    print_banner,
    print_ticket_overview,
    print_triage_decision,
)

console = Console(legacy_windows=False)


def load_sample_tickets():
    """Loads benchmark tickets from data/sample_tickets.json."""
    if not settings.sample_tickets_path.exists():
        console.print(f"[red]Error: Sample tickets file not found at {settings.sample_tickets_path}[/red]")
        sys.exit(1)

    with open(settings.sample_tickets_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_ticket_triage(ticket_raw: dict, graph_app, json_output: bool = False):
    """Processes an individual ticket through the LangGraph pipeline."""
    ticket_id = ticket_raw.get("ticket_id")
    customer_info = ticket_raw.get("customer_info", "")
    messages_raw = ticket_raw.get("messages", [])

    # Reconstruct domain model to leverage its thread formatting
    messages = [TicketMessage(**m) for m in messages_raw]
    ticket_obj = SupportTicket(
        ticket_id=ticket_id,
        customer_info=customer_info,
        messages=messages,
    )
    thread_text = ticket_obj.format_thread_for_prompt()

    if not json_output:
        console.print("\n" + "=" * 80)
        print_ticket_overview(ticket_raw)
        console.print("[dim]Running LangGraph triage agent...[/dim]")

    # Initial state
    initial_state = {
        "ticket_id": ticket_id,
        "customer_info": customer_info,
        "thread_text": thread_text,
        "language": "en",
        "messages": [],
        "tool_call_count": 0,
        "triage_result": None,
    }

    final_state = graph_app.invoke(initial_state)
    decision = final_state.get("triage_result") or {}

    if json_output:
        print(json.dumps({"ticket_id": ticket_id, "triage_decision": decision}, indent=2, ensure_ascii=False))
    else:
        print_triage_decision(decision, state=final_state)

    return decision


def main():
    """CLI argument parsing and runner dispatch."""
    parser = argparse.ArgumentParser(
        description="OOCA AI Support Ticket Triage Agent - Terminal Evaluation Runner"
    )
    parser.add_argument(
        "--ticket",
        "-t",
        type=str,
        help="Specific ticket number (1, 2, 3) or Ticket ID (TICKET-001) to run",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Run all sample benchmark tickets sequentially (default)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of Rich formatted tables",
    )

    args = parser.parse_args()

    # Pre-flight check for OpenAI API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        console.print(
            "[bold red]Configuration Alert:[/bold red] OPENAI_API_KEY is not set.\n"
            "Please provide your OpenAI API key either in `.env` file or export it via:\n"
            "  [cyan]$env:OPENAI_API_KEY='sk-...'[/cyan] (PowerShell) or [cyan]export OPENAI_API_KEY='sk-... '[/cyan] (Bash)\n"
        )
        sys.exit(1)

    tickets = load_sample_tickets()

    if not args.json:
        print_banner()

    # Compile the LangGraph state machine once
    graph_app = create_triage_graph()

    if args.ticket:
        target_str = str(args.ticket).strip()
        matched = None
        for t in tickets:
            if target_str in t.get("ticket_id", "") or target_str == t.get("ticket_id", "")[-1:]:
                matched = t
                break
        if not matched:
            console.print(f"[red]Ticket '{args.ticket}' not found. Available: 1, 2, 3[/red]")
            sys.exit(1)
        run_ticket_triage(matched, graph_app, json_output=args.json)
    else:
        # Default: Run all tickets
        for t in tickets:
            run_ticket_triage(t, graph_app, json_output=args.json)


if __name__ == "__main__":
    main()
