"""Routes for complaint ingestion and processing."""

from fastapi import APIRouter

from api.schemas.complaint_schema import ComplaintRequest, ComplaintResponse

router = APIRouter()


@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(request: ComplaintRequest) -> ComplaintResponse:
    """Process a complaint and return a structured response."""
    raise NotImplementedError
