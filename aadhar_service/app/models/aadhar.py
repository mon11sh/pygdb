"""
Aadhar Service - Data Models

Pydantic dataclass models defining the request and response schemas for the
Aadhar verification API, including validation of the 12-digit Aadhar format
and the optional holder-information fields returned on successful lookup.
"""

from pydantic.dataclasses import dataclass
from pydantic import Field, ConfigDict, field_validator
from datetime import datetime, date
from typing import Optional


@dataclass
class AadharVerificationRequest:
    """Request model for Aadhar verification."""
    aadhar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhar number")
    
    @field_validator("aadhar_number")
    @classmethod
    def validate_aadhar_format(cls, v):
        """Validate Aadhar number is exactly 12 digits."""
        if not v.isdigit():
            raise ValueError("Aadhar number must contain only digits")
        if len(v) != 12:
            raise ValueError("Aadhar number must be exactly 12 digits")
        return v


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "aadhar_number": "123456789012",
            "is_valid": True,
            "status": "VERIFIED",
            "message": "Aadhar number verified successfully",
            "name": "Rajesh Kumar",
            "mobile_no": "9876543210",
            "address": "123, MG Road, Bangalore, Karnataka - 560001",
            "gender": "Male",
            "date_of_birth": "1990-05-15",
            "photo_url": "https://example.com/photos/aadhar_123456789012.jpg",
            "timestamp": "2026-01-21T00:00:00Z"
        }
    }
))
class AadharVerificationResponse:
    """Response model for Aadhar verification."""
    aadhar_number: str = Field(..., description="Aadhar number that was verified")
    is_valid: bool = Field(..., description="Whether the Aadhar number is valid")
    status: str = Field(..., description="Verification status")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Verification timestamp")
    
    # Optional holder information
    name: Optional[str] = Field(None, description="Full name of Aadhar holder")
    mobile_no: Optional[str] = Field(None, description="Registered mobile number")
    address: Optional[str] = Field(None, description="Registered address")
    gender: Optional[str] = Field(None, description="Gender")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    photo_url: Optional[str] = Field(None, description="URL to Aadhar holder photo")
