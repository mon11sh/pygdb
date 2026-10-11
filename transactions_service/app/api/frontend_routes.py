"""
Frontend-Compatible Transaction Routes

These routes match the frontend API expectations:
- POST /api/v1/transactions/deposit
- POST /api/v1/transactions/withdraw
- POST /api/v1/transactions/transfer
- GET /api/v1/transactions
- GET /api/v1/transactions/account/{account_number}

These wrap the existing service endpoints to provide frontend compatibility.

Author: GDB Architecture Team
"""

import logging
import sys
from decimal import Decimal
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends, Query, Header
from pydantic import BaseModel, Field

from app.services.deposit_service import DepositService
from app.services.withdraw_service import WithdrawService
from app.services.transfer_service import TransferService
from app.services.transaction_log_service import TransactionLogService
from app.dependencies.providers import (
    get_deposit_service,
    get_withdraw_service,
    get_fund_transfer_service,
    get_transaction_log_service,
)
from app.exceptions.transaction_exceptions import TransactionException
from app.models.enums import TransferMode

# Import authorization dependencies from Auth Service

try:
    from gdb_common.auth_dependencies import (
        require_manager_or_teller_dependency,
        require_admin_or_teller_or_manager,
        get_current_user,
    )
    from gdb_common.jwt_validation import JWTValidator
except ImportError:
    auth_service_parent = str(Path(__file__).parent.parent.parent.parent / "auth_service")
    if auth_service_parent not in sys.path:
        sys.path.insert(0, auth_service_parent)
    from app.security.auth_dependencies import (
        require_manager_or_teller_dependency,
        require_admin_or_teller_or_manager,
        get_current_user,
    )
    from app.security.jwt_validation import JWTValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions-frontend"])


# ============================================
# Request Models (matching frontend)
# ============================================

class DepositRequest(BaseModel):
    """Deposit request from frontend."""
    account_number: int = Field(..., description="Account number to deposit to")
    amount: float = Field(..., gt=0, description="Amount to deposit")
    pin: Optional[str] = Field(None, description="PIN (not required for deposits)")


class WithdrawRequest(BaseModel):
    """Withdraw request from frontend."""
    account_number: int = Field(..., description="Account number to withdraw from")
    amount: float = Field(..., gt=0, description="Amount to withdraw")
    pin: str = Field(..., description="Account PIN for verification")


class TransferRequest(BaseModel):
    """Transfer request from frontend."""
    from_account: int = Field(..., description="Source account number")
    to_account: int = Field(..., description="Destination account number")
    amount: float = Field(..., gt=0, description="Amount to transfer")
    pin: str = Field(..., description="Source account PIN for verification")
    transfer_mode: Optional[str] = Field("NEFT", description="Transfer mode: NEFT, RTGS, IMPS, UPI")


# ============================================
# Deposit Endpoint
# ============================================

@router.post(
    "/deposit",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Deposit successful"},
        400: {"description": "Invalid input"},
        401: {"description": "Unauthorized"},
        404: {"description": "Account not found"},
    },
)
async def deposit(
    request: DepositRequest,
    claims: Dict[str, Any] = Depends(require_manager_or_teller_dependency),
    service: DepositService = Depends(get_deposit_service),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> dict:
    """
    Deposit funds to an account.

    Frontend calls: POST /api/v1/transactions/deposit
    Body: { account_number, amount, pin }
    Optional header: Idempotency-Key (retries with the same key are de-duplicated)
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"💰 Deposit by {login_id} - Account: {request.account_number}, Amount: ₹{request.amount}")

        result = await service.process_deposit(
            account_number=request.account_number,
            amount=Decimal(str(request.amount)),
            description=f"Deposit by {login_id}",
            idempotency_key=idempotency_key,
        )

        return result

    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Deposit error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": str(e)})


# ============================================
# Withdraw Endpoint
# ============================================

@router.post(
    "/withdraw",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Withdrawal successful"},
        400: {"description": "Invalid input or insufficient funds"},
        401: {"description": "Unauthorized or invalid PIN"},
        404: {"description": "Account not found"},
    },
)
async def withdraw(
    request: WithdrawRequest,
    claims: Dict[str, Any] = Depends(require_manager_or_teller_dependency),
    service: WithdrawService = Depends(get_withdraw_service),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> dict:
    """
    Withdraw funds from an account.

    Frontend calls: POST /api/v1/transactions/withdraw
    Body: { account_number, amount, pin }
    Optional header: Idempotency-Key (retries with the same key are de-duplicated)
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"💸 Withdrawal by {login_id} - Account: {request.account_number}, Amount: ₹{request.amount}")

        result = await service.process_withdraw(
            account_number=request.account_number,
            amount=Decimal(str(request.amount)),
            pin=request.pin,
            description=f"Withdrawal by {login_id}",
            idempotency_key=idempotency_key,
        )

        return result

    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Withdrawal error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": str(e)})


# ============================================
# Transfer Endpoint
# ============================================

@router.post(
    "/transfer",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Transfer successful"},
        400: {"description": "Invalid input or limit exceeded"},
        401: {"description": "Unauthorized or invalid PIN"},
        404: {"description": "Account not found"},
    },
)
async def transfer(
    request: TransferRequest,
    claims: Dict[str, Any] = Depends(require_manager_or_teller_dependency),
    service: TransferService = Depends(get_fund_transfer_service),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> dict:
    """
    Transfer funds between two accounts.
    
    Frontend calls: POST /api/v1/transactions/transfer
    Body: { from_account, to_account, amount, pin }
    
    Flow:
    1. Validate source account & PIN
    2. Validate destination account
    3. Call Central Payment Gateway for 2nd validation
    4. Execute transfer
    5. Send notifications
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(
            f"💳 Transfer by {login_id} - From: {request.from_account}, "
            f"To: {request.to_account}, Amount: ₹{request.amount}"
        )

        # Determine transfer mode
        transfer_mode = TransferMode.NEFT
        if request.transfer_mode:
            try:
                transfer_mode = TransferMode[request.transfer_mode.upper()]
            except KeyError:
                transfer_mode = TransferMode.NEFT

        result = await service.process_transfer(
            from_account=request.from_account,
            to_account=request.to_account,
            amount=Decimal(str(request.amount)),
            pin=request.pin,
            transfer_mode=transfer_mode,
            description=f"Transfer by {login_id}",
            idempotency_key=idempotency_key,
        )

        return result

    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Transfer error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": str(e)})


# ============================================
# Get All Transactions
# ============================================

@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
async def get_all_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    claims: Dict[str, Any] = Depends(require_admin_or_teller_or_manager()),
    service: TransactionLogService = Depends(get_transaction_log_service)
) -> dict:
    """
    Get all transaction logs.
    
    Frontend calls: GET /api/v1/transactions
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"📋 Get all transactions by {login_id}")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        result = await service.get_all_transactions(
            skip=skip,
            limit=limit,
            transaction_type=type,
            start_date=start_dt,
            end_date=end_dt,
        )
        return result

    except ValueError:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_DATE", "message": "Use YYYY-MM-DD format"})
    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": str(e)})


# ============================================
# Get Transactions by Account
# ============================================

@router.get(
    "/account/{account_number}",
    status_code=status.HTTP_200_OK,
)
async def get_transactions_by_account(
    account_number: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    claims: Dict[str, Any] = Depends(get_current_user),
    service: TransactionLogService = Depends(get_transaction_log_service)
) -> dict:
    """
    Get transaction logs for a specific account.
    
    Frontend calls: GET /api/v1/transactions/account/{account_number}
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"📋 Get transactions for account {account_number} by {login_id}")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        result = await service.get_transaction_logs(
            account_number=account_number,
            skip=skip,
            limit=limit,
            start_date=start_dt,
            end_date=end_dt,
            transaction_type=type,
        )
        return result

    except ValueError:
        raise HTTPException(status_code=400, detail={"error_code": "INVALID_DATE", "message": "Use YYYY-MM-DD format"})
    except TransactionException as e:
        raise HTTPException(status_code=e.http_code, detail={"error_code": e.error_code, "message": e.message})
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR", "message": str(e)})
