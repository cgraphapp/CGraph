from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.database import init_db, get_db, engine
from app.cache import cache
from app.routes import auth, messages, forums

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup/Shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting CGRAPH backend...")
    await init_db()
    await cache.connect()
    logger.info("✅ Services initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down CGRAPH backend...")
    await cache.disconnect()
    await engine.dispose()
    logger.info("✅ Services stopped")

# Create FastAPI app
app = FastAPI(
    title="CGRAPH API",
    description="Private messaging and forums platform",
    version="7.0.0",
    lifespan=lifespan,
)

# Middleware - Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cgraph.org", "https://www.cgraph.org"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600,
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["cgraph.org", "*.cgraph.org", "localhost"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "7.0.0",
        "service": "cgraph-backend"
    }

# API Routes
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
app.include_router(forums.router, prefix="/api/v1", tags=["Forums"])

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        workers=4,
        loop="uvloop",
    )
