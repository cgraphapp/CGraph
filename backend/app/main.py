"""CGRAPH FastAPI Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

# Import routes
from app.api.v1 import health, auth, messages

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("🚀 CGRAPH Backend initializing...")
    yield
    logger.info("🛑 CGRAPH Backend shutting down...")

app = FastAPI(
    title="CGRAPH API",
    description="Private messaging and community forums",
    version="3.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.cgraph.org", "https://cgraph.org", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["cgraph.org", "*.cgraph.org", "localhost"]
)

# Routes
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"app": "CGRAPH", "version": "3.0.0", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
