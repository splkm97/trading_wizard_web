"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check API health status."""
    return {"status": "healthy", "service": "trading-wizard-web"}


@router.get("/health/ready")
async def readiness_check():
    """Check if the service is ready to accept requests."""
    # TODO: Add database connectivity check
    return {"status": "ready"}
