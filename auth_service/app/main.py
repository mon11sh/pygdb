"""
Authentication Service - FastAPI Application

Central authentication service for GDB microservices.
Issues JWT tokens that other services verify independently.

Author: GDB Architecture Team
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config.settings import settings
from app.database.connection import init_db, close_db, get_provider
from app.api.auth_routes import router as auth_router
from app.exceptions.auth_exceptions import AuthenticationException


# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    
    Startup: Initialize database connection pool
    Shutdown: Close database connection pool
    """
    # Startup
    logger.info("Starting Authentication Service...")
    try:
        await init_db()
        logger.info("Database provider initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database provider: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Authentication Service...")
    await close_db()
    logger.info("Database provider disposed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Central authentication service for GDB microservices",
    docs_url="/api/v1/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)


# Exception handler for custom exceptions
@app.exception_handler(AuthenticationException)
async def auth_exception_handler(request, exc: AuthenticationException):
    """Handle custom authentication exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
        },
    )


# Include routers
app.include_router(auth_router)


# Root endpoint
@app.get("/", tags=["health"])
async def root():
    """Service information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


# Health check endpoint
@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "auth-service",
    }


# Ready check endpoint
@app.get("/ready", tags=["health"])
async def ready():
    """Readiness check (database connectivity)."""
    try:
        # Exercise the active provider's repository (works across every backend).
        await get_provider().token_repository().is_token_revoked("__healthcheck__")
        return {
            "status": "ready",
            "database": "connected",
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e),
            },
        )


# --- Enterprise remediation Phase 3.1: shared observability (gdb_common) ---
from gdb_common import install_observability

install_observability(app)






# --- Enterprise remediation Phase 2: liveness/readiness probes ---
@app.get("/live", tags=["Health"], include_in_schema=False)
async def _liveness_probe():
    """Liveness: the process is up (used by orchestrators)."""
    return {"status": "alive"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
