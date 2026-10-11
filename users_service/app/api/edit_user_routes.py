"""
Edit User Routes for User Management Service.
Endpoint: PUT /api/v1/users/{login_id}

Requires: ADMIN role
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from ..models.request_models import EditUserRequest
from ..models.response_models import EditUserResponse, ErrorResponse
from ..services.edit_user_service import EditUserService
from ..repositories.user_repository import UserRepository
from ..exceptions.user_management_exception import (
    UserManagementException,
    UserNotFoundException,
    UserInactiveException,
    InvalidUserInputException,
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

from ..dependencies.providers import get_edit_user_service

router = APIRouter(prefix="/api/v1", tags=["User Management"])


@router.put(
    "/users/{login_id}",
    response_model=EditUserResponse,
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - ADMIN role required OR User is inactive"},
        404: {"model": ErrorResponse, "description": "User not found"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def edit_user(
    login_id: str,
    request: EditUserRequest,
    service: EditUserService = Depends(get_edit_user_service),
    claims: Dict[str, Any] = Depends(require_admin()),
) -> EditUserResponse:
    """
    Edit user information.

    **Authorization:** ADMIN role required

    **Endpoint:** PUT /api/v1/users/{login_id}

    **Business Rules:**
    - User must exist
    - User must be active
    - login_id is immutable (cannot change)
    - Editable fields: username, password
    - Only ADMIN can edit users

    **Path Parameters:**
    - login_id: User's login identifier

    **Request Body:**
    - username: New username (optional)
    - password: New password (optional)

    **Success Response:** 200 OK
    **Error Responses:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN required) OR User is inactive
    - 404: User not found
    - 400: Invalid input
    """
    try:
        # Call service to edit user
        result = await service.edit_user(login_id, request, performed_by=claims.get("login_id"))

        logger.info(f"User edited by {claims.get('login_id')}: {login_id}")
        return result

    except UserNotFoundException as e:
        logger.error(f"User not found: {login_id}")
        raise HTTPException(status_code=404, detail=e.detail)

    except UserInactiveException as e:
        logger.error(f"User is inactive: {login_id}")
        raise HTTPException(status_code=403, detail=e.detail)

    except InvalidUserInputException as e:
        logger.error(f"Invalid input: {e.detail}")
        raise HTTPException(status_code=400, detail=e.detail)

    except UserManagementException as e:
        logger.error(f"User management error: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except Exception as e:
        logger.error(f"Unexpected error editing user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
