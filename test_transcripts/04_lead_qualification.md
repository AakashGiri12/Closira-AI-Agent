# Test Transcript 04 — Lead Qualification

**Scenario:** After a successful FAQ exchange, Aria transitions to lead qualification and asks 3 structured questions one at a time, storing the answers.
**Expected behaviour:** `qualify_lead` is called with each answer, the tool returns the next question, and all 3 answers are stored in `ConversationState.qual_answers`.

---

```
  ╔══════════════════════════════════════════════════════════════╗
  ║     🌸  Bloom Aesthetics — AI Support Chat  🌸              ║
  ╚══════════════════════════════════════════════════════════════╝

  Aria : Hi there! Welcome to Bloom Aesthetics 🌸 I'm Aria, your virtual
         assistant. How can I help you today?

  You  : Hi, I'm interested in getting some work done. What treatments
         do you offer?

  Aria : How lovely — welcome! We offer a range of aesthetic treatments
         at Bloom:

         • Botox (anti-wrinkle injections) — from £200
         • Dermal Fillers — from £250
         • Chemical Skin Peels — from £80
         • Microneedling (Collagen Induction Therapy) — from £120
         • LED Light Therapy — from £60

         We also offer a free 30-minute initial consultation to help
         figure out the best plan for you. Would you like to know more
         about any of these?

  You  : I'm most interested in the fillers and maybe microneedling.

  Aria : Great choices! Fillers are brilliant for adding volume and
         definition, while microneedling works beautifully for improving
         skin texture and overall glow — they can actually complement
         each other really well.

         I'd love to make sure we can give you the best experience
         possible. Do you mind if I ask a couple of quick questions?

  You  : Sure, go ahead!

  Aria : Wonderful! So — what brings you in today? Is there a specific
         concern or treatment outcome you're hoping for?

         [Tool called: qualify_lead — initialising qualification, Q1 delivered]

  You  : I want to plump up my lips and also improve some acne scarring
         on my cheeks.

  Aria : That makes total sense — lip fillers and microneedling are both
         excellent for exactly those concerns. 😊

         Have you had any aesthetic treatments before, or would this be
         your first time?

         [Tool called: qualify_lead(answer="Lip fillers for volume, microneedling for acne scarring on cheeks") → Q2 returned]

  You  : I had lip fillers done about two years ago at another clinic,
         but nothing since then.

  Aria : That's helpful to know — having had fillers before means you'll
         know what to expect during the process. 

         Last question — how did you hear about Bloom Aesthetics?

         [Tool called: qualify_lead(answer="Had lip fillers 2 years ago at another clinic, nothing since") → Q3 returned]

  You  : I found you on Instagram! Your before and after photos look
         amazing.

  Aria : That's so lovely to hear, thank you! 🌸

         [Tool called: qualify_lead(answer="Found on Instagram") → COMPLETE]

         Based on what you've shared, I'd recommend booking a free
         consultation with Dr. Priya Sharma or Sophie Reeves — they'll
         be able to assess your lips and skin in person and put together
         a personalised plan combining fillers and microneedling.

         You can book via WhatsApp at +44 7700 900456, through our
         website at www.bloomaesthetics.co.uk, or by calling us. Would
         you like me to help with anything else?
```

---

**✅ Behaviour verified:**
- Stage transitions naturally from `faq` → `qualifying` after 2 FAQ turns
- `qualify_lead` called with each answer
- Questions delivered one at a time (not listed all at once)
- All 3 answers stored in `ConversationState.qual_answers`:
  ```python
  {
    "treatment_interest": "Lip fillers for volume, microneedling for acne scarring on cheeks",
    "prior_experience": "Had lip fillers 2 years ago at another clinic, nothing since",
    "referral_source": "Found on Instagram"
  }
  ```
- Stage moves to `closing` after COMPLETE
- No escalation triggered
