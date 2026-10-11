"""Pydantic dataclass models for transaction and fund-transfer payloads.

Defines the request/response schemas for creating fund transfers and transaction
log entries, including field constraints and amount validators shared across the
transactions API and service layers.
"""

from pydantic.dataclasses import dataclass
from pydantic import Field, ConfigDict, field_validator
from typing import Literal
from decimal import Decimal
from datetime import datetime


@dataclass
class FundTransferCreate:
    """Request model for creating fund transfer."""
    from_account: int = Field(..., gt=0, description="Source account number")
    to_account: int = Field(..., gt=0, description="Destination account number")
    transfer_amount: Decimal = Field(..., gt=0, decimal_places=2, description="Transfer amount in INR")
    transfer_mode: Literal["NEFT", "RTGS", "IMPS", "UPI", "CHEQUE"] = Field(
        ...,
        description="Mode of fund transfer"
    )
    
    @field_validator("transfer_amount")
    @classmethod
    def validate_amount(cls, v):
        """Validate transfer amount."""
        if v <= 0:
            raise ValueError("Transfer amount must be greater than 0")
        if v > Decimal("999999999.99"):
            raise ValueError("Amount exceeds maximum limit")
        return v


@dataclass(config=ConfigDict(from_attributes=True))
class FundTransferResponse(FundTransferCreate):
    """Response model for fund transfer."""
    id: int = Field(..., description="Fund transfer ID (Primary Key)")
    created_at: datetime = Field(..., description="Transfer creation timestamp")
    updated_at: datetime = Field(..., description="Transfer last update timestamp")


@dataclass
class TransactionLoggingCreate:
    """Request model for creating transaction log."""
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Transaction amount in INR")
    transaction_type: Literal["WITHDRAW", "DEPOSIT", "TRANSFER"] = Field(
        ...,
        description="Type of transaction"
    )
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Validate transaction amount."""
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > Decimal("999999999.99"):
            raise ValueError("Amount exceeds maximum limit")
        return v


@dataclass(config=ConfigDict(from_attributes=True))
class TransactionLoggingResponse(TransactionLoggingCreate):
    """Response model for transaction logging."""
    id: int = Field(..., description="Transaction log ID (Primary Key)")
    created_at: datetime = Field(..., description="Transaction creation timestamp")
    updated_at: datetime = Field(..., description="Transaction last update timestamp")
