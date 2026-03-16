"""Pydantic models for WebSocket session state."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class SessionInit(BaseModel):
    """Initial message sent by the client to start a session."""
    type: str = "session_init"
    industry: str
    equipment_model: str
    technician_id: str = "anonymous"


class SessionState(BaseModel):
    """Tracks the state of an active WebSocket session."""
    session_id: str
    industry: str
    equipment_model: str
    technician_id: str = "anonymous"
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    frames_processed: int = 0
    tools_called: int = 0
    is_active: bool = True

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(timezone.utc)

    @property
    def idle_seconds(self) -> float:
        """Seconds since last activity."""
        return (datetime.now(timezone.utc) - self.last_activity).total_seconds()


class SessionReady(BaseModel):
    """Sent to client when session is ready."""
    type: str = "session_ready"
    session_id: str


class ToolResult(BaseModel):
    """Wrapper for tool results sent to client."""
    type: str = "tool_result"
    tool: str
    data: dict


class VideoFrame(BaseModel):
    """Video frame message from client."""
    type: str = "video_frame"
    data: str  # Base64 encoded JPEG


class BargeIn(BaseModel):
    """Barge-in signal from client (user started speaking)."""
    type: str = "barge_in"


class EndSession(BaseModel):
    """End session signal from client."""
    type: str = "end_session"
