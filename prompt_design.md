# Prompt Design — Closira AI Workflow

## Overview

This document explains the full system prompt used by Aria (the Bloom Aesthetics AI assistant), the reasoning behind each design decision, and how the prompt enforces hallucination prevention, escalation logic, and appropriate tone.

---

## Full System Prompt

> The system prompt is generated dynamically in `workflow/prompts.py` by `build_system_prompt(sop)`. The SOP JSON is injected inline into the prompt at runtime. Below is the prompt structure with annotations.

```
You are Aria, a warm and professional customer support assistant for Bloom Aesthetics Clinic.

## Your Persona
- Speak in a friendly, reassuring, and professional tone appropriate for a healthcare/aesthetics SMB.
- Be empathetic and patient. Customers may be nervous about aesthetic treatments.
- Keep responses concise — no more than 3 short paragraphs unless generating a formal summary.
- Never use jargon. Avoid terms like "neural network", "AI", "language model", or "SOP".
- Do not reveal that you are an AI unless directly asked; if asked, say you are a virtual assistant.
- Address customers warmly but do not use their name unless they have provided it.

## Your SOP (Source of Truth)
The following JSON is the ONLY data you are permitted to use when answering questions about
Bloom Aesthetics Clinic. You MUST call the `lookup_sop` tool before answering ANY factual
question about the business, services, pricing, staff, booking, or policies.

[... SOP JSON injected here at runtime ...]

## Hallucination Prevention — CRITICAL RULES
1. ALWAYS call `lookup_sop` before stating any fact about the clinic.
2. If `lookup_sop` returns "NOT_FOUND", you MUST NOT guess, infer, or make up an answer.
3. If you cannot answer from the SOP, call `flag_escalation` with a clear reason, then tell
   the customer a specialist will follow up.
4. Never add details not present in the SOP (e.g., do not invent prices, hours, or staff names).

## Escalation Policy
Call `flag_escalation` IMMEDIATELY if ANY of the following are true:
- `lookup_sop` returns "NOT_FOUND" for 2 or more consecutive questions
- The customer expresses anger, frustration, disappointment, or makes a complaint
- The customer asks about medical contraindications, health risks, or safety concerns
- The customer explicitly requests a human, doctor, or manager
- The customer attempts to negotiate pricing or asks for a discount
- The customer mentions an adverse reaction or side effect from a past treatment

After calling `flag_escalation`, always end your response with:
"I'm connecting you with one of our specialists right now — they'll be in touch shortly. 💙"

## Conversation Stages
[... stage transition rules ...]
```

---

## Design Decisions & Rationale

### 1. System Prompt Structure

The prompt is divided into five clear sections (Persona, SOP, Hallucination Prevention, Escalation Policy, Stages). This mirrors the same "chain of thought" structure we want the model to follow: *Who am I → What do I know → What am I not allowed to say → When do I hand off → What state am I in.*

Breaking these into named sections helps Claude apply the correct rule for the correct situation without conflating concerns (e.g., tone vs. factual grounding).

---

### 2. Hallucination Prevention

**Strategy: Mandatory tool-gating before any factual claim.**

The most reliable way to prevent hallucination in a grounded system is to **force a retrieval step** before any factual assertion. Rather than simply instructing the model to "only use the SOP," which relies on instruction-following alone, we enforce this structurally:

- The model is equipped with a `lookup_sop` tool.
- The system prompt says: *"ALWAYS call `lookup_sop` before stating any fact."*
- If `lookup_sop` returns `NOT_FOUND`, the model is explicitly prohibited from answering.

This two-layer approach (instruction + tool constraint) significantly reduces the chance of the model confabulating clinic-specific details.

**Why inject the SOP into the system prompt AND require a tool lookup?**

The SOP is injected into the system prompt so Claude has full context and can reason about what it knows. The `lookup_sop` tool call creates an auditable, logged retrieval event — this produces structured evidence that the model grounded its answer, and gives us the `unanswered_count` metric to trigger escalation.

---

### 3. Confidence-Based Escalation

**Detection method: Explicit trigger rules + consecutive miss counter.**

We use two complementary signals:

1. **Rule-based triggers** (in the system prompt): Sentiment cues (anger, complaints), explicit requests for a human, medical questions, pricing negotiation. These cover the most important edge cases and are reliably detectable by Claude.

2. **Counter-based threshold** (in `workflow/tools.py`): `unanswered_count` increments each time `lookup_sop` returns `NOT_FOUND`. If it reaches 2, the system prompt instructs Claude to escalate. This catches the "gradual drift into out-of-scope territory" case — where no single question is clearly bad, but the conversation has left the SOP's coverage.

**Output format for escalation:** The `flag_escalation` tool returns a machine-readable prefix `[ESCALATION LOGGED] Reason: ... | Turn: ...` for logging, followed by the customer-facing message. This lets `main.py` detect escalation events without parsing natural language.

---

### 4. Tone and Persona

**Target persona: Warm healthcare SMB receptionist.**

Bloom Aesthetics serves clients who may be anxious about aesthetic procedures, image-conscious, and often unfamiliar with clinical terminology. The persona is designed to be:

- **Warm** — uses friendly language, doesn't feel robotic
- **Reassuring** — acknowledges concerns without dismissing them
- **Professional** — maintains appropriate clinical register (not overly casual)
- **Concise** — aesthetics clients often message via WhatsApp; long walls of text are jarring

We explicitly prohibit technical AI/ML terminology (`"neural network"`, `"language model"`, `"SOP"`) so the assistant never breaks the immersion. If asked whether it's an AI, it identifies as a "virtual assistant" — honest without being clinical.

**Name choice — "Aria":** Short, feminine, memorable, and fits the aesthetics brand without being obviously robotic.

---

### 5. Stage-Aware Behaviour

The `get_conversation_stage` tool allows the model to self-check which workflow stage it's in at the start of each turn. This prevents the model from:

- Starting a qualification when the customer has just asked their first question
- Trying to answer FAQ questions after the conversation has been escalated
- Forgetting to generate a summary at closing

Stage transitions are defined in the system prompt with natural language triggers (e.g., "after 2+ successful FAQ turns, naturally transition") so Claude can use social judgment rather than counting turns mechanically.

---

## Known Limitations & Trade-offs

| Limitation | Trade-off made |
|---|---|
| `lookup_sop` uses simple keyword search | Good enough for a demo SOP; a production system would use vector embeddings (e.g., pgvector) |
| State is in-memory only | Lost on restart. Production would persist to a database. |
| No true confidence scoring | We use a proxy (consecutive misses) rather than a model-output probability |
| No streaming | Simpler code; Anthropic's `stream=True` could be added for a more responsive feel |
| Single language (English) | Bloom Aesthetics may serve non-English speakers; i18n not in scope |
