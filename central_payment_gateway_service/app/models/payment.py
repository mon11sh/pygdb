"""Pydantic data models for the Central Payment Gateway service.

Defines the request/response schemas and the :class:`PaymentMode` enum used by
the gateway's ``/process`` and ``/validate`` endpoints. Field-level constraints
(positive account ids, positive and upper-bounded amounts, known payment rails)
are enforced by Pydantic so invalid payloads are rejected with a 422 before
reaching the service layer.
"""
from pydantic.dataclasses import dataclass
from pydantic import Field
from decimal import Decimal
from enum import Enum
from typing import Optional


class PaymentMode(str, Enum):
    """Allowed payment rails. Anything else is rejected with a 422.

    Must stay in sync with the transactions service's TransferMode enum — every
    transfer (including CHEQUE) is routed through this gateway, so all modes the
    bank supports must be accepted here or those transfers would fail with a 422.
    """
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    UPI = "UPI"
    CHEQUE = "CHEQUE"


@dataclass
class PaymentRequest:
    """Inbound payload for a payment to be processed by the gateway.

    Represents a money-moving transfer request keyed for idempotency by an
    optional ``reference_id``. All constraints are enforced by Pydantic.

    Attributes:
        source_account_id: ID of the source account; must be positive.
        destination_account_id: ID of the destination account; must be positive.
        amount: Transfer amount as a ``Decimal``; must be > 0 and <= 10,000,000.
        mode: Payment rail as a :class:`PaymentMode` value.
        reference_id: Optional caller-supplied id used for idempotent replays.
    """
    # Account ids must be positive; reject zero/negative with 422.
    source_account_id: int = Field(..., gt=0, description="ID of the source account")
    destination_account_id: int = Field(..., gt=0, description="ID of the destination account")
    # Money as Decimal (never float) with a sane upper bound to block absurd amounts.
    amount: Decimal = Field(..., gt=0, le=10_000_000, description="Amount to transfer")
    # Constrain the rail to a known enum; unknown modes -> 422.
    mode: PaymentMode = Field(..., description="Payment mode (NEFT/RTGS/IMPS/UPI)")
    reference_id: Optional[str] = None

@dataclass
class PaymentResponse:
    """Outcome of a processed payment returned by the gateway.

    Attributes:
        success: Whether the payment was accepted and processed successfully.
        transaction_id: The request's reference id, or a generated UUID.
        message: Human-readable description of the result.
        gateway_ref_id: Gateway-generated reference id for this attempt.
    """
    success: bool
    transaction_id: str
    message: str
    gateway_ref_id: str


@dataclass
class ValidationRequest:
    """Lightweight pre-check the frontend runs before/after a transfer. Uses the
    frontend's field names (from_account/to_account) and is intentionally lenient —
    it never charges or dedupes, it only sanity-checks the transfer."""
    from_account: int = Field(..., gt=0, description="Source account number")
    to_account: int = Field(..., gt=0, description="Destination account number")
    amount: Decimal = Field(..., gt=0, le=10_000_000, description="Amount to transfer")
    transaction_id: Optional[str] = None


@dataclass
class ValidationResponse:
    """Result of the lightweight pre-transfer validation check.

    Attributes:
        valid: Whether the transfer passed the sanity check.
        message: Human-readable explanation of the validation outcome.
        transaction_id: Optional caller-supplied id echoed back for correlation.
    """
    valid: bool
    message: str
    transaction_id: Optional[str] = None
