"""Deposit API router for the transactions_service.

Exposes the ``POST /api/v1/deposits`` endpoint that credits funds to an account.
Requires manager-or-teller authorization, supports idempotent retries via the
``Idempotency-Key`` header, and delegates business logic to ``DepositService``.
"""

import logging
import sys
from decimal import Decimal
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Depends, Header
from app.services.deposit_service import DepositService
from app.dependencies.providers import get_deposit_service
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

router = APIRouter(prefix="/api/v1", tags=["deposits"])


@router.post(
    "/deposits",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Deposit successful"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized - missing or invalid token"},
        403: {"description": "Forbidden - insufficient permissions"},
        404: {"description": "Account not found"},
        503: {"description": "Service unavailable"},
    },
)
async def deposit_funds(
    account_number: int,
    amount: float,
    description: str = None,
    claims: Dict[str, Any] = Depends(require_manager_or_teller_dependency),
    service: DepositService = Depends(get_deposit_service),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> dict:
    """
    Deposit funds to an account.
    """
    try:
        # Get user info from JWT
        user_role = JWTValidator.get_role(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        logger.info(f"💰 Deposit request by {login_id} ({user_role}) - Account: {account_number}, Amount: ₹{amount}")

        # Call deposit service
        result = await service.process_deposit(
            account_number=account_number,
            amount=Decimal(str(amount)),
            description=description,
            idempotency_key=idempotency_key,
        )

        logger.info(f"✅ Deposit successful by {login_id} for account {account_number}")

        return result

    except TransactionException as e:
        logger.warning(f"⚠️ Deposit failed: {e.error_code} - {e.message}")
        raise HTTPException(
            status_code=e.http_code,
            detail={"error_code": e.error_code, "message": e.message},
        )

    except Exception as e:
        logger.error(f"❌ Unexpected error during deposit: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"},
        )
