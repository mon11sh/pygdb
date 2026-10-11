"""
Accounts Service - Account Business Logic Service (Refactored)

High-level business logic for account management using Factory + Interface pattern.
Orchestrates repository and validation layer with polymorphic account creation.

Design Pattern: Factory + Interface
- AccountImpl: Abstract interface for account types
- SavingsImpl, CurrentImpl: Concrete implementations
- AccountFactory: Creates appropriate implementation
- AccountService: Uses factory for polymorphic account creation

Author: GDB Architecture Team
"""

import logging
from typing import Optional, Union

from app.repositories.account_repo import AccountRepository
from app.models.account import (
    SavingsAccountCreate,
    CurrentAccountCreate,
    AccountUpdate,
    AccountDetailsResponse
)
from app.exceptions.account_exceptions import (
    AccountException,
    AccountNotFoundError,
    AccountInactiveError,
    AccountClosedError,
    InsufficientFundsError,
    InvalidPinError,
    AccountAlreadyActiveError,
    AccountAlreadyInactiveError
)
from app.utils.validators import validate_name, validate_privilege
from app.utils.encryption import EncryptionManager
from app.utils.analytics import summarize
from app.utils.pagination import paginate
from app.services.account_factory import AccountFactory

logger = logging.getLogger(__name__)


class AccountService:
    """
    Business logic service for account operations.
    
    Uses Factory pattern for account creation:
    - Delegates type-specific logic to AccountImpl implementations
    - No if/else branching on account type
    - Extensible for new account types
    
    Provides high-level methods for account management.
    Coordinates with repository and validation.
    """
    
    def __init__(self):
        """Initialize service with dependencies.

        The repository is resolved from the active database provider (selected by
        settings.DATABASE_PROVIDER) rather than constructed directly, so the same
        service code runs against sqlite / mysql / postgres / supabase / inmemory.
        """
        from app.database.connection import get_provider
        self.repo = get_provider().account_repository()
        self.encryption = EncryptionManager()
        self.factory = AccountFactory()
    
    async def create_savings_account(
        self,
        account: SavingsAccountCreate
    ) -> int:
        """
        Create a new savings account using polymorphic factory pattern.
        
        Args:
            account: SavingsAccountCreate model
            
        Returns:
            Account number
            
        Raises:
            AgeRestrictionError: If age < 18
            ValidationError: If validation fails
            DuplicateConstraintError: If name+DOB exists
        """
        return await self._open_account('SAVINGS', account)
    
    async def create_current_account(
        self,
        account: CurrentAccountCreate
    ) -> int:
        """
        Create a new current account using polymorphic factory pattern.
        
        Args:
            account: CurrentAccountCreate model
            
        Returns:
            Account number
            
        Raises:
            ValidationError: If validation fails
            DuplicateConstraintError: If registration_no exists
        """
        return await self._open_account('CURRENT', account)
    
    async def _open_account(
        self,
        account_type: str,
        account_data: Union[SavingsAccountCreate, CurrentAccountCreate]
    ) -> int:
        """
        Polymorphic account opening using Factory pattern.
        
        This method demonstrates the power of the Factory + Interface pattern:
        1. Factory creates the appropriate AccountImpl
        2. PIN is hashed once (common logic)
        3. Implementation handles type-specific validation and creation
        4. No if/else branching needed
        
        Args:
            account_type: Type of account ('SAVINGS' or 'CURRENT')
            account_data: Account creation data
            
        Returns:
            Account number
            
        Raises:
            ValidationError: If account type unsupported or validation fails
        """
        logger.info(f"Creating {account_type} account via factory pattern")
        
        # Hash PIN (common for all account types)
        pin_hash = self.encryption.hash_pin(account_data.pin)
        
        # Get appropriate implementation from factory
        account_impl = self.factory.create(account_type)
        
        # Polymorphic call - implementation handles type-specific logic
        account_number = await account_impl.open(account_data, pin_hash)
        
        logger.info(f"✅ {account_type} account created via factory: {account_number}")
        return account_number
    
    async def get_account_details(
        self,
        account_number: int
    ) -> AccountDetailsResponse:
        """
        Get account details.
        
        Args:
            account_number: Account number
            
        Returns:
            AccountDetailsResponse
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        account = await self.repo.get_account(account_number)
        
        if not account:
            raise AccountNotFoundError(account_number)
        
        return account
    
    async def get_all_accounts(
        self,
        account_type: str | None = None
    ) -> list[AccountDetailsResponse]:
        """
        Get all accounts, optionally filtered by account type.
        
        Args:
            account_type: Optional filter for account type (SAVINGS or CURRENT)
        
        Returns:
            List of AccountDetailsResponse
            
        Raises:
            DatabaseError: If database query fails
        """
        logger.info(
            f"Getting all accounts"
            f"{f' (filtered by {account_type})' if account_type else ''}"
        )
        
        accounts = await self.repo.get_all_accounts(account_type=account_type)
        return accounts

    async def get_accounts_summary(self, sample_size: int = 5) -> dict:
        """
        Read-only portfolio summary across all accounts.

        Combines two curriculum concepts in a real code path:
        - functional analytics (map/filter/reduce) via ``app.utils.analytics``
        - generic pagination (``Page[T]``) via ``app.utils.pagination`` for a
          small sample of accounts.

        Returns:
            A dict with totals, a privilege histogram, and a sample page.
        """
        accounts = await self.repo.get_all_accounts()

        try:
            summary = summarize(accounts)
        except (TypeError, ValueError) as exc:
            # Exception chaining (Module 6.3): preserve the original cause so a
            # trainer can see WHAT malformed the data, not just the wrapper.
            logger.error(f"❌ Failed to summarize accounts: {exc}")
            raise AccountException(
                "Failed to compute account summary", "SUMMARY_ERROR"
            ) from exc

        sample = paginate(accounts, skip=0, limit=sample_size)
        fields = ("account_number", "name", "privilege", "balance", "is_active")
        summary["sample"] = {
            "items": [
                {field: getattr(account, field, None) for field in fields}
                for account in sample.items
            ],
            "total": sample.total,
            "skip": sample.skip,
            "limit": sample.limit,
            "has_more": sample.has_more,
        }
        return summary

    async def update_account(
        self,
        account_number: int,
        update_data: AccountUpdate
    ) -> AccountDetailsResponse:
        """
        Update account details.
        
        Args:
            account_number: Account number to update
            update_data: AccountUpdate model with fields to update
            
        Returns:
            Updated AccountDetailsResponse
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            DatabaseError: If database update fails
        """
        logger.info(f"Updating account {account_number}")
        
        # First verify account exists
        account = await self.repo.get_account(account_number)
        
        # Prepare update dict (only non-None fields)
        update_dict = update_data.model_dump(exclude_none=True)
        
        if not update_dict:
            # No fields to update
            return account
        
        # Validate updated fields
        if update_data.name:
            validate_name(update_data.name)
        
        if update_data.privilege:
            validate_privilege(update_data.privilege)
        
        # Update account
        updated_account = await self.repo.update_account(
            account_number,
            update_dict,
            account['account_type']
        )
        
        logger.info(f"✅ Account {account_number} updated successfully")
        return updated_account
    
    async def get_balance(self, account_number: int) -> float:
        """
        Get account balance.
        
        Checks that account is active.
        
        Args:
            account_number: Account number
            
        Returns:
            Account balance
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            AccountInactiveError: If account is not active
        """
        account = await self.repo.get_account(account_number)
        
        if not account:
            raise AccountNotFoundError(account_number)
        
        if not account['is_active']:
            raise AccountInactiveError(account_number)
        
        return account['balance']
    
    async def verify_pin(self, account_number: int, pin: str) -> bool:
        """
        Verify account PIN.
        
        Args:
            account_number: Account number
            pin: PIN to verify
            
        Returns:
            True if PIN is correct
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            InvalidPinError: If PIN is incorrect
        """
        pin_hash = await self.repo.get_pin_hash(account_number)
        
        if not pin_hash:
            raise AccountNotFoundError(account_number)
        
        if not self.encryption.verify_pin(pin, pin_hash):
            raise InvalidPinError("PIN verification failed")
        
        return True
    
    async def debit_account(
        self,
        account_number: int,
        amount: float,
        description: str = "Withdrawal"
    ) -> bool:
        """
        Debit amount from account.
        
        Checks:
        - Account exists and is active
        - Account is not closed
        - Sufficient funds
        
        Args:
            account_number: Account to debit
            amount: Amount (positive value)
            description: Transaction description
            
        Returns:
            True if successful
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            AccountInactiveError: If account is inactive
            AccountClosedError: If account is closed
            InsufficientFundsError: If insufficient balance
        """
        account = await self.repo.get_account(account_number)
        
        if not account:
            raise AccountNotFoundError(account_number)
        
        if not account['is_active']:
            raise AccountInactiveError(account_number)
        
        if account['closed_date'] is not None:
            raise AccountClosedError(account_number)
        
        if account['balance'] < amount:
            raise InsufficientFundsError(account['balance'], amount)
        
        # Perform debit
        success = await self.repo.debit_account(account_number, amount)
        
        if not success:
            raise InsufficientFundsError(account['balance'], amount)
        
        logger.info(f"✅ Debit successful for {account_number}: ₹{amount}")
        return True
    
    async def credit_account(
        self,
        account_number: int,
        amount: float,
        description: str = "Deposit"
    ) -> bool:
        """
        Credit amount to account.
        
        Checks:
        - Account exists and is active
        - Account is not closed
        
        Args:
            account_number: Account to credit
            amount: Amount (positive value)
            description: Transaction description
            
        Returns:
            True if successful
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            AccountInactiveError: If account is inactive
            AccountClosedError: If account is closed
        """
        account = await self.repo.get_account(account_number)
        
        if not account:
            raise AccountNotFoundError(account_number)
        
        if not account['is_active']:
            raise AccountInactiveError(account_number)
        
        if account['closed_date'] is not None:
            raise AccountClosedError(account_number)
        
        # Perform credit
        success = await self.repo.credit_account(account_number, amount)
        
        if not success:
            raise AccountNotFoundError(account_number)
        
        logger.info(f"✅ Credit successful for {account_number}: ₹{amount}")
        return True
    
    async def activate_account(self, account_number: int) -> bool:
        """
        Activate an account.
        
        Args:
            account_number: Account to activate
            
        Returns:
            True if activated
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            AccountAlreadyActiveError: If account is already active
        """
        account = await self.repo.get_account(account_number)
        
        if not account:
            raise AccountNotFoundError(account_number)
        
        if account['is_active']:
            raise AccountAlreadyActiveError(account_number)
        
        success = await self.repo.activate_account(account_number)
        
        if not success:
            raise AccountNotFoundError(account_number)
        
        logger.info(f"✅ Account activated: {account_number}")
        return True
    
    async def inactivate_account(self, account_number: int) -> bool:
        """
        Inactivate an account.
        
        Args:
            account_number: Account to inactivate
            
        Returns:
            True if inactivated
            
        Raises:
            AccountNotFoundError: If account doesn't exist
            AccountAlreadyInactiveError: If account is already inactive
        """
        account = await self.repo.get_account(account_number)
        
        if not account:
            raise AccountNotFoundError(account_number)
        
        if not account['is_active']:
            raise AccountAlreadyInactiveError(account_number)
        
        success = await self.repo.inactivate_account(account_number)
        
        if not success:
            raise AccountNotFoundError(account_number)
        
        logger.info(f"✅ Account inactivated: {account_number}")
        return True
    
    async def close_account(self, account_number: int) -> bool:
        """
        Close an account.
        
        Args:
            account_number: Account to close
            
        Returns:
            True if closed
            
        Raises:
            AccountNotFoundError: If account doesn't exist
        """
        account = await self.repo.get_account(account_number)
        
        if not account:
            raise AccountNotFoundError(account_number)
        
        # Check balance before closing
        if account['balance'] > 0:
            logger.warning(
                f"⚠️ Account {account_number} has remaining balance: "
                f"₹{account['balance']}"
            )
        
        success = await self.repo.close_account(account_number)
        
        if not success:
            raise AccountNotFoundError(account_number)
        
        logger.info(f"✅ Account closed: {account_number}")
        return True
