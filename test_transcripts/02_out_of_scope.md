# Test Transcript 02 — Out-of-Scope Question

**Scenario:** Customer asks something not covered by the SOP.
**Expected behaviour:** Aria calls `lookup_sop`, gets `NOT_FOUND`, calls `flag_escalation`, and does NOT attempt to guess or make up an answer.

---

```
  ╔══════════════════════════════════════════════════════════════╗
  ║     🌸  Bloom Aesthetics — AI Support Chat  🌸              ║
  ╚══════════════════════════════════════════════════════════════╝

  Aria : Hi there! Welcome to Bloom Aesthetics 🌸 I'm Aria, your virtual
         assistant. How can I help you today?

  You  : Do you offer laser hair removal?

  Aria : That's a great question! I want to make sure I give you accurate
         information, so I've just checked with our team. Unfortunately,
         laser hair removal isn't something I have details on right now —
         it may not currently be part of our treatment menu.

         Rather than guess, I'd love to get one of our specialists to
         confirm this for you directly.

         I'm connecting you with one of our specialists right now —
         they'll be in touch shortly. 💙

  ⚠️  [ESCALATED: Out-of-scope question — laser hair removal not in SOP]

  You  : Oh okay. What about tattoo removal?

  Aria : Similarly, I don't have information about tattoo removal in our
         current treatment offerings. I wouldn't want to give you
         inaccurate details!

         Our specialist who is already being looped in will be able to
         confirm what services are available and if there's anything we
         can recommend.

         I'm connecting you with one of our specialists right now —
         they'll be in touch shortly. 💙
```

---

**✅ Behaviour verified:**
- `lookup_sop` called → returned `NOT_FOUND` for both queries
- `flag_escalation` called with specific reason (not hallucinated)
- Aria does NOT invent services, prices, or availability
- Handoff message delivered correctly
- `unanswered_count` increments correctly (2 consecutive misses → escalation on first miss due to immediate trigger, second confirms)
- `⚠️ [ESCALATED]` banner displayed in CLI
