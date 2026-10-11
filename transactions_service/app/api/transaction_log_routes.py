"""Transaction-log API router for the transactions_service.

Exposes ``/api/v1/transaction-logs`` endpoints for reading transaction history:
a paginated/filterable service-wide log, per-account logs, and per-account
summary statistics. Authorization varies per endpoint and business logic is
delegated to ``TransactionLogService``.
"""

import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import APIRouter, HTTPException, status, Query, Depends
from app.services.transaction_log_service import TransactionLogService
from app.dependencies.providers import get_transaction_log_service
from app.exceptions.transaction_exceptions import TransactionException
from app.models.enums import TransactionType

# Import authorization dependencies
from gdb_common.auth_dependencies import (
    get_current_user,
    require_admin_or_teller_dependency,
    require_admin_or_teller_or_manager,
)
from gdb_common.jwt_validation import JWTValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["transaction-logs"])


@router.get(
    "/transaction-logs",
    status_code=status.HTTP_200_OK,
)
async def get_all_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    sort_by: Optional[str] = Query('id'),
    order: Optional[str] = Query('asc'),
    claims: Dict[str, Any] = Depends(require_admin_or_teller_or_manager()),
    service: TransactionLogService = Depends(get_transaction_log_service)
):
    """Get all transaction logs."""
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"📋 Get all transaction logs by {login_id}")

        result = await service.get_all_transactions(
            skip=skip,
            limit=limit,
            transaction_type=type,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            order=order
        )
        return result

    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})


@router.get(
    "/transaction-logs/{account_number}",
    status_code=status.HTTP_200_OK,
)
async def get_transaction_logs(
    account_number: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    sort_by: Optional[str] = Query('id'),
    order: Optional[str] = Query('asc'),
    claims: Dict[str, Any] = Depends(get_current_user),
    service: TransactionLogService = Depends(get_transaction_log_service)
):
    """Get transaction logs for an account."""
    try:
        user_role = JWTValidator.get_role(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        logger.info(f"📋 Get transaction logs by {login_id} ({user_role}) - Account: {account_number}")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        result = await service.get_transaction_logs(
            account_number=account_number,
            skip=skip,
            limit=limit,
            start_date=start_dt,
            end_date=end_dt,
            transaction_type=type,
            sort_by=sort_by,
            order=order
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "INVALID_DATE_FORMAT", "message": "Use YYYY-MM-DD format"})
    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not retrieve transaction logs")


@router.get(
    "/transaction-logs/summary/{account_number}",
    status_code=status.HTTP_200_OK,
)
async def get_transaction_summary(
    account_number: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    claims: Dict[str, Any] = Depends(get_current_user),
    service: TransactionLogService = Depends(get_transaction_log_service)
):
    """Get transaction summary for an account."""
    try:
        user_role = JWTValidator.get_role(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        logger.info(f"📊 Get summary by {login_id} ({user_role}) for account {account_number}")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        result = await service.get_summary_stats(
            account_number=account_number,
            start_date=start_dt,
            end_date=end_dt,
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "INVALID_DATE_FORMAT", "message": "Use YYYY-MM-DD format"})
    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"})
