"""
SQLAlchemy repository implementation — one code path that runs on every SQL
provider: sqlite / mysql / postgres / supabase. The active engine/session is
supplied by the SQLAlchemy database provider; the ORM/SQL below is dialect-neutral
(no Postgres-only nextval / RETURNING / ON CONFLICT).

Imported ONLY when a SQL provider is selected, so non-SQL setups never load
SQLAlchemy.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError

from .account_repo import AccountRepository
from app.database.orm_models import (
    AccountORM,
    SavingsAccountDetailsORM,
    CurrentAccountDetailsORM,
    account_to_dict,
    ACCOUNT_NUMBER_START,
)
from app.exceptions.account_exceptions import (
    DatabaseError,
    DuplicateConstraintError,
)
from app.models.account import AccountDetailsResponse
from app.utils.encryption import EncryptionManager

logger = logging.getLogger(__name__)


def _to_decimal(amount) -> Decimal:
    """Coerce an incoming amount (float / str / Decimal / int) to Decimal."""
    if isinstance(amount, Decimal):
        return amount
    return Decimal(str(amount))


class SqlAlchemyAccountRepository(AccountRepository):
    """SQLAlchemy-backed AccountRepository shared by all SQL providers.

    Implements the AccountRepository contract with dialect-neutral ORM/SQL that
    runs unchanged on sqlite / mysql / postgres / supabase. Each method opens a
    session from the injected async session factory, and translates database
    failures into DatabaseError / DuplicateConstraintError.
    """

    def __init__(self, session_factory):
        """Store the async session factory used to open per-call sessions.

        Args:
            session_factory: An async_sessionmaker bound to the active engine.
        """
        # session_factory: async_sessionmaker bound to the active engine.
        self._session_factory = session_factory

    async def _next_account_number(self, session) -> int:
        """Reproduce the old Postgres sequence (START WITH 1000) portably:
        next = max(account_number) + 1, floored at 1000."""
        result = await session.execute(select(func.max(AccountORM.account_number)))
        current_max = result.scalar_one_or_none()
        if current_max is None or current_max < ACCOUNT_NUMBER_START:
            return ACCOUNT_NUMBER_START
        return int(current_max) + 1

    async def create_savings_account(self, account, pin_hash: str) -> int:
        """Create a savings account plus its encrypted savings details.

        Aadhaar is encrypted at rest and a blind index is stored for duplicate
        detection and lookup.

        Args:
            account: SavingsAccountCreate payload with the account fields.
            pin_hash: Pre-hashed PIN to store on the account row.

        Returns:
            The newly generated account number (>= ACCOUNT_NUMBER_START).

        Raises:
            DuplicateConstraintError: If the Aadhaar already exists (detected
                pre-insert or via an IntegrityError mentioning "aadhar").
            DatabaseError: On any other integrity or database failure.
        """
        try:
            async with self._session_factory() as session:
                # Check duplicate Aadhar BEFORE generating an account number.
                aadhar_hash = EncryptionManager.blind_index(account.aadhar_number)
                existing = await session.execute(
                    select(SavingsAccountDetailsORM.account_number).where(
                        SavingsAccountDetailsORM.aadhar_hash == aadhar_hash
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    raise DuplicateConstraintError("aadhar_number")

                dob = datetime.strptime(account.date_of_birth, "%Y-%m-%d").date()
                account_number = await self._next_account_number(session)

                session.add(AccountORM(
                    account_number=account_number,
                    account_type="SAVINGS",
                    name=account.name,
                    pin_hash=pin_hash,
                    balance=_to_decimal(account.initial_balance),
                    privilege=account.privilege,
                    bank_name=account.bank_name,
                    bank_branch=account.bank_branch,
                    ifsc_code=account.ifsc_code,
                    is_active=True,
                    activated_date=datetime.utcnow(),
                ))
                session.add(SavingsAccountDetailsORM(
                    account_number=account_number,
                    date_of_birth=dob,
                    gender=account.gender,
                    phone_no=account.phone_no,
                    # Encrypt Aadhaar at rest; store the blind index for lookup (H-4).
                    aadhar_number=EncryptionManager.encrypt_data(account.aadhar_number),
                    aadhar_hash=aadhar_hash,
                ))
                await session.commit()
                logger.info(f"✅ Savings account created: {account_number}")
                return account_number
        except DuplicateConstraintError:
            raise
        except IntegrityError as e:
            if "aadhar" in str(e).lower():
                raise DuplicateConstraintError("aadhar_number")
            raise DatabaseError(str(e))
        except Exception as e:
            logger.error(f"❌ Error creating savings account: {e}")
            raise DatabaseError(str(e))

    async def create_current_account(self, account, pin_hash: str) -> int:
        """Create a current account plus its current details.

        The opening balance for a current account is always fixed at 0.00.

        Args:
            account: CurrentAccountCreate payload with the account fields.
            pin_hash: Pre-hashed PIN to store on the account row.

        Returns:
            The newly generated account number (>= ACCOUNT_NUMBER_START).

        Raises:
            DuplicateConstraintError: If the registration number already exists
                (detected pre-insert or via an IntegrityError mentioning
                "registration").
            DatabaseError: On any other integrity or database failure.
        """
        try:
            async with self._session_factory() as session:
                existing = await session.execute(
                    select(CurrentAccountDetailsORM.account_number).where(
                        CurrentAccountDetailsORM.registration_no == account.registration_no
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    raise DuplicateConstraintError("registration_no")

                account_number = await self._next_account_number(session)

                session.add(AccountORM(
                    account_number=account_number,
                    account_type="CURRENT",
                    name=account.name,
                    pin_hash=pin_hash,
                    balance=Decimal("0.00"),
                    privilege=account.privilege,
                    bank_name=account.bank_name,
                    bank_branch=account.bank_branch,
                    ifsc_code=account.ifsc_code,
                    is_active=True,
                    activated_date=datetime.utcnow(),
                ))
                session.add(CurrentAccountDetailsORM(
                    account_number=account_number,
                    company_name=account.company_name,
                    website=account.website,
                    registration_no=account.registration_no,
                ))
                await session.commit()
                logger.info(f"✅ Current account created: {account_number}")
                return account_number
        except DuplicateConstraintError:
            raise
        except IntegrityError as e:
            if "registration" in str(e).lower():
                raise DuplicateConstraintError("registration_no")
            raise DatabaseError(str(e))
        except Exception as e:
            logger.error(f"❌ Error creating current account: {e}")
            raise DatabaseError(str(e))

    async def get_account(self, account_number: int) -> Optional[dict]:
        """Return the full account dict, or None if the account does not exist.

        Loads the base account row plus its type-specific details (savings or
        current) and serialises them via account_to_dict.

        Args:
            account_number: Account number to look up.

        Returns:
            The combined account dict (with `balance` as float), or None.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AccountORM).where(AccountORM.account_number == account_number)
                )
                acc = result.scalar_one_or_none()
                if acc is None:
                    return None

                savings = None
                current = None
                if acc.account_type == "SAVINGS":
                    sres = await session.execute(
                        select(SavingsAccountDetailsORM).where(
                            SavingsAccountDetailsORM.account_number == account_number
                        )
                    )
                    savings = sres.scalar_one_or_none()
                elif acc.account_type == "CURRENT":
                    cres = await session.execute(
                        select(CurrentAccountDetailsORM).where(
                            CurrentAccountDetailsORM.account_number == account_number
                        )
                    )
                    current = cres.scalar_one_or_none()

                return account_to_dict(acc, savings=savings, current=current)
        except Exception as e:
            logger.error(f"❌ Error fetching account {account_number}: {e}")
            raise DatabaseError(str(e))

    async def get_all_accounts(
        self, account_type: Optional[str] = None
    ) -> List[AccountDetailsResponse]:
        """Return all accounts, optionally filtered by type, newest first.

        Args:
            account_type: Optional "SAVINGS"/"CURRENT" filter; None returns all.

        Returns:
            A list of AccountDetailsResponse objects ordered by account number
            descending.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            async with self._session_factory() as session:
                stmt = select(AccountORM)
                if account_type:
                    stmt = stmt.where(AccountORM.account_type == account_type)
                stmt = stmt.order_by(AccountORM.account_number.desc())
                result = await session.execute(stmt)
                rows = result.scalars().all()

                accounts = [
                    AccountDetailsResponse(
                        account_number=r.account_number,
                        account_type=r.account_type,
                        name=r.name,
                        balance=float(r.balance) if r.balance is not None else 0.0,
                        privilege=r.privilege,
                        is_active=r.is_active,
                        activated_date=r.activated_date,
                        closed_date=r.closed_date,
                        bank_name=r.bank_name,
                        bank_branch=r.bank_branch,
                        ifsc_code=r.ifsc_code,
                    )
                    for r in rows
                ]
                logger.info(f"✅ Fetched {len(accounts)} accounts from database")
                return accounts
        except Exception as e:
            logger.error(f"❌ Error fetching all accounts: {e}")
            raise DatabaseError(str(e))

    async def update_account(
        self, account_number: int, update_data: dict, account_type: str
    ) -> Optional[dict]:
        """Apply common and type-specific field updates and return the account.

        Updates `name`/`privilege` on the base row when present, and the
        type-specific fields (`phone_no` for savings; `company_name`/`website`
        for current) when present in update_data, then re-reads via get_account.

        Args:
            account_number: Account number to update.
            update_data: Mapping of field names to new values; only recognised
                keys are applied.
            account_type: "SAVINGS" or "CURRENT", selecting which detail table
                to update.

        Returns:
            The refreshed account dict (same shape as get_account), or None if
            the account does not exist.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            async with self._session_factory() as session:
                acc_res = await session.execute(
                    select(AccountORM).where(AccountORM.account_number == account_number)
                )
                acc = acc_res.scalar_one_or_none()
                if acc is not None:
                    if "name" in update_data:
                        acc.name = update_data["name"]
                    if "privilege" in update_data:
                        acc.privilege = update_data["privilege"]

                if account_type == "SAVINGS":
                    if "phone_no" in update_data:
                        s_res = await session.execute(
                            select(SavingsAccountDetailsORM).where(
                                SavingsAccountDetailsORM.account_number == account_number
                            )
                        )
                        s = s_res.scalar_one_or_none()
                        if s is not None:
                            s.phone_no = update_data["phone_no"]
                elif account_type == "CURRENT":
                    c_res = await session.execute(
                        select(CurrentAccountDetailsORM).where(
                            CurrentAccountDetailsORM.account_number == account_number
                        )
                    )
                    c = c_res.scalar_one_or_none()
                    if c is not None:
                        if "company_name" in update_data:
                            c.company_name = update_data["company_name"]
                        if "website" in update_data:
                            c.website = update_data["website"]

                await session.commit()
                logger.info(f"✅ Account {account_number} updated successfully")

            return await self.get_account(account_number)
        except Exception as e:
            logger.error(f"❌ Error updating account {account_number}: {e}")
            raise DatabaseError(str(e))

    async def get_account_balance(self, account_number: int) -> Optional[float]:
        """Return the account balance as a float, or None if not found.

        Args:
            account_number: Account number to look up.

        Returns:
            The balance as a float, or None if the account does not exist.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AccountORM.balance).where(
                        AccountORM.account_number == account_number
                    )
                )
                balance = result.scalar_one_or_none()
                return float(balance) if balance is not None else None
        except Exception as e:
            logger.error(f"❌ Error fetching balance for {account_number}: {e}")
            raise DatabaseError(str(e))

    async def debit_account(self, account_number: int, amount) -> bool:
        """Atomically debit `amount` iff the account is active and funded.

        Uses a single conditional UPDATE guarded by balance >= amount and
        is_active, so the check and decrement cannot race.

        Args:
            account_number: Account to debit.
            amount: Amount to subtract (coerced to Decimal).

        Returns:
            True if a row was updated; False if the account is missing,
            inactive, or underfunded.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            amount = _to_decimal(amount)
            async with self._session_factory() as session:
                # Atomic conditional update: only succeeds when active AND funded.
                stmt = (
                    update(AccountORM)
                    .where(
                        AccountORM.account_number == account_number,
                        AccountORM.balance >= amount,
                        AccountORM.is_active.is_(True),
                    )
                    .values(
                        balance=AccountORM.balance - amount,
                        updated_at=datetime.utcnow(),
                    )
                )
                result = await session.execute(stmt)
                await session.commit()
                if result.rowcount == 0:
                    logger.warning(
                        f"⚠️ Debit failed for {account_number}: insufficient balance or inactive"
                    )
                    return False
                logger.info(f"✅ Debit successful: {account_number}, Amount: ₹{amount}")
                return True
        except Exception as e:
            logger.error(f"❌ Error debiting account {account_number}: {e}")
            raise DatabaseError(str(e))

    async def credit_account(self, account_number: int, amount) -> bool:
        """Atomically credit `amount` iff the account is active.

        Uses a single conditional UPDATE guarded by is_active.

        Args:
            account_number: Account to credit.
            amount: Amount to add (coerced to Decimal).

        Returns:
            True if a row was updated; False if the account is missing or
            inactive.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            amount = _to_decimal(amount)
            async with self._session_factory() as session:
                stmt = (
                    update(AccountORM)
                    .where(
                        AccountORM.account_number == account_number,
                        AccountORM.is_active.is_(True),
                    )
                    .values(
                        balance=AccountORM.balance + amount,
                        updated_at=datetime.utcnow(),
                    )
                )
                result = await session.execute(stmt)
                await session.commit()
                if result.rowcount == 0:
                    logger.warning(
                        f"⚠️ Credit failed for {account_number}: account not found or inactive"
                    )
                    return False
                logger.info(f"✅ Credit successful: {account_number}, Amount: ₹{amount}")
                return True
        except Exception as e:
            logger.error(f"❌ Error crediting account {account_number}: {e}")
            raise DatabaseError(str(e))

    async def _set_status(self, account_number, is_active, close=False) -> bool:
        """Update an account's active flag (and optionally its closed_date).

        Shared helper behind activate/inactivate/close.

        Args:
            account_number: Account to update.
            is_active: New value for the is_active column.
            close: When True, also set closed_date to the current UTC time.

        Returns:
            True if a row was updated (the account exists), False otherwise.
        """
        async with self._session_factory() as session:
            values = {"is_active": is_active, "updated_at": datetime.utcnow()}
            if close:
                values["closed_date"] = datetime.utcnow()
            stmt = (
                update(AccountORM)
                .where(AccountORM.account_number == account_number)
                .values(**values)
            )
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def activate_account(self, account_number: int) -> bool:
        """Set is_active=True on the account.

        Args:
            account_number: Account to activate.

        Returns:
            True if the account exists, False otherwise.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            ok = await self._set_status(account_number, True)
            if ok:
                logger.info(f"✅ Account activated: {account_number}")
            return ok
        except Exception as e:
            logger.error(f"❌ Error activating account {account_number}: {e}")
            raise DatabaseError(str(e))

    async def inactivate_account(self, account_number: int) -> bool:
        """Set is_active=False on the account.

        Args:
            account_number: Account to deactivate.

        Returns:
            True if the account exists, False otherwise.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            ok = await self._set_status(account_number, False)
            if ok:
                logger.info(f"✅ Account inactivated: {account_number}")
            return ok
        except Exception as e:
            logger.error(f"❌ Error inactivating account {account_number}: {e}")
            raise DatabaseError(str(e))

    async def close_account(self, account_number: int) -> bool:
        """Soft-close the account: set is_active=False and closed_date=now.

        Args:
            account_number: Account to close.

        Returns:
            True if the account exists, False otherwise.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            ok = await self._set_status(account_number, False, close=True)
            if ok:
                logger.info(f"✅ Account closed: {account_number}")
            return ok
        except Exception as e:
            logger.error(f"❌ Error closing account {account_number}: {e}")
            raise DatabaseError(str(e))

    async def get_pin_hash(self, account_number: int) -> Optional[str]:
        """Return the stored PIN hash, or None if the account does not exist.

        Args:
            account_number: Account whose PIN hash is requested.

        Returns:
            The stored PIN hash string, or None.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AccountORM.pin_hash).where(
                        AccountORM.account_number == account_number
                    )
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error fetching PIN hash: {e}")
            raise DatabaseError(str(e))

    async def check_aadhar_has_active_account(self, aadhar_number: str) -> bool:
        """Report whether an Aadhaar already owns an active, open savings account.

        Matches on the Aadhaar blind index and requires is_active and a null
        closed_date.

        Args:
            aadhar_number: Aadhaar number to check.

        Returns:
            True if such an account exists; False otherwise.

        Raises:
            DatabaseError: On any database failure.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AccountORM.account_number)
                    .join(
                        SavingsAccountDetailsORM,
                        AccountORM.account_number
                        == SavingsAccountDetailsORM.account_number,
                    )
                    .where(
                        SavingsAccountDetailsORM.aadhar_hash
                        == EncryptionManager.blind_index(aadhar_number),
                        AccountORM.is_active.is_(True),
                        AccountORM.closed_date.is_(None),
                    )
                )
                return result.first() is not None
        except Exception as e:
            logger.error(f"❌ Error checking active Aadhar account: {e}")
            raise DatabaseError(str(e))
