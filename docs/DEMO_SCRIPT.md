# FieldFix AI — Demo Script (4 minutes)

## Pre-Demo Setup
1. Run `python ../scripts/seed_firestore.py` to seed historical cases
2. Ensure the sample solar inverter manual has been ingested
3. Have a printed photo of an SMA inverter with a red blinking LED (or use a tablet)
4. Open the app on a phone with rear camera

---

## Scene 1: Introduction (0:00 – 0:30)

**[Show the app landing screen]**

> "This is FieldFix AI — a real-time AI assistant for field technicians. It uses Gemini Live API for voice and vision, with answers grounded in actual equipment manuals."

**[Tap Solar → SMA-Sunny5000]**

> "I'm a solar technician. Let me select my equipment."

---

## Scene 2: Visual Diagnosis (0:30 – 1:30)

**[Point camera at the inverter photo showing red LED]**

> "Hey FieldFix, I've got a red blinking LED on this SMA inverter. Three blinks."

**[Wait for AI to analyze — diagnosis overlay appears]**

**[Wait for AI to call search_manual — citation cards appear]**

> The AI should:
> - Identify the blinking pattern as DC overvoltage
> - Show a citation: "SMA Inverter Manual §6.2 · p.44"
> - Give one specific action to take

---

## Scene 3: Case History (1:30 – 2:15)

**[The AI should automatically call lookup_similar_cases]**

> The AI should say something like:
> "Three of your colleagues fixed this same fault. The most recent case was 18 days ago — they reconfigured the string from 11 to 10 panels."

**[Open the Case History panel to show the sidebar]**

> "I can see previous cases right here in the sidebar."

---

## Scene 4: Barge-In (2:15 – 2:45)

**[While the AI is speaking, interrupt it]**

> "Wait — I don't have a multimeter. What can I do without one?"

> The AI should:
> - Stop immediately (barge-in)
> - Acknowledge the interruption
> - Provide an alternative approach

---

## Scene 5: Step-by-Step Guidance (2:45 – 3:30)

**[Follow the AI's guided steps]**

> Each step appears in the Step Tracker panel. Confirm each step verbally.

> "OK, I checked the string voltage display on the inverter. It reads 615V."

> The AI provides the next step based on your confirmation.

---

## Scene 6: Resolution (3:30 – 4:00)

> "OK, I've reconfigured the string. The red LED stopped blinking — it's green now."

> The AI should:
> - Confirm the fix worked
> - Automatically call save_resolved_case
> - Say: "This case has been saved to your team's knowledge base."

**[End with a shot of the app showing the completed steps]**

> "That's FieldFix AI — real-time expert guidance, grounded in your manuals, learning from every fix."

---

## Key Points to Hit
- ✅ Real-time audio + vision (Gemini Live API)
- ✅ Google ADK with tool calling (4 tools shown)
- ✅ Manual citations (RAG via Cloud Storage)
- ✅ Case history (Firestore)
- ✅ Barge-in / interruption
- ✅ Institutional memory (save resolved case)
