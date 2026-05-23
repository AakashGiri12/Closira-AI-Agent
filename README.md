# Closira — AI Customer Support Workflow

An AI-powered customer support workflow for **Bloom Aesthetics Clinic**, built as part of the Closira AI Engineering internship assignment.

Aria, the virtual assistant, handles inbound customer conversations across four structured stages: FAQ answering, lead qualification, escalation detection, and conversation summary — all grounded strictly in a business SOP with no hallucination.

---

## Architecture

```
main.py                  ← CLI entry point & conversation loop
workflow/
  agent.py               ← Anthropic tool-use loop (ClosiraAgent)
  tools.py               ← 5 tool schemas + Python handlers
  state.py               ← ConversationState dataclass
  prompts.py             ← System prompt builder
sop/
  bloom_aesthetics.json  ← Extended SOP data (source of truth)
test_transcripts/        ← 5 sample conversations
prompt_design.md         ← Full prompt design rationale
```

**Tech stack:** Python 3.11+, Anthropic Claude (`claude-3-5-sonnet-20241022`), native `tool_use` API

---

## Prerequisites

- Python 3.11 or higher
- A Gemini API key.

---

## Setup

```bash
# 1. Clone / navigate to the project
cd Closira

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up your API key
cp .env.example .env
# Open .env and replace 'sk-ant-your-key-here' with your real Anthropic API key
```

---

## Running the Workflow

```bash
python main.py
```

You'll see a welcome banner and an opening greeting from Aria. Type your customer messages at the `You:` prompt.

**To end the session:** type `quit`, `exit`, or `bye`. This triggers a structured session summary before closing.

**To force-quit without summary:** press `Ctrl+C`.

---

## Four Workflow Stages

| Stage | Trigger | Behaviour |
|-------|---------|-----------|
| `faq` | Default start | Answers questions using `lookup_sop`. Escalates if SOP can't answer. |
| `qualifying` | After 2+ successful FAQ turns | Asks 3 structured qualification questions one at a time. |
| `escalated` | Anger, out-of-scope, medical Q, price negotiation | Logs reason, hands off to specialist. |
| `closing` | Customer says goodbye | Calls `generate_summary`, prints structured session summary. |

---

## Escalation Triggers

The AI automatically escalates when any of the following are detected:

- Customer expresses anger, frustration, or makes a complaint
- Question cannot be answered from the SOP (2+ consecutive misses)
- Medical question or contraindication enquiry
- Request to speak to a human, doctor, or manager
- Pricing negotiation attempt
- Mention of an adverse reaction to a past treatment

Escalation events are logged with reason, turn number, and timestamp. An `⚠️ [ESCALATED: ...]` banner is displayed in the CLI.

---

## Test Transcripts

Five sample conversations are provided in `test_transcripts/`, one per expected behaviour:

| File | Scenario |
|------|----------|
| `01_in_scope_faq.md` | Customer asks about Botox prices → answered from SOP |
| `02_out_of_scope.md` | Customer asks something not in the SOP → escalated, no guessing |
| `03_escalation_trigger.md` | Customer expresses frustration → escalated with reason logged |
| `04_lead_qualification.md` | Full 3-question qualification flow |
| `05_conversation_summary.md` | Full session ending with structured summary |

---

## SOP Data

The SOP file (`sop/bloom_aesthetics.json`) contains the business's complete source of truth:

- **Original (from assignment):** Botox (£200+), Fillers (£250+), free consultations, WhatsApp/website booking, 24hr cancellation policy
- **Extended:** Skin peels (£80+), Microneedling (£120+), LED therapy (£60+), staff bios (Dr. Priya Sharma & Sophie Reeves), loyalty programme (Bloom Rewards), gift vouchers, parking info, aftercare instructions, FAQs

The AI is **strictly prohibited** from stating any fact not present in this file.

---

## Known Trade-offs & Limitations

| Limitation | Notes |
|---|---|
| SOP lookup is keyword-based | Production would use semantic search / vector embeddings |
| State is in-memory | Lost on process restart; production would persist to a DB |
| No streaming | Responses appear all at once; `stream=True` could improve UX |
| English only | No i18n support |
| Single conversation per run | No multi-session management |

---

## Prompt Design

See [`prompt_design.md`](./prompt_design.md) for the full system prompt, design decisions, hallucination prevention approach, escalation logic, and tone rationale.
