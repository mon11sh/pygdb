"""HTTP API routes for the Central Payment Gateway service.

Exposes the ``/process`` and ``/validate`` endpoints under the payment router.
Both endpoints delegate to :class:`PaymentGatewayService` and translate any
unexpected service-layer error into an HTTP 500 response. The router itself is
mounted with an internal API-key dependency in :mod:`app.main`.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.payment import (
    PaymentRequest,
    PaymentResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.payment_gateway_service import PaymentGatewayService
from app.dependencies.providers import get_payment_gateway_service

router = APIRouter()

@router.post("/process", response_model=PaymentResponse)
async def process_payment(
    request: PaymentRequest,
    service: PaymentGatewayService = Depends(get_payment_gateway_service)
):
    """
    Process a payment through the Central Payment Gateway.
    Acts as a 2nd level validation for reliability.
    """
    try:
        response = await service.process_payment(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidationResponse)
async def validate_payment(
    request: ValidationRequest,
    service: PaymentGatewayService = Depends(get_payment_gateway_service)
):
    """
    Lightweight pre-check the frontend runs around a transfer. Does NOT move money;
    it only sanity-checks the request and returns {valid, message}.
    """
    try:
        return await service.validate_transfer(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
