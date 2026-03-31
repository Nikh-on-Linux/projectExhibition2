import logging

from fastapi import APIRouter
from datetime import datetime

from config import PORT
from schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["status"])


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """
    Health check endpoint — no database required.
    Returns timestamp for monitoring freshness.
    """
    return {
        "status": "ok",
        "service": "cleaning",
        "port": PORT,
        "timestamp": datetime.utcnow().isoformat(),
    }
