"""Application entrypoint for the Central Payment Gateway service.

Constructs the FastAPI application, configures CORS, mounts the payment router
behind an internal API-key dependency, installs shared observability, and
registers health/liveness/readiness probes. Running this module directly starts
the service via uvicorn.
"""
from fastapi import FastAPI, Depends
from app.api.routes import router as payment_router
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.dependencies.internal_auth import verify_internal_api_key

app = FastAPI(
    title=settings.APP_NAME,
    description="Simulated Third-Party Payment Gateway for GDB Ecosystem",
    version=settings.APP_VERSION
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    payment_router,
    prefix="/api/v1/payment",
    tags=["Payment Gateway"],
    dependencies=[Depends(verify_internal_api_key)],
)

@app.get("/health")
def health_check():
    """Report basic service health.

    Returns:
        dict: A payload with the service status and configured application name.
    """
    return {"status": "active", "service": settings.APP_NAME}

# --- Enterprise remediation Phase 3.1: shared observability (gdb_common) ---
from gdb_common import install_observability

install_observability(app)






# --- Enterprise remediation Phase 2: liveness/readiness probes ---
@app.get("/live", tags=["Health"], include_in_schema=False)
async def _liveness_probe():
    """Liveness: the process is up (used by orchestrators)."""
    return {"status": "alive"}


@app.get("/ready", tags=["Health"], include_in_schema=False)
async def _readiness_probe():
    """Readiness: the service is ready to accept traffic."""
    return {"status": "ready"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
