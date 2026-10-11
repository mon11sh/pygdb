"""
View User Routes for User Management Service.
Endpoints:
- GET /api/v1/users/{login_id} - View single user (self or ADMIN)
- GET /api/v1/users - List all users (ADMIN/TELLER only)

Authorization:
- View self profile: MANAGER, TELLER, ADMIN
- View any user: ADMIN only
- List all users: ADMIN, TELLER only
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from ..models.response_models import (
    ViewUserResponse,
    ListUsersResponse,
    ErrorResponse,
)
from ..services.view_user_service import ViewUserService
from ..repositories.user_repository import UserRepository
from ..exceptions.user_management_exception import (
    UserManagementException,
    UserNotFoundException,
)
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Import authorization dependencies from Auth Service

try:
    from gdb_common.auth_dependencies import get_current_user, require_admin_or_teller
    from gdb_common.jwt_validation import JWTValidator, RoleChecker
except ImportError:
    # Fallback path
    auth_service_parent = str(Path(__file__).parent.parent.parent.parent / "auth_service")
    if auth_service_parent not in sys.path:
        sys.path.insert(0, auth_service_parent)
    from app.security.auth_dependencies import get_current_user, require_admin_or_teller
    from app.security.jwt_validation import JWTValidator, RoleChecker

from ..dependencies.providers import get_view_user_service

router = APIRouter(prefix="/api/v1", tags=["User Management"])


@router.get(
    "/users/{login_id}",
    response_model=ViewUserResponse,
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Cannot view other users"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def view_user(
    login_id: str,
    service: ViewUserService = Depends(get_view_user_service),
    claims: Dict[str, Any] = Depends(get_current_user),
) -> ViewUserResponse:
    """
    View user details by login_id.

    **Authorization:**
    - View own profile: MANAGER, TELLER, ADMIN
    - View other users: ADMIN only

    **Endpoint:** GET /api/v1/users/{login_id}

    **Business Rules:**
    - User must exist
    - Password is never returned
    - Returns user profile data
    - MANAGER/TELLER can only view themselves
    - ADMIN can view any user

    **Path Parameters:**
    - login_id: User's login identifier

    **Success Response:** 200 OK
    **Error Responses:**
    - 401: Missing or invalid authorization token
    - 403: Cannot view other users (non-ADMIN users can only view themselves)
    - 404: User not found
    """
    try:
        # Extract claims
        user_role = JWTValidator.get_role(claims)
        requesting_login_id = JWTValidator.get_login_id(claims)
        
        # Check authorization: non-ADMIN users can only view themselves
        if user_role != "ADMIN" and requesting_login_id != login_id:
            logger.warning(
                f"Access denied: user {requesting_login_id} tried to view {login_id}"
            )
            raise HTTPException(
                status_code=403,
                detail="You can only view your own profile",
            )
        
        # Call service to view user
        result = await service.get_user(login_id)

        return result

    except UserNotFoundException as e:
        logger.error(f"User not found: {login_id}")
        raise HTTPException(status_code=404, detail=e.detail)

    except UserManagementException as e:
        logger.error(f"User management error: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Unexpected error viewing user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/users",
    response_model=ListUsersResponse,
    status_code=200,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - ADMIN or TELLER role required"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def list_users(
    service: ViewUserService = Depends(get_view_user_service),
    claims: Dict[str, Any] = Depends(require_admin_or_teller()),
) -> ListUsersResponse:
    """
    List all active users.

    **Authorization:** ADMIN or TELLER role required

    **Endpoint:** GET /api/v1/users

    **Business Rules:**
    - Returns only active users
    - Passwords are never returned
    - Ordered by creation date (newest first)
    - Only ADMIN and TELLER can list users

    **Success Response:** 200 OK
    **Error Responses:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN or TELLER required)
    """
    try:
        # Call service to list users
        result = await service.list_users()

        logger.info(f"Users listed by {claims.get('login_id')}")
        return result

    except UserManagementException as e:
        logger.error(f"User management error: {e.detail}")
        raise HTTPException(status_code=e.status_code, detail=e.detail)

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Unexpected error listing users: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
