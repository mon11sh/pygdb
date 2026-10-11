"""
Account Repository — provider-agnostic data-access CONTRACT.

This is the interface every database provider implements. It contains no SQL and
no database driver, so services and dependency-injection depend only on this
abstraction and never on a concrete database.

Concrete implementations (selected by the database provider factory based on
DATABASE_PROVIDER) live in:
  - sqlalchemy_repositories.SqlAlchemyAccountRepository  → sqlite / mysql / postgres / supabase
  - inmemory_repositories.InMemoryAccountRepository       → inmemory

The public method signatures and dict return shapes below are the exact contract
the existing services / internal API already rely on, so no service or route code
changes. Money is handled as Decimal internally by every implementation, while
get_account()/get_all_accounts() continue to expose `balance` as a float — the
historical dict shape.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from app.models.account import (
    AccountDetailsResponse,
    SavingsAccountCreate,
    CurrentAccountCreate,
)


class AccountRepository(ABC):
    """Abstract, database-agnostic repository for accounts."""

    @abstractmethod
    async def create_savings_account(
        self, account: SavingsAccountCreate, pin_hash: str
    ) -> int:
        """Create a savings account (+ its savings details). Returns the newly
        generated account number (>= 1000).

        Raises DuplicateConstraintError('aadhar_number') if the Aadhar already
        exists, DatabaseError on other failures."""

    @abstractmethod
    async def create_current_account(
        self, account: CurrentAccountCreate, pin_hash: str
    ) -> int:
        """Create a current account (+ its current details). Returns the newly
        generated account number (>= 1000).

        Raises DuplicateConstraintError('registration_no') if the registration
        number already exists, DatabaseError on other failures."""

    @abstractmethod
    async def get_account(self, account_number: int) -> Optional[dict]:
        """Return the full account dict (base fields + type-specific fields) with
        `balance` as float, or None if the account does not exist."""

    @abstractmethod
    async def get_all_accounts(
        self, account_type: Optional[str] = None
    ) -> List[AccountDetailsResponse]:
        """Return all accounts (optionally filtered by type) as
        AccountDetailsResponse objects, newest account_number first."""

    @abstractmethod
    async def update_account(
        self, account_number: int, update_data: dict, account_type: str
    ) -> Optional[dict]:
        """Apply the given common/type-specific field updates and return the
        refreshed account dict (same shape as get_account)."""

    @abstractmethod
    async def get_account_balance(self, account_number: int) -> Optional[float]:
        """Return the account balance as float, or None if not found."""

    @abstractmethod
    async def debit_account(self, account_number: int, amount) -> bool:
        """Atomically debit `amount` iff the account is active AND has balance
        >= amount. Returns True on success, False otherwise."""

    @abstractmethod
    async def credit_account(self, account_number: int, amount) -> bool:
        """Atomically credit `amount` iff the account is active. Returns True on
        success, False otherwise."""

    @abstractmethod
    async def activate_account(self, account_number: int) -> bool:
        """Set is_active=True. Returns True if the account exists, else False."""

    @abstractmethod
    async def inactivate_account(self, account_number: int) -> bool:
        """Set is_active=False. Returns True if the account exists, else False."""

    @abstractmethod
    async def close_account(self, account_number: int) -> bool:
        """Soft-close: is_active=False + closed_date=now. Returns True if the
        account exists, else False."""

    @abstractmethod
    async def get_pin_hash(self, account_number: int) -> Optional[str]:
        """Return the stored PIN hash, or None if the account does not exist."""

    @abstractmethod
    async def check_aadhar_has_active_account(self, aadhar_number: str) -> bool:
        """True if the Aadhar already has an active, not-closed savings account."""
