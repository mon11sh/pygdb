"""
Add User Routes for User Management Service.
Endpoint: POST /api/v1/users

Requires: ADMIN role
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from ..models.request_models import AddUserRequest
from ..models.response_models import AddUserResponse, ErrorResponse
from ..services.add_user_service import AddUserService
from ..exceptions.user_management_exception import (
    UserManagementException,
    UserAlreadyExistsException,
    InvalidUserInputException,
)
from ..repositories.user_repository import UserRepository
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

from ..dependencies.providers import get_add_user_service

router = APIRouter(prefix="/api/v1", tags=["User Management"])


@router.post(
    "/users",
    response_model=AddUserResponse,
    status_code=201,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - ADMIN role required"},
        409: {"model": ErrorResponse, "description": "User already exists"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def add_user(
    request: AddUserRequest,
    service: AddUserService = Depends(get_add_user_service),
    claims: Dict[str, Any] = Depends(require_admin()),
) -> AddUserResponse:
    """
    Add a new user to the system.

    **Authorization:** ADMIN role required

    **Endpoint:** POST /api/v1/users

    **Business Rules:**
    - login_id must be unique
    - Password will be hashed before storage
    - User is active by default
    - Only ADMIN can create users

    **Request Body:**
    - username: User name (1-255 characters)
    - login_id: Unique login identifier (3-50 characters, alphanumeric + . - _)
    - password: Password (min 8 chars, uppercase, digit)
    - role: User role (ADMIN, TELLER, MANAGER)

    **Success Response:** 201 Created
    **Error Responses:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN required)
    - 409: User already exists
    - 400: Invalid input
    """
    try:
        # Call service to add user
        result = await service.add_user(request, performed_by=claims.get("login_id"))

        logger.info(f"User created by {claims.get('login_id')}: {request.login_id}")
        return result

    except UserAlreadyExistsException as e:
        logger.error(f"User already exists: {request.login_id}")
        raise HTTPException(status_code=409, detail=e.detail)

    except InvalidUserInputException as e:
        logger.error(f"Invalid input: {e.detail}")
        raise HTTPException(status_code=400, detail=e.detail)

    except UserManagementException as e:
        logger.error(f"User management error: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except Exception as e:
        logger.error(f"Unexpected error adding user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
