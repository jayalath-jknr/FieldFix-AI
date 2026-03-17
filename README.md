# FieldFix AI

> Real-time AI assistant for field technicians — grounded in your equipment manuals.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Available-green)](YOUR_DEMO_URL)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Cloud%20Run-blue)](https://cloud.google.com)
[![Gemini Live](https://img.shields.io/badge/Gemini-Live%20API-purple)](https://ai.google.dev)

**Gemini Live Agent Challenge submission** — Track 1: Live Agent

## What it does

Field technicians point their phone camera at a broken device, describe the problem by voice, and receive live expert guidance — grounded in the actual equipment manual with section citations shown in real-time.

- 📷 **Camera + voice** → real-time Gemini Live API session
- 📖 **Every answer cited** from manual PDFs (RAG via Cloud Storage)
- 🧠 **Institutional memory**: learns from every resolved case (Firestore)
- 🎙️ **Interruptible**: technician can cut the agent off mid-sentence
- 🔧 **Step-by-step**: one repair action at a time, wait for confirmation

## Demo

[Watch the 4-minute demo video](YOUR_DEMO_VIDEO_URL)

## Architecture

![Architecture](docs/architecture.png)

### Tech Stack

| Layer | Technology |
|-------|-----------|
| AI | Gemini 2.5 Flash Live API + ADK |
| Backend | FastAPI + WebSocket on Cloud Run |
| Knowledge Base | PDF → Cloud Storage (embedded chunks) |
| Case History | Firestore |
| Frontend | React + TypeScript + Tailwind CSS (PWA) |
| Infrastructure | Terraform IaC |

## Quick start (local)

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/fieldfix-ai
cd fieldfix-ai

# Backend
cd backend
cp .env.example .env  # fill in GCP_PROJECT_ID
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Using Docker Compose (recommended)

```bash
docker compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Deploy to Google Cloud

```bash
# Set your project
export PROJECT_ID=your-gcp-project-id

# Authenticate
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com

# Build and push
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/fieldfix/backend:latest backend/
docker push us-central1-docker.pkg.dev/$PROJECT_ID/fieldfix/backend:latest

# Deploy infrastructure
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your project ID
terraform init
terraform apply -var="project_id=$PROJECT_ID"

# Ingest a sample manual
cd ../backend
python -m tools.ingest_pdf \
  --pdf ../manuals/sample_solar_inverter.pdf \
  --industry solar \
  --model SMA-Sunny5000 \
  --source "SMA Inverter Manual"

# Seed demo data
python ../scripts/seed_firestore.py
```

## Project Structure

```
fieldfix-ai/
├── backend/           # FastAPI + ADK LiveAgent
│   ├── main.py        # WebSocket handler
│   ├── agent.py       # ADK agent definition
│   ├── tools/         # 4 agent tools
│   ├── core/          # Config, logging, GCP clients
│   ├── models/        # Pydantic models
│   └── tests/         # Pytest test suite
├── frontend/          # React + TypeScript + Tailwind
│   └── src/
│       ├── components/  # 6 UI components
│       ├── hooks/       # WebSocket, camera, microphone
│       └── store/       # Zustand state management
├── infra/             # Terraform IaC
├── scripts/           # Seed scripts
├── docs/              # Architecture diagram + demo script
├── docker-compose.yml # Local dev environment
├── cloudbuild.yaml    # CI/CD pipeline
├── BLOG_POST.md       # Challenge blog post
└── README.md
```

## Agent Tools

| Tool | Purpose |
|------|---------|
| `diagnose_frame` | Camera frame → Gemini Vision → structured fault diagnosis |
| `search_manual` | RAG search over equipment manual chunks (cosine similarity) |
| `lookup_similar_cases` | Query Firestore for previously resolved cases |
| `save_resolved_case` | Save resolved case to Firestore institutional memory |

## GDG Profile

[YOUR_GDG_PROFILE_URL]

## License

See [LICENSE](LICENSE) for details.

---

# Medium Article: Building FieldFix AI — A Real-Time AI Repair Partner for Field Technicians

> *Originally published on Medium. Cross-posted here for reference.*
>
> **By Nirasha Jayalath · March 2026**

---

## The Problem Nobody Talks About

There is a forty-seven billion dollar industry that still runs on phone calls and PDF manuals. It is called field service — and it employs millions of technicians who maintain solar arrays, telecommunications equipment, industrial machinery, HVAC systems, and everything in between.

Here is what a typical Tuesday looks like for one of those technicians.

You drive two hours to a commercial rooftop installation. A solar inverter is throwing a fault code you have never encountered before. The equipment manual is a 400-page PDF sitting on your laptop back in the van. Your hands are gloved. The customer is standing behind you. Your senior engineer — the one person who would know the answer in thirty seconds — is sixty miles away on a different job.

So you guess. Sometimes you get it right. Often you don't. Twenty-seven percent of field dispatches end in a repeat visit. The average cost of a failed first-time fix is sixteen hundred dollars. Teams average three phone escalations per technician shift.

This is not an AI problem. The knowledge exists. It is in the manual, in the engineer's head, and in every resolved case filed in the last decade. The problem is a **delivery problem** — getting the right knowledge to the right person, in real time, at the point of work.

That is what I set out to build with FieldFix AI.

---

## Why Existing Solutions Don't Work

Before writing a single line of code, I mapped the solution space.

**General-purpose LLMs** (ChatGPT, Gemini chat) fail because they hallucinate. Asking an LLM to advise on a specific SMA inverter fault without grounding it in the actual manual is asking it to confabulate confidently. In a repair scenario where wrong guidance can damage equipment or injure someone, confident confabulation is worse than no answer at all.

**Enterprise FSM platforms** like ServiceMax cost forty thousand dollars per year per enterprise seat and require proprietary hardware. They are designed for operations managers, not for a technician standing on a rooftop.

**Training programs** scale slowly and go stale. A technician trained six months ago has not seen the firmware update released last month.

The gap I identified was specific: a solution that is **grounded** (cannot hallucinate), **conversational** (no typing required), **multimodal** (can see the equipment), and **accessible** (works on any smartphone the technician already has).

---

## The Core Architecture Decision: One WebSocket, Two Data Types

The most consequential early decision was transport architecture.

In a field environment — a warehouse, a cell tower site, a factory floor — network conditions are unreliable. LTE coverage drops. Wi-Fi is patchy. Every open network connection is a potential point of failure, and every reconnect event costs time and state.

I made a deliberate choice to route everything through **a single multiplexed WebSocket**:

- **Binary frames**: raw PCM audio from the microphone, streamed continuously at 16kHz
- **JSON frames**: base64-encoded camera images sent at approximately 2fps, plus control signals like `barge_in`

A single-byte prefix distinguishes the two frame types on the backend. One TLS handshake. One reconnect path. One connection to monitor. This sounds like a small optimisation — in a flaky field network, it is the difference between a working product and a frustrating one.

```
Client ──── ws:// ────────────────────── Server
           Binary [PCM audio]      →  ADK Live stream
           JSON  [camera frame]    →  diagnose_frame tool
           JSON  [barge_in]        →  session interrupt
                                   ←  Binary [TTS audio response]
                                   ←  JSON  [citation card data]
```

---

## RAG Without a Vector Database

The standard advice for building a retrieval-augmented generation system in 2025 is: spin up a vector database. Pinecone, Weaviate, pgvector, Vertex AI Vector Search — pick one.

I chose none of them. Here is why.

For FieldFix AI's MVP use case — one manual per equipment model, retrieved per session — a managed vector database is architecture for a problem I do not yet have. Instead:

**At ingest time**, each PDF is split into overlapping 512-token chunks. Each chunk is embedded using Vertex AI's `text-embedding-004` model to produce a 768-dimensional vector. The chunks and their embeddings are serialised as JSON and written to Google Cloud Storage.

**At query time**, the user's search query is embedded with the same model. Cosine similarity is computed in-process against all cached chunk vectors using NumPy:

$$\text{similarity}(Q, C) = \frac{Q \cdot C}{\|Q\| \cdot \|C\|}$$

The knowledge base is loaded once and held in an `lru_cache`. For 100–500 chunks, the similarity scan completes in under one millisecond. The top three chunks are returned with their source section and page number.

The agent is architecturally forbidden from dispensing repair advice until it has called `search_manual` and received a result. If no relevant chunk is found, it tells the technician it cannot advise safely without a verified source. **The citation is not a bonus feature — it is a structural safety constraint.**

This approach works beautifully for the MVP. When the knowledge base grows to thousands of manuals across entire equipment lines, migrating to Vertex AI Vector Search is a one-component swap. But that migration should happen when the use case demands it, not speculatively.

---

## The Barge-In Problem: Getting AI to Stop Talking

Early in testing, I discovered the most frustrating quality of a naive conversational AI: it does not stop.

Picture a technician on step two of a six-step repair sequence. The AI is reading out step three. The technician sees something unexpected on the panel and needs to interject. With a naive implementation, they have two options: wait for the AI to finish, or hang up and start over.

Neither is acceptable.

I implemented a **two-layer barge-in system**:

**Layer 1 — Frontend.** The audio capture loop runs an `AudioWorkletProcessor` that continuously calculates the RMS energy of the microphone buffer. When speech energy exceeds a calibrated threshold, a `{ type: "barge_in" }` JSON message is dispatched immediately over the WebSocket — before the audio buffer even reaches the server. This triggers an instantaneous interruption.

**Layer 2 — Backend.** The FastAPI handler receives the `barge_in` signal and triggers an interruption of the active ADK session's audio output. Gemini Live's `automatic_activity_detection` with high sensitivity serves as the fallback for cases where the frontend signal arrives late.

The result: the AI can be interrupted mid-sentence with sub-200ms latency on a standard mobile connection.

This is not a convenience feature. Every time the AI stops immediately when interrupted, the technician's trust in the system increases. It signals: *this tool respects your authority over the repair*. Without barge-in, a conversational AI feels like a lecture. With it, it feels like a conversation.

---

## The Seven-Step Repair Flow

Every session follows the same structured sequence, enforced by the agent's system prompt:

```
1.  Technician selects industry and equipment model
2.  Camera is pointed at the device
        ↓
3.  Camera frames → diagnose_frame → Gemini Vision
        → Structured JSON: { fault_type, severity, visible_symptoms }
        ↓
4.  Technician describes the fault by voice
        → Gemini Live API (bidirectional audio stream)
        ↓
5.  Agent calls search_manual
        → Cosine similarity search over Cloud Storage chunks
        → Top 3 cited passages returned
        ↓
6.  Agent calls lookup_similar_cases
        → Firestore query on equipment model + symptom keywords
        → Previous resolved cases surfaced
        ↓
7.  One repair step is given — agent waits for confirmation
        → Technician: "Done" or "That didn't work"
        → Next step, or alternative path
        ↓
8.  Issue resolved → save_resolved_case → Firestore
```

The single-step-at-a-time cadence is deliberate. Dumping a ten-step repair sequence onto a stressed technician working with their hands is how mistakes happen. Pace is a user experience decision. It is also a safety decision.

---

## Institutional Memory as a Flywheel

Every resolved case is saved to Firestore with structured metadata: equipment model, fault type, symptom keywords, resolution steps, and timestamp. When the next technician encounters a similar fault — even weeks later, on a different site — the `lookup_similar_cases` tool surfaces the prior repair.

The agent might say: *"A technician on your team resolved a similar fault on this inverter model last month by replacing the DC fuse string. Want me to check that first?"*

This is a flywheel effect. The more the system is used, the more accurate and specific its guidance becomes. It transforms the organisation's accumulated repair experience — which normally lives in the heads of senior engineers and gets lost when they leave — into a persistent, queryable institutional memory.

---

## Building for the Field: PWA as the Distribution Strategy

The frontend is a React + TypeScript Progressive Web App built with Vite. The decision to build a PWA rather than a native mobile app was strategic.

A PWA can be deployed as a URL. There is no app store review process, no separate iOS and Android codebase, and no binary to distribute. A field service organisation can onboard an entire technician team by sharing a link. The app installs to the home screen and behaves like a native application.

State is managed with Zustand — lightweight, no boilerplate, reactive. Audio is captured as raw PCM and streamed as binary. Camera frames are captured from a `getUserMedia` stream and sent as base64 JSON. The `useWebSocket` hook handles connection management, a reconnect backoff strategy, and frame-type routing.

---

## What the Tech Stack Looks Like

| Layer | Technology | Decision Rationale |
|---|---|---|
| AI model | Gemini 2.5 Flash Live API | Bidirectional audio + vision in one session |
| Agent framework | Google ADK | Structured tool calling over live streaming |
| Backend | FastAPI + uvicorn | Async WebSocket handling, minimal overhead |
| Compute | Google Cloud Run | Stateless, auto-scaling, pay-per-request |
| Knowledge base | Cloud Storage + NumPy | No vector DB needed at MVP scale |
| Case history | Firestore | Serverless NoSQL, fast keyword queries |
| Frontend | React + TypeScript + Vite (PWA) | Cross-platform, no app store, installable |
| State | Zustand | Minimal bundle, reactive, zero boilerplate |
| Styling | Tailwind CSS | Utility-first, no CSS-in-JS overhead |
| Infrastructure | Terraform IaC | Reproducible, version-controlled deployments |
| CI/CD | Cloud Build | Git-triggered container builds and deploy |

---

## Five Things I Learned Building This

**1. Gemini Live API is a genuinely different interaction model.**
Streaming bidirectional audio while simultaneously sending vision frames creates something that has no equivalent in request-response AI. The interaction feels like a phone call, not a form. When the latency is low enough, the technician stops thinking about the technology and focuses entirely on the repair. That is the goal.

**2. Design tools as constraints, not just capabilities.**
The `search_manual` requirement is not a feature — it is a guardrail. Designing the agent so that it *cannot* give repair advice without a verified citation changes the entire risk profile of the product. Safety-critical AI is built from constraints, not from hopes.

**3. Barge-in is a trust signal.**
Responsiveness to interruption communicates respect for the user's agency. This sounds soft, but it is the single interaction detail that most affects whether users describe the product as "natural" or "robotic."

**4. Pace is a superpower.**
One step at a time, wait for confirmation. I resisted every temptation to demonstrate the AI's depth by delivering comprehensive multi-step answers. A technician with grease on their gloves doing step one needs to complete step one before they can think about step two.

**5. Simple RAG is often the right RAG.**
Cosine similarity over pre-embedded chunks is perfectly adequate for the single-manual-per-model retrieval case. Managed vector databases are powerful — and they are also infrastructure. Add infrastructure when the use case demands it, not speculatively.

---

## What Comes Next

The MVP proves the core loop works. The path to production scale is clear:

- **Vertex AI Vector Search** — scale from one manual per model to thousands of manuals across entire equipment lines
- **Semantic case matching** — replace Firestore keyword overlap with embedding-based similarity over fault summaries
- **Enterprise integrations** — sync resolved cases to ServiceNow, SAP PM, or Jira; surface FieldFix guidance natively inside existing ticketing workflows
- **Offline mode** — cache the knowledge base locally on the PWA for zero-connectivity environments
- **Multilingual voice** — Gemini Live's native multilingual support means a Spanish-speaking technician can work in Spanish from an English-language manual, without translation overhead

---

## Try It

The entire project is open source. The live demo, source code, and a four-minute walkthrough are linked at the top of this README.

If you build something on top of it, or if you work in field service and want to talk — I would genuinely like to hear from you.

📧 jknrjayalath@gmail.com
🔗 [linkedin.com/in/nirasha-jayalath](https://www.linkedin.com/in/nirasha-jayalath/)
💻 [github.com/jayalath-jknr](https://github.com/jayalath-jknr/)

---

*Built for the Gemini Live Agent Hackathon · March 2026 · Nirasha Jayalath*
