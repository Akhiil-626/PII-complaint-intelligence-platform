"""FastAPI application entrypoint for Privacy-Preserving Complaint Intelligence Platform."""

from __future__ import annotations

from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.complaints import router as complaints_router
from api.routes.dashboard import router as dashboard_router

app = FastAPI(
    title="Privacy-Preserving Complaint Intelligence Platform",
    description="End-to-end API for PII redaction, multi-model classification, sentiment scoring, and operational insights.",
    version="1.0.0",
)

# Enable CORS for flexible dashboard or frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints_router, prefix="/api", tags=["Complaints"])
app.include_router(dashboard_router, prefix="/api", tags=["Dashboard"])

# Root routes for backward compatibility
app.include_router(complaints_router, tags=["Complaints"])
app.include_router(dashboard_router, tags=["Dashboard"])


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """Liveness and readiness health probe."""
    return {
        "status": "healthy",
        "service": "Complaint Intelligence Platform",
        "privacy_mode": "strict_pii_redaction",
    }
