"""
Accounts Service - Internal Service

Service-to-service operations (called only by other microservices).
Not exposed via public API.

Author: GDB Architecture Team
"""

import logging
from typing import Optional

from app.services.account_service import AccountService
from app.exceptions.account_exceptions import (
    AccountNotFoundError,
    AccountInactiveError,
    InsufficientFundsError,
    InvalidPinError
)
from app.utils.helpers import mask_account_number

logger = logging.getLogger(__name__)


class InternalAccountService:
    """
    Internal service for inter-microservice communication.
    
    Provides API endpoints for other services to call.
    Transactions Service uses this to debit/credit accounts.
    """
    
    def __init__(self):
        """Initialize service."""
        self.account_service = AccountService()
    
    async def get_account_details(self, account_number: int) -> dict:
        """
        Get account details for internal use.
        
        Called by: Transactions Service
        Purpose: Fetch account details before transaction
        
        Args:
            account_number: Account number
            
        Returns:
            dict with account details
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        account = await self.account_service.get_account_details(account_number)
        
        # account is a dict, use dictionary key access
        return {
            "account_number": account['account_number'],
            "account_type": account['account_type'],
            "name": account['name'],
            "balance": account['balance'],
            "privilege": account['privilege'],
            "is_active": account['is_active'],
            "activated_date": account['activated_date'].isoformat() if account['activated_date'] else None,
            "closed_date": account['closed_date'].isoformat() if account['closed_date'] else None
        }
    
    async def debit_for_transfer(
        self,
        account_number: int,
        amount: float
    ) -> dict:
        """
        Debit account for transfer operation.
        
        Called by: Transactions Service (TRANSFER, WITHDRAW)
        
        Args:
            account_number: Account to debit
            amount: Amount to debit
            
        Returns:
            dict with result and new balance
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            AccountInactiveError: If account is inactive
            InsufficientFundsError: If insufficient balance
        """
        try:
            # Perform debit
            success = await self.account_service.debit_account(
                account_number,
                amount,
                description="Fund Transfer Debit"
            )
            
            # Fetch updated balance
            account = await self.account_service.get_account_details(account_number)
            
            return {
                "success": success,
                "account_number": account_number,
                "amount_debited": float(amount),
                "new_balance": float(account['balance']),
                "status": "SUCCESS"
            }
            
        except (AccountNotFoundError, AccountInactiveError, InsufficientFundsError) as e:
            logger.error(f"❌ Debit failed: {e.error_code}")
            return {
                "success": False,
                "account_number": account_number,
                "status": "FAILED",
                "error_code": e.error_code,
                "error_message": e.message
            }
    
    async def credit_for_transfer(
        self,
        account_number: int,
        amount: float
    ) -> dict:
        """
        Credit account for transfer operation.
        
        Called by: Transactions Service (TRANSFER, DEPOSIT)
        
        Args:
            account_number: Account to credit
        Internal credit for fund transfers (No Auth).
        """
        try:
            # Perform credit
            success = await self.account_service.credit_account(
                account_number,
                amount,
                description="Fund Transfer Credit"
            )
            
            # Fetch updated account details for new balance
            account = await self.account_service.get_account_details(account_number)
            
            return {
                "success": success,
                "account_number": account_number,
                "amount_credited": float(amount),
                "new_balance": float(account['balance']),
                "status": "SUCCESS"
            }
            
        except (AccountNotFoundError, AccountInactiveError) as e:
            logger.error(f"❌ Credit failed: {e.error_code}")
            return {
                "success": False,
                "account_number": account_number,
                "status": "FAILED",
                "error_code": e.error_code,
                "error_message": e.message
            }
    
    async def verify_account_pin(
        self,
        account_number: int,
        pin: str
    ) -> dict:
        """
        Verify account PIN.
        
        Called by: Auth/Transactions Service
        Purpose: Validate PIN before transactions
        
        Args:
            account_number: Account number
            pin: PIN to verify
            
        Returns:
            dict with verification result
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            InvalidPinError: If PIN is invalid
        """
        try:
            is_valid = await self.account_service.verify_pin(account_number, pin)
            
            return {
                "account_number": account_number,
                "pin_valid": is_valid,
                "status": "SUCCESS"
            }
            
        except (AccountNotFoundError, InvalidPinError) as e:
            logger.warning(f"⚠️ PIN verification failed: {e.error_code}")
            return {
                "account_number": account_number,
                "pin_valid": False,
                "status": "FAILED",
                "error_code": e.error_code
            }
    
    async def check_account_active(self, account_number: int) -> dict:
        """
        Check if account is active.
        
        Called by: Any service needing to verify account status
        
        Args:
            account_number: Account number
            
        Returns:
            dict with active status
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        try:
            account = await self.account_service.get_account_details(account_number)
            
            return {
                "account_number": account_number,
                "is_active": account['is_active'],
                "status": "SUCCESS"
            }
            
        except AccountNotFoundError as e:
            logger.warning(f"⚠️ Account not found: {account_number}")
            return {
                "account_number": account_number,
                "is_active": False,
                "status": "FAILED",
                "error_code": e.error_code
            }
    
    async def get_privilege(self, account_number: int) -> dict:
        """
        Get account privilege level.
        
        Called by: Transactions Service
        Purpose: Determine transfer limits
        
        Args:
            account_number: Account number
            
        Returns:
            dict with privilege level
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        try:
            account = await self.account_service.get_account_details(account_number)
            
            return {
                "account_number": account_number,
                "privilege": account['privilege'],
                "status": "SUCCESS"
            }
            
        except AccountNotFoundError as e:
            logger.error(f"❌ Account not found: {account_number}")
            return {
                "account_number": account_number,
                "privilege": None,
                "status": "FAILED",
                "error_code": e.error_code
            }
