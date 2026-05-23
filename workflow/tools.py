"""
Tool definitions for the Bloom Aesthetics AI workflow.

Each tool has:
  - SCHEMA: the JSON schema dict passed to Anthropic's API
  - A handler function that executes the tool logic and updates ConversationState
"""

import json
from datetime import datetime

from workflow.state import ConversationState

# ---------------------------------------------------------------------------
# Qualification questions (ordered)
# ---------------------------------------------------------------------------
QUALIFICATION_QUESTIONS = [
    {
        "label": "treatment_interest",
        "question": "What brings you in today — is there a specific concern or treatment you're interested in?",
    },
    {
        "label": "prior_experience",
        "question": "Have you had any aesthetic treatments before, or would this be your first time?",
    },
    {
        "label": "referral_source",
        "question": "How did you hear about Bloom Aesthetics?",
    },
]


# ---------------------------------------------------------------------------
# Tool schemas (passed to Anthropic API)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "lookup_sop",
        "description": (
            "Search the Bloom Aesthetics SOP for information about services, pricing, "
            "hours, booking, staff, policies, or FAQs. ALWAYS call this before stating "
            "any factual claim about the business. Returns relevant information as a "
            "string, or 'NOT_FOUND' if the SOP does not contain an answer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The customer's question or the topic to look up in the SOP.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "qualify_lead",
        "description": (
            "Record a customer's answer to a qualification question and retrieve the next "
            "question to ask. Call this once per qualification answer. Returns the next "
            "question string, or 'COMPLETE' when all 3 questions have been answered."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The customer's answer to the most recent qualification question.",
                }
            },
            "required": ["answer"],
        },
    },
    {
        "name": "flag_escalation",
        "description": (
            "Log an escalation event and mark the conversation as escalated. Call this "
            "when: the customer is angry/frustrated, asks out-of-scope questions, requests "
            "a human, mentions medical concerns, negotiates price, or reports a side effect. "
            "Returns a handoff message to relay to the customer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "A concise internal reason for the escalation (e.g. 'Customer expressed frustration', 'Out-of-scope medical question').",
                }
            },
            "required": ["reason"],
        },
    },
    {
        "name": "generate_summary",
        "description": (
            "Generate a structured end-of-session summary covering: customer intent, "
            "key details collected, SOP gaps identified, and recommended next action. "
            "Call this when the conversation is ending or the customer says goodbye."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_conversation_stage",
        "description": (
            "Returns the current conversation stage: 'faq', 'qualifying', 'escalated', or 'closing'. "
            "Use this at the start of each turn to stay aware of the current workflow stage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handler functions
# ---------------------------------------------------------------------------

def handle_lookup_sop(query: str, sop: dict, state: ConversationState) -> str:
    """
    Search the SOP JSON for relevant information.
    Uses a scoring approach: candidate passages are scored by how many
    query keywords they contain. Requires a minimum relevance score so
    incidental single-word matches (e.g. "laser" in aftercare) don't
    surface as results for "laser hair removal".
    Returns matched content or 'NOT_FOUND'.
    """
    query_lower = query.lower()
    # Filter out common stop words to focus on meaningful terms
    stop_words = {"a", "an", "the", "is", "are", "do", "you", "your",
                  "can", "what", "how", "any", "for", "in", "of", "to",
                  "and", "or", "i", "me", "my", "we", "our", "about"}
    query_words = [w for w in query_lower.split() if w not in stop_words]

    if not query_words:
        query_words = query_lower.split()

    # Minimum fraction of query words that must appear in a passage
    # For 1-word queries: 100% match; for 2+ word queries: at least 50%
    min_score = 1.0 if len(query_words) == 1 else 0.5

    scored: list[tuple[float, str]] = []

    def _score_text(text: str) -> float:
        text_lower = text.lower()
        matches = sum(1 for w in query_words if w in text_lower)
        return matches / len(query_words) if query_words else 0.0

    def _collect(obj, parent_key=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{parent_key}.{k}" if parent_key else k
                # Score the key itself + its serialized value
                key_score = _score_text(k)
                if key_score >= min_score:
                    scored.append((key_score, f"{full_key}: {json.dumps(v, indent=2)}"))
                else:
                    _collect(v, full_key)
        elif isinstance(obj, list):
            for item in obj:
                _collect(item, parent_key)
        elif isinstance(obj, str):
            s = _score_text(obj)
            if s >= min_score:
                scored.append((s, obj))
        elif isinstance(obj, (int, float)):
            if str(obj) in query_lower:
                scored.append((1.0, str(obj)))

    _collect(sop)

    if scored:
        # Sort by score descending, deduplicate, take top 6
        scored.sort(key=lambda x: x[0], reverse=True)
        seen: set[str] = set()
        unique: list[str] = []
        for _, text in scored:
            if text not in seen:
                seen.add(text)
                unique.append(text)
            if len(unique) >= 6:
                break

        state.unanswered_count = 0  # Reset miss counter on successful hit
        return "\n\n".join(unique)

    # No sufficiently relevant match found
    state.unanswered_count += 1
    return "NOT_FOUND"


def handle_qualify_lead(answer: str, state: ConversationState) -> str:
    """
    Record a qualification answer and return the next question or COMPLETE.
    """
    # Figure out which question we're on
    answered_count = len(state.qual_answers)

    if answered_count < len(QUALIFICATION_QUESTIONS):
        current_q = QUALIFICATION_QUESTIONS[answered_count]
        state.record_qual_answer(current_q["label"], answer)
        answered_count += 1

    if answered_count < len(QUALIFICATION_QUESTIONS):
        next_q = QUALIFICATION_QUESTIONS[answered_count]
        state.stage = "qualifying"
        return next_q["question"]
    else:
        state.stage = "closing"
        return "COMPLETE"


def handle_flag_escalation(reason: str, state: ConversationState) -> str:
    """
    Log an escalation event and return a handoff message.
    """
    state.log_escalation(reason)
    return (
        f"[ESCALATION LOGGED] Reason: {reason} | Turn: {state.turn_count} | "
        f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
        "Relay to customer: I'm connecting you with one of our specialists right now — "
        "they'll be in touch shortly. 💙"
    )


def handle_generate_summary(state: ConversationState, sop: dict) -> str:
    """
    Build a structured end-of-session summary.
    """
    # Customer intent
    intent = state.qual_answers.get(
        "treatment_interest", "Not specified (qualification not completed)"
    )

    # Key details collected
    details_lines = []
    for label, answer in state.qual_answers.items():
        q_text = next(
            (q["question"] for q in QUALIFICATION_QUESTIONS if q["label"] == label),
            label,
        )
        details_lines.append(f"  • {q_text}\n    → {answer}")
    details_section = "\n".join(details_lines) if details_lines else "  • None collected"

    # SOP gaps
    if state.escalation_log:
        gaps_lines = [
            f"  • Turn {e.turn}: {e.reason}" for e in state.escalation_log
        ]
        gaps_section = "\n".join(gaps_lines)
    else:
        gaps_section = "  • None identified — all questions answered from SOP"

    # Recommended next action
    if state.is_escalated():
        next_action = (
            "URGENT: Assign a human specialist to follow up. Escalation occurred — "
            "review escalation log for details."
        )
    elif state.qual_answers:
        next_action = (
            "Send a follow-up WhatsApp or email with a consultation booking link. "
            "Customer showed interest in: " + intent
        )
    else:
        next_action = (
            "Log as a general enquiry. No lead qualification completed. "
            "Consider a follow-up if contact details were shared."
        )

    summary = f"""
╔══════════════════════════════════════════════════════════════╗
║              BLOOM AESTHETICS — SESSION SUMMARY              ║
╚══════════════════════════════════════════════════════════════╝

SESSION DETAILS
  Date/Time : {datetime.now().strftime('%d %B %Y, %H:%M')}
  Duration  : {state.turn_count} conversation turn(s)
  Stage reached: {state.stage.upper()}

CUSTOMER INTENT
  {intent}

KEY DETAILS COLLECTED
{details_section}

SOP GAPS / ESCALATION EVENTS
{gaps_section}

RECOMMENDED NEXT ACTION
  {next_action}

══════════════════════════════════════════════════════════════
"""
    return summary.strip()


def handle_get_conversation_stage(state: ConversationState) -> str:
    """Return the current conversation stage."""
    return state.stage


# ---------------------------------------------------------------------------
# Dispatcher — maps tool name -> handler
# ---------------------------------------------------------------------------

def dispatch_tool(
    tool_name: str,
    tool_input: dict,
    state: ConversationState,
    sop: dict,
) -> str:
    """Execute a tool call and return the string result."""
    if tool_name == "lookup_sop":
        return handle_lookup_sop(tool_input["query"], sop, state)

    elif tool_name == "qualify_lead":
        return handle_qualify_lead(tool_input["answer"], state)

    elif tool_name == "flag_escalation":
        return handle_flag_escalation(tool_input["reason"], state)

    elif tool_name == "generate_summary":
        return handle_generate_summary(state, sop)

    elif tool_name == "get_conversation_stage":
        return handle_get_conversation_stage(state)

    else:
        return f"ERROR: Unknown tool '{tool_name}'"
