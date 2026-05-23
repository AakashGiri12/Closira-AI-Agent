# Test Transcript 01 — In-SOP FAQ Question

**Scenario:** Customer asks a straightforward question that is fully covered by the SOP.
**Expected behaviour:** Aria calls `lookup_sop`, finds the answer, and responds accurately with no hallucination.

---

```
  ╔══════════════════════════════════════════════════════════════╗
  ║     🌸  Bloom Aesthetics — AI Support Chat  🌸              ║
  ║         Powered by Closira · Aria v1.0                       ║
  ╚══════════════════════════════════════════════════════════════╝

  Aria : Hi there! Welcome to Bloom Aesthetics 🌸 I'm Aria, your virtual
         assistant. I'm here to help you with any questions about our
         treatments, bookings, or anything else. How can I help you today?

  You  : Hi! What are your Botox prices?

  Aria : Great question! Our anti-wrinkle injections (Botox) start from
         £200 for a single area. Here's a quick breakdown:

         • 1 area  → £200
         • 2 areas → £320
         • 3 areas → £380

         Popular treatment areas include the forehead, frown lines, and
         crow's feet. Results typically last 3–6 months, and a prior
         consultation is required — which is completely free! 😊

         Would you like to book a consultation, or do you have any other
         questions?

  You  : What about fillers? What do those cost?

  Aria : Our dermal fillers use hyaluronic acid to restore volume and
         contour different areas. Prices vary by area:

         • Lips             → from £250
         • Cheeks           → from £350
         • Jawline          → from £350
         • Nasolabial folds → from £280
         • Under-eye (tear trough) → from £380

         Filler results last between 9–18 months depending on the area
         treated. Like Botox, a free consultation is required before
         your first injectable treatment.

         Would you like to book a consultation, or is there anything else
         I can help you with?

  You  : Are consultations really free?

  Aria : Absolutely — our initial consultations are completely
         complimentary! 🎉 It's a 30-minute session with one of our
         practitioners, where they'll assess your concerns and put
         together a bespoke treatment plan just for you. No obligation
         at all.

         You can book via WhatsApp, our website, or by phone. Would you
         like to arrange one?
```

---

**✅ Behaviour verified:**
- `lookup_sop` called for each factual question
- All prices and details match `sop/bloom_aesthetics.json` exactly
- No information fabricated or inferred beyond the SOP
- Tone: warm, reassuring, concise
