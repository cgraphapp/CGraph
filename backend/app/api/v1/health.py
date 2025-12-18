"""Health check endpoints"""

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health():
    """Application health check"""
    return {"status": "ok", "version": "3.0.0"}

@router.get("/ready")
async def readiness():
    """Readiness probe for Kubernetes"""
    # Check database
    # Check Redis
    # Check external services
    return {"ready": True}

@router.get("/live")
async def liveness():
    """Liveness probe for Kubernetes"""
    return {"alive": True}
