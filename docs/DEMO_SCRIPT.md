# FieldFix AI — Pitch Deck & Demo Script

> **Format:** Investor / hackathon pitch (8-minute version) + standalone 4-minute live demo.
> Presenter notes appear in `> blockquotes`. Slide cues appear in **[brackets]**.

---

---

# PART 1 — PITCH DECK (Slides 1–12)

---

## SLIDE 1 — Title

**[Full-screen: technician on a rooftop at sunrise, hands on equipment, phone in hand]**

# FieldFix AI
### The Senior Engineer in Every Technician's Ear
*Real-time multimodal AI for field repair — powered by Gemini Live API*

> **SAY:** "What happens when your most experienced engineer can't be on every job at once — but your least experienced technician is?"

---

## SLIDE 2 — The Problem (The $47B Headache)

**[Split: left = frustrated technician with a PDF manual, right = customer waiting beside broken equipment]**

### Every field repair has the same four failure modes:

| Failure | Cost |
|---|---|
| Technician calls senior engineer for guidance | 45–90 min delay per incident |
| Wrong diagnosis from memory — repeat dispatch | $800–$2,400 per truck roll |
| Safety incident from ungrounded advice | Liability + downtime |
| Senior engineer leaves the company | Institutional knowledge gone |

> **SAY:** "Field service is a $47 billion industry in the US alone — and it runs on phone calls and PDFs. When the senior engineer is busy, the junior technician guesses. That guess costs money, time, and sometimes safety."

**Key stat to land:**
- 📞 **Field technicians average 3.2 phone escalations per shift** (ServiceMax 2024 Field Service Report)
- 🔁 **27% of field service dispatches result in a repeat visit** due to misdiagnosis (Aberdeen Group)
- 💸 **Average cost of a failed first-time fix: $1,600** in wasted labor + re-dispatch

---

## SLIDE 3 — The Root Cause

**[Diagram: Technician brain in the middle, arrows pulling in every direction — hands occupied, bad signal, 400-page PDF, customer pressure, time pressure]**

### The real problem isn't knowledge. It's **access**.

- The manual exists. It has every answer.
- The senior engineer exists. They know every fault.
- But neither is accessible **in the moment, with dirty hands, under pressure, at the equipment**.

> **SAY:** "This isn't an AI problem. It's an interface problem. The knowledge already exists — in manuals, in engineers' heads, in past repairs. The gap is getting that knowledge to the right person, at the right equipment, in real time."

---

## SLIDE 4 — The Solution

**[App screenshot: camera pointed at inverter, AI speaking a cited repair step, step tracker showing progress]**

# FieldFix AI
### Point. Speak. Fix.

**Three core capabilities:**

1. **See** — Point your camera at the equipment. The AI identifies it and sees the fault state.
2. **Speak** — Describe the symptom by voice. No typing. No menus. Fully hands-free.
3. **Guided Fix** — Receive one step at a time, read aloud, cited from the actual equipment manual. Interrupt at any moment.

> **SAY:** "FieldFix AI is not a chatbot you type questions into. It's an active repair partner that watches, listens, and guides — like a senior engineer on a video call, but available 24/7, for every technician, on every job."

**The three hard constraints baked into the AI:**
- ❌ No advice without a manual citation — hallucinations are eliminated by design
- ✅ One step at a time — waits for confirmation before proceeding
- ✅ Fully interruptible — if the technician cuts in, the AI stops mid-sentence

---

## SLIDE 5 — Live Demo Teaser

**[Short 20-second auto-playing clip: technician points camera at router → AI diagnoses LED pattern → citation card appears → technician says "wait, I don't have a multimeter" → AI instantly pivots]**

> **SAY:** "Let me show you — I'll run the full live demo in a moment. But the thing I want you to notice is this: the moment I interrupt it, it stops. That's the hardest part of conversational AI to get right, and it's working live right now."

*(Segue into live demo — see Part 2)*

---

## SLIDE 6 — How It Works (Technical Architecture)

**[Clean architecture diagram with three columns: Frontend PWA → WebSocket → Backend + Gemini Live API + Tools]**

```
┌─────────────────────────────────────────────────────────────┐
│                    TECHNICIAN'S PHONE                        │
│  React PWA  ──  AudioWorklet ──  Camera  ──  Zustand State  │
└──────────────────────┬──────────────────────────────────────┘
                       │  Single Multiplexed WebSocket
          ┌────────────▼────────────────────────────┐
          │         FastAPI  ·  Cloud Run            │
          │                                          │
          │   ┌─────────────────────────────────┐   │
          │   │      Gemini 2.0 Flash Live       │   │
          │   │   (Bidirectional Audio + Vision) │   │
          │   └──────────────┬──────────────────┘   │
          │                  │  Tool Calls           │
          │   ┌──────────────▼──────────────────┐   │
          │   │  diagnose_frame  search_manual   │   │
          │   │  lookup_similar  save_resolved   │   │
          │   └─────────┬──────────────┬─────────┘   │
          └─────────────┼──────────────┼─────────────┘
                        │              │
              ┌─────────▼──┐    ┌──────▼──────┐
              │  Firestore  │    │  Cloud GCS  │
              │ (Case DB)   │    │ (Manuals)   │
              └─────────────┘    └─────────────┘
```

> **SAY:** "The entire system runs through a single WebSocket. Audio, video frames, and control signals share one connection — this is critical for field environments with unreliable mobile data. The backend is stateless on Cloud Run, horizontally scalable, and the AI can never give ungrounded advice because the system prompt architecturally prevents it."

**Key technical choices:**
- **Gemini 2.0 Flash Live** — sub-500ms latency bidirectional audio
- **Single WebSocket** — minimizes connection overhead on poor networks
- **In-memory cosine similarity RAG** — no vector DB needed, sub-1ms retrieval per manual
- **AudioWorklet** (not ScriptProcessorNode) — zero audio dropouts, no deprecation warnings

---

## SLIDE 7 — Market Opportunity

**[Visual: large TAM/SAM/SOM funnel diagram]**

### Field Service Management — A Massive, Underserved Market

| Market | Size | Notes |
|---|---|---|
| **TAM** — Global Field Service Management | **$6.0B (2024)** → $29.9B (2034) | 17.4% CAGR (MarketsandMarkets) |
| **SAM** — AI-assisted field technician tools | **~$1.8B** | Sub-segment of FSM with AI/AR components |
| **SOM** — Enterprise telecom + energy + HVAC (Year 1–3) | **~$180M** | Focus on high-fault-frequency verticals |

**Why now:**
- 📈 Global shortage of experienced field technicians — 2.4M skilled trades jobs unfilled in the US by 2028 (Deloitte)
- 📱 Smartphone penetration in field workforces: 94%  — the device is already in their pocket
- 🤖 Gemini Live API (2025) makes real-time multimodal interaction economically viable for the first time
- 🏭 Industries with the highest fault resolution costs (solar, telecom, HVAC, industrial) are exactly where manual-grounded AI adds the most value

> **SAY:** "The field service management market is growing at 17% annually and the AI-assisted segment is growing even faster. But more importantly — the skill gap is accelerating. Companies can't hire their way out of this. They need to make every technician as capable as their best one."

---

## SLIDE 8 — Competitive Landscape

**[2x2 matrix: X-axis = Manual-grounded vs. General AI, Y-axis = Real-time voice/vision vs. Text-only]**

```
                    REAL-TIME VOICE + VISION
                              ▲
                              │
              ServiceMax AR   │   ★ FieldFix AI
   (expensive, hardware-req.) │   (mobile, grounded, conversational)
                              │
GENERAL ──────────────────────┼──────────────────── MANUAL-GROUNDED
  AI                          │                          AI
                              │
          ChatGPT / Copilot   │   Traditional service
          (no grounding,      │   documentation tools
           hallucination risk)│   (text-only, no voice)
                              │
                              ▼
                         TEXT ONLY
```

**FieldFix AI differentiators vs. closest alternatives:**

| | FieldFix AI | ServiceMax (Salesforce) | Generic LLM chatbot |
|---|---|---|---|
| Real-time voice | ✅ | ✅ (add-on) | ❌ |
| Camera + vision | ✅ | Partial (AR headset) | ❌ |
| Manual-grounded (no hallucination) | ✅ | ❌ | ❌ |
| Institutional memory (Firestore) | ✅ | ✅ (expensive CRM) | ❌ |
| Cost | Low (Cloud Run) | $$$$ (enterprise) | $ (but unsafe for repairs) |
| Works on any smartphone | ✅ | ❌ (proprietary HW) | ✅ |

> **SAY:** "ServiceMax requires $40K/year per enterprise seat and proprietary AR hardware. Generic LLMs will confidently tell a technician the wrong thing. FieldFix AI is the only solution that is grounded in the actual manual, conversational, and works on any smartphone the technician already has."

---

## SLIDE 9 — Business Model

**[Clean revenue model diagram]**

### Three Revenue Streams

**1. SaaS Subscription (Primary)**
- Per-seat pricing: **$49/technician/month** (SMB) · **$29/seat/month** (enterprise 100+ seats)
- Includes: unlimited sessions, up to 50 manual uploads, Firestore case history
- Estimated ARPU: $420/technician/year

**2. Manual Ingestion & Knowledge Base Setup (Professional Services)**
- One-time onboarding: **$500–$5,000** per equipment line
- Includes: PDF ingestion, embedding, QA validation
- Scales with enterprise manual libraries

**3. API / White-Label (Enterprise)**
- Manufacturers (ZTE, SMA, Carrier HVAC) embed FieldFix AI into their own support portals
- Revenue share: **15–20%** of customer billing

### Unit Economics (Year 1 target: 500 technician seats)

| Metric | Value |
|---|---|
| ARR (500 seats × $420) | $210,000 |
| Cloud Run + GCS cost est. | ~$800/month |
| Gross Margin | ~95% |
| CAC (direct sales + demo) | ~$200/seat |
| LTV (3-year, 85% retention) | ~$1,260/seat |
| **LTV:CAC** | **6.3:1** |

> **SAY:** "The unit economics are strong because the marginal cost of serving an additional technician is essentially just compute — Cloud Run scales to zero when not in use. The high gross margin and strong LTV:CAC ratio means we can invest aggressively in sales without destroying margins."

---

## SLIDE 10 — Traction & Validation

**[Timeline showing milestones + logos of target pilot industries]**

### What We've Built (MVP — Hackathon Phase)

- ✅ End-to-end working product — live demo today
- ✅ 5 industries supported: Solar, Telecom, HVAC, Lab Equipment, Industrial
- ✅ ZTE MF687 manual ingested and live in knowledge base
- ✅ SMA Sunny5000 inverter fault cases seeded in Firestore
- ✅ Deployed on Google Cloud Run (production-ready containerization)
- ✅ Real Gemini 2.0 Flash Live API integration (not a mock)

### Next 90 Days (Post-Hackathon Roadmap)

| Month | Milestone |
|---|---|
| Month 1 | Recruit 3 field service SMBs for paid pilot (solar + telecom focus) |
| Month 2 | Ingest 20+ real equipment manuals; add Vertex AI Vector Search |
| Month 3 | Integrate with ServiceNow ticketing (enterprise entry point) |
| Month 3 | Target: 50 pilot seats, $25K ARR, NPS > 50 |

---

## SLIDE 11 — The Team

**[Headshots and bios — customize with actual team details]**

### Built for the Field, by People Who Understand It

**[Your Name] — Founder & CEO**
- Background: [Your background — e.g., software engineer / field service experience]
- Built the entire MVP solo during hackathon — all code is production-quality

**Advisors / Target Hires:**
- Field Service Operations Lead (target hire: Month 2)
- Enterprise Sales — FSM vertical (target hire: Month 3)

> **SAY:** "I built this entire working system solo during the hackathon. That's not a flex — it's proof that the architecture is clean enough that one engineer can build the full stack. That's also a signal of how lean this company can run while scaling."

---

## SLIDE 12 — The Ask

**[Clean slide: three bullet points, contact info]**

### What We're Looking For

**Raising:** $500K pre-seed
**Use of funds:**
- 40% — Engineering (Vector DB, enterprise integrations, iOS/Android PWA hardening)
- 35% — Sales & pilots (first 3 enterprise customers)
- 25% — Manual library expansion (20+ equipment lines, 5 verticals)

**What we need beyond capital:**
- 🤝 Introductions to field service companies with 50–500 technician fleets
- 🏭 Pilot partnerships with equipment manufacturers (ZTE, SMA, Carrier, Trane)
- 🧪 Access to Google Cloud credits for Vertex AI Vector Search at scale

> **SAY:** "The technology is real and working — you just saw it live. The market is large and the timing is right. We're looking for $500K to go from one working product to three paying enterprise pilots. Let's talk."

**Contact:** [your@email.com] · [linkedin.com/in/yourprofile] · [github.com/yourrepo]

---
---

# PART 2 — LIVE DEMO SCRIPT (4 minutes)

> **Pre-Demo Setup Checklist (do before presenting):**
> 1. `cd backend && python ../scripts/seed_firestore.py` — seed Firestore case history
> 2. Confirm backend health: `curl http://localhost:8000/health` → `{"status":"ok"}`
> 3. Frontend running at http://localhost:5174
> 4. ZTE MF687 manual confirmed ingested in GCS: `telecom/ZTE-MF687/chunks.json`
> 5. Have a physical ZTE MF687 router OR a clear photo of one on a second device
> 6. Test microphone permissions in browser before presenting
> 7. Use Chrome or Edge — best AudioWorklet support
> 8. Set phone/laptop to Do Not Disturb

---

## Scene 1 — Hook (0:00 – 0:30)

**[Show blank app landing screen on a phone or browser]**

> "It's 8 AM. You're a telecom technician. You've just driven an hour to a customer site. Their 4G router is down. You've never seen this fault pattern before. Your senior engineer is in a meeting until noon."

**[Tap the FieldFix AI app]**

> "This is what you do instead."

---

## Scene 2 — Session Start (0:30 – 1:00)

**[Select Telecom from industry dropdown]**

> "I select my industry — Telecom."

**[Select ZTE-MF687 from equipment dropdown]**

> "And my equipment model — the ZTE MF687 router."

**[Session connect animation — green WebSocket connected indicator]**

> "The AI connects in under a second. It already knows the ZTE MF687 manual. It's ready."

---

## Scene 3 — Visual Diagnosis (1:00 – 2:00)

**[Point camera at the ZTE MF687 device — ensure the Signal/Network LED is visible showing solid red]**

> **SPEAK TO THE APP:** *"Hey FieldFix, I've got a ZTE MF687 here and the network LED is solid red. No SIM card detected according to the display. I've already checked the SIM is inserted."*

**[Wait — AI processes camera frame + voice simultaneously]**

> The AI should respond approximately:
> *"I can see the solid red network LED on your MF687. Based on the manual, a solid red Signal LED specifically indicates one of three conditions: SIM not seated correctly, SIM card damaged, or the SIM is not activated by the carrier. Since you've confirmed it's physically inserted — let's verify seating first. Power the device off completely, remove the back cover and battery, then carefully re-seat the micro-SIM ensuring the gold contacts face down and the cut corner matches the slot diagram."*

**[Citation card should appear: "ZTE MF687 Technical Reference Manual — Section 4: SIM Card Installation"]**

> "Notice that — it cited the exact section of the manual before giving any advice. It cannot give me a repair step without grounding it in the documentation. This is how we prevent hallucinations in a safety-critical environment."

---

## Scene 4 — Barge-In (2:00 – 2:30)

**[While AI is speaking, interrupt mid-sentence]**

> **INTERRUPT:** *"Wait — what if the SIM itself is faulty? How do I test that?"*

**[AI stops immediately — barge-in working]**

> The AI should pivot:
> *"Good question. To isolate whether it's the SIM or the device — if you have another micro-SIM card available, insert it in the MF687. If the red LED clears, your original SIM is faulty or not activated. If the red LED stays, the fault is in the device SIM slot or firmware."*

> "That's barge-in. I interrupted mid-sentence and the AI stopped, acknowledged my question, and redirected. In a field environment where the technician is moving fast, this is critical — they can't wait for the AI to finish a paragraph they don't need."

---

## Scene 5 — Case History (2:30 – 3:00)

**[AI should call lookup_similar_cases automatically, or prompt it:]**

> **SAY:** *"Have any of my colleagues seen this before?"*

> The AI should respond:
> *"Yes — checking your team's case history. Two previous cases with the ZTE MF687 and a SIM detection failure: one was resolved by replacing the micro-SIM with a fresh one from the carrier. The other was caused by a bent contact pin in the SIM slot, resolved with a SIM slot replacement. Most recent case was 14 days ago."*

**[Open the Case History sidebar panel]**

> "The institutional memory is live. Every time a colleague resolves a fault, it goes into Firestore. The next technician doesn't start from zero — they start from the last solution."

---

## Scene 6 — Step Confirmation (3:00 – 3:30)

> **SAY:** *"OK, I re-seated the SIM. The red LED is still on."*

> The AI should give next step:
> *"Understood. Next step: test with a known-working SIM card from another device. This will confirm whether the fault is in the SIM card itself or the MF687's SIM reader."*

**[Step tracker panel updates — shows Step 1 complete, Step 2 in progress]**

> "One step at a time. It waits for me to confirm before moving on. This is intentional design — a 10-step list causes mistakes. One step, one confirmation, one step."

---

## Scene 7 — Resolution (3:30 – 4:00)

> **SAY:** *"I tested with another SIM — the red LED cleared. It's showing green now with a 4G signal. The original SIM card was deactivated. I've got the customer's carrier activating a new SIM now. Issue resolved."*

> The AI should confirm and save:
> *"Excellent. SIM card deactivation confirmed as root cause. I'm saving this to your team's knowledge base — ZTE MF687, SIM detection failure, resolved by carrier SIM reactivation. The next technician who sees this fault on this equipment will have your resolution as the first suggestion."*

**[save_resolved_case tool call completes — case saved confirmation in sidebar]**

> **CLOSING LINE:**
> "That's FieldFix AI. A senior engineer's knowledge, available to every technician, at every piece of equipment, in real time. Thank you."

---

## Demo Contingency — If Voice Doesn't Connect

> If the Gemini Live WebSocket fails to connect (1011 error):
> 1. Check backend terminal for error — most common: ADC token expired
> 2. Run `gcloud auth application-default print-access-token` — if error, re-run `gcloud auth application-default login`
> 3. Restart backend: `cd backend && .\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000`
> 4. If still failing: switch to narrated walkthrough using the screenshots in `docs/`

---

## Key Messages Checklist

| Message | When to land it |
|---|---|
| "Cannot give advice without a manual citation" | Scene 3 — when citation card appears |
| "Barge-in stops the AI cold" | Scene 4 — demonstrate interrupt |
| "One step at a time by design" | Scene 6 — step tracker |
| "Every fix makes the next technician faster" | Scene 7 — save_resolved_case |
| "$47B market, 27% repeat dispatch problem" | Slide 2 (pitch) or opening hook |
| "Works on any smartphone, no hardware needed" | Vs. ServiceMax comparison (Slide 8) |
| "95% gross margin, 6.3x LTV:CAC" | Slide 9 — if investor audience |
