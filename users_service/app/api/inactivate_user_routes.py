"""
Inactivate User Routes for User Management Service.
Endpoint: PATCH /api/v1/users/{login_id}/inactivate

Requires: ADMIN role
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from ..models.response_models import InactivateUserResponse, ErrorResponse
from ..services.inactivate_user_service import InactivateUserService
from ..repositories.user_repository import UserRepository
from ..exceptions.user_management_exception import (
    UserManagementException,
    UserNotFoundException,
    UserAlreadyInactiveException,
)
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Import authorization dependencies from Auth Service

try:
    from gdb_common.auth_dependencies import require_admin
except ImportError:
    # Fallback path
    auth_service_parent = str(Path(__file__).parent.parent.parent.parent / "auth_service")
    if auth_service_parent not in sys.path:
        sys.path.insert(0, auth_service_parent)
    from app.security.auth_dependencies import require_admin

from ..dependencies.providers import get_inactivate_user_service

router = APIRouter(prefix="/api/v1", tags=["User Management"])

@router.patch(
    "/users/{login_id}/inactivate",
    response_model=InactivateUserResponse,
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - ADMIN role required"},
        404: {"model": ErrorResponse, "description": "User not found"},
        400: {"model": ErrorResponse, "description": "User already inactive"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def inactivate_user(
    login_id: str,
    service: InactivateUserService = Depends(get_inactivate_user_service),
    claims: Dict[str, Any] = Depends(require_admin()),
) -> InactivateUserResponse:
    """
    Inactivate a user (soft delete).

    **Authorization:** ADMIN role required

    **Endpoint:** PATCH /api/v1/users/{login_id}/inactivate

    **Business Rules:**
    - User must exist
    - User must be active (cannot inactivate already inactive user)
    - Sets is_active = false
    - No hard delete operation
    - Only ADMIN can inactivate users

    **Path Parameters:**
    - login_id: User's login identifier

    **Success Response:** 200 OK
    **Error Responses:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN required)
    - 404: User not found
    - 400: User already inactive
    """
    try:
        # Call service to inactivate user
        result = await service.inactivate_user(login_id, performed_by=claims.get("login_id"))

        logger.info(f"User inactivated by {claims.get('login_id')}: {login_id}")
        return result

    except UserNotFoundException as e:
        logger.error(f"User not found: {login_id}")
        raise HTTPException(status_code=404, detail=e.detail)

    except UserAlreadyInactiveException as e:
        logger.error(f"User already inactive: {login_id}")
        raise HTTPException(status_code=400, detail=e.detail)

    except UserManagementException as e:
        logger.error(f"User management error: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except Exception as e:
        logger.error(f"Unexpected error inactivating user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
