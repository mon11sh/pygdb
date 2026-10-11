"""Dependency-injection providers for the User Management Service.

Defines FastAPI dependency callables that wire the shared ``UserRepository``
into each user-management service class. The repository is resolved lazily from
the configured database provider so selecting a non-SQL backend never imports
SQLAlchemy.
"""
from fastapi import Depends
from ..repositories.user_repository import UserRepository
from ..services.add_user_service import AddUserService
from ..services.edit_user_service import EditUserService
from ..services.view_user_service import ViewUserService
from ..services.activate_user_service import ActivateUserService
from ..services.inactivate_user_service import InactivateUserService
from ..services.internal_user_service import InternalUserService

def get_user_repository() -> UserRepository:
    """Provider for UserRepository — resolved from the active database provider
    (chosen by settings.DATABASE_PROVIDER). Imported lazily so selecting a
    non-SQL provider never loads SQLAlchemy."""
    from ..database.connection import get_provider
    return get_provider().user_repository()

def get_add_user_service(repo: UserRepository = Depends(get_user_repository)) -> AddUserService:
    """Provider for AddUserService."""
    return AddUserService(repo)

def get_edit_user_service(repo: UserRepository = Depends(get_user_repository)) -> EditUserService:
    """Provider for EditUserService."""
    return EditUserService(repo)

def get_view_user_service(repo: UserRepository = Depends(get_user_repository)) -> ViewUserService:
    """Provider for ViewUserService."""
    return ViewUserService(repo)

def get_activate_user_service(repo: UserRepository = Depends(get_user_repository)) -> ActivateUserService:
    """Provider for ActivateUserService."""
    return ActivateUserService(repo)

def get_inactivate_user_service(repo: UserRepository = Depends(get_user_repository)) -> InactivateUserService:
    """Provider for InactivateUserService."""
    return InactivateUserService(repo)

def get_internal_user_service(repo: UserRepository = Depends(get_user_repository)) -> InternalUserService:
    """Provider for InternalUserService."""
    return InternalUserService(repo)
