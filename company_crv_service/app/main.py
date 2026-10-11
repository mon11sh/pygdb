"""
Company CRV Service - FastAPI Application Entry Point

Defines the FastAPI app, CORS middleware, lifecycle hooks, and the HTTP routes
for verifying Company Registration Numbers (CIN) against the MCA/ROC simulation.
Also wires shared observability plus liveness/readiness probes and the uvicorn
runner used for local execution.
"""

import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.models.company import CompanyVerificationRequest, CompanyVerificationResponse
from app.services.company_verification_service import CompanyVerificationService
from app.dependencies.providers import get_company_service
from app.dependencies.internal_auth import verify_internal_api_key

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Company Registration Validation Service",
    description="Third-party API for validating Company Registration Numbers (CIN) - MCA/ROC Simulation",
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
    logger.info(f"📋 Valid company records loaded: {len(CompanyVerificationService.VALID_REGISTRATION_NUMBERS)}")


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
    f"{settings.API_V1_PREFIX}/company/verify/{{registration_number}}",
    response_model=CompanyVerificationResponse,
    summary="Verify Company Registration Number (GET)",
)
async def verify_company_get(
    registration_number: str,
    service: CompanyVerificationService = Depends(get_company_service)
):
    """
    Verify a company registration number using GET request.
    Frontend calls: GET /api/v1/company/verify/{registration_number}
    """
    try:
        logger.info(f"GET Verification request for CIN: {registration_number[:8]}*************")
        response = await service.verify(registration_number)
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
    f"{settings.API_V1_PREFIX}/company/verify",
    response_model=CompanyVerificationResponse,
    summary="Verify Company Registration Number (POST)",
)
async def verify_company(
    request: CompanyVerificationRequest,
    service: CompanyVerificationService = Depends(get_company_service)
):
    """Verify a company registration number."""
    try:
        logger.info(f"Received verification request for CIN: {request.registration_number[:8]}*************")
        response = await service.verify(request.registration_number)
        return response
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail={"error_code": "VERIFICATION_ERROR", "message": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get(
    f"{settings.API_V1_PREFIX}/company/valid-companies",
    summary="Get Valid Company Registration Numbers",
)
async def get_valid_companies(
    service: CompanyVerificationService = Depends(get_company_service)
):
    """Get list of valid company registration numbers (for testing)."""
    valid_numbers = await service.get_valid_registration_numbers()
    return {
        "valid_companies": valid_numbers,
        "count": len(valid_numbers)
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
