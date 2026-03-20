"""
Campaign Operations OS - FastAPI Application Entry Point

This is the main FastAPI application that serves the Campaign Operations OS API.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, close_db
from app.core.redis import RedisClient
from app.core.scheduler import get_scheduler
from app.core.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan handler.

    Runs startup and shutdown logic.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    if settings.debug:
        # In development, create tables if they don't exist
        # In production, use Alembic migrations
        await init_db()
        logger.debug("Database initialized (dev mode)")

    # Start background scheduler
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down application")
    scheduler.shutdown()
    await close_db()
    await RedisClient.close()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Campaign Operations OS - A multi-tenant SaaS for election campaign management",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)

# Setup rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS with restricted methods and headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "X-Campaign-ID",
        "X-Requested-With",
        "X-CSRF-Token",
    ],
    expose_headers=["X-Total-Count", "X-Page", "X-Page-Size"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    # Log the error
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
        },
        exc_info=True,
    )

    if settings.debug:
        # In debug mode, return full error details
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )
    else:
        # In production, return generic error
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# Detailed health check for monitoring
@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with component status.

    Checks database and Redis connectivity.
    """
    from app.database import engine
    from sqlalchemy import text

    status_info = {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "components": {},
    }

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        status_info["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        status_info["components"]["database"] = {"status": "unhealthy", "error": str(e)}
        status_info["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")

    # Check Redis
    try:
        redis = await RedisClient.get_client()
        await redis.ping()
        status_info["components"]["redis"] = {"status": "healthy"}
    except Exception as e:
        status_info["components"]["redis"] = {"status": "unhealthy", "error": str(e)}
        status_info["status"] = "degraded"
        logger.error(f"Redis health check failed: {e}")

    return status_info


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/api/docs" if settings.debug else "Disabled in production",
    }


# Import and include API routers
from app.api.v1.router import api_router

app.include_router(api_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
