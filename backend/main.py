"""
FastAPI app. Key responsibilities:
- Accept WebSocket connections at /ws/{session_id}
- Multiplex binary audio frames and JSON control messages
- Bridge frontend microphone/camera to Gemini Live (google.genai)
- Auto-execute tool calls and return results to both Gemini and the frontend UI
- Structured logging (Cloud Logging compatible JSON)
"""

import asyncio
import base64
import json
import os

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

from core.config import settings
from core.logging import get_logger
from agent import TOOLS_MAP, build_live_config

logger = get_logger(__name__)

_genai_client: genai.Client | None = None


def _make_genai_client() -> genai.Client:
    """Create a genai Client.

    Tries (in order):
    1. GOOGLE_API_KEY env var → plain AI Studio client
    2. Vertex AI mode using ADC (works with `gcloud auth application-default login`)
    """
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_GENAI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)
    # Use Vertex AI mode — authenticates via Application Default Credentials
    return genai.Client(
        vertexai=True,
        project=settings.gcp_project_id,
        location=settings.gcp_region,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _genai_client
    _genai_client = _make_genai_client()
    logger.info("FieldFix AI starting", env=settings.environment)
    yield
    logger.info("FieldFix AI shutting down")


app = FastAPI(
    title="FieldFix AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/industries")
async def list_industries():
    """Return available industry + equipment model combinations."""
    return {
        "industries": [
            {
                "id": "solar",
                "label": "Solar",
                "equipment": ["SMA-Sunny5000", "Fronius-Symo", "Huawei-SUN2000"],
            },
            {
                "id": "telecom",
                "label": "Telecom",
                "equipment": ["Cisco-ASR9000", "Nokia-FSED", "Ericsson-RBS", "ZTE-MF687"],
            },
            {
                "id": "hvac",
                "label": "HVAC",
                "equipment": ["Carrier-30XA", "Daikin-VRV", "Trane-CGAM"],
            },
            {
                "id": "lab",
                "label": "Lab Equipment",
                "equipment": ["Agilent-HPLC", "Thermo-Centrifuge", "Beckman-UV"],
            },
            {
                "id": "factory",
                "label": "Factory",
                "equipment": ["Siemens-S7-1500", "ABB-IRB6700", "Fanuc-R2000"],
            },
        ]
    }


@app.websocket("/ws/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
):
    """Main WebSocket handler for live technician sessions."""
    await websocket.accept()
    logger.info("WebSocket connected", session_id=session_id)

    try:
        # First message must be session init
        init_raw = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        init_msg = json.loads(init_raw)
        assert init_msg["type"] == "session_init", "First message must be session_init"

        industry = init_msg["industry"]
        equipment_model = init_msg["equipment_model"]
        technician_id = init_msg.get("technician_id", "anonymous")

        config = build_live_config(
            industry=industry,
            equipment_model=equipment_model,
            technician_id=technician_id,
        )

        if _genai_client is None:
            await websocket.send_text(json.dumps({
                "type": "error", "message": "Server not ready — genai client unavailable"
            }))
            await websocket.close(code=1011)
            return

        async with _genai_client.aio.live.connect(
            model=settings.gemini_live_model, config=config
        ) as live_session:

            # Notify frontend that the session is ready
            await websocket.send_text(
                json.dumps({"type": "session_ready", "session_id": session_id})
            )

            # --- Task: receive from Gemini Live and forward to frontend ---
            async def receive_from_gemini():
                try:
                    # Wrap in while True so we re-enter receive() after each
                    # turn_complete — without this the agent goes silent after
                    # its first response.
                    while True:
                        async for msg in live_session.receive():
                            # Forward audio output to the browser
                            if msg.data:
                                await websocket.send_bytes(msg.data)

                            # Handle tool/function calls
                            if msg.tool_call:
                                responses = []
                                for fc in msg.tool_call.function_calls:
                                    func = TOOLS_MAP.get(fc.name)
                                    if func:
                                        try:
                                            # Run blocking I/O (Firestore/GCS)
                                            # off the event loop thread so it
                                            # doesn't stall audio streaming.
                                            result = await asyncio.to_thread(
                                                func, **dict(fc.args)
                                            )
                                        except Exception as tool_err:
                                            result = {"error": str(tool_err)}
                                        responses.append(
                                            types.FunctionResponse(
                                                id=fc.id,
                                                name=fc.name,
                                                response=result
                                                if isinstance(result, dict)
                                                else {"result": str(result)},
                                            )
                                        )
                                        # Forward result to frontend for UI update
                                        try:
                                            await websocket.send_text(
                                                json.dumps(
                                                    {
                                                        "type": "tool_result",
                                                        "tool": fc.name,
                                                        "data": result,
                                                    }
                                                )
                                            )
                                        except Exception:
                                            pass
                                if responses:
                                    await live_session.send_tool_response(
                                        function_responses=responses
                                    )
                except Exception as recv_err:
                    logger.error(
                        "Gemini receive error",
                        session_id=session_id,
                        error=str(recv_err),
                    )

            recv_task = asyncio.create_task(receive_from_gemini())

            try:
                # --- Main loop: forward frontend messages to Gemini Live ---
                while True:
                    message = await websocket.receive()

                    if "bytes" in message:
                        # Raw PCM audio from microphone (16 kHz, 16-bit, mono)
                        await live_session.send_realtime_input(
                            audio=types.Blob(
                                data=message["bytes"],
                                mime_type="audio/pcm;rate=16000",
                            )
                        )

                    elif "text" in message:
                        msg = json.loads(message["text"])

                        if msg["type"] == "video_frame":
                            frame_bytes = base64.b64decode(msg["data"])
                            if len(frame_bytes) <= settings.max_frame_size_bytes:
                                await live_session.send_realtime_input(
                                    video=types.Blob(
                                        data=frame_bytes,
                                        mime_type="image/jpeg",
                                    )
                                )

                        elif msg["type"] == "barge_in":
                            # VAD handles barge-in automatically; no action needed
                            pass

                        elif msg["type"] == "end_session":
                            break
            finally:
                recv_task.cancel()
                try:
                    await recv_task
                except asyncio.CancelledError:
                    pass

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected", session_id=session_id)
    except asyncio.TimeoutError:
        logger.warning("Session init timeout", session_id=session_id)
        await websocket.close(code=1008)
    except Exception as e:
        logger.error("Session error", session_id=session_id, error=str(e))
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        logger.info("Session cleaned up", session_id=session_id)
