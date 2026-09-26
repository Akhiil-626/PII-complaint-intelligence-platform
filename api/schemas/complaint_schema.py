"""Request and response models for complaint processing."""

from pydantic import BaseModel, Field


class ComplaintRequest(BaseModel):
    """Incoming complaint payload."""
    text: str = Field(..., description="Customer complaint text")
    source: str | None = Field(default=None, description="Complaint source")


class ComplaintResponse(BaseModel):
    """Structured response payload for a processed complaint."""
    redacted_text: str
    category: str | None = None
    sentiment: str | None = None
    duplicate_score: float | None = None
