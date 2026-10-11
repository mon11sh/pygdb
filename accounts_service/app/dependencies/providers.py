"""FastAPI dependency providers for the Accounts Service.

Factory callables wired into route handlers via ``Depends(...)`` to supply the
account repository and the public/internal service layers. Centralizing
construction here keeps handlers decoupled from concrete implementations and
from the active database provider (selected by ``settings.DATABASE_PROVIDER``).
"""
from fastapi import Depends
from app.repositories.account_repo import AccountRepository
from app.services.account_service import AccountService
from app.services.internal_service import InternalAccountService

def get_account_repository() -> AccountRepository:
    """Provider for AccountRepository — resolved from the active database
    provider (chosen by settings.DATABASE_PROVIDER). Imported lazily so
    selecting a non-SQL provider never loads SQLAlchemy."""
    from app.database.connection import get_provider
    return get_provider().account_repository()

def get_account_service() -> AccountService:
    """Provider for AccountService."""
    return AccountService()

def get_internal_service() -> InternalAccountService:
    """Provider for InternalAccountService."""
    return InternalAccountService()
