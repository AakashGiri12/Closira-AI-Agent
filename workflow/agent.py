"""
Agentic tool-use loop for Bloom Aesthetics AI workflow.
Backend: Google Gemini via google-generativeai (free via Google AI Studio).
"""

import google.generativeai as genai
from google.generativeai import protos

from workflow.prompts import build_system_prompt
from workflow.state import ConversationState
from workflow.tools import dispatch_tool

GEMINI_MODEL = "gemini-2.5-flash"
MAX_TOOL_ROUNDS = 10

# ---------------------------------------------------------------------------
# Gemini function declarations (mirrors TOOL_SCHEMAS in tools.py)
# ---------------------------------------------------------------------------

GEMINI_TOOLS = protos.Tool(
    function_declarations=[
        protos.FunctionDeclaration(
            name="lookup_sop",
            description=(
                "Search the Bloom Aesthetics SOP for information about services, pricing, "
                "hours, booking, staff, policies, or FAQs. ALWAYS call this before stating "
                "any factual claim about the business. Returns relevant information as a "
                "string, or 'NOT_FOUND' if the SOP does not contain an answer."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "query": protos.Schema(
                        type=protos.Type.STRING,
                        description="The customer's question or topic to look up in the SOP.",
                    )
                },
                required=["query"],
            ),
        ),
        protos.FunctionDeclaration(
            name="qualify_lead",
            description=(
                "Record a customer's answer to a qualification question and retrieve the "
                "next question to ask. Call once per answer. Returns the next question "
                "string, or 'COMPLETE' when all 3 questions have been answered."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "answer": protos.Schema(
                        type=protos.Type.STRING,
                        description="The customer's answer to the most recent qualification question.",
                    )
                },
                required=["answer"],
            ),
        ),
        protos.FunctionDeclaration(
            name="flag_escalation",
            description=(
                "Log an escalation event and mark the conversation as escalated. Call when: "
                "the customer is angry/frustrated, asks out-of-scope questions, requests a "
                "human, mentions medical concerns, negotiates price, or reports a side effect."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={
                    "reason": protos.Schema(
                        type=protos.Type.STRING,
                        description="A concise internal reason for the escalation.",
                    )
                },
                required=["reason"],
            ),
        ),
        protos.FunctionDeclaration(
            name="generate_summary",
            description=(
                "Generate a structured end-of-session summary covering customer intent, "
                "key details collected, SOP gaps, and recommended next action. "
                "Call when the conversation is ending or the customer says goodbye."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={},
            ),
        ),
        protos.FunctionDeclaration(
            name="get_conversation_stage",
            description=(
                "Returns the current conversation stage: 'faq', 'qualifying', 'escalated', "
                "or 'closing'. Use at the start of each turn to stay stage-aware."
            ),
            parameters=protos.Schema(
                type=protos.Type.OBJECT,
                properties={},
            ),
        ),
    ]
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_text(response) -> str:
    """Safely extract text from a Gemini response (returns '' if only function calls)."""
    try:
        return response.text or ""
    except ValueError:
        return ""


def _get_function_calls(response) -> list:
    """Extract all function_call parts from a Gemini response."""
    calls = []
    for part in response.parts:
        if part.function_call.name:  # non-empty name = real function call
            calls.append(part.function_call)
    return calls


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ClosiraAgent:
    """
    Wraps the Gemini client and drives the agentic function-calling loop.
    One instance shared across the entire conversation session.
    """

    def __init__(self, api_key: str, sop: dict):
        genai.configure(api_key=api_key)
        self.sop = sop
        self.system_prompt = build_system_prompt(sop)

        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            tools=[GEMINI_TOOLS],
            system_instruction=self.system_prompt,
        )
        # Chat session maintains history automatically
        self.chat = self.model.start_chat()

    def run_turn(self, user_input: str, state: ConversationState) -> str:
        """
        Process one user turn through the full agentic function-calling loop.
        Returns the final assistant text response.
        """
        state.turn_count += 1
        state.transcript_lines.append(f"You   : {user_input}")

        response = self.chat.send_message(user_input)
        response_text = ""

        for _ in range(MAX_TOOL_ROUNDS):
            fn_calls = _get_function_calls(response)
            current_text = _get_text(response)
            if current_text:
                response_text = current_text

            if not fn_calls:
                break  # No more tool calls — done

            # Execute all function calls
            result_parts = []
            for fc in fn_calls:
                result = dispatch_tool(
                    tool_name=fc.name,
                    tool_input=dict(fc.args),
                    state=state,
                    sop=self.sop,
                )
                result_parts.append(
                    protos.Part(
                        function_response=protos.FunctionResponse(
                            name=fc.name,
                            response={"result": result},
                        )
                    )
                )

            # Send tool results back to the model
            response = self.chat.send_message(result_parts)

        state.transcript_lines.append(f"Aria  : {response_text}")
        return response_text

    def force_summary(self, state: ConversationState) -> str:
        """Force a summary turn when the user quits."""
        return self.run_turn(
            "The customer has ended the session. Please generate a session summary.",
            state,
        )
