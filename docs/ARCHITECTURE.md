# FieldFix AI — Architecture & Design Decisions

> This document explains **why** FieldFix AI is designed the way it is — the constraints, trade-offs, and rationale behind every major architectural choice.

---

## Table of Contents

- [Design Philosophy](#design-philosophy)
- [System Architecture Overview](#system-architecture-overview)
- [Why Gemini Live API (Not REST)](#why-gemini-live-api-not-rest)
- [Why Google ADK with Tool Calling](#why-google-adk-with-tool-calling)
- [Why FastAPI + WebSocket (Not gRPC)](#why-fastapi--websocket-not-grpc)
- [Why RAG Without a Vector Database](#why-rag-without-a-vector-database)
- [Why Firestore for Case History](#why-firestore-for-case-history)
- [Why a Single WebSocket (Not Separate Channels)](#why-a-single-websocket-not-separate-channels)
- [Why React PWA (Not Native)](#why-react-pwa-not-native)
- [Why Zustand (Not Redux / Context)](#why-zustand-not-redux--context)
- [Why Tailwind CSS](#why-tailwind-css)
- [Why Cloud Run (Not GKE / App Engine)](#why-cloud-run-not-gke--app-engine)
- [Why Terraform (Not Pulumi / CDK)](#why-terraform-not-pulumi--cdk)
- [Barge-In Architecture](#barge-in-architecture)
- [Error Handling Philosophy](#error-handling-philosophy)
- [Security Design](#security-design)
- [Scalability Considerations](#scalability-considerations)

---

## Design Philosophy

FieldFix AI is built for a **stressed human working with their hands**. Every design decision flows from this core constraint:

1. **Hands-free first** — Voice + camera are the primary inputs. The technician's hands are greasy, gloved, or holding a tool.
2. **One step at a time** — Never overwhelm. Give exactly one action, wait for confirmation.
3. **Trust through citation** — Every answer is grounded in the equipment manual. Say the section and page number out loud.
4. **Interruptible always** — The technician is the boss. They can cut the AI off mid-sentence at any time.
5. **Fail gracefully** — On a cell tower in rural Montana, connectivity is unreliable. Never crash, never show a stack trace.

---

## System Architecture Overview

![Architecture Diagram](architecture.png)

```
┌─────────────────────────────────────────────────────────┐
│                   Mobile PWA (React)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │  Camera   │  │   Mic    │  │    UI (Citations,    │  │
│  │ (frames)  │  │ (PCM)    │  │  Steps, Diagnosis)   │  │
│  └─────┬─────┘  └─────┬────┘  └──────────────────────┘  │
│        │              │                ▲                  │
│        └──────┬───────┘                │                  │
│               │ WebSocket              │                  │
└───────────────┼────────────────────────┼──────────────────┘
                │                        │
┌───────────────┼────────────────────────┼──────────────────┐
│  Cloud Run    │                        │                  │
│  ┌────────────▼────────────────────────┤──────────────┐   │
│  │         FastAPI WebSocket Handler                  │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │            ADK LiveAgent                     │  │   │
│  │  │  ┌─────────────┐  ┌──────────────────────┐  │  │   │
│  │  │  │diagnose_    │  │  search_manual        │  │  │   │
│  │  │  │frame        │  │  (RAG)                │  │  │   │
│  │  │  └──────┬──────┘  └──────────┬───────────┘  │  │   │
│  │  │  ┌──────┴──────┐  ┌──────────┴───────────┐  │  │   │
│  │  │  │lookup_      │  │  save_resolved_case  │  │  │   │
│  │  │  │similar_cases│  │                      │  │  │   │
│  │  │  └──────┬──────┘  └──────────┬───────────┘  │  │   │
│  │  └─────────┼────────────────────┼───────────────┘  │   │
│  └────────────┼────────────────────┼──────────────────┘   │
│               │                    │                      │
└───────────────┼────────────────────┼──────────────────────┘
                │                    │
    ┌───────────┼────────┐     ┌─────┼────────────┐
    │           ▼        │     │     ▼            │
    │  Gemini Live API   │     │  Cloud Storage   │
    │  (Audio + Vision)  │     │  (Manual Chunks) │
    │                    │     │                  │
    └────────────────────┘     └──────────────────┘
    ┌────────────────────┐
    │                    │
    │    Firestore       │
    │  (Case History)    │
    │                    │
    └────────────────────┘
```

The architecture follows a **hub-and-spoke** pattern: the ADK LiveAgent is the central hub, with 4 tools as spokes reaching out to external services. The frontend connects to this hub through a single multiplexed WebSocket.

---

## Why Gemini Live API (Not REST)

### The Problem
A field repair session is a conversation, not a query. The technician talks while working, asks follow-ups, interrupts, and needs the AI to "see" what they're seeing in real time. Traditional REST-based AI APIs (send text, get text) cannot support this.

### Why Live API
| Requirement | REST API | Live API |
|------------|----------|----------|
| Real-time voice conversation | ❌ Requires separate STT + TTS services | ✅ Native bidirectional audio |
| Vision during conversation | ❌ Separate vision call, loses context | ✅ Image frames integrated into conversation context |
| Barge-in (interruption) | ❌ No concept of interruption | ✅ Built-in automatic activity detection |
| Emotional tone awareness | ❌ Text-only | ✅ `enable_affective_dialog` detects stress/urgency |
| Sub-second response latency | ❌ HTTP round-trip overhead | ✅ Persistent streaming connection |

### Trade-offs Accepted
- **Higher complexity**: WebSocket management, audio serialization, session lifecycle
- **Stateful sessions**: Cannot be load-balanced trivially (addressed via Cloud Run session affinity)
- **Newer API surface**: Less community documentation than REST Gemini

---

## Why Google ADK with Tool Calling

### The Problem
A raw Gemini Live conversation would produce ungrounded responses — the AI might hallucinate repair steps that sound plausible but aren't in the manual. It also wouldn't be able to read from or write to databases.

### Why ADK
The Agent Development Kit (ADK) provides **structured tool calling** within a Live session. This is the critical architectural decision that makes FieldFix reliable:

1. **`diagnose_frame`** — Forces the agent to analyze the camera image through a structured Gemini Vision call, returning JSON with severity, confidence, and specific attention directives. Without this tool, the agent would make vague observations.

2. **`search_manual`** — **The most important tool.** Forces the agent to ground every answer in the actual equipment manual before giving advice. The agent physically cannot bypass this — the system prompt mandates calling it before any repair guidance.

3. **`lookup_similar_cases`** — Queries institutional memory. A new technician benefits from what 50 other technicians have already solved.

4. **`save_resolved_case`** — Creates a feedback loop. Every fix becomes a future training example.

### Why Not LangChain / LlamaIndex?
- ADK integrates natively with Gemini Live API. LangChain would require a separate orchestration layer.
- Competition requirement: ADK is mandatory for the Gemini Live Agent Challenge.
- ADK's `LiveAgent` handles audio/vision natively — no adapter code needed.

---

## Why FastAPI + WebSocket (Not gRPC)

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| **gRPC** | Efficient binary protocol, streaming | No browser support without proxy, complex client code |
| **Socket.IO** | Auto-reconnect, rooms, namespaces | Extra abstraction layer, not needed for 1:1 sessions |
| **FastAPI WebSocket** | Native browser support, simple client, good Python async support | Manual reconnect logic needed |

### Decision
**FastAPI WebSocket** — because the client is a mobile browser. gRPC would require a proxy (Envoy/etc), adding operational complexity. Socket.IO adds unnecessary abstraction for a 1:1 session model.

### Multiplexing Design
A single WebSocket carries both binary audio and JSON control messages:

```
Binary frames  → PCM audio from microphone
                ← PCM audio from agent

JSON frames   → { type: "video_frame", data: base64jpeg }
              → { type: "barge_in" }
              → { type: "session_init", ... }
              ← { type: "tool_result", tool: "search_manual", data: {...} }
              ← { type: "session_ready" }
```

**Why single connection?** Mobile networks are unreliable. Establishing and maintaining one WebSocket is hard enough — managing two or three (audio, video, control) would multiply failure modes.

---

## Why RAG Without a Vector Database

### The Problem
Equipment manuals need to be searchable by semantic meaning, not just keywords. "DC overvoltage fault on string 3" needs to match a section titled "High Voltage Protection Mechanisms."

### Alternatives Considered
| Option | Pros | Cons |
|--------|------|------|
| **Pinecone / Weaviate** | Scalable, fast, purpose-built | Extra service to manage, additional cost, latency |
| **pgvector (Cloud SQL)** | Familiar PostgreSQL, ACID | Overkill for 100-500 chunks per manual, expensive for demo |
| **In-process cosine similarity** | Zero additional services, cached after first load, sub-ms search | Doesn't scale past ~10K chunks |

### Decision
**In-process cosine similarity with NumPy**, chunks stored as JSON in Cloud Storage.

The reasoning:
1. A typical equipment manual produces **100–500 chunks** after splitting. Cosine similarity over 500 vectors of dimension 768 takes **< 1ms** in NumPy.
2. Chunks are cached in-process with `@lru_cache` — first request loads from GCS, all subsequent searches are memory-only.
3. **Zero additional infrastructure** — no database to manage, no connection pooling, no schema migrations.
4. **Scales horizontally** by nature: each Cloud Run instance loads its own cache. No shared state.

### When to Upgrade
If FieldFix needed to search across **thousands of manuals simultaneously**, we'd add a vector database. For the per-model-per-industry scoping (one manual per equipment model), in-process search is the optimal choice.

---

## Why Firestore for Case History

### The Problem
When a technician encounters a fault, they should immediately know: "Has anyone on my team fixed this before?"

### Why Firestore (Not Cloud SQL / BigQuery)
| Requirement | Firestore | Cloud SQL | BigQuery |
|-------------|-----------|-----------|----------|
| Schema-flexible documents | ✅ Native | ❌ Rigid schema | ❌ Analytical, not transactional |
| Real-time writes from tools | ✅ Sub-second | ✅ | ❌ Batch-oriented |
| Querying by equipment model | ✅ Composite index | ✅ | ✅ |
| Serverless (no connection management) | ✅ | ❌ Needs connection pooling | ✅ |
| Competition requirement (GCP service) | ✅ | ✅ | ✅ |

**Firestore wins** because:
1. **Schema flexibility** — fault cases vary wildly. Solar inverter cases have "string voltage," HVAC cases have "refrigerant pressure." A rigid SQL schema would require constant migrations.
2. **Serverless** — no connection pools to manage. Each Cloud Run instance calls Firestore directly.
3. **Composite indexes** — the `(equipment_model, resolved, timestamp)` index supports the exact query pattern the `lookup_similar_cases` tool needs.

### Keyword Matching vs. Embedding Similarity
The current MVP uses **keyword overlap** for case matching. This is intentionally simple:

```python
fault_words = set(description.lower().split()) - stop_words
overlap = len(fault_words & summary_words)
```

**Why not embeddings?** Adding embedding-based search to Firestore would require storing and comparing vectors, essentially building a vector database inside Firestore. The keyword approach works well because fault descriptions are highly technical and share specific terms ("overvoltage," "CRC errors," "discharge pressure"). A v2 upgrade path is documented in the code.

---

## Why a Single WebSocket (Not Separate Channels)

### Alternatives
1. **Separate WebSockets** for audio, video, and control messages
2. **WebRTC** for audio/video, WebSocket for control
3. **Single multiplexed WebSocket** for everything

### Decision: Single Multiplexed WebSocket

The key insight is that **mobile networks treat all connections as competition**. On a cell tower or satellite link:
- Each TCP connection competes for bandwidth
- Connection establishment (TLS handshake) is expensive on high-latency links
- Connection failures are correlated (if one drops, they all drop)

A single WebSocket means:
- **One TLS handshake** instead of three
- **One reconnect logic** instead of three
- **Natural ordering** — audio and control messages arrive in order relative to each other
- **Simpler client code** — the `useWebSocket` hook manages one connection

---

## Why React PWA (Not Native)

### The Problem
Field technicians use a mix of Android and iOS devices. Some use company-issued phones, others use personal devices.

### Why PWA
| Requirement | Native App | React PWA |
|-------------|-----------|-----------|
| Cross-platform (iOS + Android) | ❌ Two codebases (or React Native) | ✅ Single codebase |
| Camera + microphone access | ✅ Full access | ✅ getUserMedia API |
| No app store approval needed | ❌ Review process | ✅ Just a URL |
| Offline support | ✅ | ✅ Service worker |
| Installation without app store | ❌ | ✅ "Add to Home Screen" |
| Update delivery | App store push | ✅ Automatic on next visit |

**The dealbreaker for native**: app store review timelines. In an enterprise context, deploying an update to fix a bug in a tool function should take minutes, not days.

### Trade-offs Accepted
- No background audio processing when app is minimized (acceptable — technician should have the app open while working)
- Slightly less precise audio on some iOS Safari versions (mitigated with echo cancellation + noise suppression flags)

---

## Why Zustand (Not Redux / Context)

### The Problem
Session state is complex: connection status, agent state, diagnosis results, citations, repair steps, case history, and errors. This state is updated from WebSocket messages, tool results, and user actions.

### Why Zustand
| Feature | React Context | Redux | Zustand |
|---------|--------------|-------|---------|
| Bundle size | 0 KB | ~7 KB | ~1 KB |
| Boilerplate | Low | High | Very low |
| Re-render optimization | Manual (useMemo) | connect() | Built-in selectors |
| TypeScript support | Manual | Good | Excellent |
| Devtools | ❌ | ✅ | ✅ (optional) |

**Zustand** because:
1. **Minimal boilerplate** — the entire store is ~80 lines including types
2. **Selective re-renders** — components subscribe to only the slices they need
3. **No Provider wrapper** — simpler component tree, works naturally with hooks
4. **Tiny bundle** — matters for PWA first-load performance on mobile

---

## Why Tailwind CSS

Tailwind was **explicitly required** by the project specification. Beyond the requirement:

1. **Utility-first** — glassmorphism, gradients, and responsive layouts compose naturally from utilities
2. **Dark mode design system** — custom theme tokens (CSS variables in Tailwind v4) define the entire visual language
3. **No CSS-in-JS runtime cost** — styles are compiled at build time, zero runtime overhead
4. **Mobile-first responsive** — `lg:` breakpoint handles the desktop sidebar layout

---

## Why Cloud Run (Not GKE / App Engine)

| Requirement | Cloud Run | GKE | App Engine |
|-------------|-----------|-----|------------|
| WebSocket support | ✅ (with session affinity) | ✅ | ❌ (60s timeout) |
| Scale to zero | ✅ | ❌ | ✅ (Standard) |
| Container-based | ✅ | ✅ | ❌ (Flexible only) |
| Terraform support | ✅ Simple | ✅ Complex | ✅ |
| Cost at low traffic | Very low | High (cluster overhead) | Low |
| Competition requirement | ✅ | ✅ | ✅ |

**Cloud Run wins** because:
1. **WebSocket support with min-instance = 1** — keeps at least one warm instance to avoid cold-start latency for the first technician of the day
2. **Scale to 10 instances** — handles concurrent sessions during peak hours
3. **Simple Terraform resource** — `google_cloud_run_v2_service` is one resource, not a cluster + node pool + deployment + service + ingress
4. **Startup CPU boost** — doubles CPU during container startup for fast first-response

---

## Why Terraform (Not Pulumi / CDK)

1. **Competition requirement** — Terraform IaC in `/infra/` is specified
2. **Google provider maturity** — `hashicorp/google` ~5.0 has first-class support for all GCP resources used
3. **Declarative** — the entire infrastructure is readable in `main.tf` without understanding a programming language
4. **State in GCS** — remote backend ensures team collaboration (with the noted chicken-and-egg for the state bucket)

---

## Barge-In Architecture

Barge-in (the technician interrupting the AI mid-sentence) is the most complex real-time feature:

```
Time ──────────────────────────────────────────────────────►

Agent:  "According to the manual, section 6.2, you should ch--"
           ▲                                               ▲
           │                                               │
           └── Agent speaking (audio chunks flowing)       └── INTERRUPTED

Tech:                                    "Wait, I don't have—"
                                          ▲
                                          │
                                          └── Speech detected (RMS > threshold)
```

### How It Works

1. **Frontend detects speech** — `useMicrophone` calculates RMS energy per audio buffer. When RMS > 0.01, it fires `onSpeechStart`.
2. **Frontend sends barge-in** — `useWebSocket.sendBargeIn()` sends `{ type: "barge_in" }` to the backend.
3. **Backend interrupts agent** — `runner.interrupt()` tells the ADK LiveAgent to stop generating audio.
4. **Agent acknowledges** — The agent's system prompt says: "Never restart a sentence that was interrupted — just answer the new question."
5. **Gemini's own VAD** — `automatic_activity_detection` with high sensitivity provides a second layer of interruption detection at the API level.

### Why Two Layers?
The frontend speech detection provides **faster** interruption (no network round-trip to Gemini's servers). Gemini's built-in VAD provides a **more accurate** fallback. Together, they ensure the technician is never stuck waiting for the AI to finish talking.

---

## Error Handling Philosophy

### Backend: Never Crash, Always Return
Every tool function follows this pattern:

```python
try:
    # Normal operation
    return {"found": True, "results": [...]}
except Exception as e:
    logger.error("Tool failed", error=str(e))
    return {"found": False, "results": [], "message": "Service unavailable."}
```

**Why?** An unhandled exception in a tool would terminate the entire Live session. The technician would have to reconnect, re-describe their problem, and re-point their camera. Instead, the agent receives an error-state dict and can tell the technician: "I couldn't search the manual right now, but based on what I can see..."

### Frontend: Degrade, Don't Die
- Camera fails → Show fallback UI, allow voice-only mode
- WebSocket drops → Exponential backoff reconnect (5 attempts)
- Audio context suspended → Resume on next user interaction (browser autoplay policy)

---

## Security Design

| Threat | Mitigation |
|--------|-----------|
| API key exposure | Application Default Credentials (ADC) — no keys in code or env vars |
| Oversized frames (DoS) | `max_frame_size_bytes` = 500KB enforced before Gemini call |
| CORS bypass | `cors_origins` from config, not hardcoded `*` |
| Session hijacking | UUID session IDs, session timeout after 30min inactivity |
| Malicious PDF upload | `ingest_pdf.py` is a CLI tool, not an API endpoint — only admins run it |

---

## Scalability Considerations

### Current Design (MVP — handles ~50 concurrent sessions)
- Single Cloud Run instance per session (stateful WebSocket)
- In-process chunk cache (no shared state)
- Firestore handles concurrent writes natively

### Scaling Path (v2 — hundreds of concurrent sessions)
| Bottleneck | Current | Upgrade Path |
|-----------|---------|-------------|
| Session state | In-memory dict | Redis for session registry |
| KB search | In-process NumPy | Vector database (Vertex AI Vector Search) |
| Case matching | Keyword overlap | Embedding similarity via Firestore extensions |
| Audio processing | Single-threaded per session | Already handled by Gemini API |
| Static frontend | Served by Vite dev server | CDN (Cloud Storage + Cloud CDN) |

The key insight is that **the current architecture doesn't need to change fundamentally to scale** — each component has a clear upgrade path that replaces the implementation without changing the interfaces.
