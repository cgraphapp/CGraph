from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from app.config import settings
from app.database import engine, Base, get_db
from app.api.v1 import auth, messages, rooms, forums, payments, cosmetics
from app.middleware.rate_limiting import RateLimitMiddleware
from app.middleware.error_handler import ErrorHandlerMiddleware
import structlog

# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Create tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 CGRAPH Backend Starting...")
    yield
    # Shutdown
    logger.info("💤 CGRAPH Backend Shutting Down...")

# Initialize FastAPI
app = FastAPI(
    title="CGRAPH API",
    description="Complete Graph Communication Platform",
    version="7.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# Error Handler Middleware
app.add_middleware(ErrorHandlerMiddleware)

# Health Check Endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "7.0.0",
        "environment": settings.ENVIRONMENT
    }

# API Routes v1
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(messages.router, prefix="/api/v1/messages", tags=["Messages"])
app.include_router(rooms.router, prefix="/api/v1/rooms", tags=["Rooms"])
app.include_router(forums.router, prefix="/api/v1/forums", tags=["Forums"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(cosmetics.router, prefix="/api/v1/cosmetics", tags=["Cosmetics"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "CGRAPH",
        "version": "7.0.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1"
    }

# Metrics endpoint (Prometheus)
@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return generate_latest()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

