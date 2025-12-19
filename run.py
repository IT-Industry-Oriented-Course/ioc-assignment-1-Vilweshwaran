#!/usr/bin/env python3
"""
Main entry point for the Clinical Workflow Agent.
Supports both CLI and Streamlit modes.
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Clinical Workflow Agent - Healthcare Administrative Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=["cli", "web"],
        default="cli",
        help="Run mode: 'cli' for command line, 'web' for Streamlit UI (default: cli)"
    )
    
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Run in dry-run mode"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run CLI in interactive mode"
    )
    
    parser.add_argument(
        "request",
        nargs="?",
        help="Natural language request (CLI mode only)"
    )
    
    args, unknown = parser.parse_known_args()
    
    if args.mode == "web":
        # Launch Streamlit
        import subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app/streamlit_ui.py"])
    else:
        # Run CLI
        from app.cli import main as cli_main
        
        # Reconstruct sys.argv for CLI
        cli_args = []
        if args.dry_run:
            cli_args.append("--dry-run")
        if args.interactive:
            cli_args.append("--interactive")
        if args.request:
            cli_args.append(args.request)
        
        # Check for json flag in unknown args since argparse might not have caught it if it was after the request
        if "--json" in sys.argv or "-j" in sys.argv:
             cli_args.append("--json")
        
        sys.argv = ["run.py"] + cli_args
        cli_main()


if __name__ == "__main__":
    main()
