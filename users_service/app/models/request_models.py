"""
Request models for User Management Service.
Pydantic schemas for API validation and serialization.
"""

import re
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional


class AddUserRequest(BaseModel):
    """Request model for adding a new user."""

    username: str = Field(..., min_length=1, max_length=255, description="User name")
    login_id: str = Field(
        ..., min_length=3, max_length=50, description="Unique login identifier"
    )
    password: str = Field(..., min_length=8, description="User password")
    role: Optional[str] = Field(None, description="User role (MANAGER, TELLER, ADMIN) - defaults to MANAGER")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "John Doe",
                "login_id": "john.doe",
                "password": "SecurePassword123!",
                "role": "MANAGER",
            }
        }
    )

    @field_validator("login_id")
    @classmethod
    def login_id_valid_format(cls, v):
        """Validate login_id format."""
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError("login_id can only contain alphanumeric, dots, hyphens, underscores")
        return v

    @field_validator("password")
    @classmethod
    def password_strong(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class EditUserRequest(BaseModel):
    """Request model for editing user information."""

    username: Optional[str] = Field(None, min_length=1, max_length=255, description="New username")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    role: Optional[str] = Field(None, description="New role (MANAGER, TELLER, ADMIN)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "Jane Doe",
                "password": "NewSecurePassword123!",
                "role": "TELLER",
            }
        }
    )

    @field_validator("password")
    @classmethod
    def password_strong(cls, v):
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
