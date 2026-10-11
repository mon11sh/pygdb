"""FastAPI dependency providers for the Central Payment Gateway service.

Contains factory callables wired into route handlers via ``Depends`` so that
service instances are constructed per request and can be overridden in tests.
"""
from fastapi import Depends
from app.services.payment_gateway_service import PaymentGatewayService

def get_payment_gateway_service() -> PaymentGatewayService:
    """Provider for PaymentGatewayService."""
    return PaymentGatewayService()
