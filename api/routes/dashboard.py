"""Routes for dashboard metrics and visual insights."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard-data")
def get_dashboard_data() -> dict[str, object]:
    """Return summary statistics for the dashboard."""
    raise NotImplementedError
