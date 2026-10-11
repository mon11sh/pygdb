"""
Company CRV Service - Data Models

Pydantic dataclass models defining the request and response schemas for company
registration number (CIN) verification, including CIN format validation and the
detailed company payload returned on a successful match.
"""

from pydantic.dataclasses import dataclass
from pydantic import Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List


@dataclass
class CompanyVerificationRequest:
    """Request model for company registration verification."""
    registration_number: str = Field(..., min_length=21, max_length=21, description="21-character CIN")
    
    @field_validator("registration_number")
    @classmethod
    def validate_cin_format(cls, v):
        """Validate CIN format."""
        if not v.isalnum():
            raise ValueError("Registration number must be alphanumeric")
        if len(v) != 21:
            raise ValueError("Registration number must be exactly 21 characters")
        return v.upper()


@dataclass(config=ConfigDict(
    json_schema_extra={
        "example": {
            "registration_number": "U72900KA2020PTC123456",
            "is_valid": True,
            "status": "VERIFIED",
            "message": "Company registration number verified successfully",
            "company_name": "Tech Innovations Pvt Ltd",
            "type": "Private Limited",
            "address": "123 Tech Park, Bangalore, Karnataka",
            "email": "info@techinnovations.com",
            "phone": "+91-80-12345678",
            "website": "https://techinnovations.com",
            "incorporation_date": "2020-01-15",
            "paid_up_capital": "10,00,000",
            "directors": ["Rajesh Kumar", "Priya Sharma"],
            "timestamp": "2026-01-21T00:00:00Z"
        }
    }
))
class CompanyVerificationResponse:
    """Response model for company verification."""
    registration_number: str = Field(..., description="Registration number that was verified")
    is_valid: bool = Field(..., description="Whether the registration number is valid")
    status: str = Field(..., description="Verification status")
    message: str = Field(..., description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Verification timestamp")
    # Additional company details
    company_name: Optional[str] = Field(default=None, description="Company name")
    type: Optional[str] = Field(default=None, description="Company type")
    address: Optional[str] = Field(default=None, description="Company address")
    email: Optional[str] = Field(default=None, description="Company email")
    phone: Optional[str] = Field(default=None, description="Company phone")
    website: Optional[str] = Field(default=None, description="Company website")
    incorporation_date: Optional[str] = Field(default=None, description="Date of incorporation")
    paid_up_capital: Optional[str] = Field(default=None, description="Paid up capital")
    directors: Optional[List[str]] = Field(default=None, description="List of directors")
