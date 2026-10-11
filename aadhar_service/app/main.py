"""
Aadhar Verification Service - Main Application

FastAPI application for Aadhar number verification.
Simulates UIDAI (Unique Identification Authority of India) API.

Author: GDB Architecture Team
"""

import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.models.aadhar import AadharVerificationRequest, AadharVerificationResponse
from app.services.aadhar_verification_service import AadharVerificationService
from app.dependencies.providers import get_aadhar_service
from app.dependencies.internal_auth import verify_internal_api_key

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Aadhar Verification Service",
    description="Third-party API for validating Aadhar numbers (UIDAI Simulation)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info(f"🚀 {settings.SERVICE_NAME} starting on port {settings.PORT}")
    logger.info(f"📋 Valid Aadhar numbers loaded: {len(AadharVerificationService.VALID_AADHAR_NUMBERS)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown information."""
    logger.info(f"🛑 {settings.SERVICE_NAME} shutting down")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": settings.SERVICE_NAME,
        "status": "healthy",
        "version": "1.0.0"
    }


# ============================================
# GET endpoint - Frontend uses this
# ============================================
@app.get(
    f"{settings.API_V1_PREFIX}/verify/{{aadhar_number}}",
    response_model=AadharVerificationResponse,
    summary="Verify Aadhar Number (GET)",
)
async def verify_aadhar_get(
    aadhar_number: str,
    service: AadharVerificationService = Depends(get_aadhar_service)
):
    """
    Verify an Aadhar number using GET request.
    Frontend calls: GET /api/v1/verify/{aadhar_number}
    """
    try:
        logger.info(f"GET Verification request for Aadhar: {aadhar_number[:4]}********")
        response = await service.verify(aadhar_number)
        return response
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail={"error_code": "VERIFICATION_ERROR", "message": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================
# POST endpoint - Original API
# ============================================
@app.post(
    f"{settings.API_V1_PREFIX}/verify",
    response_model=AadharVerificationResponse,
    summary="Verify Aadhar Number (POST)",
)
async def verify_aadhar(
    request: AadharVerificationRequest,
    service: AadharVerificationService = Depends(get_aadhar_service)
):
    """Verify an Aadhar number using POST request."""
    try:
        logger.info(f"POST Verification request for Aadhar: {request.aadhar_number[:4]}********")
        response = await service.verify(request.aadhar_number)
        return response
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail={"error_code": "VERIFICATION_ERROR", "message": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    f"{settings.API_V1_PREFIX}/valid-numbers",
    summary="Get Valid Aadhar Numbers",
)
async def get_valid_numbers(
    service: AadharVerificationService = Depends(get_aadhar_service)
):
    """Get list of valid Aadhar numbers (for testing)."""
    valid_numbers = await service.get_valid_aadhar_numbers()
    return {
        "valid_aadhar_numbers": valid_numbers,
        "count": len(service.VALID_AADHAR_NUMBERS)
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )


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
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
