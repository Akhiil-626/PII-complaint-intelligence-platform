"""Request and response models for complaint processing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComplaintRequest(BaseModel):
    """Incoming complaint payload."""
    text: str = Field(..., description="Customer complaint text narrative")
    source: Optional[str] = Field(default="api", description="Complaint intake channel or source")


class EntityItem(BaseModel):
    """Detected and redacted PII entity metadata."""
    entity_type: str
    text: str
    start: int
    end: int
    score: float


class ComplaintResponse(BaseModel):
    """Structured response payload for a processed complaint."""
    complaint_id: str = Field(..., description="Unique complaint identifier")
    timestamp: str = Field(..., description="ISO 8601 processing timestamp")
    redacted_text: str = Field(..., description="Privacy-safe redacted narrative")
    category: Optional[str] = Field(default=None, description="Predicted financial domain category")
    sub_issue: Optional[str] = Field(default=None, description="Fine-grained sub-issue")
    confidence: Optional[float] = Field(default=None, description="Domain classification confidence score")
    sentiment: Optional[str] = Field(default=None, description="Sentiment label (negative, neutral, positive)")
    urgency_score: Optional[float] = Field(default=None, description="Computed urgency factor [0.0 - 1.0]")
    emotion: Optional[str] = Field(default=None, description="Inferred consumer emotion")
    duplicate_score: Optional[float] = Field(default=None, description="Highest similarity score with existing records")
    needs_review: bool = Field(default=False, description="Whether flagged for human review due to disagreement")
    review_reason: Optional[str] = Field(default=None, description="Reason for escalation if flagged")
    entities_count: int = Field(default=0, description="Number of PII entities redacted")
    entities: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of redacted entity details")
