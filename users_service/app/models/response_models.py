"""Response models for User Management Service.

Pydantic dataclass schemas describing the API responses for user operations
(add, edit, view, list, activate/inactivate) plus the standard error envelope.
"""

from pydantic.dataclasses import dataclass
from pydantic import Field, ConfigDict
from typing import List, Optional
from datetime import datetime


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "user_id": 1,
            "username": "John Doe",
            "login_id": "john.doe",
            "role": "MANAGER",
            "created_at": "2025-12-22T10:30:00",
            "is_active": True,
        }
    }
))
class UserResponse:
    """Base response model for user details."""

    user_id: int = Field(..., description="User unique identifier")
    username: str = Field(..., description="User name")
    login_id: str = Field(..., description="Unique login identifier")
    created_at: datetime = Field(..., description="User creation timestamp")
    is_active: bool = Field(..., description="Active status")
    role: str = Field(default="MANAGER", description="User role (MANAGER, TELLER, ADMIN)")


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "user_id": 1,
            "username": "John Doe",
            "login_id": "john.doe",
            "role": "MANAGER",
            "created_at": "2025-12-22T10:30:00",
            "is_active": True,
            "message": "User created successfully",
        }
    }
))
class AddUserResponse(UserResponse):
    """Response model for add user operation."""
    message: str = Field(default="User created successfully", description="Success message")


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "user_id": 1,
            "username": "Jane Doe",
            "login_id": "john.doe",
            "role": "TELLER",
            "created_at": "2025-12-22T10:30:00",
            "is_active": True,
            "message": "User updated successfully",
        }
    }
))
class EditUserResponse(UserResponse):
    """Response model for edit user operation."""
    message: str = Field(default="User updated successfully", description="Success message")


@dataclass
class ViewUserResponse(UserResponse):
    """Response model for view user operation."""
    pass


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "users": [
                {
                    "username": "John Doe",
                    "login_id": "john.doe",
                    "role": "MANAGER",
                    "created_at": "2025-12-22T10:30:00",
                    "is_active": True,
                }
            ],
            "total_count": 1,
        }
    }
))
class ListUsersResponse:
    """Response model for list users operation."""

    users: List[UserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total number of users")


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "username": "John Doe",
            "login_id": "john.doe",
            "role": "MANAGER",
            "created_at": "2025-12-22T10:30:00",
            "is_active": False,
            "message": "User inactivated successfully",
        }
    }
))
class InactivateUserResponse(UserResponse):
    """Response model for inactivate/activate user operation."""
    message: str = Field(default="User inactivated successfully", description="Success message")


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "error_code": "USER_NOT_FOUND",
            "detail": "User with login_id 'john.doe' not found",
        }
    }
))
class ErrorResponse:
    """Error response model."""
    error_code: str = Field(..., description="Error code")
    detail: str = Field(..., description="Error message")
