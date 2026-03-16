"""Pydantic models for fault case data (Firestore documents)."""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class FaultCase(BaseModel):
    """A resolved fault case stored in Firestore."""
    equipment_model: str
    industry: str
    fault_summary: str
    steps_taken: list[str]
    resolution: str
    technician_id: str
    note: str = ""
    parts_replaced: list[str] = Field(default_factory=list)
    resolved: bool = True
    technician_count: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FaultCaseResponse(BaseModel):
    """A fault case as returned by the API."""
    case_id: str
    fault_summary: str
    resolution: str
    steps_taken: list[str]
    technician_note: str = ""
    resolved_date: str
    technician_count: int = 1


class CaseLookupResult(BaseModel):
    """Result from looking up similar cases."""
    found: bool
    cases: list[FaultCaseResponse] = Field(default_factory=list)
    message: str = ""


class CaseSaveResult(BaseModel):
    """Result from saving a resolved case."""
    saved: bool
    case_id: Optional[str] = None
    message: str = ""


class DiagnosisIssue(BaseModel):
    """A single issue found in visual diagnosis."""
    description: str
    location_in_frame: str


class DiagnosisResult(BaseModel):
    """Structured result from visual diagnosis."""
    issues_found: list[DiagnosisIssue] = Field(default_factory=list)
    severity: str = "unknown"
    likely_fault: str = ""
    confidence: float = 0.0
    draw_attention_to: str = ""
    immediate_action: str = ""
    parts_likely_needed: list[str] = Field(default_factory=list)
    safe_to_operate: bool = False
    needs_closer_view: bool = False
    closer_view_instruction: str = ""


class KBSearchResult(BaseModel):
    """A single knowledge base search result."""
    text: str
    citation: str
    source: str
    section: str
    page: int
    relevance_score: float


class KBSearchResponse(BaseModel):
    """Response from knowledge base search."""
    found: bool
    results: list[KBSearchResult] = Field(default_factory=list)
    message: str = ""
