"""
Accounts Service - Account API Routes

Public REST API endpoints for account management.

Authorization:
- Create Account: ADMIN, TELLER
- Update Account: ADMIN, TELLER
- Close Account: ADMIN only
- Activate/Inactivate: ADMIN only
- View All Accounts: ADMIN, TELLER
- View Own Account: MANAGER (only their own accounts)

Author: GDB Architecture Team
"""

import logging
import sys
from typing import Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status, Query
from datetime import datetime
from pydantic import BaseModel, Field

from app.services.account_service import AccountService
from app.models.account import (
    SavingsAccountCreate,
    CurrentAccountCreate,
    AccountUpdate,
    AccountResponse,
    SavingsAccountResponse,
    CurrentAccountResponse,
    BalanceResponse,
    ErrorResponse
)
from app.exceptions.account_exceptions import AccountException
from app.utils import pin_lockout
from app.utils.pin_lockout import AccountLockedError

# Import authorization dependencies from Auth Service
# Import authorization dependencies
# Assumes sys.path is set up by main.py to include auth_service/app
from gdb_common.auth_dependencies import (
    get_current_user,
    require_admin_or_teller,
    require_admin,
    require_admin_or_teller_or_manager,
)
from gdb_common.jwt_validation import JWTValidator, RoleChecker

from app.dependencies.providers import get_account_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _mask_aadhar(account: Any) -> Any:
    """
    Return a copy of the account dict with `aadhar_number` masked so only the
    last 4 digits are visible (e.g. "********9012"). Non-dict inputs or dicts
    without an aadhar_number are returned unchanged.
    """
    if isinstance(account, dict) and account.get("aadhar_number"):
        masked = dict(account)
        value = str(masked["aadhar_number"])
        masked["aadhar_number"] = "*" * 8 + value[-4:]
        return masked
    return account


# ========================================
# ACCOUNT CREATION ENDPOINTS
# ========================================

@router.post(
    "/accounts/savings",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Accounts - Creation"],
    summary="Create Savings Account",
    description="Create a new savings account for individuals (age >= 18)"
)
async def create_savings_account(
    request: SavingsAccountCreate,
    claims: Dict[str, Any] = Depends(require_admin_or_teller()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Create a new savings account.

    **Authorization:** ADMIN or TELLER role required
    
    **Request Body:**
    - `name`: Account holder name (1-255 characters)
    - `account_type`: Fixed as SAVINGS
    - `pin`: 4-6 digit PIN
    - `date_of_birth`: DOB in YYYY-MM-DD format
    - `gender`: M, F, or OTHER
    - `phone_no`: 10-digit phone number
    - `privilege`: PREMIUM, GOLD, or SILVER (default: SILVER)
    
    **Validations:**
    - Age must be >= 18
    - PIN must be 4-6 digits (no sequential/same digits)
    - Unique name + DOB combination
    - Only ADMIN or TELLER can create accounts
    
    **Response:**
    - `account_number`: Auto-generated unique account number (starts from 1000)
    - `balance`: Initial balance (₹0)
    - `is_active`: TRUE by default
    - `activated_date`: Account creation timestamp
    
    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN or TELLER required)
    - `ACCOUNT_ALREADY_EXISTS`: name + DOB already exists
    - `AGE_RESTRICTION`: Age < 18
    - `INVALID_PIN`: Invalid PIN format
    - `VALIDATION_ERROR`: Input validation failed
    """
    try:
        account_number = await account_service.create_savings_account(request)
        
        logger.info(f"Savings account created by {claims.get('login_id')}: {account_number}")
        
        return AccountResponse(
            account_number=account_number,
            account_type="SAVINGS",
            name=request.name,
            privilege=request.privilege,
            balance=request.initial_balance,
            is_active=True,
            activated_date=datetime.utcnow(),
            closed_date=None,
            bank_name=request.bank_name,
            bank_branch=request.bank_branch,
            ifsc_code=request.ifsc_code
        )
        
    except AccountException as e:
        logger.error(f"❌ Account creation failed: {e.error_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


@router.post(
    "/accounts/current",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Accounts - Creation"],
    summary="Create Current Account",
    description="Create a new current account for businesses/companies"
)
async def create_current_account(
    request: CurrentAccountCreate,
    claims: Dict[str, Any] = Depends(require_admin_or_teller()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Create a new current account.

    **Authorization:** ADMIN or TELLER role required
    
    **Request Body:**
    - `name`: Account holder/company name (1-255 characters)
    - `account_type`: Fixed as CURRENT
    - `pin`: 4-6 digit PIN
    - `company_name`: Company name (1-255 characters)
    - `website`: Company website (optional)
    - `registration_no`: Company registration number (unique, 1-50 chars)
    - `privilege`: PREMIUM, GOLD, or SILVER (default: SILVER)
    
    **Validations:**
    - PIN must be 4-6 digits (no sequential/same digits)
    - Unique registration_no
    - Only ADMIN or TELLER can create accounts
    
    **Response:**
    - `account_number`: Auto-generated unique account number (starts from 1000)
    - `balance`: Initial balance (₹0)
    - `is_active`: TRUE by default
    - `activated_date`: Account creation timestamp
    
    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN or TELLER required)
    - `ACCOUNT_ALREADY_EXISTS`: registration_no already exists
    - `INVALID_PIN`: Invalid PIN format
    - `VALIDATION_ERROR`: Input validation failed
    """
    try:
        account_number = await account_service.create_current_account(request)
        
        logger.info(f"Current account created by {claims.get('login_id')}: {account_number}")
        
        return AccountResponse(
            account_number=account_number,
            account_type="CURRENT",
            name=request.name,
            privilege=request.privilege,
            balance=0.00,
            is_active=True,
            activated_date=datetime.utcnow(),
            closed_date=None,
            bank_name=request.bank_name,
            bank_branch=request.bank_branch,
            ifsc_code=request.ifsc_code
        )
        
    except AccountException as e:
        logger.error(f"❌ Account creation failed: {e.error_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": e.error_code,
                "message": e.message
            }
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


# ========================================
# ACCOUNT QUERY ENDPOINTS
# ========================================

@router.get(
    "/accounts",
    response_model=list[AccountResponse],
    tags=["Accounts - Query"],
    summary="Get All Accounts",
    description="Retrieve all accounts (ADMIN/TELLER only), optionally filtered by account type"
)
async def get_all_accounts(
    account_type: str | None = None,
    skip: int = Query(0, ge=0, description="Number of accounts to skip (pagination)"),
    limit: int | None = Query(None, ge=1, le=200, description="Max accounts to return; omit for all"),
    claims: Dict[str, Any] = Depends(require_admin_or_teller_or_manager()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Get all accounts, optionally filtered by account type.
    
    **Authorization:** ADMIN, TELLER, or MANAGER role required
    
    **Query Parameters:**
    - `account_type` (optional): Filter by account type (SAVINGS or CURRENT)
    
    **Response:**
    - List of all accounts (or filtered accounts) with details
    
    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN or TELLER required)
    - 400: Invalid account_type value
    - `DATABASE_ERROR`: Database query failed
    """
    try:
        # Validate account_type if provided
        if account_type and account_type not in ["SAVINGS", "CURRENT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_ACCOUNT_TYPE",
                    "message": "account_type must be either 'SAVINGS' or 'CURRENT'"
                }
            )
        
        login_id = JWTValidator.get_login_id(claims)

        # Get all accounts from database (with optional filter)
        accounts = await account_service.get_all_accounts(account_type=account_type)

        # Optional pagination (M-9): backward-compatible — omitting limit returns all.
        accounts = accounts[skip: skip + limit] if limit is not None else accounts[skip:]

        filter_msg = f" (filtered by {account_type})" if account_type else ""
        logger.info(f"All accounts retrieved by {login_id}: {len(accounts)} accounts{filter_msg}")
        
        return [
            AccountResponse(
                account_number=account.account_number,
                account_type=account.account_type,
                name=account.name,
                privilege=account.privilege,
                balance=account.balance,
                is_active=account.is_active,
                activated_date=account.activated_date,
                closed_date=account.closed_date,
                bank_name=account.bank_name,
                bank_branch=account.bank_branch,
                ifsc_code=account.ifsc_code
            )
            for account in accounts
        ]
        
    except AccountException as e:
        logger.error(f"❌ Get all accounts failed: {e.error_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )



@router.get(
    "/accounts/summary",
    tags=["Accounts - Query"],
    summary="Account Portfolio Summary",
    description="Aggregate summary across all accounts (totals, privilege breakdown, sample page)"
)
async def get_accounts_summary(
    claims: Dict[str, Any] = Depends(require_admin_or_teller_or_manager()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Read-only portfolio summary across all accounts.

    **Authorization:** ADMIN, TELLER, or MANAGER role required

    **Response:**
    - `total_accounts`, `active_accounts`, `total_balance`
    - `by_privilege`: count of accounts per privilege tier
    - `sample`: a generic paginated preview (first few accounts)

    NOTE: declared BEFORE `/accounts/{account_number}` so the literal path
    "summary" is not parsed as an account number.
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        summary = await account_service.get_accounts_summary()
        logger.info(f"Accounts summary retrieved by {login_id}")
        return summary

    except AccountException as e:
        logger.error(f"❌ Accounts summary failed: {e.error_code}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


@router.get(
    "/accounts/{account_number}",
    tags=["Accounts - Query"],
    summary="Get Account Details",
    description="Retrieve account details with type-specific information"
)
async def get_account(
    account_number: int,
    claims: Dict[str, Any] = Depends(require_admin_or_teller_or_manager()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Get account details by account number.

    **Authorization:** any staff role (ADMIN/TELLER/MANAGER) may view accounts.
    (Accounts are not linked to platform users in this model; all authenticated
    users are staff, so there is no per-owner restriction.)

    **Path Parameters:**
    - `account_number`: Account number

    **Response:**
    - Full account details with balance, status, and type-specific info.
      The Aadhaar number is masked (only the last 4 digits are shown).

    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Caller lacks a staff role (ADMIN/TELLER/MANAGER)
    - `ACCOUNT_NOT_FOUND`: Account doesn't exist
    - `DATABASE_ERROR`: Database query failed
    """
    try:
        # Get user info from JWT
        user_role = JWTValidator.get_role(claims)
        user_id = JWTValidator.get_user_id(claims)
        login_id = JWTValidator.get_login_id(claims)

        # Get account details (now returns dict with all details)
        account = await account_service.get_account_details(account_number)

        # Mask the full 12-digit Aadhaar before returning: expose only the
        # last 4 digits so raw government-ID PII never leaves the service.
        account = _mask_aadhar(account)

        logger.info(f"Account details retrieved by {login_id} ({user_role}): {account_number}")

        # Return the full account dict directly
        return account
        
    except AccountException as e:
        logger.error(f"❌ Get account failed: {e.error_code}")
        status_code = status.HTTP_404_NOT_FOUND if "NOT_FOUND" in e.error_code else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


@router.get(
    "/accounts/{account_number}/balance",
    response_model=BalanceResponse,
    tags=["Accounts - Query"],
    summary="Get Account Balance",
    description="Retrieve current account balance"
)
async def get_balance(
    account_number: int,
    claims: Dict[str, Any] = Depends(require_admin_or_teller_or_manager()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Get account balance.

    **Authorization:** any staff role (ADMIN/TELLER/MANAGER) may view balances.
    (Accounts are not linked to platform users in this model; all authenticated
    users are staff, so there is no per-owner restriction.)

    **Path Parameters:**
    - `account_number`: Account number

    **Response:**
    - `account_number`: Account number
    - `balance`: Current balance in INR
    - `currency`: Fixed as INR

    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Caller lacks a staff role (ADMIN/TELLER/MANAGER)
    - `ACCOUNT_NOT_FOUND`: Account doesn't exist
    - `ACCOUNT_INACTIVE`: Account is inactive
    - `DATABASE_ERROR`: Database query failed
    """
    try:
        # Get user info from JWT
        user_role = JWTValidator.get_role(claims)
        user_id = JWTValidator.get_user_id(claims)
        login_id = JWTValidator.get_login_id(claims)
        
        # Get account details
        account = await account_service.get_account_details(account_number)
        
        # Note: Authorization is enforced at the transaction service level
        # Accounts service allows viewing any account's balance
        
        balance = await account_service.get_balance(account_number)
        
        logger.info(f"Account balance retrieved by {login_id} ({user_role}): {account_number}")
        
        return BalanceResponse(
            account_number=account_number,
            balance=balance,
            currency="INR"
        )
        
    except AccountException as e:
        logger.error(f"❌ Get balance failed: {e.error_code}")
        status_code = status.HTTP_404_NOT_FOUND if "NOT_FOUND" in e.error_code else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


# NOTE: A `GET /accounts/user/{user_id}` handler previously lived here. The
# accounts schema has no `user_id` column (accounts are not linked to platform
# users in this training model), so its query always failed with a 500. It was
# not called by the frontend. Removed. To reintroduce per-user account listing,
# first add a `user_id` column + FK to the `accounts` table and seed data.


# ========================================
# ACCOUNT MANAGEMENT ENDPOINTS
# ========================================

@router.put(
    "/accounts/{account_number}",
    response_model=dict,
    tags=["Accounts - Management"],
    summary="Update Account",
    description="Update account details (name, privilege)"
)
async def update_account(
    account_number: int,
    request: AccountUpdate,
    claims: Dict[str, Any] = Depends(require_admin_or_teller()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Update account details.
    
    **Authorization:** ADMIN or TELLER role required
    
    **Path Parameters:**
    - `account_number`: Account to update
    
    **Request Body:**
    - `name`: New account name (optional)
    - `privilege`: New privilege level (optional)
    
    **Response:**
    - `success`: true if updated
    - `message`: Status message
    
    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN or TELLER required)
    - `ACCOUNT_NOT_FOUND`: Account doesn't exist
    - `VALIDATION_ERROR`: Invalid input data
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        
        updated_account = await account_service.update_account(account_number, request)
        
        logger.info(f"Account {account_number} updated by {login_id}")
        
        return {
            "success": True,
            "message": "Account updated successfully",
            "account_number": account_number
        }
        
    except AccountException as e:
        logger.error(f"❌ Update account failed: {e.error_code}")
        status_code = status.HTTP_404_NOT_FOUND if "NOT_FOUND" in e.error_code else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


@router.post(
    "/accounts/{account_number}/activate",
    response_model=dict,
    tags=["Accounts - Management"],
    summary="Activate Account",
    description="Activate an inactive account"
)
async def activate_account(
    account_number: int,
    claims: Dict[str, Any] = Depends(require_admin()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Activate an account.
    
    **Authorization:** ADMIN role required
    
    **Path Parameters:**
    - `account_number`: Account to activate
    
    **Response:**
    - `success`: true if activated
    - `message`: Status message
    
    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN required)
    - `ACCOUNT_NOT_FOUND`: Account doesn't exist
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        
        success = await account_service.activate_account(account_number)
        
        logger.info(f"Account activated by {login_id}: {account_number}")
        
        return {
            "success": success,
            "message": "Account activated successfully",
            "account_number": account_number
        }
        
    except AccountException as e:
        logger.error(f"❌ Activate account failed: {e.error_code}")
        # Map error codes to appropriate HTTP status codes
        status_code = status.HTTP_400_BAD_REQUEST
        if "NOT_FOUND" in e.error_code:
            status_code = status.HTTP_404_NOT_FOUND
        elif "ALREADY_ACTIVE" in e.error_code:
            status_code = status.HTTP_409_CONFLICT
        
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


@router.post(
    "/accounts/{account_number}/inactivate",
    response_model=dict,
    tags=["Accounts - Management"],
    summary="Inactivate Account",
    description="Inactivate an active account"
)
async def inactivate_account(
    account_number: int,
    claims: Dict[str, Any] = Depends(require_admin()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Inactivate an account.
    
    **Authorization:** ADMIN role required
    
    **Path Parameters:**
    - `account_number`: Account to inactivate
    
    **Response:**
    - `success`: true if inactivated
    - `message`: Status message
    
    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN required)
    - `ACCOUNT_NOT_FOUND`: Account doesn't exist
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        
        success = await account_service.inactivate_account(account_number)
        
        logger.info(f"Account inactivated by {login_id}: {account_number}")
        
        return {
            "success": success,
            "message": "Account inactivated successfully",
            "account_number": account_number
        }
        
    except AccountException as e:
        logger.error(f"❌ Inactivate account failed: {e.error_code}")
        # Map error codes to appropriate HTTP status codes
        status_code = status.HTTP_400_BAD_REQUEST
        if "NOT_FOUND" in e.error_code:
            status_code = status.HTTP_404_NOT_FOUND
        elif "ALREADY_INACTIVE" in e.error_code:
            status_code = status.HTTP_409_CONFLICT
        
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


@router.post(
    "/accounts/{account_number}/close",
    response_model=dict,
    tags=["Accounts - Management"],
    summary="Close Account",
    description="Close (soft delete) an account"
)
async def close_account(
    account_number: int,
    claims: Dict[str, Any] = Depends(require_admin()),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Close an account.
    
    **Authorization:** ADMIN role required
    
    **Path Parameters:**
    - `account_number`: Account to close
    
    **Response:**
    - `success`: true if closed
    - `message`: Status message
    
    **Possible Errors:**
    - 401: Missing or invalid authorization token
    - 403: Insufficient permissions (ADMIN required)
    - `ACCOUNT_NOT_FOUND`: Account doesn't exist
    
    **Note:**
    - Account can be closed even with remaining balance
    - Closed accounts cannot perform transactions
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        
        success = await account_service.close_account(account_number)
        
        logger.info(f"Account closed by {login_id}: {account_number}")
        
        return {
            "success": success,
            "message": "Account closed successfully",
            "account_number": account_number
        }
        
    except AccountException as e:
        logger.error(f"❌ Close account failed: {e.error_code}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "NOT_FOUND" in e.error_code else status.HTTP_400_BAD_REQUEST,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


# ============================================
# PIN VERIFICATION ENDPOINT (Frontend requires this)
# ============================================

class PinVerifyRequest(BaseModel):
    """PIN verification request."""
    pin: str = Field(..., min_length=4, max_length=6, description="4-6 digit PIN")


@router.post(
    "/accounts/{account_number}/verify-pin",
    status_code=status.HTTP_200_OK,
    tags=["Accounts - Verification"],
    summary="Verify Account PIN",
    description="Verify if the provided PIN matches the account PIN"
)
async def verify_pin(
    account_number: int,
    request: PinVerifyRequest,
    claims: Dict[str, Any] = Depends(get_current_user),
    account_service: AccountService = Depends(get_account_service)
):
    """
    Verify account PIN.
    
    Frontend calls: POST /api/v1/accounts/{account_number}/verify-pin
    Body: { pin: "1234" }
    
    **Authorization:** Any authenticated user

    **Returns:**
    - valid: true if PIN matches
    - message: Verification result message

    **Brute-force protection:** after 5 consecutive wrong PINs the account is
    locked for 15 minutes and this endpoint returns 423 Locked.
    """
    try:
        login_id = JWTValidator.get_login_id(claims)
        logger.info(f"🔐 PIN verification for account {account_number} by {login_id}")

        # Brute-force lockout: reject before verifying if currently locked.
        try:
            pin_lockout.check_locked(account_number)
        except AccountLockedError as lock_err:
            logger.warning(f"🔒 PIN verify blocked (locked) for account {account_number}")
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail={"error_code": "ACCOUNT_LOCKED", "message": str(lock_err)},
                headers={"Retry-After": str(lock_err.retry_after_seconds)},
            )

        # Verify PIN using the account service
        is_valid = await account_service.verify_pin(account_number, request.pin)

        if is_valid:
            pin_lockout.record_success(account_number)
            return {"valid": True, "message": "PIN verified successfully"}
        else:
            pin_lockout.record_failure(account_number)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "INVALID_PIN", "message": "Invalid PIN"}
            )

    except AccountException as e:
        logger.error(f"❌ PIN verification failed: {e.error_code}")
        # A wrong PIN surfaces as InvalidPinError -> count it toward lockout.
        # An unknown account (NOT_FOUND) is not a brute-force signal.
        if "NOT_FOUND" not in e.error_code:
            pin_lockout.record_failure(account_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "NOT_FOUND" in e.error_code else status.HTTP_401_UNAUTHORIZED,
            detail={"error_code": e.error_code, "message": e.message}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in PIN verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "INTERNAL_ERROR", "message": "Internal server error"}
        )


# NOTE: A second `PUT /accounts/{account_number}` handler previously lived here.
# It was unreachable (the handler defined earlier in this file wins route
# matching) and additionally used attribute access on a dict return value, which
# would have raised on execution. Removed to avoid confusion and a latent 500.
