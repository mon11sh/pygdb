"""
In-memory repository implementation (DATABASE_PROVIDER=inmemory).

Pure Python dicts — no SQL engine, no external driver. Data lives only for the
process lifetime. Implements the same AccountRepository contract as the SQL
implementation, so services never know the difference. Money is stored and
compared as Decimal; get_account exposes `balance` as float (historical shape).
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from .account_repo import AccountRepository
from app.exceptions.account_exceptions import DuplicateConstraintError
from app.models.account import AccountDetailsResponse

logger = logging.getLogger(__name__)

ACCOUNT_NUMBER_START = 1000


def _to_decimal(amount) -> Decimal:
    """Coerce an incoming amount (float / str / Decimal / int) to Decimal.

    Args:
        amount: Numeric-like value to normalise. Already-Decimal values are
            returned unchanged; everything else is stringified first to avoid
            binary float imprecision.

    Returns:
        The value as a Decimal.
    """
    if isinstance(amount, Decimal):
        return amount
    return Decimal(str(amount))


class InMemoryStore:
    """Process-lifetime store shared by the in-memory repository."""

    def __init__(self):
        """Initialise the three empty in-memory tables backing the store."""
        # account_number -> account row dict
        self.accounts: dict = {}
        # account_number -> savings details dict
        self.savings: dict = {}
        # account_number -> current details dict
        self.current: dict = {}

    def next_account_number(self) -> int:
        """Return the next account number to assign.

        Returns:
            ACCOUNT_NUMBER_START when the store is empty, otherwise one past the
            current highest account number (floored at ACCOUNT_NUMBER_START).
        """
        if not self.accounts:
            return ACCOUNT_NUMBER_START
        return max(max(self.accounts.keys()) + 1, ACCOUNT_NUMBER_START)

    def clear(self):
        """Empty all three tables, resetting the store to its initial state."""
        self.accounts.clear()
        self.savings.clear()
        self.current.clear()


class InMemoryAccountRepository(AccountRepository):
    """In-memory AccountRepository backed by an InMemoryStore.

    Implements the full AccountRepository contract using plain dict tables held
    in the injected InMemoryStore, so services behave identically to the SQL
    implementation without any database. Money is stored/compared as Decimal.
    """

    def __init__(self, store: InMemoryStore):
        """Bind this repository to the shared in-memory store.

        Args:
            store: The InMemoryStore whose dict tables hold the account data.
        """
        self._store = store

    def _account_dict(self, account_number: int) -> Optional[dict]:
        """Assemble the full public account dict for the given account number.

        Merges the base account row with its type-specific details (savings or
        current) and exposes `balance` as a float to match the historical shape.

        Args:
            account_number: Account number to look up.

        Returns:
            The combined account dict, or None if the account does not exist.
        """
        acc = self._store.accounts.get(account_number)
        if acc is None:
            return None
        result = {
            "account_number": acc["account_number"],
            "account_type": acc["account_type"],
            "name": acc["name"],
            "balance": float(acc["balance"]) if acc["balance"] is not None else 0.0,
            "privilege": acc["privilege"],
            "is_active": acc["is_active"],
            "activated_date": acc["activated_date"],
            "closed_date": acc["closed_date"],
            "bank_name": acc["bank_name"],
            "bank_branch": acc["bank_branch"],
            "ifsc_code": acc["ifsc_code"],
        }
        if acc["account_type"] == "SAVINGS":
            s = self._store.savings.get(account_number)
            if s:
                result["date_of_birth"] = str(s["date_of_birth"]) if s["date_of_birth"] else None
                result["gender"] = s["gender"]
                result["phone_no"] = s["phone_no"]
                result["aadhar_number"] = s["aadhar_number"]
        elif acc["account_type"] == "CURRENT":
            c = self._store.current.get(account_number)
            if c:
                result["company_name"] = c["company_name"]
                result["registration_no"] = c["registration_no"]
                result["website"] = c["website"]
        return result

    async def create_savings_account(self, account, pin_hash: str) -> int:
        """Create a savings account plus its savings details.

        Args:
            account: SavingsAccountCreate payload with the account fields.
            pin_hash: Pre-hashed PIN to store on the account row.

        Returns:
            The newly generated account number (>= ACCOUNT_NUMBER_START).

        Raises:
            DuplicateConstraintError: If the Aadhaar number already exists,
                mirroring the UNIQUE(aadhar_number) database constraint.
        """
        # Mirror UNIQUE(aadhar_number).
        if any(
            s["aadhar_number"] == account.aadhar_number
            for s in self._store.savings.values()
        ):
            raise DuplicateConstraintError("aadhar_number")

        account_number = self._store.next_account_number()
        now = datetime.utcnow()
        self._store.accounts[account_number] = {
            "account_number": account_number,
            "account_type": "SAVINGS",
            "name": account.name,
            "pin_hash": pin_hash,
            "balance": _to_decimal(account.initial_balance),
            "privilege": account.privilege,
            "bank_name": account.bank_name,
            "bank_branch": account.bank_branch,
            "ifsc_code": account.ifsc_code,
            "is_active": True,
            "activated_date": now,
            "closed_date": None,
            "created_at": now,
            "updated_at": now,
        }
        self._store.savings[account_number] = {
            "account_number": account_number,
            "date_of_birth": account.date_of_birth,
            "gender": account.gender,
            "phone_no": account.phone_no,
            "aadhar_number": account.aadhar_number,
        }
        logger.info(f"✅ Savings account created: {account_number}")
        return account_number

    async def create_current_account(self, account, pin_hash: str) -> int:
        """Create a current account plus its current details.

        The opening balance for a current account is always fixed at 0.00.

        Args:
            account: CurrentAccountCreate payload with the account fields.
            pin_hash: Pre-hashed PIN to store on the account row.

        Returns:
            The newly generated account number (>= ACCOUNT_NUMBER_START).

        Raises:
            DuplicateConstraintError: If the registration number already exists,
                mirroring the UNIQUE(registration_no) database constraint.
        """
        if any(
            c["registration_no"] == account.registration_no
            for c in self._store.current.values()
        ):
            raise DuplicateConstraintError("registration_no")

        account_number = self._store.next_account_number()
        now = datetime.utcnow()
        self._store.accounts[account_number] = {
            "account_number": account_number,
            "account_type": "CURRENT",
            "name": account.name,
            "pin_hash": pin_hash,
            "balance": Decimal("0.00"),
            "privilege": account.privilege,
            "bank_name": account.bank_name,
            "bank_branch": account.bank_branch,
            "ifsc_code": account.ifsc_code,
            "is_active": True,
            "activated_date": now,
            "closed_date": None,
            "created_at": now,
            "updated_at": now,
        }
        self._store.current[account_number] = {
            "account_number": account_number,
            "company_name": account.company_name,
            "website": account.website,
            "registration_no": account.registration_no,
        }
        logger.info(f"✅ Current account created: {account_number}")
        return account_number

    async def get_account(self, account_number: int) -> Optional[dict]:
        """Return the full account dict, or None if the account does not exist.

        Args:
            account_number: Account number to look up.

        Returns:
            The combined account dict (with `balance` as float), or None.
        """
        return self._account_dict(account_number)

    async def get_all_accounts(
        self, account_type: Optional[str] = None
    ) -> List[AccountDetailsResponse]:
        """Return all accounts, optionally filtered by type, newest first.

        Args:
            account_type: Optional "SAVINGS"/"CURRENT" filter; None returns all.

        Returns:
            A list of AccountDetailsResponse objects sorted by account number
            in descending order.
        """
        rows = list(self._store.accounts.values())
        if account_type:
            rows = [r for r in rows if r["account_type"] == account_type]
        rows.sort(key=lambda r: r["account_number"], reverse=True)
        return [
            AccountDetailsResponse(
                account_number=r["account_number"],
                account_type=r["account_type"],
                name=r["name"],
                balance=float(r["balance"]) if r["balance"] is not None else 0.0,
                privilege=r["privilege"],
                is_active=r["is_active"],
                activated_date=r["activated_date"],
                closed_date=r["closed_date"],
                bank_name=r["bank_name"],
                bank_branch=r["bank_branch"],
                ifsc_code=r["ifsc_code"],
            )
            for r in rows
        ]

    async def update_account(
        self, account_number: int, update_data: dict, account_type: str
    ) -> Optional[dict]:
        """Apply common and type-specific field updates and return the account.

        Updates `name`/`privilege` on the base row when present, and the
        type-specific fields (`phone_no` for savings; `company_name`/`website`
        for current) when present in update_data.

        Args:
            account_number: Account number to update.
            update_data: Mapping of field names to new values; only recognised
                keys are applied.
            account_type: "SAVINGS" or "CURRENT", selecting which detail table
                to update.

        Returns:
            The refreshed account dict (same shape as get_account), or None if
            the account does not exist.
        """
        acc = self._store.accounts.get(account_number)
        if acc is not None:
            if "name" in update_data:
                acc["name"] = update_data["name"]
            if "privilege" in update_data:
                acc["privilege"] = update_data["privilege"]
            acc["updated_at"] = datetime.utcnow()

        if account_type == "SAVINGS":
            s = self._store.savings.get(account_number)
            if s is not None and "phone_no" in update_data:
                s["phone_no"] = update_data["phone_no"]
        elif account_type == "CURRENT":
            c = self._store.current.get(account_number)
            if c is not None:
                if "company_name" in update_data:
                    c["company_name"] = update_data["company_name"]
                if "website" in update_data:
                    c["website"] = update_data["website"]

        return self._account_dict(account_number)

    async def get_account_balance(self, account_number: int) -> Optional[float]:
        """Return the account balance as a float, or None if not found.

        Args:
            account_number: Account number to look up.

        Returns:
            The balance as a float, or None if the account does not exist.
        """
        acc = self._store.accounts.get(account_number)
        return float(acc["balance"]) if acc is not None else None

    async def debit_account(self, account_number: int, amount) -> bool:
        """Debit `amount` iff the account is active and sufficiently funded.

        Args:
            account_number: Account to debit.
            amount: Amount to subtract (coerced to Decimal).

        Returns:
            True on success; False if the account is missing, inactive, or has
            a balance below the requested amount.
        """
        amount = _to_decimal(amount)
        acc = self._store.accounts.get(account_number)
        if acc is None or not acc["is_active"] or acc["balance"] < amount:
            logger.warning(
                f"⚠️ Debit failed for {account_number}: insufficient balance or inactive"
            )
            return False
        acc["balance"] = acc["balance"] - amount
        acc["updated_at"] = datetime.utcnow()
        logger.info(f"✅ Debit successful: {account_number}, Amount: ₹{amount}")
        return True

    async def credit_account(self, account_number: int, amount) -> bool:
        """Credit `amount` iff the account exists and is active.

        Args:
            account_number: Account to credit.
            amount: Amount to add (coerced to Decimal).

        Returns:
            True on success; False if the account is missing or inactive.
        """
        amount = _to_decimal(amount)
        acc = self._store.accounts.get(account_number)
        if acc is None or not acc["is_active"]:
            logger.warning(
                f"⚠️ Credit failed for {account_number}: account not found or inactive"
            )
            return False
        acc["balance"] = acc["balance"] + amount
        acc["updated_at"] = datetime.utcnow()
        logger.info(f"✅ Credit successful: {account_number}, Amount: ₹{amount}")
        return True

    async def activate_account(self, account_number: int) -> bool:
        """Set is_active=True on the account.

        Args:
            account_number: Account to activate.

        Returns:
            True if the account exists, False otherwise.
        """
        acc = self._store.accounts.get(account_number)
        if acc is None:
            return False
        acc["is_active"] = True
        acc["updated_at"] = datetime.utcnow()
        logger.info(f"✅ Account activated: {account_number}")
        return True

    async def inactivate_account(self, account_number: int) -> bool:
        """Set is_active=False on the account.

        Args:
            account_number: Account to deactivate.

        Returns:
            True if the account exists, False otherwise.
        """
        acc = self._store.accounts.get(account_number)
        if acc is None:
            return False
        acc["is_active"] = False
        acc["updated_at"] = datetime.utcnow()
        logger.info(f"✅ Account inactivated: {account_number}")
        return True

    async def close_account(self, account_number: int) -> bool:
        """Soft-close the account: set is_active=False and closed_date=now.

        Args:
            account_number: Account to close.

        Returns:
            True if the account exists, False otherwise.
        """
        acc = self._store.accounts.get(account_number)
        if acc is None:
            return False
        acc["is_active"] = False
        acc["closed_date"] = datetime.utcnow()
        acc["updated_at"] = datetime.utcnow()
        logger.info(f"✅ Account closed: {account_number}")
        return True

    async def get_pin_hash(self, account_number: int) -> Optional[str]:
        """Return the stored PIN hash, or None if the account does not exist.

        Args:
            account_number: Account whose PIN hash is requested.

        Returns:
            The stored PIN hash string, or None.
        """
        acc = self._store.accounts.get(account_number)
        return acc["pin_hash"] if acc is not None else None

    async def check_aadhar_has_active_account(self, aadhar_number: str) -> bool:
        """Report whether an Aadhaar already owns an active, open savings account.

        Args:
            aadhar_number: Aadhaar number to check.

        Returns:
            True if a savings account for this Aadhaar exists and is both active
            and not closed; False otherwise.
        """
        for s in self._store.savings.values():
            if s["aadhar_number"] == aadhar_number:
                acc = self._store.accounts.get(s["account_number"])
                if acc and acc["is_active"] and acc["closed_date"] is None:
                    return True
        return False
