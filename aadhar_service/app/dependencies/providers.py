"""
Aadhar Service - Dependency Providers

FastAPI dependency-injection providers that construct service-layer
instances (e.g. AadharVerificationService) for injection into route handlers.
"""

from fastapi import Depends
from app.services.aadhar_verification_service import AadharVerificationService

def get_aadhar_service() -> AadharVerificationService:
    """Provider for AadharVerificationService."""
    return AadharVerificationService()
