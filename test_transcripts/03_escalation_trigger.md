# Test Transcript 03 — Escalation Trigger (Angry Customer / Complaint)

**Scenario:** Customer expresses frustration or makes a complaint about a past experience.
**Expected behaviour:** Aria detects the negative sentiment, immediately calls `flag_escalation` with the detected reason, does NOT try to resolve the complaint itself, and hands off to a specialist.

---

```
  ╔══════════════════════════════════════════════════════════════╗
  ║     🌸  Bloom Aesthetics — AI Support Chat  🌸              ║
  ╚══════════════════════════════════════════════════════════════╝

  Aria : Hi there! Welcome to Bloom Aesthetics 🌸 I'm Aria, your virtual
         assistant. How can I help you today?

  You  : I had fillers done here last month and my face has been swollen
         ever since. I'm really unhappy about this.

  Aria : I'm so sorry to hear you're experiencing this — that must be
         really worrying, and I completely understand your concern. 💙

         This is something that one of our practitioners needs to look
         into personally and urgently. Please don't worry — you're in
         the right place to get this sorted.

         I'm connecting you with one of our specialists right now —
         they'll be in touch shortly. 💙

  ⚠️  [ESCALATED: Customer reported adverse reaction (prolonged swelling after fillers) and expressed dissatisfaction]

  You  : I've been waiting for someone to call me back for days and
         nobody has. This is absolutely ridiculous.

  Aria : I completely hear you, and I sincerely apologise for the lack
         of follow-up — that is not the standard of care we pride
         ourselves on. Your concern is being treated as a priority.

         I'm flagging this as urgent and making sure the right person
         contacts you as quickly as possible.

         I'm connecting you with one of our specialists right now —
         they'll be in touch shortly. 💙

  ⚠️  [ESCALATED: Customer expressed anger and frustration about lack of follow-up after adverse reaction]
```

---

**✅ Behaviour verified:**
- First message: adverse reaction + dissatisfaction → `flag_escalation` triggered immediately
- Reason logged: `"Customer reported adverse reaction (prolonged swelling after fillers) and expressed dissatisfaction"`
- Aria does NOT attempt to diagnose, explain, or dismiss the complaint
- Second escalation logs continued frustration separately
- Empathetic tone maintained throughout — no defensive language
- Handoff message delivered correctly both times
- `⚠️ [ESCALATED]` banner shown in CLI for each event
