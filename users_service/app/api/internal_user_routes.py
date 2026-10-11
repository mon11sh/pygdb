"""
Internal User Routes for User Management Service

INTERNAL API ENDPOINTS (Simplified - 6 endpoints)

CORE ENDPOINTS (3 - Required for Auth Service):
- POST /internal/v1/users/verify - Verify user credentials (login_id + password)
- GET /internal/v1/users/{login_id}/status - Get user status and role
- GET /internal/v1/users/{login_id}/role - Get user role only

OPTIONAL ENDPOINTS (2 - Advanced Features):
- POST /internal/v1/users/validate-role - Validate if user has required role
- POST /internal/v1/users/bulk-validate - Bulk validate multiple users

UTILITY ENDPOINTS (1):
- GET /internal/v1/health - Health check with endpoint listing

DEPRECATED/REMOVED ENDPOINTS (3):
- Removed: GET /internal/v1/users/{user_id} (redundant, use status endpoint)
- Removed: GET /internal/v1/users (search functionality - moved to public API)
- Removed: GET /internal/v1/users/{user_id}/role (replaced with login_id version)

Design Philosophy:
- Minimal surface area: Only endpoints needed for Auth Service integration
- Security first: All endpoints validate credentials/permissions before returning data
- Audit ready: All operations are logged for compliance
"""

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Optional
from pydantic import BaseModel
import bcrypt
import logging

from ..models.response_models import ErrorResponse
from ..repositories.user_repository import UserRepository
from ..exceptions.user_management_exception import (
    UserManagementException,
    UserNotFoundException,
)
from ..dependencies.providers import get_internal_user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/v1", tags=["Internal User APIs"])


# ============================================================================
# REQUEST MODELS
# ============================================================================

class BulkValidateRequest(BaseModel):
    """Request model for bulk user validation endpoint."""
    login_ids: List[str]


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class VerifyCredentialsResponse(BaseModel):
    """Response model for verify user credentials endpoint."""
    is_valid: bool
    user_id: Optional[int] = None
    role: Optional[str] = None
    is_active: bool = False


# ============================================================================
# SERVICE CLASS
# ============================================================================

from ..services.internal_user_service import InternalUserService


# ============================================================================
# CORE ENDPOINTS (3)
# ============================================================================

@router.post(
    "/users/verify",
    status_code=200,
    response_model=VerifyCredentialsResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid credentials"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def verify_user_credentials(
    login_id: str = Body(..., embed=True),
    password: str = Body(..., embed=True),
    service: InternalUserService = Depends(get_internal_user_service),
) -> VerifyCredentialsResponse:
    """
    Verify user credentials (CORE - Required for Auth Service).
    
    **Endpoint:** POST /internal/v1/users/verify
    
    **Purpose:** Authenticate user by login_id and password
    
    **Request Body:**
    ```json
    {
        "login_id": "user.name",
        "password": "SecurePass123"
    }
    ```
    
    **Success Response (200 - Valid Credentials):**
    ```json
    {
        "is_valid": true,
        "user_id": 123,
        "role": "MANAGER",
        "is_active": true
    }
    ```
    
    **Error Response (200 - Invalid Credentials or User Not Found):**
    ```json
    {
        "is_valid": false,
        "user_id": null,
        "role": null,
        "is_active": false
    }
    ```
    
    **Response Fields:**
    - `is_valid`: Boolean indicating if credentials are correct
    - `user_id`: User ID if credentials valid, null otherwise
    - `role`: User role (MANAGER/TELLER/ADMIN) if credentials valid, null otherwise
    - `is_active`: User active status if credentials valid, false otherwise
    """
    try:
        result = await service.verify_user_credentials(login_id, password)
        return VerifyCredentialsResponse(**result)
    
    except Exception as e:
        logger.error(f"Error verifying credentials: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/users/{login_id}/status",
    status_code=200,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def get_user_status(
    login_id: str,
    service: InternalUserService = Depends(get_internal_user_service),
):
    """
    Get user status and role (CORE - Required for Auth Service).
    
    **Endpoint:** GET /internal/v1/users/{login_id}/status
    
    **Purpose:** Get user's active status and role for authorization
    
    **Path Parameters:**
    - login_id: User's login identifier
    
    **Success Response (200):**
    ```json
    {
        "user_id": 123,
        "login_id": "user.name",
        "is_active": true,
        "role": "MANAGER"
    }
    ```
    
    **Error Response (404):**
    ```json
    {
        "detail": "User not found"
    }
    ```
    """
    try:
        result = await service.get_user_status(login_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/users/{login_id}/role",
    status_code=200,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def get_user_role(
    login_id: str,
    service: InternalUserService = Depends(get_internal_user_service),
):
    """
    Get user role only (CORE - Required for Auth Service).
    
    **Endpoint:** GET /internal/v1/users/{login_id}/role
    
    **Purpose:** Quick role lookup for authorization checks
    
    **Path Parameters:**
    - login_id: User's login identifier
    
    **Success Response (200):**
    ```json
    {
        "user_id": 123,
        "login_id": "user.name",
        "role": "MANAGER"
    }
    ```
    
    **Error Response (404):**
    ```json
    {
        "detail": "User not found"
    }
    ```
    """
    try:
        result = await service.get_user_role(login_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# OPTIONAL ENDPOINTS (2)
# ============================================================================

@router.post(
    "/users/validate-role",
    status_code=200,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def validate_user_role(
    login_id: str = Body(..., embed=True),
    required_role: str = Body(..., embed=True),
    service: InternalUserService = Depends(get_internal_user_service),
):
    """
    Validate if user has required role (OPTIONAL - Advanced feature).
    
    **Endpoint:** POST /internal/v1/users/validate-role
    
    **Purpose:** Check if user has specific role for authorization
    
    **Request Body:**
    ```json
    {
        "login_id": "user.name",
        "required_role": "TELLER"
    }
    ```
    
    **Success Response (200):**
    ```json
    {
        "has_role": true,
        "user_role": "TELLER",
        "is_active": true
    }
    ```
    
    **Error Response (404):**
    ```json
    {
        "detail": "User not found"
    }
    ```
    """
    try:
        result = await service.validate_user_role(login_id, required_role)
        
        if result is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/users/bulk-validate",
    status_code=200,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def bulk_validate_users(
    request: BulkValidateRequest,
    service: InternalUserService = Depends(get_internal_user_service),
):
    """
    Bulk validate multiple users (OPTIONAL - Batch processing).
    
    **Endpoint:** POST /internal/v1/users/bulk-validate
    
    **Purpose:** Validate multiple users in single request
    
    **Request Body:**
    ```json
    {
        "login_ids": ["user1.name", "user2.name", "user3.name"]
    }
    ```
    
    **Success Response (200):**
    ```json
    {
        "valid_users": [
            {
                "user_id": 123,
                "login_id": "user1.name",
                "role": "MANAGER",
                "is_active": true
            },
            {
                "user_id": 124,
                "login_id": "user2.name",
                "role": "TELLER",
                "is_active": true
            }
        ],
        "invalid_users": ["user3.name"],
        "total_valid": 2,
        "total_invalid": 1
    }
    ```
    """
    try:
        if not request.login_ids:
            raise HTTPException(status_code=400, detail="login_ids cannot be empty")
        
        result = await service.bulk_validate_users(request.login_ids)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk validate: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# UTILITY ENDPOINTS (1)
# ============================================================================

@router.get(
    "/health",
    status_code=200,
)
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "User Management Service - Internal APIs",
        "version": "1.0.0"
    }
