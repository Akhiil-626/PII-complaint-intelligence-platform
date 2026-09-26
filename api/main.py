"""FastAPI application entrypoint."""

from fastapi import FastAPI

from api.routes.complaints import router as complaints_router
from api.routes.dashboard import router as dashboard_router

app = FastAPI(title="Complaint Intelligence Platform")

app.include_router(complaints_router)
app.include_router(dashboard_router)
