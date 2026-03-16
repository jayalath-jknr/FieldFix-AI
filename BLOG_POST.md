# FieldFix AI: I Gave Every Field Technician a Senior Engineer in Their Ear

**#GeminiLiveAgentChallenge** | **#GeminiLiveAPI** | **#GoogleADK** | **#GoogleCloud**

---

## TL;DR

**FieldFix AI** is a real-time, multimodal AI assistant for field technicians. Point your phone camera at broken equipment, describe the problem by voice, and receive live expert guidance — grounded in the actual equipment manual with section citations read out loud. Every resolved case is saved to Firestore, building a shared institutional memory that makes the next technician faster than the last. Built with Gemini 2.5 Flash Live API, Google ADK, FastAPI on Cloud Run, and a React PWA frontend.

---

## The Problem: A 400-Page PDF in a Greasy Glove

Imagine you're a field technician. You've driven two hours to a commercial rooftop installation. A solar inverter is throwing a fault code you've never seen before. The equipment manual is a 400-page PDF — back in the van. Your hands are gloved and covered in grime. The customer is waiting. You call your senior engineer, but he's on another site.

This is not an edge case. This is Tuesday.

Field technicians work at the intersection of urgency, complexity, and physical constraint. They can't easily type. They can't scroll through dense PDFs with greasy fingers. They don't have time for a chatbot that responds 10 seconds later with a generic answer. They need something that can *see* what they're seeing, *hear* them out, and guide them — one step at a time — without ever making things up.

That frustration is what led me to build **FieldFix AI**.

---

## The Insight: Make the Manual Talk Back

The core insight was simple: **the manual already has all the answers**. The problem is accessing it. So instead of building a general-purpose chatbot, I built a system that:

1. **Reads the manual deeply** — Every PDF is chunked, embedded with `text-embedding-004`, and stored in Google Cloud Storage for retrieval.
2. **Is forced to cite its sources** — The ADK system prompt contains a hard constraint: the agent cannot dispense repair advice unless it has successfully called the `search_manual` tool. No citation, no answer. This one rule eliminates hallucinations in a high-stakes environment.
3. **Remembers every repair** — Every resolved case is saved to Firestore with structured metadata. The next technician facing the same fault on the same equipment starts with the benefit of every previous repair.
4. **Listens and watches in real time** — Gemini's Live API handles bidirectional audio streaming and camera frame analysis simultaneously, making the interaction feel like a real video call — not a slow Q&A form.

---

## How It Works: The 7-Step Flow

Here's what happens from the moment a technician opens the app:

```
1. Select industry & equipment model
2. Point camera at the device
       ↓
3. Camera frames → diagnose_frame tool → Gemini Vision
       ↓
4. Voice describes the fault → Gemini Live API (real-time bidirectional audio)
       ↓
5. search_manual (RAG) → Cloud Storage chunks → cited answer
       ↓
6. lookup_similar_cases → Firestore → similar past repairs surfaced
       ↓
7. One step given → technician confirms → next step → ... → issue resolved
       ↓
8. save_resolved_case → Firestore (future technicians benefit)
```

The agent only ever gives **one repair action at a time**. It waits for the technician to confirm ("Done" or "That didn't work") before proceeding. This pace is deliberate — dumping a 10-step list is how technicians get overwhelmed and make mistakes.

---

## Architecture Deep Dive

![Architecture Diagram](docs/architecture.png)

### The Frontend: A PWA for the Field

The UI is a **React + TypeScript Progressive Web App** built with Vite. A PWA matters for this use case: it works on both iOS and Android without requiring an app store listing, and it can be bookmarked to the home screen like a native app. This means deployment is a URL, not a binary.

State is managed with **Zustand** — lightweight, no boilerplate, reactive. The app captures camera frames via `getUserMedia` and sends them as base64 JSON. Audio is captured as raw PCM and streamed as binary. Both go over a **single multiplexed WebSocket** — one connection, two data types, minimal overhead.

### The Single WebSocket: A Field Engineering Decision

On a cell tower in rural Montana or a warehouse with spotty Wi-Fi, every open connection costs latency and risk. I engineered the transport layer so that the same WebSocket carries:

- **Binary frames**: raw PCM audio from the microphone
- **JSON frames**: base64-encoded camera images and control messages (like `barge_in`)

A simple byte prefix distinguishes the two in the backend dispatcher. One connection means one TLS handshake, one reconnect logic path, and dramatically lower overhead on weak networks.

### The Backend: FastAPI + ADK on Cloud Run

The backend is a **stateless FastAPI WebSocket server** hosted on **Google Cloud Run**. Cloud Run's automatic scaling means I pay nothing when no technicians are connected and scale horizontally within seconds under load. Each instance is fully stateless — session state lives in the client and the persistent stores (Firestore/Cloud Storage), not in the server.

The AI brain is a **Google ADK `LiveAgent`** configured with Gemini 2.5 Flash Live. ADK gives me structured tool calling over the live audio session — something that isn't trivial to implement from scratch with raw WebSocket streaming.

The agent has exactly four tools:

| Tool | Purpose |
|------|---------|
| `diagnose_frame` | Sends a camera frame to Gemini Vision, returns a structured diagnosis JSON |
| `search_manual` | Cosine similarity search over embedded manual chunks in Cloud Storage |
| `lookup_similar_cases` | Queries Firestore for previously resolved cases on the same equipment |
| `save_resolved_case` | Persists the resolved case to Firestore for future reference |

### RAG Without a Vector Database: A Deliberate Choice

I wanted semantic search without the operational overhead of a managed vector database for an MVP. Here's what I built instead:

- **Ingest time**: Each PDF is split into overlapping 512-token chunks. Each chunk is embedded with Vertex AI's `text-embedding-004` model to produce a 768-dimensional vector. The chunks and their embeddings are serialized as JSON and saved to Cloud Storage.
- **Query time**: The search query is embedded with the same model. Cosine similarity is computed in-process using NumPy against all cached chunk vectors.

The math is:

$$\text{Similarity}(Q, C) = \frac{Q \cdot C}{\|Q\| \|C\|}$$

For 100–500 chunks, this runs in **under a millisecond**. The knowledge base is cached with Python's `lru_cache` after the first request, so cold starts are the only cost. This works perfectly for the single-manual-per-model use case and eliminates an entire infrastructure dependency.

### Firestore: Institutional Memory as a Flywheel

Every team that uses FieldFix contributes to a shared knowledge base of real-world repairs. When a new fault is diagnosed, the `lookup_similar_cases` tool queries Firestore for records with overlapping equipment model and symptom keywords. If a match is found, the agent surfaces it: *"A technician on your team resolved a similar fault on this inverter model last month by replacing the DC fuse string. Want me to check that first?"*

This is a flywheel effect: the more the system is used, the more accurate and specific its guidance becomes.

---

## The Hard Problems

### Barge-In: Getting the AI to Shut Up

The single most frustrating thing about early AI assistants is that they don't stop talking. A stressed technician stuck on step 2 doesn't need to hear steps 4 through 10 at full speed. They need to be able to say "Wait, stop — the panel is still online" and have the AI immediately course-correct.

I implemented a **two-layer barge-in system**:

1. **Frontend layer**: The audio capture loop continuously calculates the RMS energy of the microphone buffer using `AudioWorkletProcessor`. When speech energy exceeds a threshold, a `{ type: "barge_in" }` JSON message is sent immediately over the WebSocket — before the audio even reaches the server.
2. **Backend layer**: The FastAPI handler receives the `barge_in` signal and triggers an interruption of the active ADK session's audio output. Gemini's `automatic_activity_detection` with high sensitivity serves as the fallback for cases where the frontend signal is delayed.

The result: the AI can be cut off mid-sentence with less than 200ms latency on a decent mobile connection. This is what makes the interaction feel natural rather than robotic.

### The Hallucination Problem: Solved by Architecture

LLMs hallucinate. In a repair context — where incorrect guidance can damage equipment or cause injury — this is unacceptable. The solution isn't prompting the AI to be careful. It's making hallucination structurally impossible.

The ADK system prompt contains a hard rule: **the agent must call `search_manual` and receive a result before it is permitted to give any repair advice**. If the tool fails (e.g., the manual hasn't been ingested), the agent tells the technician it cannot safely advise them without a verified source. The citation — section name and page number — is read out loud and displayed in the UI as a `CitationCard` component.

This architectural guardrail is more reliable than any prompt instruction.

---

## Tech Stack At a Glance

| Layer | Technology | Why |
|-------|-----------|-----|
| AI Model | Gemini 2.5 Flash Live API | Bidirectional audio + vision in a single session |
| Agent Framework | Google ADK | Structured tool calling over live streaming |
| Backend | FastAPI + uvicorn | Async WebSocket handling, minimal overhead |
| Compute | Google Cloud Run | Stateless, auto-scaling, pay-per-request |
| Knowledge Base | Cloud Storage + NumPy RAG | No vector DB needed for single-manual retrieval |
| Case History | Firestore | Serverless NoSQL, fast keyword queries |
| Frontend | React + TypeScript + Vite (PWA) | Cross-platform, no app store, home screen installable |
| State | Zustand | Minimal bundle, reactive, no boilerplate |
| Styling | Tailwind CSS | Utility-first, no CSS-in-JS overhead |
| Infrastructure | Terraform IaC | Reproducible, version-controlled deployments |
| CI/CD | Cloud Build | Git-triggered container builds and deploys |

---

## What I Learned

**1. Gemini Live API is genuinely different from chat.**
Streaming bidirectional audio while simultaneously sending vision frames creates an interaction model that has no equivalent in request-response AI. It feels like a phone call, not a form. The latency is low enough that the technician stops thinking about the technology and starts thinking about the repair.

**2. ADK tool calling is a forcing function for reliability.**
Designing tools as guardrails — not just capabilities — fundamentally changes how you think about AI agent safety. The `search_manual` requirement isn't a feature; it's a constraint. Constraints are what make AI safe to deploy in high-stakes environments.

**3. Barge-in is a trust signal, not just a feature.**
Every time the AI stops immediately when interrupted, the technician's trust in the system goes up. It signals: *this tool respects your authority*. Without barge-in, the AI feels like a lecture. With it, it feels like a conversation.

**4. Pace is a UX superpower.**
One step at a time, wait for confirmation. I resisted the temptation to show off by providing comprehensive multi-step answers. The technician is stressed and working with their hands. Pacing is respect. It's also safer — a technician who completes step 1 correctly is in a better position to complete step 2 than one who was handed all 10 steps at once.

**5. Simple RAG is often the right RAG.**
Cosine similarity over pre-embedded chunks in Cloud Storage is perfectly adequate for the single-manual-per-model use case. Vector databases are powerful — they're also infrastructure. Don't add infrastructure until you've proven the use case warrants it.

---

## What's Next

The MVP validates the core loop. The roadmap to production scale is clear:

- **Vertex AI Vector Search**: Scale the knowledge base from one manual per model to thousands of manuals across entire equipment lines.
- **Embedding-based case matching**: Replace keyword overlap in Firestore with semantic similarity over embedded fault summaries for more accurate historical case retrieval.
- **Enterprise integrations**: Sync resolved cases back to ServiceNow, Jira, or SAP PM. Surface FieldFix guidance natively inside existing ticketing workflows.
- **Offline mode**: Cache the knowledge base locally on the PWA for zero-connectivity environments (underground, shielded rooms, remote sites).
- **Multi-language voice**: Gemini Live's multilingual support means a Spanish-speaking technician can speak naturally and receive guidance in Spanish — from the same English-language manual.

---

## Try It Yourself

| Resource | Link |
|----------|------|
| Live Demo | [YOUR_DEMO_URL] |
| Source Code | [YOUR_REPO_URL] |
| Demo Video (< 4 min) | [YOUR_VIDEO_URL] |

Built with Gemini 2.5 Flash Live API, Google Agent Development Kit, FastAPI, Cloud Run, Cloud Storage, Firestore, React, TypeScript, Tailwind CSS, Zustand, Terraform, and NumPy.

Submitted to the [Gemini Live Agent Challenge](https://ai.google.dev) — Track 1: Live Agent.
