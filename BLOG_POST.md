# Building FieldFix AI for the Gemini Live Agent Challenge

#GeminiLiveAgentChallenge

## TL;DR

FieldFix AI is a real-time AI assistant that helps field technicians diagnose and repair equipment on-site. By combining Gemini's Live API for voice and vision with a RAG knowledge base built from equipment manuals, it delivers expert guidance — one step at a time — with inline citations. Every resolved case is saved to Firestore, building institutional memory that helps the next technician facing the same fault.

## The Problem

Field technicians work in high-pressure environments. Equipment is down, customers are waiting, and the manual is either a 400-page PDF or back in the van. Current solutions — calling the office, scrolling through PDFs on a phone, or searching forums — are slow, imprecise, and error-prone.

We built FieldFix AI to give every technician a senior engineer in their ear — one who has read the entire manual and remembers every repair their team has ever done.

## Architecture

![Architecture](docs/architecture.png)

### How it works

1. **Technician opens the app** → selects industry + equipment model
2. **Camera captures the device** → frames are sent to Gemini Vision for visual diagnosis
3. **Voice describes the problem** → audio streams via Gemini Live API for real-time conversation
4. **RAG search** → every answer is grounded in the equipment manual (pre-embedded chunks in Cloud Storage)
5. **Case history check** → Firestore is queried for previously resolved cases on the same equipment
6. **Step-by-step guidance** → one action at a time, waiting for confirmation before proceeding
7. **Resolved case saved** → once the fix is confirmed, the case is saved to Firestore for future reference

### Tech Stack

- **AI**: Gemini 2.5 Flash Live API (audio + vision) via Google ADK
- **Backend**: FastAPI + WebSocket, deployed on Cloud Run
- **Knowledge Base**: PDF manuals → chunked + embedded → Cloud Storage (RAG without a vector DB)
- **Case History**: Firestore (institutional memory across all technicians)
- **Frontend**: React + TypeScript + Tailwind CSS (PWA-ready)
- **Infrastructure**: Terraform IaC, Cloud Build CI/CD

## The Hard Parts

### Real-time Barge-In

The biggest UX challenge was interruption handling. A stressed technician will absolutely talk over the AI when they have an urgent question. We configured Gemini's `automatic_activity_detection` with high sensitivity for both speech start and end, and implemented a barge-in signal from the frontend's speech detection to immediately interrupt the agent's audio output.

### RAG Without a Vector Database

For the MVP, we avoided adding a vector database dependency by storing pre-embedded chunks as JSON in Cloud Storage. Cosine similarity search runs in-process with NumPy. The knowledge base is cached with `lru_cache` after first load, so subsequent searches are sub-millisecond. This approach works surprisingly well for single-manual-per-model scenarios and keeps the architecture simple.

### Firestore as Institutional Memory

Every resolved case is saved with structured metadata: equipment model, fault summary, steps taken, resolution, and parts replaced. When a new fault is identified, we query Firestore for matching cases using keyword overlap (with plans for embedding-based semantic search in v2). This creates a flywheel effect — the more your team uses FieldFix, the smarter it gets.

## What We Learned

1. **Gemini Live API is genuinely conversational** — the ability to stream audio bidirectionally while also sending vision frames creates an experience that feels like a real video call with an expert.

2. **ADK tools make the agent grounded** — without the `search_manual` tool, the agent would hallucinate repair steps. With citations, the technician can trust the guidance.

3. **Barge-in is a killer feature** — being able to interrupt the AI mid-sentence makes the interaction feel natural rather than robotic. It's the difference between a useful tool and a frustrating one.

4. **Simple RAG is often enough** — cosine similarity over pre-embedded chunks, stored as JSON, is perfectly adequate for single-document retrieval. Don't over-engineer the first version.

## Try It Yourself

- **Live Demo**: [YOUR_DEMO_URL]
- **Source Code**: [YOUR_REPO_URL]
- **Demo Video**: [YOUR_VIDEO_URL]

Built for the [Gemini Live Agent Challenge](https://ai.google.dev) — Track 1: Live Agent.
