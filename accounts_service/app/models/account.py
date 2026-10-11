"""Account domain models for the Accounts microservice.

Defines the Pydantic dataclasses used across the API and service layers for
creating and representing accounts: creation requests (``SavingsAccountCreate``,
``CurrentAccountCreate``), response shapes (``AccountResponse`` and subtypes,
``AccountDetailsResponse``, ``BalanceResponse``), internal debit/credit requests,
update payloads, and the standard ``ErrorResponse``. Includes field-level
validators for DOB, phone, and Aadhar formatting/masking.
"""
from pydantic.dataclasses import dataclass
from pydantic import Field, ConfigDict, field_validator
from typing import Optional, Literal, List
from datetime import datetime


@dataclass
class AccountBase:
    """Base account model with common fields."""
    name: str = Field(..., min_length=2, max_length=255, description="Account holder name")
    privilege: Literal["PREMIUM", "GOLD", "SILVER"] = Field(
        default="SILVER",
        description="Account privilege level"
    )
    bank_name: str = Field(default="Global Digital Bank", description="Name of the Bank")
    bank_branch: str = Field(default="Main Branch", description="Branch Name")
    ifsc_code: str = Field(default="GDB0000001", description="Bank IFSC Code")

    def model_dump(self, **kwargs):
        """
        Helper method to mimic Pydantic model_dump for dataclasses.
        """
        from dataclasses import asdict
        data = asdict(self)
        if kwargs.get('exclude_none'):
            return {k: v for k, v in data.items() if v is not None}
        return data


@dataclass
class SavingsAccountCreate(AccountBase):
    """Request model for creating savings account."""
    pin: str = Field(..., min_length=4, max_length=4, description="4-digit PIN")
    date_of_birth: str = Field(..., description="DOB in YYYY-MM-DD format")
    gender: Literal["Male", "Female", "Others"] = Field(..., description="Gender")
    phone_no: str = Field(..., min_length=10, max_length=10, description="10-digit Phone number")
    aadhar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhar number")
    account_type: Literal["SAVINGS"] = "SAVINGS"
    initial_balance: float = Field(default=2000.0, ge=2000.0, description="Initial deposit (must be >= 2000)")
    
    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v):
        """Validate date of birth format."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v
    
    @field_validator("phone_no")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number is numeric."""
        if not v.isdigit():
            raise ValueError("Phone number must be numeric")
        return v
    
    @field_validator("aadhar_number")
    @classmethod
    def validate_aadhar(cls, v):
        """Validate Aadhar number is exactly 12 digits."""
        if not v.isdigit():
            raise ValueError("Aadhar number must contain only digits")
        if len(v) != 12:
            raise ValueError("Aadhar number must be exactly 12 digits")
        return v


@dataclass
class CurrentAccountCreate(AccountBase):
    """Request model for creating current account."""
    pin: str = Field(..., min_length=4, max_length=4, description="4-digit PIN")
    company_name: str = Field(..., min_length=1, max_length=255, description="Company name")
    registration_no: str = Field(..., min_length=1, max_length=50, description="Company registration number")
    account_type: Literal["CURRENT"] = "CURRENT"
    website: Optional[str] = Field(None, max_length=255, description="Company website")


@dataclass(config=ConfigDict(from_attributes=True))
class AccountResponse(AccountBase):
    """Response model for account details."""
    account_number: int = Field(..., description="Unique account number")
    account_type: Literal["SAVINGS", "CURRENT"] = Field(..., description="Account type")
    balance: float = Field(..., description="Current account balance")
    is_active: bool = Field(..., description="Account active status")
    activated_date: datetime = Field(..., description="Account opening date")
    closed_date: Optional[datetime] = Field(None, description="Account closing date")


@dataclass(config=ConfigDict(from_attributes=True))
class SavingsAccountResponse(AccountResponse):
    """Response model for savings account with details."""
    date_of_birth: str = Field(..., description="Date of birth")
    gender: str = Field(..., description="Gender")
    phone_no: str = Field(..., description="Phone number")
    aadhar_number: str = Field(..., description="Aadhar number")
    
    @field_validator("aadhar_number", mode="after")
    @classmethod
    def mask_aadhar(cls, v: str) -> str:
        """Mask Aadhar number for security (e.g., 123456781234 -> ********1234)."""
        if len(v) == 12:
            return "*" * 8 + v[-4:]
        return v


@dataclass(config=ConfigDict(from_attributes=True))
class CurrentAccountResponse(AccountResponse):
    """Response model for current account with details."""
    company_name: str = Field(..., description="Company name")
    registration_no: str = Field(..., description="Registration number")
    website: Optional[str] = Field(None, description="Company website")


@dataclass
class BalanceResponse:
    """Response model for balance query."""
    account_number: int
    balance: float
    currency: str = "INR"


@dataclass
class DebitRequest:
    """Internal request model for debit operation."""
    account_number: int
    amount: float = Field(..., gt=0, description="Amount to debit")
    description: Optional[str] = None
    idempotency_key: Optional[str] = None


@dataclass
class CreditRequest:
    """Internal request model for credit operation."""
    account_number: int
    amount: float = Field(..., gt=0, description="Amount to credit")
    description: Optional[str] = None
    idempotency_key: Optional[str] = None


@dataclass(config=ConfigDict(from_attributes=True))
class AccountDetailsResponse:
    """Response model for account details (internal use)."""
    account_number: int
    account_type: Literal["SAVINGS", "CURRENT"]
    name: str
    balance: float
    privilege: Literal["PREMIUM", "GOLD", "SILVER"]
    is_active: bool
    activated_date: datetime
    bank_name: str
    bank_branch: str
    ifsc_code: str
    closed_date: Optional[datetime] = None


@dataclass
class AccountUpdate(AccountBase):
    """Request model for updating account details."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Account holder name")
    privilege: Optional[Literal["PREMIUM", "GOLD", "SILVER"]] = Field(None, description="Account privilege level")
    # Savings-specific fields
    phone_no: Optional[str] = Field(None, min_length=10, max_length=20, description="Phone number")
    # Current-specific fields
    company_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Company name")
    website: Optional[str] = Field(None, max_length=255, description="Company website")
    
    @field_validator("phone_no")
    @classmethod
    def validate_phone(cls, v):
        """Validate phone number is numeric."""
        if v is not None and not v.isdigit():
            raise ValueError("Phone number must be numeric")
        return v


@dataclass
class ErrorResponse:
    """Standard error response model."""
    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = None
