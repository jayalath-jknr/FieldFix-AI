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
import base64
import json

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.logging import get_logger
from agent import create_agent_runner

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
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

# In-memory session registry (use Redis in production scale-out)
active_sessions: dict[str, dict] = {}


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
                "equipment": ["Cisco-ASR9000", "Nokia-FSED", "Ericsson-RBS"],
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
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "tool_result",
                        "tool": tool_name,
                        "data": result,
                    }
                )
            )

        runner.on_audio_output(on_audio_output)
        runner.on_tool_result(on_tool_result)
        await runner.start()

        await websocket.send_text(
            json.dumps(
                {
                    "type": "session_ready",
                    "session_id": session_id,
                }
            )
        )

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
                        await runner.send_image(
                            frame_bytes, mime_type="image/jpeg"
                        )

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
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        if runner:
            await runner.close()
        active_sessions.pop(session_id, None)
        logger.info("Session cleaned up", session_id=session_id)
