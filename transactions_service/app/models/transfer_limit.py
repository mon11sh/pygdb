"""Pydantic dataclass models for transfer limit rules and limit checks.

Defines the schemas describing per-privilege transfer ceilings (daily, monthly,
and per-transaction limits) and the request payload used to check a proposed
transfer amount against the applicable limit.
"""

from pydantic.dataclasses import dataclass
from pydantic import Field, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal


@dataclass
class TransferLimitBase:
    """Base transfer limit fields: daily, monthly, and per-transaction ceilings."""
    daily_limit: Decimal = Field(..., ge=0)
    monthly_limit: Decimal = Field(..., ge=0)
    per_transaction_limit: Decimal = Field(..., ge=0)


@dataclass
class TransferLimitCreate(TransferLimitBase):
    """Request model for creating a transfer limit rule, optionally per privilege."""
    privilege: Optional[str] = None


@dataclass(config=ConfigDict(from_attributes=True))
class TransferLimitResponse(TransferLimitBase):
    """Response model for a persisted transfer limit rule, including identity and timestamps."""
    id: int
    privilege: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class LimitCheckRequest:
    """Request model for checking a transfer amount against an account's privilege limit."""
    account_number: int
    amount: Decimal
    privilege: str
