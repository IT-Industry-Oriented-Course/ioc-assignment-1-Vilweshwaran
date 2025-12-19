#!/usr/bin/env python3
"""
Clinical Workflow Agent - Command Line Interface.

Usage:
    python -m app.cli "Schedule a cardiology follow-up for patient Ravi Kumar next week"
    python -m app.cli --dry-run "Book appointment for patient 12345 on Monday"
    python -m app.cli --interactive
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON as RichJSON
from rich.table import Table
from rich.markdown import Markdown

from src.agent import ClinicalWorkflowAgent, AgentResponse


console = Console()


def print_response(response: AgentResponse):
    """Pretty print an agent response."""
    
    if response.safety_refused:
        console.print(Panel(
            f"[bold red]⚠️ Request Refused[/bold red]\n\n{response.message}\n\n"
            f"[yellow]Suggested action:[/yellow] {response.data.get('suggested_action', 'N/A')}",
            title="Safety Guardrail",
            border_style="red"
        ))
        return
    
    if not response.success:
        console.print(Panel(
            f"[yellow]⚠️ Could not complete request[/yellow]\n\n{response.message}",
            title="Agent Response",
            border_style="yellow"
        ))
        return
    
    # Success response
    status = "[bold green]✓ Success[/bold green]"
    if response.dry_run:
        status += " [cyan](DRY RUN)[/cyan]"
    
    console.print(Panel(
        f"{status}\n\n{response.message}",
        title="Agent Response",
        border_style="green"
    ))
    
    # Print function calls
    if response.function_calls:
        console.print("\n[bold]Function Calls Made:[/bold]")
        for i, fc in enumerate(response.function_calls, 1):
            console.print(f"  {i}. [cyan]{fc.get('name')}[/cyan]({json.dumps(fc.get('arguments', {}))})")
    
    # Print results
    if response.data and "results" in response.data:
        console.print("\n[bold]Results:[/bold]")
        for result in response.data["results"]:
            func_name = result.get("function", "unknown")
            func_result = result.get("result", {})
            
            # Create a panel for each result
            if func_result.get("resourceType") == "Bundle":
                # Handle FHIR Bundle results
                total = func_result.get("total", 0)
                entries = func_result.get("entry", [])
                
                table = Table(title=f"{func_name} Results ({total} found)")
                
                if entries:
                    first_resource = entries[0].get("resource", {})
                    for key in first_resource.keys():
                        if key != "resourceType":
                            table.add_column(key.replace("_", " ").title())
                    
                    for entry in entries[:5]:  # Show max 5
                        resource = entry.get("resource", {})
                        row = []
                        for key in first_resource.keys():
                            if key != "resourceType":
                                val = resource.get(key, "")
                                if isinstance(val, list):
                                    if val and isinstance(val[0], dict):
                                        if "family" in val[0]:  # Name
                                            val = f"{' '.join(val[0].get('given', []))} {val[0].get('family', '')}"
                                        else:
                                            val = str(val[0])
                                    else:
                                        val = ", ".join(str(v) for v in val)
                                row.append(str(val)[:50])
                        table.add_row(*row)
                    
                    console.print(table)
                else:
                    console.print(f"  [dim]No results found[/dim]")
            
            elif func_result.get("resourceType") == "Coverage":
                # Insurance coverage result
                eligible = func_result.get("isEligible", False)
                status = "[green]ELIGIBLE[/green]" if eligible else "[red]NOT ELIGIBLE[/red]"
                console.print(Panel(
                    f"Status: {status}\n"
                    f"Plan: {func_result.get('planName', 'N/A')}\n"
                    f"Payor: {', '.join(func_result.get('payor', []))}\n"
                    f"Copay: ${func_result.get('copayAmount', 'N/A')}\n"
                    f"Reason: {func_result.get('eligibilityReason', 'N/A')}",
                    title="Insurance Eligibility",
                    border_style="blue"
                ))
            
            elif func_result.get("success") and "appointment" in func_result:
                # Appointment booking result
                apt = func_result.get("appointment", {})
                dry_run_note = " [DRY RUN]" if apt.get("_dryRun") else ""
                console.print(Panel(
                    f"[bold]Appointment ID:[/bold] {apt.get('id', 'N/A')}{dry_run_note}\n"
                    f"[bold]Status:[/bold] {apt.get('status', 'N/A')}\n"
                    f"[bold]Specialty:[/bold] {apt.get('specialty', 'N/A')}\n"
                    f"[bold]Provider:[/bold] {apt.get('practitionerName', 'N/A')}\n"
                    f"[bold]Location:[/bold] {apt.get('location', 'N/A')}\n"
                    f"[bold]Time:[/bold] {apt.get('start', 'N/A')}\n"
                    f"[bold]Reason:[/bold] {apt.get('reason', 'N/A')}",
                    title="📅 Appointment Booked",
                    border_style="green"
                ))
            
            elif func_result.get("error"):
                console.print(Panel(
                    f"[red]Error:[/red] {func_result.get('message', 'Unknown error')}",
                    title=f"{func_name} Error",
                    border_style="red"
                ))
            
            else:
                # Generic result
                console.print(Panel(
                    RichJSON(json.dumps(func_result, indent=2, default=str)),
                    title=func_name,
                    border_style="blue"
                ))


def run_interactive(agent: ClinicalWorkflowAgent, dry_run: bool = False):
    """Run the agent in interactive mode."""
    console.print(Panel(
        "[bold cyan]Clinical Workflow Agent[/bold cyan]\n\n"
        "I can help you with:\n"
        "• Searching for patients\n"
        "• Checking insurance eligibility\n"
        "• Finding available appointment slots\n"
        "• Booking appointments\n\n"
        "[dim]Type 'quit' or 'exit' to leave, 'help' for examples[/dim]",
        title="Welcome",
        border_style="cyan"
    ))
    
    if dry_run:
        console.print("[yellow]⚠️ DRY RUN MODE - No actual changes will be made[/yellow]\n")
    
    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("[dim]Goodbye![/dim]")
                break
            
            if user_input.lower() == 'help':
                console.print(Panel(
                    "**Example requests:**\n\n"
                    "• \"Search for patient Ravi Kumar\"\n"
                    "• \"Check insurance eligibility for patient P001 for cardiology\"\n"
                    "• \"Find available cardiology slots for next week\"\n"
                    "• \"Schedule a cardiology follow-up for patient Ravi Kumar next week\"\n"
                    "• \"Book appointment for patient P001 at slot SLOT-CARD-20241223-001\"\n\n"
                    "**Commands:**\n"
                    "• `functions` - Show available functions\n"
                    "• `audit` - Show audit log summary\n"
                    "• `quit` - Exit the agent",
                    title="Help",
                    border_style="blue"
                ))
                continue
            
            if user_input.lower() == 'functions':
                table = Table(title="Available Functions")
                table.add_column("Function", style="cyan")
                table.add_column("Description")
                for func in agent.get_available_functions():
                    table.add_row(func["name"], func["description"])
                console.print(table)
                continue
            
            if user_input.lower() == 'audit':
                summary = agent.get_audit_summary()
                console.print(Panel(
                    f"Session ID: {summary.get('session_id')}\n"
                    f"Total entries: {summary.get('total_entries')}\n"
                    f"Actions: {json.dumps(summary.get('action_counts', {}), indent=2)}\n"
                    f"Log path: {summary.get('log_path')}",
                    title="Audit Summary",
                    border_style="magenta"
                ))
                continue
            
            # Process the request
            console.print("\n[dim]Processing...[/dim]")
            response = agent.process_request(user_input, dry_run=dry_run)
            print_response(response)
            
        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")


def main():
    parser = argparse.ArgumentParser(
        description="Clinical Workflow Agent - Automate healthcare administrative tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app.cli "Search for patient Ravi Kumar"
  python -m app.cli "Schedule a cardiology follow-up for patient Ravi Kumar next week"
  python -m app.cli --dry-run "Book appointment for patient P001"
  python -m app.cli --interactive
        """
    )
    
    parser.add_argument(
        "request",
        nargs="?",
        help="Natural language request to process"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Run in dry-run mode (no actual changes made)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = ClinicalWorkflowAgent(dry_run=args.dry_run)
    
    if args.interactive:
        run_interactive(agent, dry_run=args.dry_run)
    elif args.request:
        response = agent.process_request(args.request)
        
        if args.json:
            output = {
                "success": response.success,
                "message": response.message,
                "data": response.data,
                "function_calls": response.function_calls,
                "safety_refused": response.safety_refused,
                "dry_run": response.dry_run,
                "audit_session_id": response.audit_session_id
            }
            print(json.dumps(output, indent=2, default=str))
        else:
            print_response(response)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
