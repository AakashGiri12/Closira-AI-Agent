"""
Closira — AI Customer Support Workflow
Entry point: CLI conversation loop for Bloom Aesthetics Clinic.

Usage:
    python main.py

Commands during conversation:
    quit / exit / bye  →  triggers session summary then exits
    Ctrl+C             →  force-exits without summary
"""

import json
import os
import sys
import warnings
from pathlib import Path

from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=FutureWarning)

from workflow.agent import ClosiraAgent
from workflow.state import ConversationState

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent
SOP_PATH = ROOT / "sop" / "bloom_aesthetics.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
GREY = "\033[90m"
MAGENTA = "\033[95m"


def print_header():
    print(f"\n{CYAN}{BOLD}")
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║     🌸  Bloom Aesthetics — AI Support Chat  🌸   ║")
    print("  ║         Powered by Closira · Aria v1.0           ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print(f"{RESET}")
    print(f"{GREY}  Type 'quit', 'exit', or 'bye' to end the session.{RESET}\n")


def print_aria(text: str):
    print(f"\n{MAGENTA}{BOLD}  Aria :{RESET} {text}\n")


def print_escalation_banner(reason: str):
    print(f"\n{RED}{BOLD}  ⚠️  [ESCALATED: {reason}]{RESET}\n")


def print_stage(stage: str):
    colour = {
        "faq": GREEN,
        "qualifying": YELLOW,
        "escalated": RED,
        "closing": CYAN,
    }.get(stage, GREY)
    print(f"  {colour}{GREY}[stage: {stage}]{RESET}", end="")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    # 1. Load environment
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print(
            f"\n{RED}ERROR: GOOGLE_API_KEY not set. "
            "Please create a .env file with your key from "
            "https://aistudio.google.com/app/apikeys{RESET}\n"
        )
        sys.exit(1)

    # 2. Load SOP
    if not SOP_PATH.exists():
        print(f"\n{RED}ERROR: SOP file not found at {SOP_PATH}{RESET}\n")
        sys.exit(1)

    with open(SOP_PATH) as f:
        sop = json.load(f)

    # 3. Initialise agent and state
    agent = ClosiraAgent(api_key=api_key, sop=sop)
    state = ConversationState()

    print_header()

    # 4. Opening greeting (first turn with empty-ish prompt)
    opening = agent.run_turn(
        "A new customer has just started a conversation. Greet them warmly and offer to help.",
        state,
    )
    print_aria(opening)

    # 5. Conversation loop
    while True:
        try:
            user_input = input(f"{CYAN}{BOLD}  You   :{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Session interrupted. Goodbye!")
            break

        if not user_input:
            continue

        # Check for exit commands
        if user_input.lower() in {"quit", "exit", "bye", "goodbye"}:
            print(f"\n{GREY}  Generating session summary...{RESET}")
            summary_response = agent.force_summary(state)
            print_aria(summary_response)
            print(f"\n{GREEN}  Session ended. Goodbye! 🌸{RESET}\n")
            break

        # Run one conversation turn
        response = agent.run_turn(user_input, state)

        # Show escalation banner if one was logged this turn
        if state.escalated_this_turn():
            latest = state.escalation_log[-1]
            print_escalation_banner(latest.reason)

        print_aria(response)


if __name__ == "__main__":
    main()
