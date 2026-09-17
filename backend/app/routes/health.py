import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    logger.info("Health check requested")
    return {"status": "healthy"}
