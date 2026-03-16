# FieldFix AI — Coding Agent Prompt
## Production-Grade Field Technician Assistant (Gemini Live Agent Challenge)

---

## OVERVIEW

Build **FieldFix AI** — a production-grade, real-time AI assistant for on-site field technicians (solar, telecom, HVAC, lab equipment, factory maintenance). The technician points their phone camera at a broken device, describes the problem by voice, and receives live expert voice guidance grounded in the actual equipment manual — with inline citations shown in the UI.

This application is a submission for the **Gemini Live Agent Challenge** (Track 1: Live Agent). Every architectural and implementation decision must satisfy the judging criteria for that competition.

---

## MANDATORY COMPETITION REQUIREMENTS

Every item below is a hard requirement. Missing any one of them risks disqualification.

1. Uses **Gemini Live API** (real-time audio + vision streaming)
2. Uses **Google Agent Development Kit (ADK)** with tool calling
3. Backend hosted on **Google Cloud Run**
4. At least one additional GCP service — use **Firestore** AND **Cloud Storage**
5. **Terraform IaC** deployment scripts in `/infra/` directory
6. Architecture diagram PNG saved to `/docs/architecture.png`
7. Demo video <4 minutes (real interactions, no mockups) — README must link to it
8. Blog post placeholder in `BLOG_POST.md` with hashtag `#GeminiLiveAgentChallenge`
9. `README.md` must include: live demo URL, one-command local setup, GCP deploy instructions, GDG profile link placeholder

---

## TECH STACK

### Backend
- **Runtime**: Python 3.12
- **Framework**: FastAPI with uvicorn
- **AI**: Google Gemini 2.5 Flash Live API via `google-genai` SDK
- **Agent**: Google ADK (`google-adk`) — `LiveAgent` with 4 tools
- **Database**: Google Cloud Firestore (fault case history)
- **Storage**: Google Cloud Storage (manual PDFs + embedded chunks)
- **Deployment**: Docker → Cloud Run (via Terraform)
- **Embeddings**: `text-embedding-004` model (via Vertex AI)

### Frontend
- **Framework**: React 18 + Vite (PWA-ready)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Real-time**: Native WebSocket API
- **Camera/Mic**: MediaDevices API (getUserMedia)
- **State**: Zustand
- **Build**: Vite with PWA plugin (`vite-plugin-pwa`)

### Infrastructure
- **IaC**: Terraform >= 1.6
- **Services**: Cloud Run, Firestore, Cloud Storage, Vertex AI, Artifact Registry, IAM, Secret Manager
- **CI/CD**: Cloud Build trigger (optional, include `cloudbuild.yaml`)

---

## PROJECT STRUCTURE

```
fieldfix-ai/
├── backend/
│   ├── main.py                    # FastAPI app + WebSocket handler
│   ├── agent.py                   # ADK LiveAgent definition
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── visual_diagnosis.py    # Camera frame → Gemini vision → structured JSON
│   │   ├── kb_lookup.py           # Cosine search on Cloud Storage chunks
│   │   ├── case_history.py        # Firestore: lookup similar + save resolved case
│   │   └── ingest_pdf.py          # One-shot PDF ingestion pipeline (CLI script)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── session.py             # Pydantic models for session state
│   │   └── case.py                # Pydantic models for fault cases
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings via pydantic-settings + env vars
│   │   ├── logging.py             # Structured JSON logging (Cloud Logging compatible)
│   │   └── gcp.py                 # GCP client singletons (Firestore, GCS, Vertex)
│   ├── tests/
│   │   ├── test_kb_lookup.py
│   │   ├── test_case_history.py
│   │   └── test_visual_diagnosis.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── components/
│   │   │   ├── CameraFeed.tsx     # Live camera with frame capture overlay
│   │   │   ├── CitationCard.tsx   # Animated citation panel (manual ref + page)
│   │   │   ├── CaseHistoryPanel.tsx  # Firestore case history sidebar
│   │   │   ├── VoiceIndicator.tsx # Speaking/listening/interrupted state
│   │   │   ├── IndustrySelector.tsx  # Solar / Telecom / HVAC / Lab / Factory
│   │   │   └── StepTracker.tsx    # Current repair step + progress
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts    # WS connection + reconnect logic
│   │   │   ├── useCamera.ts       # getUserMedia + frame sampling
│   │   │   └── useMicrophone.ts   # PCM audio capture + streaming
│   │   ├── store/
│   │   │   └── sessionStore.ts    # Zustand store for session state
│   │   ├── types/
│   │   │   └── index.ts           # Shared TypeScript interfaces
│   │   └── utils/
│   │       ├── audio.ts           # PCM encoding helpers
│   │       └── frameCapture.ts    # Canvas frame extraction
│   ├── public/
│   │   ├── manifest.json          # PWA manifest
│   │   └── icons/                 # PWA icons (192, 512)
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
├── infra/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── docs/
│   ├── architecture.png           # System architecture diagram (required by competition)
│   └── DEMO_SCRIPT.md             # 4-minute demo script
├── manuals/
│   └── sample_solar_inverter.pdf  # Sample manual for seeding the demo KB
├── scripts/
│   └── seed_firestore.py          # Seeds 10 realistic historical cases
├── docker-compose.yml             # Local dev with emulators
├── cloudbuild.yaml
├── BLOG_POST.md
└── README.md
```

---

## BACKEND: DETAILED IMPLEMENTATION

### `backend/core/config.py`
```python
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # GCP
    gcp_project_id: str
    gcp_region: str = "us-central1"
    gcs_bucket_name: str = "fieldfix-knowledge-base"
    firestore_collection: str = "fault_cases"

    # Gemini
    gemini_live_model: str = "gemini-2.5-flash-live"
    gemini_vision_model: str = "gemini-2.5-flash"
    embedding_model: str = "text-embedding-004"

    # App
    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]
    max_frame_size_bytes: int = 500_000  # 500KB max per frame
    frame_sample_interval_ms: int = 2500  # Sample camera every 2.5s

    class Config:
        env_file = ".env"

settings = Settings()
```

### `backend/main.py`

```python
"""
FastAPI app. Key responsibilities:
- Accept WebSocket connections at /ws/{session_id}
- Multiplex binary audio frames and JSON control messages
- Maintain per-session ADK LiveAgent runner
- Handle barge-in: signal to agent when user starts speaking mid-response
- Forward agent audio output back to client
- Structured logging (Cloud Logging compatible JSON)
"""

import asyncio
import json
import base64
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import get_logger
from core.gcp import get_firestore, get_gcs_client
from agent import create_agent_runner

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FieldFix AI starting", env=settings.environment)
    yield
    logger.info("FieldFix AI shutting down")

app = FastAPI(
    title="FieldFix AI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session registry (use Redis in production scale-out)
active_sessions: dict[str, dict] = {}

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/industries")
async def list_industries():
    """Return available industry + equipment model combinations."""
    return {
        "industries": [
            {
                "id": "solar",
                "label": "Solar",
                "equipment": ["SMA-Sunny5000", "Fronius-Symo", "Huawei-SUN2000"]
            },
            {
                "id": "telecom",
                "label": "Telecom",
                "equipment": ["Cisco-ASR9000", "Nokia-FSED", "Ericsson-RBS"]
            },
            {
                "id": "hvac",
                "label": "HVAC",
                "equipment": ["Carrier-30XA", "Daikin-VRV", "Trane-CGAM"]
            },
            {
                "id": "lab",
                "label": "Lab Equipment",
                "equipment": ["Agilent-HPLC", "Thermo-Centrifuge", "Beckman-UV"]
            },
            {
                "id": "factory",
                "label": "Factory",
                "equipment": ["Siemens-S7-1500", "ABB-IRB6700", "Fanuc-R2000"]
            }
        ]
    }

@app.websocket("/ws/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str
):
    await websocket.accept()
    logger.info("WebSocket connected", session_id=session_id)

    runner = None
    try:
        # First message must be session init
        init_raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        init_msg = json.loads(init_raw)
        assert init_msg["type"] == "session_init", "First message must be session_init"

        industry = init_msg["industry"]
        equipment_model = init_msg["equipment_model"]
        technician_id = init_msg.get("technician_id", "anonymous")

        runner = await create_agent_runner(
            session_id=session_id,
            industry=industry,
            equipment_model=equipment_model,
            technician_id=technician_id,
        )

        active_sessions[session_id] = {
            "runner": runner,
            "industry": industry,
            "equipment_model": equipment_model,
        }

        # Forward agent audio output to client
        async def on_audio_output(audio_bytes: bytes):
            await websocket.send_bytes(audio_bytes)

        # Forward citation/step updates to client
        async def on_tool_result(tool_name: str, result: dict):
            await websocket.send_text(json.dumps({
                "type": "tool_result",
                "tool": tool_name,
                "data": result
            }))

        runner.on_audio_output(on_audio_output)
        runner.on_tool_result(on_tool_result)
        await runner.start()

        await websocket.send_text(json.dumps({
            "type": "session_ready",
            "session_id": session_id
        }))

        # Main receive loop
        while True:
            message = await websocket.receive()

            if "bytes" in message:
                # Raw PCM audio from microphone
                await runner.send_audio(message["bytes"])

            elif "text" in message:
                msg = json.loads(message["text"])

                if msg["type"] == "video_frame":
                    # Base64-encoded JPEG from camera
                    frame_bytes = base64.b64decode(msg["data"])
                    if len(frame_bytes) <= settings.max_frame_size_bytes:
                        await runner.send_image(frame_bytes, mime_type="image/jpeg")

                elif msg["type"] == "barge_in":
                    # User started speaking — interrupt agent
                    await runner.interrupt()

                elif msg["type"] == "end_session":
                    break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", session_id=session_id)
    except asyncio.TimeoutError:
        logger.warning("Session init timeout", session_id=session_id)
        await websocket.close(code=1008)
    except Exception as e:
        logger.error("Session error", session_id=session_id, error=str(e))
        await websocket.close(code=1011)
    finally:
        if runner:
            await runner.close()
        active_sessions.pop(session_id, None)
        logger.info("Session cleaned up", session_id=session_id)
```

### `backend/agent.py`

```python
"""
ADK LiveAgent definition.
One agent instance per WebSocket session (per technician on-site job).
"""

from google.adk.agents import LiveAgent
from google.adk.runners import LiveRunner
from google.genai.types import LiveConnectConfig, SpeechConfig, VoiceConfig

from core.config import settings
from tools.visual_diagnosis import diagnose_frame
from tools.kb_lookup import search_manual
from tools.case_history import lookup_similar_cases, save_resolved_case

SYSTEM_PROMPT = """You are FieldFix AI, an expert field technician assistant.

CONTEXT:
- Industry: {industry}
- Equipment: {equipment_model}
- Technician ID: {technician_id}

YOUR ROLE:
You are an experienced senior engineer with 20 years of hands-on experience
with this equipment. The technician is on-site, likely with limited cell
signal, probably with greasy or gloved hands. They are stressed. Help them.

MANDATORY BEHAVIOUR:
1. OBSERVE BEFORE SPEAKING. When you receive a camera frame, study it
   carefully. If you cannot see the relevant part clearly, ask them to
   move closer or adjust the angle before diagnosing.

2. GROUND EVERY ANSWER IN THE KNOWLEDGE BASE. Before giving any repair
   advice, call search_manual. Cite the section and page number in your
   response — say it aloud AND it will appear in the UI. Example:
   "According to the SMA Inverter Manual, section 6.2, page 44..."

3. ONE STEP AT A TIME. Give exactly one repair action. Wait for the
   technician to confirm before proceeding. Never front-load all steps.

4. CHECK CASE HISTORY FIRST. When a fault is identified, call
   lookup_similar_cases. If there's a match, mention it:
   "Two of your colleagues fixed this same fault last month —
   here's what worked."

5. SAVE EVERY RESOLVED CASE. When the technician says the fix worked,
   call save_resolved_case immediately.

6. BE INTERRUPTIBLE. You can and should be interrupted at any time.
   Always acknowledge the interruption and adapt. Never restart a
   sentence that was interrupted — just answer the new question.

7. DRAW ATTENTION. When you see something specific in the camera frame
   that needs action, be precise: "I can see the DC+ terminal — the
   red connector on the lower left of the inverter. That's the one
   you need to check."

TONE:
- Direct. No filler phrases like "Certainly!" or "Great question!"
- Calm and confident even in urgent situations
- Short sentences — the technician is working while listening
"""

async def create_agent_runner(
    session_id: str,
    industry: str,
    equipment_model: str,
    technician_id: str,
) -> LiveRunner:
    system = SYSTEM_PROMPT.format(
        industry=industry,
        equipment_model=equipment_model,
        technician_id=technician_id,
    )

    agent = LiveAgent(
        model=settings.gemini_live_model,
        system_instruction=system,
        tools=[
            diagnose_frame,
            search_manual,
            lookup_similar_cases,
            save_resolved_case,
        ],
        config=LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config={"voice_name": "Aoede"}
                )
            ),
            enable_affective_dialog=True,
            # Barge-in: agent stops when user speaks
            realtime_input_config={
                "automatic_activity_detection": {
                    "disabled": False,
                    "start_of_speech_sensitivity": "START_SENSITIVITY_HIGH",
                    "end_of_speech_sensitivity": "END_SENSITIVITY_HIGH",
                }
            },
        ),
    )

    runner = LiveRunner(
        agent=agent,
        session_id=session_id,
    )

    return runner
```

### `backend/tools/visual_diagnosis.py`

```python
"""
Tool: diagnose_frame
Accepts a base64 JPEG camera frame + verbal description.
Returns structured diagnosis with attention directive and parts list.
"""

import base64
import json
import re
from google.adk.tools import tool
from google import genai

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

VISION_PROMPT = """You are an expert field technician analyzing a photo of equipment.

User description: "{description}"
Industry: {industry}
Equipment: {equipment_model}

Examine this image carefully. Look for:
- Visible damage, burn marks, corrosion, loose connectors
- LED status lights and their color/blink patterns
- Cable routing issues, missing components
- Error codes on displays

Respond ONLY with valid JSON in this exact format:
{{
  "issues_found": [
    {{
      "description": "specific description of what you see",
      "location_in_frame": "where exactly in the image (e.g. lower-left connector)"
    }}
  ],
  "severity": "low | medium | high | critical",
  "likely_fault": "concise fault name",
  "confidence": 0.0 to 1.0,
  "draw_attention_to": "one specific thing in the image to look at now",
  "immediate_action": "single next action for the technician",
  "parts_likely_needed": ["part name", ...],
  "safe_to_operate": true or false,
  "needs_closer_view": true or false,
  "closer_view_instruction": "what angle/area to show if needs_closer_view is true"
}}

If the image is too blurry, dark, or not showing the relevant equipment part,
set needs_closer_view to true and provide a clear instruction."""


@tool
def diagnose_frame(
    image_base64: str,
    description: str,
    industry: str,
    equipment_model: str,
) -> dict:
    """
    Analyze a camera frame of the equipment to identify visible faults.
    Call this whenever a new image is received or when the technician
    describes a visual symptom. Always call search_manual after this
    to ground the diagnosis in documentation.

    Args:
        image_base64: Base64-encoded JPEG image from the camera
        description: What the technician says they're seeing or experiencing
        industry: Equipment industry category (solar, telecom, hvac, lab, factory)
        equipment_model: Specific equipment model identifier

    Returns:
        Structured diagnosis with fault details, severity, and attention directive
    """
    try:
        client = genai.Client()

        response = client.models.generate_content(
            model=settings.gemini_vision_model,
            contents=[
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64,
                            }
                        },
                        {
                            "text": VISION_PROMPT.format(
                                description=description,
                                industry=industry,
                                equipment_model=equipment_model,
                            )
                        },
                    ]
                }
            ],
        )

        raw = response.text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        result = json.loads(raw)

        logger.info(
            "Visual diagnosis complete",
            fault=result.get("likely_fault"),
            severity=result.get("severity"),
            confidence=result.get("confidence"),
        )
        return result

    except json.JSONDecodeError as e:
        logger.error("Vision response not valid JSON", error=str(e))
        return {
            "issues_found": [],
            "severity": "unknown",
            "likely_fault": "Unable to parse visual",
            "confidence": 0.0,
            "draw_attention_to": "",
            "immediate_action": "Please describe the issue verbally",
            "parts_likely_needed": [],
            "safe_to_operate": False,
            "needs_closer_view": True,
            "closer_view_instruction": "Show the equipment label and any indicator lights"
        }
    except Exception as e:
        logger.error("Visual diagnosis failed", error=str(e))
        raise
```

### `backend/tools/kb_lookup.py`

```python
"""
Tool: search_manual
RAG over equipment manuals stored in Cloud Storage as pre-embedded chunks.
No external vector DB required — cosine similarity in-process for MVP.

Ingestion: run tools/ingest_pdf.py once per manual.
Storage: gs://{bucket}/{industry}/{equipment_model}/chunks.json
"""

import json
import numpy as np
from functools import lru_cache
from google.adk.tools import tool
from google.cloud import storage
from google import genai

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=20)
def _load_chunks(industry: str, equipment_model: str) -> list[dict]:
    """Load and cache chunks from Cloud Storage."""
    gcs = storage.Client()
    bucket = gcs.bucket(settings.gcs_bucket_name)
    blob = bucket.blob(f"{industry}/{equipment_model}/chunks.json")

    if not blob.exists():
        logger.warning(
            "No knowledge base found",
            industry=industry,
            equipment_model=equipment_model
        )
        return []

    return json.loads(blob.download_as_text())


def _embed(text: str) -> list[float]:
    client = genai.Client()
    response = client.models.embed_content(
        model=settings.embedding_model,
        content=text,
    )
    return response.embeddings[0].values


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr = np.array(a)
    b_arr = np.array(b)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / norm)


@tool
def search_manual(
    query: str,
    industry: str,
    equipment_model: str,
    top_k: int = 3,
) -> dict:
    """
    Search the equipment manual knowledge base for relevant sections.
    ALWAYS call this before giving repair advice. The results must be
    cited in your response with section and page number.

    Args:
        query: The technical question or fault description to search for
        industry: Equipment industry (solar, telecom, hvac, lab, factory)
        equipment_model: Specific model identifier
        top_k: Number of results to return (default 3)

    Returns:
        Top matching manual sections with citation references
    """
    chunks = _load_chunks(industry, equipment_model)

    if not chunks:
        return {
            "found": False,
            "message": f"No manual loaded for {equipment_model}. Proceeding from general knowledge.",
            "results": []
        }

    query_embedding = _embed(query)

    scored = []
    for chunk in chunks:
        if "embedding" not in chunk:
            continue
        score = _cosine_similarity(query_embedding, chunk["embedding"])
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:top_k]

    results = []
    for score, chunk in top:
        if score < 0.3:  # Relevance threshold
            continue
        results.append({
            "text": chunk["text"][:600],  # Truncate for context window
            "citation": f"{chunk['source']} §{chunk['section']} · p.{chunk['page']}",
            "source": chunk["source"],
            "section": chunk["section"],
            "page": chunk["page"],
            "relevance_score": round(score, 3),
        })

    logger.info(
        "KB search complete",
        query=query[:50],
        results_found=len(results),
    )

    return {
        "found": len(results) > 0,
        "results": results,
    }
```

### `backend/tools/case_history.py`

```python
"""
Tools: lookup_similar_cases, save_resolved_case
Firestore-backed institutional memory of fault resolutions.
"""

from datetime import datetime, timezone
from google.adk.tools import tool
from google.cloud import firestore

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


def _get_db():
    return firestore.Client()


@tool
def lookup_similar_cases(
    fault_description: str,
    equipment_model: str,
    industry: str,
    limit: int = 3,
) -> dict:
    """
    Look up Firestore for previously resolved cases matching this fault
    on the same equipment model. Call this immediately after diagnosing
    the fault type. If results exist, mention them to the technician.

    Args:
        fault_description: Brief description of the fault observed
        equipment_model: Equipment model identifier
        industry: Industry category
        limit: Max cases to return

    Returns:
        List of similar resolved cases with resolution steps
    """
    db = _get_db()

    try:
        cases_ref = (
            db.collection(settings.firestore_collection)
            .where("equipment_model", "==", equipment_model)
            .where("resolved", "==", True)
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(50)
        )

        # Simple keyword matching for MVP (replace with embedding similarity in v2)
        fault_words = set(fault_description.lower().split())
        stop_words = {"the", "a", "an", "is", "it", "not", "and", "or", "in", "on"}
        fault_words -= stop_words

        ranked = []
        for doc in cases_ref.stream():
            data = doc.to_dict()
            summary_words = set(data.get("fault_summary", "").lower().split())
            overlap = len(fault_words & summary_words)
            if overlap > 0:
                ranked.append((overlap, data, doc.id))

        ranked.sort(reverse=True)
        top = ranked[:limit]

        cases = []
        for _, data, doc_id in top:
            cases.append({
                "case_id": doc_id,
                "fault_summary": data.get("fault_summary", ""),
                "resolution": data.get("resolution", ""),
                "steps_taken": data.get("steps_taken", []),
                "technician_note": data.get("note", ""),
                "resolved_date": data.get("timestamp", datetime.now(timezone.utc)).strftime("%Y-%m-%d"),
                "technician_count": data.get("technician_count", 1),
            })

        logger.info(
            "Case history lookup",
            equipment_model=equipment_model,
            results=len(cases)
        )

        return {
            "found": len(cases) > 0,
            "cases": cases,
            "message": (
                f"Found {len(cases)} similar resolved case(s) for {equipment_model}."
                if cases else
                f"No previous cases found for this fault on {equipment_model}."
            )
        }

    except Exception as e:
        logger.error("Case lookup failed", error=str(e))
        return {"found": False, "cases": [], "message": "Case history unavailable."}


@tool
def save_resolved_case(
    equipment_model: str,
    industry: str,
    fault_summary: str,
    steps_taken: list[str],
    resolution: str,
    technician_id: str,
    technician_note: str = "",
    parts_replaced: list[str] = None,
) -> dict:
    """
    Save this successfully resolved repair case to Firestore.
    Call this ONLY when the technician confirms the fix worked.
    This builds institutional memory for future technicians.

    Args:
        equipment_model: Equipment model identifier
        industry: Industry category
        fault_summary: One-sentence description of the fault
        steps_taken: Ordered list of repair steps that were performed
        resolution: What ultimately fixed the problem
        technician_id: ID of the technician who resolved this
        technician_note: Optional note from the technician
        parts_replaced: List of parts that were replaced

    Returns:
        Confirmation with the saved case ID
    """
    db = _get_db()

    try:
        doc_data = {
            "equipment_model": equipment_model,
            "industry": industry,
            "fault_summary": fault_summary,
            "steps_taken": steps_taken,
            "resolution": resolution,
            "technician_id": technician_id,
            "note": technician_note,
            "parts_replaced": parts_replaced or [],
            "resolved": True,
            "technician_count": 1,
            "timestamp": datetime.now(timezone.utc),
        }

        _, doc_ref = db.collection(settings.firestore_collection).add(doc_data)

        logger.info(
            "Case saved",
            case_id=doc_ref.id,
            equipment_model=equipment_model,
            fault=fault_summary[:50],
        )

        return {
            "saved": True,
            "case_id": doc_ref.id,
            "message": "This case has been saved to your team's knowledge base."
        }

    except Exception as e:
        logger.error("Case save failed", error=str(e))
        return {"saved": False, "case_id": None, "message": "Failed to save case."}
```

### `backend/tools/ingest_pdf.py`

```python
"""
CLI script: PDF ingestion pipeline.
Run once per manual before deploying.

Usage:
    python -m tools.ingest_pdf \
        --pdf manuals/sma_inverter.pdf \
        --industry solar \
        --model SMA-Sunny5000 \
        --source "SMA Inverter Manual"
"""

import json
import argparse
import fitz  # PyMuPDF
from google import genai
from google.cloud import storage

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)

CHUNK_SIZE = 350   # words per chunk
CHUNK_OVERLAP = 50 # word overlap between chunks


def detect_section(lines: list[str]) -> str:
    """Heuristic section heading detection."""
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue
        # Numbered section (e.g. "4.3 DC Connection Procedure")
        if line and (line[0].isdigit() or line.isupper()):
            return line[:60]
    return "—"


def chunk_text(text: str, page_num: int, source: str) -> list[dict]:
    """Chunk a page's text into overlapping windows."""
    words = text.split()
    chunks = []
    for i in range(0, max(1, len(words) - CHUNK_SIZE + CHUNK_OVERLAP), CHUNK_SIZE - CHUNK_OVERLAP):
        chunk_words = words[i: i + CHUNK_SIZE]
        if len(chunk_words) < 30:
            continue
        chunk_text = " ".join(chunk_words)
        lines = chunk_text.split("\n")
        chunks.append({
            "text": chunk_text,
            "source": source,
            "section": detect_section(lines),
            "page": page_num,
        })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Add embeddings to all chunks using Vertex AI text-embedding-004."""
    client = genai.Client()
    embedded = []

    batch_size = 5  # Embed in batches to respect rate limits
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        texts = [c["text"] for c in batch]

        for j, text in enumerate(texts):
            response = client.models.embed_content(
                model=settings.embedding_model,
                content=text,
            )
            batch[j]["embedding"] = response.embeddings[0].values

        embedded.extend(batch)
        logger.info(f"Embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

    return embedded


def upload_to_gcs(
    chunks: list[dict],
    industry: str,
    equipment_model: str,
) -> str:
    """Upload embedded chunks JSON to Cloud Storage."""
    gcs = storage.Client()
    bucket = gcs.bucket(settings.gcs_bucket_name)
    path = f"{industry}/{equipment_model}/chunks.json"
    blob = bucket.blob(path)
    blob.upload_from_string(
        json.dumps(chunks),
        content_type="application/json",
    )
    return f"gs://{settings.gcs_bucket_name}/{path}"


def ingest(pdf_path: str, industry: str, equipment_model: str, source: str):
    logger.info(f"Opening {pdf_path}")
    doc = fitz.open(pdf_path)
    all_chunks = []

    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if not text.strip():
            continue
        page_chunks = chunk_text(text, page_num, source)
        all_chunks.extend(page_chunks)

    logger.info(f"Generated {len(all_chunks)} chunks from {len(doc)} pages")
    embedded = embed_chunks(all_chunks)
    uri = upload_to_gcs(embedded, industry, equipment_model)
    logger.info(f"Uploaded to {uri}")
    return uri


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--industry", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    ingest(args.pdf, args.industry, args.model, args.source)
```

---

## FRONTEND: DETAILED IMPLEMENTATION

### `frontend/src/types/index.ts`

```typescript
export type Industry = "solar" | "telecom" | "hvac" | "lab" | "factory";
export type AgentState = "idle" | "listening" | "thinking" | "speaking" | "interrupted";
export type Severity = "low" | "medium" | "high" | "critical" | "unknown";

export interface Citation {
  source: string;
  section: string;
  page: number;
  citation: string;  // formatted: "Manual Name §4.3 · p.44"
  text: string;      // relevant excerpt
}

export interface Diagnosis {
  likely_fault: string;
  severity: Severity;
  confidence: number;
  draw_attention_to: string;
  immediate_action: string;
  parts_likely_needed: string[];
  safe_to_operate: boolean;
  needs_closer_view: boolean;
  closer_view_instruction?: string;
}

export interface HistoricalCase {
  case_id: string;
  fault_summary: string;
  resolution: string;
  steps_taken: string[];
  resolved_date: string;
  technician_count: number;
}

export interface RepairStep {
  index: number;
  instruction: string;
  confirmed: boolean;
  timestamp: Date;
}

export interface SessionState {
  sessionId: string | null;
  industry: Industry | null;
  equipmentModel: string | null;
  agentState: AgentState;
  currentDiagnosis: Diagnosis | null;
  citations: Citation[];
  repairSteps: RepairStep[];
  historicalCases: HistoricalCase[];
  isConnected: boolean;
  error: string | null;
}
```

### `frontend/src/hooks/useWebSocket.ts`

```typescript
/**
 * WebSocket hook — handles:
 * - Connection lifecycle with exponential backoff reconnect
 * - Multiplexing binary audio and JSON control messages
 * - Barge-in detection (when user speaks while agent is speaking)
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useSessionStore } from "../store/sessionStore";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_MS = 1000;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const [isConnecting, setIsConnecting] = useState(false);

  const {
    setConnected,
    setAgentState,
    setDiagnosis,
    addCitation,
    addHistoricalCase,
    setError,
    sessionId,
  } = useSessionStore();

  const connect = useCallback((sid: string, industry: string, equipmentModel: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setIsConnecting(true);
    const ws = new WebSocket(`${WS_URL}/ws/${sid}`);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnecting(false);
      reconnectAttempts.current = 0;
      setConnected(true);
      // Send session init
      ws.send(JSON.stringify({
        type: "session_init",
        industry,
        equipment_model: equipmentModel,
        technician_id: localStorage.getItem("technician_id") ?? "anonymous",
      }));
    };

    ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        // Audio bytes from agent — play back
        playAudioChunk(event.data);
        setAgentState("speaking");
      } else {
        const msg = JSON.parse(event.data as string);
        handleControlMessage(msg);
      }
    };

    ws.onerror = () => setError("Connection error");
    ws.onclose = () => {
      setConnected(false);
      scheduleReconnect(sid, industry, equipmentModel);
    };
  }, []);

  const scheduleReconnect = (sid: string, industry: string, model: string) => {
    if (reconnectAttempts.current >= MAX_RECONNECT_ATTEMPTS) {
      setError("Connection lost. Please refresh.");
      return;
    }
    const delay = RECONNECT_BASE_MS * Math.pow(2, reconnectAttempts.current);
    reconnectAttempts.current++;
    reconnectTimer.current = setTimeout(() => connect(sid, industry, model), delay);
  };

  const handleControlMessage = (msg: Record<string, unknown>) => {
    if (msg.type === "session_ready") {
      setAgentState("listening");
    } else if (msg.type === "tool_result") {
      const tool = msg.tool as string;
      const data = msg.data as Record<string, unknown>;

      if (tool === "diagnose_frame") {
        setDiagnosis(data as never);
        setAgentState("thinking");
      } else if (tool === "search_manual") {
        const results = (data as Record<string, unknown[]>).results ?? [];
        results.forEach(r => addCitation(r as never));
      } else if (tool === "lookup_similar_cases") {
        const cases = (data as Record<string, unknown[]>).cases ?? [];
        cases.forEach(c => addHistoricalCase(c as never));
      }
    }
  };

  const sendAudio = useCallback((pcmData: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(pcmData);
    }
  }, []);

  const sendVideoFrame = useCallback((base64jpeg: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "video_frame",
        data: base64jpeg,
      }));
    }
  }, []);

  const sendBargeIn = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "barge_in" }));
      setAgentState("interrupted");
    }
  }, []);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.send(JSON.stringify({ type: "end_session" }));
    wsRef.current?.close();
  }, []);

  useEffect(() => () => disconnect(), []);

  return { connect, sendAudio, sendVideoFrame, sendBargeIn, disconnect, isConnecting };
}

// Audio playback via Web Audio API
let audioCtx: AudioContext | null = null;
let nextPlayTime = 0;

function playAudioChunk(buffer: ArrayBuffer) {
  if (!audioCtx) audioCtx = new AudioContext({ sampleRate: 24000 });
  if (audioCtx.state === "suspended") audioCtx.resume();

  const pcm = new Int16Array(buffer);
  const float32 = new Float32Array(pcm.length);
  for (let i = 0; i < pcm.length; i++) {
    float32[i] = pcm[i] / 32768.0;
  }

  const audioBuffer = audioCtx.createBuffer(1, float32.length, 24000);
  audioBuffer.copyToChannel(float32, 0);

  const source = audioCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioCtx.destination);

  const startTime = Math.max(audioCtx.currentTime, nextPlayTime);
  source.start(startTime);
  nextPlayTime = startTime + audioBuffer.duration;
}
```

### `frontend/src/hooks/useCamera.ts`

```typescript
/**
 * Camera hook — manages getUserMedia stream + periodic frame capture.
 * Sends JPEG frames to the WebSocket every `intervalMs` milliseconds.
 * Respects battery by pausing frame capture when tab is hidden.
 */

import { useCallback, useEffect, useRef } from "react";

interface UseCameraOptions {
  intervalMs?: number;
  quality?: number;  // 0.0 to 1.0 JPEG quality
  onFrame: (base64jpeg: string) => void;
  onError: (error: string) => void;
}

export function useCamera({
  intervalMs = 2500,
  quality = 0.75,
  onFrame,
  onError,
}: UseCameraOptions) {
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();
  const isCapturing = useRef(false);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" }, // Rear camera on phones
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      streamRef.current = stream;
      return stream;
    } catch (err) {
      onError(`Camera access denied: ${(err as Error).message}`);
      throw err;
    }
  }, [onError]);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !isCapturing.current) return;
    if (document.hidden) return; // Pause when tab hidden

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video.videoWidth === 0) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL("image/jpeg", quality);
    const base64 = dataUrl.split(",")[1];
    onFrame(base64);
  }, [onFrame, quality]);

  const startCapture = useCallback(() => {
    isCapturing.current = true;
    intervalRef.current = setInterval(captureFrame, intervalMs);
  }, [captureFrame, intervalMs]);

  const stopCapture = useCallback(() => {
    isCapturing.current = false;
    clearInterval(intervalRef.current);
  }, []);

  const stopCamera = useCallback(() => {
    stopCapture();
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
  }, [stopCapture]);

  useEffect(() => () => stopCamera(), [stopCamera]);

  return {
    videoRef,
    canvasRef: canvasRef as React.RefObject<HTMLCanvasElement>,
    startCamera,
    startCapture,
    stopCapture,
    stopCamera,
    stream: streamRef.current,
  };
}
```

### `frontend/src/hooks/useMicrophone.ts`

```typescript
/**
 * Microphone hook — captures raw PCM at 16kHz (what Gemini Live expects).
 * Uses ScriptProcessorNode for broad device compatibility.
 * Detects speech start for barge-in notification to backend.
 */

import { useCallback, useRef, useState } from "react";

const SAMPLE_RATE = 16000;
const BUFFER_SIZE = 4096;
const SPEECH_THRESHOLD = 0.01; // RMS threshold for speech detection

interface UseMicrophoneOptions {
  onAudioChunk: (pcmBuffer: ArrayBuffer) => void;
  onSpeechStart: () => void;
}

export function useMicrophone({ onAudioChunk, onSpeechStart }: UseMicrophoneOptions) {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const wasSpeeaking = useRef(false);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
      audioCtxRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      const processor = audioCtx.createScriptProcessor(BUFFER_SIZE, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const float32 = e.inputBuffer.getChannelData(0);

        // RMS for speech detection
        const rms = Math.sqrt(float32.reduce((sum, s) => sum + s * s, 0) / float32.length);
        const isSpeaking = rms > SPEECH_THRESHOLD;

        if (isSpeaking && !wasSpeeaking.current) {
          onSpeechStart();
          wasSpeeaking.current = true;
        } else if (!isSpeaking) {
          wasSpeeaking.current = false;
        }

        // Convert Float32 to Int16 PCM
        const int16 = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
          int16[i] = Math.max(-32768, Math.min(32767, Math.round(float32[i] * 32767)));
        }
        onAudioChunk(int16.buffer);
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);
      setIsRecording(true);
    } catch (err) {
      throw new Error(`Microphone access denied: ${(err as Error).message}`);
    }
  }, [onAudioChunk, onSpeechStart]);

  const stopRecording = useCallback(() => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    audioCtxRef.current?.close();
    streamRef.current?.getTracks().forEach(t => t.stop());
    setIsRecording(false);
    wasSpeeaking.current = false;
  }, []);

  return { startRecording, stopRecording, isRecording };
}
```

### `frontend/src/components/CitationCard.tsx`

```tsx
/**
 * CitationCard — appears below the camera feed when the agent
 * cites a manual section. Animates in from below.
 */

import { useEffect, useState } from "react";
import type { Citation } from "../types";

interface Props {
  citation: Citation;
  isLatest: boolean;
}

export function CitationCard({ citation, isLatest }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, []);

  return (
    <div
      className={`
        transition-all duration-300 ease-out
        ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}
        ${isLatest ? "border-blue-500 bg-blue-50" : "border-gray-200 bg-white"}
        border rounded-xl p-3 mb-2
      `}
    >
      <p className="text-sm text-gray-800 leading-relaxed mb-2">
        {citation.text}
      </p>
      <div className="flex items-center gap-2">
        <div className={`
          text-xs font-semibold px-2 py-0.5 rounded-full
          ${isLatest
            ? "bg-blue-100 text-blue-700"
            : "bg-gray-100 text-gray-600"
          }
        `}>
          {citation.citation}
        </div>
      </div>
    </div>
  );
}
```

---

## INFRASTRUCTURE (TERRAFORM)

### `infra/main.tf`

```hcl
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "fieldfix-tf-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Service Account ──────────────────────────────────────────────────────────
resource "google_service_account" "backend" {
  account_id   = "fieldfix-backend"
  display_name = "FieldFix Backend Service Account"
}

locals {
  backend_roles = [
    "roles/aiplatform.user",
    "roles/datastore.user",
    "roles/storage.objectViewer",
    "roles/storage.objectCreator",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
  ]
}

resource "google_project_iam_member" "backend_roles" {
  for_each = toset(local.backend_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.backend.email}"
}

# ── Firestore ─────────────────────────────────────────────────────────────────
resource "google_firestore_database" "fieldfix" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

resource "google_firestore_index" "cases_by_model_time" {
  project    = var.project_id
  database   = google_firestore_database.fieldfix.name
  collection = "fault_cases"
  fields {
    field_path = "equipment_model"
    order      = "ASCENDING"
  }
  fields {
    field_path = "resolved"
    order      = "ASCENDING"
  }
  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }
}

# ── Cloud Storage ─────────────────────────────────────────────────────────────
resource "google_storage_bucket" "knowledge_base" {
  name                        = "${var.project_id}-fieldfix-kb"
  location                    = "US-CENTRAL1"
  uniform_bucket_level_access = true
  versioning { enabled = true }
  lifecycle_rule {
    action { type = "Delete" }
    condition { age = 365 }
  }
}

resource "google_storage_bucket" "tf_state" {
  name                        = "fieldfix-tf-state"
  location                    = "US-CENTRAL1"
  uniform_bucket_level_access = true
  versioning { enabled = true }
}

# ── Artifact Registry ─────────────────────────────────────────────────────────
resource "google_artifact_registry_repository" "fieldfix" {
  location      = var.region
  repository_id = "fieldfix"
  format        = "DOCKER"
}

# ── Cloud Run ─────────────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "backend" {
  name     = "fieldfix-backend"
  location = var.region

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/fieldfix/backend:${var.image_tag}"

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.knowledge_base.name
      }
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      resources {
        limits = {
          memory = "2Gi"
          cpu    = "2"
        }
        startup_cpu_boost = true
      }

      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 10
      }

      liveness_probe {
        http_get { path = "/health" }
        period_seconds    = 30
        failure_threshold = 3
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Allow unauthenticated access (public demo)
resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_v2_service.backend.location
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "backend_url" {
  value = google_cloud_run_v2_service.backend.uri
}
output "knowledge_base_bucket" {
  value = google_storage_bucket.knowledge_base.name
}
```

### `infra/variables.tf`

```hcl
variable "project_id" {
  description = "GCP project ID"
  type        = string
}
variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}
variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}
variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}
```

---

## BACKEND DEPENDENCIES

### `backend/requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
websockets==13.1
google-genai==1.0.0
google-adk==1.0.0
google-cloud-firestore==2.19.0
google-cloud-storage==2.18.2
pydantic==2.9.2
pydantic-settings==2.6.1
PyMuPDF==1.24.13
numpy==2.1.3
structlog==24.4.0
```

### `backend/requirements-dev.txt`

```
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
pytest-cov==6.0.0
ruff==0.8.0
```

---

## FRONTEND DEPENDENCIES

### `frontend/package.json`

```json
{
  "name": "fieldfix-ai",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "zustand": "^5.0.1",
    "framer-motion": "^11.11.0",
    "lucide-react": "^0.460.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.15",
    "typescript": "^5.6.3",
    "vite": "^5.4.11",
    "vite-plugin-pwa": "^0.20.5"
  }
}
```

---

## BACKEND DOCKERFILE

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# System deps for PyMuPDF
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    mupdf \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "1", "--log-config", "logging_config.json"]
```

---

## SEED SCRIPT

### `scripts/seed_firestore.py`

```python
"""
Seed Firestore with realistic historical fault cases for demo.
Run once before recording the demo video.
"""
from google.cloud import firestore
from datetime import datetime, timezone, timedelta
import random

db = firestore.Client()
collection = db.collection("fault_cases")

CASES = [
    {
        "equipment_model": "SMA-Sunny5000",
        "industry": "solar",
        "fault_summary": "Red LED blinking 3 times — DC input overvoltage",
        "steps_taken": [
            "Checked DC string voltage with multimeter — measured 620V (limit 600V)",
            "Inspected string configuration — found extra panel added to string",
            "Reconfigured string to 10 panels from 11",
            "Verified voltage at 570V after reconfiguration",
        ],
        "resolution": "Reduced string size from 11 to 10 panels to bring DC voltage within spec",
        "note": "Common during summer peak hours — voltage rises with temperature",
        "parts_replaced": [],
        "resolved": True,
        "technician_id": "tech_001",
        "technician_count": 3,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=18),
    },
    {
        "equipment_model": "SMA-Sunny5000",
        "industry": "solar",
        "fault_summary": "No AC output despite green LED — grid impedance fault",
        "steps_taken": [
            "Verified AC grid voltage — within spec",
            "Checked grid impedance setting in installer menu",
            "Found impedance threshold set to 0.2 ohm (default) — actual was 0.35 ohm",
            "Adjusted threshold to 0.5 ohm per local grid spec",
        ],
        "resolution": "Adjusted grid impedance threshold in inverter settings to match local grid",
        "note": "Local utility has higher impedance than German default settings",
        "parts_replaced": [],
        "resolved": True,
        "technician_id": "tech_002",
        "technician_count": 2,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=35),
    },
    {
        "equipment_model": "Carrier-30XA",
        "industry": "hvac",
        "fault_summary": "High discharge pressure alarm — compressor shutting down",
        "steps_taken": [
            "Checked condenser coil — found blocked by debris",
            "Cleaned condenser coil with coil cleaner",
            "Verified condenser fan operation — all 4 fans running",
            "Monitored discharge pressure after cleaning — returned to normal",
        ],
        "resolution": "Blocked condenser coil causing inadequate heat rejection",
        "note": "Schedule quarterly coil cleaning on this unit — dusty environment",
        "parts_replaced": [],
        "resolved": True,
        "technician_id": "tech_003",
        "technician_count": 1,
        "timestamp": datetime.now(timezone.utc) - timedelta(days=7),
    },
]

for case in CASES:
    collection.add(case)
    print(f"Added: {case['fault_summary'][:50]}...")

print(f"\nSeeded {len(CASES)} cases into Firestore")
```

---

## README TEMPLATE

### `README.md`

```markdown
# FieldFix AI

> Real-time AI assistant for field technicians — grounded in your equipment manuals.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Available-green)](YOUR_DEMO_URL)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Cloud%20Run-blue)](https://cloud.google.com)
[![Gemini Live](https://img.shields.io/badge/Gemini-Live%20API-purple)](https://ai.google.dev)

**Gemini Live Agent Challenge submission** — Track 1: Live Agent

## What it does

Field technicians point their phone camera at a broken device, describe the
problem by voice, and receive live expert guidance — grounded in the actual
equipment manual with section citations shown in real-time.

- Camera + voice → real-time Gemini Live API session
- Every answer cited from manual PDFs (RAG via Cloud Storage)
- Institutional memory: learns from every resolved case (Firestore)
- Interruptible: technician can cut the agent off mid-sentence

## Demo

[Watch the 4-minute demo video](YOUR_DEMO_VIDEO_URL)

## Quick start (local)

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/fieldfix-ai
cd fieldfix-ai

# Backend
cd backend
cp .env.example .env  # fill in GCP_PROJECT_ID
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
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

## GDG Profile
[YOUR_GDG_PROFILE_URL]

## Architecture

![Architecture](docs/architecture.png)
```

---

## PRODUCTION-GRADE REQUIREMENTS

The following must be implemented for every component:

### Error handling
- All tool functions: try/except with structured logging. Never throw unhandled exceptions — return error state dicts.
- WebSocket handler: catch all exceptions, close cleanly with appropriate status codes, log session_id in every log entry.
- Frontend: error boundary wrapping the entire app. Show user-friendly messages, not raw errors.

### Logging
- Backend: structured JSON logging via `structlog` (compatible with Cloud Logging). Every log entry must include `session_id` when in a session context.
- Log levels: DEBUG for frame captures, INFO for tool calls and results, WARNING for degraded state, ERROR for failures.

### Testing
- `tests/test_kb_lookup.py`: mock Cloud Storage, verify cosine search returns top-3 by score, verify relevance threshold filters low-score results.
- `tests/test_case_history.py`: mock Firestore, verify keyword overlap ranking, verify save round-trips correctly.
- `tests/test_visual_diagnosis.py`: mock Gemini API, verify JSON parsing, verify fallback on malformed response.

### Security
- All GCP clients use Application Default Credentials (ADC) — never hardcode keys.
- Validate frame size before sending to Gemini (500KB limit enforced in `main.py`).
- CORS origins from config, not hardcoded.
- WebSocket sessions expire after 30 minutes of inactivity.

### Performance
- Frame sampling throttled to 1 frame per 2.5 seconds (configurable).
- KB chunks cached in-process with `lru_cache` after first load.
- Audio playback uses seamless PCM buffer queuing to avoid gaps.

---

## BLOG POST PLACEHOLDER

### `BLOG_POST.md`

```markdown
# Building FieldFix AI for the Gemini Live Agent Challenge

#GeminiLiveAgentChallenge

## TL;DR
[One paragraph summary]

## The problem
[Why technicians need this]

## Architecture
[Reference architecture.png]

## The hard parts
### Real-time barge-in
[How we handled interruption]

### RAG without a vector database
[The Cloud Storage + cosine similarity approach]

### Firestore as institutional memory
[Case history design]

## What we learned
[Key takeaways from the Gemini Live API]

## Try it yourself
[Links]
```

---

## IMPLEMENTATION NOTES FOR THE CODING AGENT

1. **Start with `backend/` first**. Get the WebSocket session + Gemini Live API connection working with a simple echo before adding tools.

2. **Use a real PDF for the demo**. Download a free equipment manual PDF (Fronius or SMA solar inverter manuals are publicly available) and run `ingest_pdf.py` before testing `search_manual`.

3. **Seed Firestore before recording the demo**. Run `scripts/seed_firestore.py` to ensure the case history feature shows data during the demo.

4. **Test barge-in explicitly**. After basic flow works, explicitly test: let agent speak for 3+ seconds, then speak over it. The session's `interrupt()` must be called immediately on speech detection.

5. **The `draw_attention_to` field in visual diagnosis** should be read aloud naturally by the agent: "I can see [draw_attention_to] — that's what you need to look at."

6. **Local development**: Use `docker-compose.yml` with Firestore emulator and fake GCS (fake-gcs-server) so the full stack works without GCP billing during development.

7. **Terraform state**: Create the `fieldfix-tf-state` GCS bucket manually before running `terraform init` (chicken-and-egg issue with remote backends).

8. **Environment variables**: Never commit `.env` files. The `.env.example` must document every required variable with a comment explaining what it is.
```
