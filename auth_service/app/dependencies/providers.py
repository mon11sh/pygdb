"""
Dependency Injection Providers

FastAPI dependency callables that construct and supply auth-layer collaborators
(repositories and the authentication service) to route handlers. Repository
providers resolve concrete implementations from the active database provider
selected by settings, keeping backend selection out of the request handlers.

Author: GDB Architecture Team
"""

from fastapi import Depends
from app.services.auth_service import AuthService
from app.repositories.auth_token_repo import AuthTokenRepository
from app.repositories.auth_audit_repo import AuthAuditRepository


def get_token_repository() -> AuthTokenRepository:
    """Provider for AuthTokenRepository — resolved from the active database
    provider (chosen by settings.DATABASE_PROVIDER). Imported lazily so
    selecting a non-SQL provider never loads SQLAlchemy."""
    from app.database.connection import get_provider
    return get_provider().token_repository()


def get_audit_repository() -> AuthAuditRepository:
    """Provider for AuthAuditRepository — resolved from the active database provider."""
    from app.database.connection import get_provider
    return get_provider().audit_repository()


def get_auth_service() -> AuthService:
    """Provider for AuthService."""
    return AuthService()
