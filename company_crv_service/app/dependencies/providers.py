"""
Company CRV Service - Dependency Providers

FastAPI dependency-injection providers that construct and supply service-layer
instances (e.g. CompanyVerificationService) to route handlers via `Depends`.
"""

from fastapi import Depends
from app.services.company_verification_service import CompanyVerificationService

def get_company_service() -> CompanyVerificationService:
    """Provider for CompanyVerificationService."""
    return CompanyVerificationService()
