"""Withdrawal API router for the transactions_service.

Exposes the ``POST /api/v1/withdrawals`` endpoint that debits funds from an
account after PIN verification. Requires manager-or-teller authorization,
supports idempotent retries via the ``Idempotency-Key`` header, and delegates
business logic to ``WithdrawService``.
"""

import logging
import sys
from decimal import Decimal
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Depends, Header
from app.services.withdraw_service import WithdrawService
from app.dependencies.providers import get_withdraw_service
from app.exceptions.transaction_exceptions import TransactionException

# Import authorization dependencies from Auth Service

try:
    from gdb_common.auth_dependencies import (
        require_manager_or_teller_dependency,
    )
    from gdb_common.jwt_validation import JWTValidator
except ImportError:
    # Fallback path
    auth_service_parent = str(Path(__file__).parent.parent.parent.parent / "auth_service")
    if auth_service_parent not in sys.path:
        sys.path.insert(0, auth_service_parent)
    from app.security.auth_dependencies import (
        require_manager_or_teller_dependency,
    )
    from app.security.jwt_validation import JWTValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["withdrawals"])


@router.post(
    "/withdrawals",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Withdrawal successful"},
        400: {"description": "Invalid input or insufficient funds"},
        401: {"description": "Unauthorized - missing/invalid token or invalid PIN"},
        403: {"description": "Forbidden - insufficient permissions"},
        404: {"description": "Account not found"},
        503: {"description": "Service unavailable"},
    },
)
async def withdraw_funds(
    account_number: int,
    amount: float,
    pin: str,
    description: str = None,
    claims: Dict[str, Any] = Depends(require_manager_or_teller_dependency),
    service: WithdrawService = Depends(get_withdraw_service),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> dict:
    """
    Withdraw funds from an account.
    """
    try:
        # Get user info from JWT
        user_role = JWTValidator.get_role(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        logger.info(f"💸 Withdrawal request by {login_id} ({user_role}) - Account: {account_number}, Amount: ₹{amount}")

        # Call withdraw service
        result = await service.process_withdraw(
            account_number=account_number,
            amount=Decimal(str(amount)),
            pin=pin,
            description=description,
            idempotency_key=idempotency_key,
        )

        logger.info(f"✅ Withdrawal successful by {login_id} for account {account_number}")

        return result

    except TransactionException as e:
        logger.warning(f"⚠️ Withdrawal failed: {e.error_code} - {e.message}")
        raise HTTPException(
            status_code=e.http_code,
            detail={"error_code": e.error_code, "message": e.message},
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error during withdrawal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"},
        )
