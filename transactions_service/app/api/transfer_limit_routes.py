"""Transfer-limit API router for the transactions_service.

Exposes ``/api/v1/transfer-limits`` endpoints for querying an account's daily
and per-transaction limits, checking remaining capacity, validating a proposed
transfer, listing all limit rules, and updating a rule for a privilege tier.
Authorization varies per endpoint and business logic is delegated to
``TransferLimitService``.
"""

import logging
import sys
from decimal import Decimal
from typing import Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from app.services.transfer_limit_service import TransferLimitService
from app.dependencies.providers import get_transfer_limit_service
from app.exceptions.transaction_exceptions import TransactionException

# Import authorization dependencies
from gdb_common.auth_dependencies import (
    get_current_user,
    require_admin_or_teller_dependency,
    require_admin_or_teller_or_manager,
)
from gdb_common.jwt_validation import JWTValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["transfer-limits"])


class TransferLimitRuleUpdate(BaseModel):
    """Request schema for updating a transfer-limit rule.

    Attributes:
        daily_limit: New daily transfer limit; must be greater than zero.
        transaction_limit: New per-transaction limit; must be greater than zero.
    """

    daily_limit: float = Field(..., gt=0)
    transaction_limit: int = Field(..., gt=0)


@router.get(
    "/transfer-limits/{account_number}",
    status_code=status.HTTP_200_OK,
)
async def get_transfer_limit(
    account_number: int,
    claims: Dict[str, Any] = Depends(get_current_user),
    service: TransferLimitService = Depends(get_transfer_limit_service)
) -> dict:
    """Get transfer limits for an account."""
    try:
        user_role = JWTValidator.get_role(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        logger.info(f"Get transfer limits by {login_id} ({user_role}) - Account: {account_number}")

        result = await service.get_transfer_limit(account_number)
        return result

    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})


@router.get(
    "/transfer-limits/remaining/{account_number}",
    status_code=status.HTTP_200_OK,
)
async def get_remaining_limit(
    account_number: int,
    claims: Dict[str, Any] = Depends(get_current_user),
    service: TransferLimitService = Depends(get_transfer_limit_service)
):
    """Get remaining transfer limit."""
    try:
        user_role = JWTValidator.get_role(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        logger.info(f"Quick check remaining limit by {login_id} ({user_role}) - Account: {account_number}")

        result = await service.get_remaining_limit(account_number)
        return result

    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})


@router.get(
    "/transfer-limits/rules/all",
    status_code=status.HTTP_200_OK,
)
async def get_all_transfer_rules(
    claims: Dict[str, Any] = Depends(require_admin_or_teller_or_manager()),
    service: TransferLimitService = Depends(get_transfer_limit_service)
):
    """Get all transfer limit rules."""
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"Get all transfer limit rules by {login_id}")

        result = await service.get_all_transfer_rules()
        return result

    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})


@router.post(
    "/transfer-limits/check",
    status_code=status.HTTP_200_OK,
)
async def check_can_transfer(
    account_number: int,
    amount: float,
    claims: Dict[str, Any] = Depends(get_current_user),
    service: TransferLimitService = Depends(get_transfer_limit_service)
):
    """Check if an account can make a transfer."""
    try:
        user_role = JWTValidator.get_role(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        logger.info(f"Check if can transfer by {login_id} ({user_role}) - Account: {account_number}, Amount: ₹{amount}")

        result = await service.check_can_transfer(
            account_number=account_number,
            proposed_amount=Decimal(str(amount)),
        )
        return result

    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})


@router.put(
    "/transfer-limits/rules/{privilege}",
    status_code=status.HTTP_200_OK,
)
async def update_transfer_rule(
    privilege: str,
    rule: TransferLimitRuleUpdate,
    claims: Dict[str, Any] = Depends(require_admin_or_teller_dependency),
    service: TransferLimitService = Depends(get_transfer_limit_service)
):
    """Update transfer limit rule."""
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"Update transfer rule for {privilege} by {login_id}")
        
        result = await service.update_transfer_rule(
            privilege=privilege.upper(),
            daily_limit=Decimal(str(rule.daily_limit)),
            transaction_limit=rule.transaction_limit
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "INVALID_PARAM", "message": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})
