"""
SQLAlchemy repository implementations — one code path that runs on every SQL
provider: sqlite / mysql / postgres / supabase. The active engine/session is
supplied by the SQLAlchemy database provider; the SQL below is dialect-neutral
(no Postgres-only $n / RETURNING / nextval / ON CONFLICT).

Imported ONLY when a SQL provider is selected, so non-SQL setups never load
SQLAlchemy.

Portable ports of the original Postgres-only SQL:
  - RETURNING id             → session.refresh(row) / row.id after flush.
  - INSERT ... ON CONFLICT   → try INSERT, catch IntegrityError → already exists.
  - DATE(created_at) = $2    → half-open [start_of_day, next_day) range.
  - money                    → Decimal end-to-end (Numeric(15, 2) columns).
"""

import json
import logging
from datetime import datetime, timedelta, date as date_cls
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.exceptions.database_exception import DatabaseException
from app.database.orm_models import (
    FundTransferORM,
    TransactionLoggingORM,
    TransferLimitORM,
    IdempotencyKeyORM,
)
from .transaction_repository import TransactionRepositoryInterface
from .transaction_log_repository import TransactionLogRepositoryInterface
from .transfer_limit_repository import TransferLimitRepositoryInterface
from .idempotency_repository import IdempotencyRepositoryInterface

logger = logging.getLogger(__name__)


def _day_bounds(date):
    """Half-open [start, next_day) bounds for a date/datetime (portable DATE())."""
    if date is None:
        date = datetime.utcnow()
    if isinstance(date, datetime):
        day = date.date()
    elif isinstance(date, date_cls):
        day = date
    else:
        day = datetime.utcnow().date()
    start = datetime(day.year, day.month, day.day)
    return start, start + timedelta(days=1)


def _transfer_to_dict(r: FundTransferORM) -> Dict[str, Any]:
    """Serialize a FundTransferORM row into the plain dict callers expect."""
    return {
        "id": r.id,
        "from_account": r.from_account,
        "to_account": r.to_account,
        "transfer_amount": r.transfer_amount,
        "transfer_mode": r.transfer_mode,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
    }


def _log_to_dict(r: TransactionLoggingORM) -> Dict[str, Any]:
    """Serialize a TransactionLoggingORM row into the plain dict callers expect."""
    return {
        "id": r.id,
        "account_number": r.account_number,
        "amount": r.amount,
        "transaction_type": r.transaction_type,
        "reference_id": r.reference_id,
        "description": r.description,
        "mode": r.mode,
        "status": r.status,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
    }


class SqlAlchemyTransactionRepository(TransactionRepositoryInterface):
    """SQLAlchemy-backed repository for fund_transfers (any SQL provider)."""

    def __init__(self, session_factory):
        """Store the async session factory used to open per-call sessions."""
        self._session_factory = session_factory

    async def create_transaction(self, from_account, to_account, amount,
                                 transaction_type, description=None):
        """Insert a fund_transfers row and return its generated id.

        Args:
            from_account: Source account, or None.
            to_account: Destination account, or None.
            amount: Transfer amount (coerced to Decimal for the Numeric column).
            transaction_type: Transaction type (unused by the persisted row).
            description: Optional description (not persisted here).

        Returns:
            The generated transaction id.
        """
        async with self._session_factory() as session:
            row = FundTransferORM(
                from_account=from_account,
                to_account=to_account,
                transfer_amount=Decimal(str(amount)),
                transfer_mode="NEFT",
                created_at=datetime.utcnow(),
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            logger.info(f"✅ Transaction {row.id} created")
            return row.id

    async def get_transaction(self, transaction_id):
        """Fetch a single fund_transfers row by primary key.

        Args:
            transaction_id: Primary key of the fund_transfers row.

        Returns:
            The row serialized as a dict, or None if no row exists.
        """
        async with self._session_factory() as session:
            row = await session.get(FundTransferORM, transaction_id)
            return _transfer_to_dict(row) if row else None

    async def get_account_transactions(self, account_number, skip=0, limit=10, days=30):
        """Return a page of transfers touching an account within a recent window.

        Matches rows where the account is either the source or destination and
        whose created_at falls within the last ``days`` days, newest first.

        Args:
            account_number: Account that must appear as from_account or to_account.
            skip: Number of rows to skip for pagination (OFFSET).
            limit: Maximum number of rows to return (LIMIT).
            days: Size of the trailing time window, in days.

        Returns:
            A tuple of (list of transfer dicts, total matching count).
        """
        from_date = datetime.utcnow() - timedelta(days=days)
        async with self._session_factory() as session:
            cond = (
                (FundTransferORM.from_account == account_number)
                | (FundTransferORM.to_account == account_number)
            ) & (FundTransferORM.created_at >= from_date)
            total = int((await session.execute(
                select(func.count()).select_from(FundTransferORM).where(cond)
            )).scalar_one() or 0)
            rows = (await session.execute(
                select(FundTransferORM).where(cond)
                .order_by(FundTransferORM.created_at.desc())
                .limit(limit).offset(skip)
            )).scalars().all()
            return [_transfer_to_dict(r) for r in rows], total

    async def update_transaction_status(self, transaction_id, error_message=None):
        """Touch a transfer's updated_at timestamp if the row exists.

        Args:
            transaction_id: Primary key of the fund_transfers row.
            error_message: Accepted for interface compatibility; not persisted.

        Returns:
            True in all cases (whether or not a matching row was found).
        """
        async with self._session_factory() as session:
            row = await session.get(FundTransferORM, transaction_id)
            if row:
                row.updated_at = datetime.utcnow()
                await session.commit()
            return True

    async def get_daily_transactions(self, account_number, date=None):
        """Return all transfers touching an account on a single calendar day.

        Uses a half-open [start_of_day, next_day) range so it behaves the same
        on every SQL dialect, newest first.

        Args:
            account_number: Account that must appear as from_account or to_account.
            date: Day to query as a date/datetime; defaults to today (UTC).

        Returns:
            A list of transfer dicts for that day.
        """
        start, end = _day_bounds(date if date else datetime.utcnow())
        async with self._session_factory() as session:
            rows = (await session.execute(
                select(FundTransferORM).where(
                    ((FundTransferORM.from_account == account_number)
                     | (FundTransferORM.to_account == account_number))
                    & (FundTransferORM.created_at >= start)
                    & (FundTransferORM.created_at < end)
                ).order_by(FundTransferORM.created_at.desc())
            )).scalars().all()
            return [_transfer_to_dict(r) for r in rows]


class SqlAlchemyTransactionLogRepository(TransactionLogRepositoryInterface):
    """SQLAlchemy-backed repository for the transaction_logging table.

    Persists per-account transaction audit log rows (deposits, withdrawals and
    related events) via async sessions on any supported SQL provider.
    """

    def __init__(self, session_factory):
        """Store the async session factory used to open per-call sessions."""
        self._session_factory = session_factory

    async def log_to_database(self, account_number, amount, transaction_type,
                              reference_id=None, description=None):
        """Persist a transaction log row and return its generated id.

        Args:
            account_number: Account the log entry belongs to.
            amount: Transaction amount (coerced to Decimal for the Numeric column).
            transaction_type: Enum whose ``.value`` is stored as the type string.
            reference_id: Optional id linking the log to a source transaction.
            description: Optional free-text description.

        Returns:
            The generated log id, or None if the insert failed (errors are
            swallowed and logged rather than raised).
        """
        try:
            async with self._session_factory() as session:
                row = TransactionLoggingORM(
                    account_number=account_number,
                    amount=Decimal(str(amount)),
                    transaction_type=transaction_type.value,
                    reference_id=reference_id,
                    description=description,
                    created_at=datetime.utcnow(),
                )
                session.add(row)
                await session.commit()
                await session.refresh(row)
                logger.info(
                    f"✅ Logged {transaction_type.value} for account "
                    f"{account_number} to DB (ID: {row.id})"
                )
                return row.id
        except Exception as e:
            logger.error(f"❌ Failed to log to database: {str(e)}")
            return None

    async def get_logs_for_transaction(self, transaction_id):
        """Return all log rows referencing a given transaction id, newest first.

        Args:
            transaction_id: Value matched against each log's reference_id.

        Returns:
            A dict of the form ``{"transaction_id": <id>, "logs": [<log dict>, ...]}``.
        """
        async with self._session_factory() as session:
            rows = (await session.execute(
                select(TransactionLoggingORM)
                .where(TransactionLoggingORM.reference_id == transaction_id)
                .order_by(TransactionLoggingORM.created_at.desc())
            )).scalars().all()
            return {"transaction_id": transaction_id, "logs": [_log_to_dict(r) for r in rows]}

    @staticmethod
    def _type_condition(transaction_type: str):
        """Build the SQLAlchemy filter for a transaction type.

        Treats ``"WITHDRAW"`` as an alias covering both stored spellings
        (``"WITHDRAW"`` and ``"WITHDRAWAL"``); any other type matches exactly.

        Args:
            transaction_type: The requested transaction type string.

        Returns:
            A SQLAlchemy boolean expression suitable for use in a WHERE clause.
        """
        if transaction_type == "WITHDRAW":
            return TransactionLoggingORM.transaction_type.in_(["WITHDRAW", "WITHDRAWAL"])
        return TransactionLoggingORM.transaction_type == transaction_type

    async def get_account_logs(self, account_number, skip=0, limit=10,
                               start_date=None, end_date=None, transaction_type=None,
                               sort_by="id", order="asc"):
        """Return a filtered, sorted page of one account's transaction logs.

        Args:
            account_number: Account whose logs are queried.
            skip: Number of rows to skip for pagination (OFFSET).
            limit: Maximum number of rows to return (LIMIT).
            start_date: Optional inclusive lower bound on created_at.
            end_date: Optional inclusive upper bound on created_at.
            transaction_type: Optional type filter; ``"ALL"`` (or falsy) disables
                it, and ``"WITHDRAW"`` also matches ``"WITHDRAWAL"``.
            sort_by: ``"id"`` to sort by primary key, otherwise by created_at.
            order: ``"asc"`` for ascending, anything else for descending.

        Returns:
            A tuple of (list of log dicts for the page, total matching count).
        """
        async with self._session_factory() as session:
            cond = TransactionLoggingORM.account_number == account_number
            if transaction_type and transaction_type != "ALL":
                cond = cond & self._type_condition(transaction_type)
            if start_date:
                cond = cond & (TransactionLoggingORM.created_at >= start_date)
            if end_date:
                cond = cond & (TransactionLoggingORM.created_at <= end_date)

            total = int((await session.execute(
                select(func.count()).select_from(TransactionLoggingORM).where(cond)
            )).scalar_one() or 0)

            sort_col = TransactionLoggingORM.id if sort_by == "id" else TransactionLoggingORM.created_at
            sort_col = sort_col.asc() if order.lower() == "asc" else sort_col.desc()
            rows = (await session.execute(
                select(TransactionLoggingORM).where(cond)
                .order_by(sort_col).limit(limit).offset(skip)
            )).scalars().all()
            return [_log_to_dict(r) for r in rows], total

    async def get_all_transactions(self, skip=0, limit=50, transaction_type=None,
                                   start_date=None, end_date=None, sort_by="id", order="asc"):
        """Return a merged, sorted page across deposit/withdraw logs and transfers.

        Combines rows from the transaction_logging table (DEPOSIT / WITHDRAW /
        WITHDRAWAL) and the fund_transfers table (as synthetic ``"TRANSFER"``
        rows) into a single normalized shape, then sorts and paginates in memory.
        The ``transaction_type`` filter selects which source tables to include.

        Args:
            skip: Number of merged rows to skip for pagination.
            limit: Maximum number of merged rows to return.
            transaction_type: Optional type filter (case-insensitive); ``"ALL"``
                or falsy includes everything, ``"TRANSFER"`` only transfers, and
                a log type only the matching logs.
            start_date: Optional inclusive lower bound on created_at.
            end_date: Optional inclusive upper bound on created_at.
            sort_by: ``"id"`` to sort by transaction_id, otherwise by timestamp.
            order: ``"asc"`` for ascending, anything else for descending.

        Returns:
            A list of normalized transaction dicts for the requested page.
        """
        if transaction_type:
            transaction_type = str(transaction_type).upper()
        combined: List[Dict[str, Any]] = []

        include_logs = (not transaction_type or transaction_type == "ALL"
                        or transaction_type in ("DEPOSIT", "WITHDRAW", "WITHDRAWAL"))
        include_transfers = (not transaction_type or transaction_type == "ALL"
                             or transaction_type == "TRANSFER")

        async with self._session_factory() as session:
            if include_logs:
                cond = TransactionLoggingORM.transaction_type.in_(
                    ["DEPOSIT", "WITHDRAW", "WITHDRAWAL"]
                )
                if transaction_type in ("DEPOSIT", "WITHDRAW", "WITHDRAWAL"):
                    cond = cond & self._type_condition(transaction_type)
                if start_date:
                    cond = cond & (TransactionLoggingORM.created_at >= start_date)
                if end_date:
                    cond = cond & (TransactionLoggingORM.created_at <= end_date)
                for r in (await session.execute(
                    select(TransactionLoggingORM).where(cond)
                )).scalars().all():
                    combined.append({
                        "transaction_id": r.id,
                        "account_number": r.account_number,
                        "from_account": None,
                        "to_account": None,
                        "amount": r.amount,
                        "transaction_type": r.transaction_type,
                        "mode": None,
                        "status": "SUCCESS",
                        "timestamp": r.created_at,
                    })

            if include_transfers:
                cond = None
                if start_date:
                    cond = FundTransferORM.created_at >= start_date
                if end_date:
                    c2 = FundTransferORM.created_at <= end_date
                    cond = c2 if cond is None else (cond & c2)
                stmt = select(FundTransferORM)
                if cond is not None:
                    stmt = stmt.where(cond)
                for r in (await session.execute(stmt)).scalars().all():
                    combined.append({
                        "transaction_id": r.id,
                        "account_number": None,
                        "from_account": r.from_account,
                        "to_account": r.to_account,
                        "amount": r.transfer_amount,
                        "transaction_type": "TRANSFER",
                        "mode": r.transfer_mode,
                        "status": "SUCCESS",
                        "timestamp": r.created_at,
                    })

        key = (lambda r: r["transaction_id"]) if sort_by == "id" else (lambda r: r["timestamp"])
        combined.sort(key=key, reverse=(order.lower() != "asc"))
        return combined[skip:skip + limit]

    async def get_total_count(self, transaction_type=None, start_date=None, end_date=None):
        """Count all merged transactions matching the given filters.

        Delegates to :meth:`get_all_transactions` with an effectively unbounded
        limit and returns the length of the result.

        Args:
            transaction_type: Optional type filter (see get_all_transactions).
            start_date: Optional inclusive lower bound on created_at.
            end_date: Optional inclusive upper bound on created_at.

        Returns:
            The total number of matching merged transactions.
        """
        rows = await self.get_all_transactions(
            skip=0, limit=10**9, transaction_type=transaction_type,
            start_date=start_date, end_date=end_date,
        )
        return len(rows)

    async def delete_old_logs(self, days_to_keep=90):
        """Delete transaction log rows older than a retention window.

        Args:
            days_to_keep: Number of days to retain; rows with created_at before
                ``now - days_to_keep`` are deleted.

        Returns:
            True on success, or False if the delete failed (errors are logged,
            not raised).
        """
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        try:
            async with self._session_factory() as session:
                await session.execute(
                    delete(TransactionLoggingORM)
                    .where(TransactionLoggingORM.created_at < cutoff)
                )
                await session.commit()
            logger.info(f"✅ Deleted transaction logs older than {days_to_keep} days")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete old logs: {str(e)}")
            return False


class SqlAlchemyTransferLimitRepository(TransferLimitRepositoryInterface):
    """SQLAlchemy-backed repository for the transfer_limits table.

    Persists per-privilege transfer rules (daily and per-transaction limits)
    and derives per-account daily usage from fund_transfers, via async sessions
    on any supported SQL provider.
    """

    def __init__(self, session_factory):
        """Store the async session factory used to open per-call sessions."""
        self._session_factory = session_factory

    async def get_transfer_rule(self, privilege):
        """Fetch the transfer limit rule for a privilege tier.

        Args:
            privilege: Privilege tier used as the transfer_limits primary key.

        Returns:
            A dict with ``daily_limit`` and ``transaction_limit`` (as floats)
            plus ``created_at``, or None if no rule exists for the privilege.
        """
        async with self._session_factory() as session:
            row = await session.get(TransferLimitORM, privilege)
            if row:
                return {
                    "daily_limit": float(row.daily_limit),
                    "transaction_limit": float(row.per_transaction_limit),
                    "created_at": row.created_at,
                }
            return None

    async def create_transfer_rule(self, privilege, daily_limit, transaction_limit):
        """Create or update the transfer limit rule for a privilege tier (upsert).

        If a rule already exists for the privilege its limits and updated_at are
        overwritten; otherwise a new row is inserted. Amounts are stored as
        Decimal for the Numeric columns.

        Args:
            privilege: Privilege tier used as the transfer_limits primary key.
            daily_limit: New daily transfer limit.
            transaction_limit: New per-transaction transfer limit.

        Returns:
            True on successful commit.

        Raises:
            Exception: Re-raises any error encountered while persisting, after
                logging it.
        """
        try:
            async with self._session_factory() as session:
                row = await session.get(TransferLimitORM, privilege)
                if row:
                    row.daily_limit = Decimal(str(daily_limit))
                    row.per_transaction_limit = Decimal(str(transaction_limit))
                    row.updated_at = datetime.utcnow()
                else:
                    session.add(TransferLimitORM(
                        privilege=privilege,
                        daily_limit=Decimal(str(daily_limit)),
                        per_transaction_limit=Decimal(str(transaction_limit)),
                    ))
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error creating/updating transfer rule: {str(e)}")
            raise

    async def get_daily_used_amount(self, account_number, date=None):
        """Sum the amount an account has sent as source on a single day.

        Sums transfer_amount over fund_transfers where the account is the
        from_account within the half-open [start_of_day, next_day) range.

        Args:
            account_number: Account whose outgoing transfers are summed.
            date: Day to query as a date/datetime; defaults to today (UTC).

        Returns:
            The total sent amount as a Decimal (``Decimal("0")`` if none).

        Raises:
            DatabaseException: If the query fails.
        """
        start, end = _day_bounds(date)
        try:
            async with self._session_factory() as session:
                total = (await session.execute(
                    select(func.coalesce(func.sum(FundTransferORM.transfer_amount), 0))
                    .where(
                        (FundTransferORM.from_account == account_number)
                        & (FundTransferORM.created_at >= start)
                        & (FundTransferORM.created_at < end)
                    )
                )).scalar_one()
                result = Decimal(str(total)) if total is not None else Decimal("0")
                logger.info(f"Daily used amount for account {account_number}: ₹{result}")
                return result
        except Exception as e:
            logger.error(f"Error getting daily used amount: {str(e)}")
            raise DatabaseException("Failed to read daily used amount")

    async def get_daily_transaction_count(self, account_number, date=None):
        """Count the transfers an account has sent as source on a single day.

        Counts fund_transfers where the account is the from_account within the
        half-open [start_of_day, next_day) range.

        Args:
            account_number: Account whose outgoing transfers are counted.
            date: Day to query as a date/datetime; defaults to today (UTC).

        Returns:
            The number of outgoing transfers that day as an int.

        Raises:
            DatabaseException: If the query fails.
        """
        start, end = _day_bounds(date)
        try:
            async with self._session_factory() as session:
                count = (await session.execute(
                    select(func.count()).select_from(FundTransferORM).where(
                        (FundTransferORM.from_account == account_number)
                        & (FundTransferORM.created_at >= start)
                        & (FundTransferORM.created_at < end)
                    )
                )).scalar_one()
                count = int(count or 0)
                logger.info(f"Daily transaction count for account {account_number}: {count}")
                return count
        except Exception as e:
            logger.error(f"Error getting daily transaction count: {str(e)}")
            raise DatabaseException("Failed to read daily transaction count")


class SqlAlchemyIdempotencyRepository(IdempotencyRepositoryInterface):
    """SQLAlchemy-backed repository for the idempotency_keys table.

    Enforces exactly-once execution of money-moving operations by reserving a
    unique idempotency key, caching the completed response, and releasing keys
    for abandoned attempts, via async sessions on any supported SQL provider.
    """

    def __init__(self, session_factory):
        """Store the async session factory used to open per-call sessions."""
        self._session_factory = session_factory

    async def reserve(self, idempotency_key, operation):
        """Insert-first: try INSERT; a duplicate key raises IntegrityError → False.
        A real DB error fails CLOSED (raise DatabaseException)."""
        try:
            async with self._session_factory() as session:
                now = datetime.utcnow()
                session.add(IdempotencyKeyORM(
                    idempotency_key=idempotency_key,
                    operation=operation,
                    status="IN_PROGRESS",
                    created_at=now,
                    updated_at=now,
                ))
                try:
                    await session.commit()
                except IntegrityError:
                    await session.rollback()
                    return False
                return True
        except DatabaseException:
            raise
        except IntegrityError:
            return False
        except SQLAlchemyError as e:
            logger.error(f"❌ Idempotency reserve failed for {idempotency_key}: {e}")
            raise DatabaseException("Failed to reserve idempotency key")
        except Exception as e:
            logger.error(f"❌ Idempotency reserve failed for {idempotency_key}: {e}")
            raise DatabaseException("Failed to reserve idempotency key")

    async def get_completed_response(self, idempotency_key):
        """Return the cached response for a completed idempotent operation.

        Looks up the key and only returns a result when the row exists, its
        status is exactly ``"COMPLETED"``, and a stored response_json is present;
        the JSON is decoded back into the original response object. Any other
        state (missing, IN_PROGRESS, or no stored body) yields None, and lookup
        errors are swallowed and logged, also returning None — so a caller never
        mistakes a failed read for a real cached result.

        Args:
            idempotency_key: The client-supplied key identifying the operation.

        Returns:
            The previously stored response (decoded from JSON), or None if there
            is no completed response for the key.
        """
        try:
            async with self._session_factory() as session:
                row = await session.get(IdempotencyKeyORM, idempotency_key)
                if row and row.status == "COMPLETED" and row.response_json:
                    return json.loads(row.response_json)
                return None
        except Exception as e:
            logger.error(f"❌ Idempotency lookup failed for {idempotency_key}: {e}")
            return None

    async def complete(self, idempotency_key, response):
        """Mark a reserved key COMPLETED and cache its response for replay.

        Loads the existing key row; if it is missing this is a no-op. Otherwise
        it stores ``response`` serialized to JSON (``default=str`` for
        non-serializable values), sets status to ``"COMPLETED"``, and commits so
        that later :meth:`get_completed_response` calls replay the same result.
        Failures are swallowed and logged, not raised.

        Args:
            idempotency_key: The key previously reserved for this operation.
            response: The operation's result to persist for future replays.

        Returns:
            None.
        """
        try:
            async with self._session_factory() as session:
                row = await session.get(IdempotencyKeyORM, idempotency_key)
                if row is None:
                    return
                row.response_json = json.dumps(response, default=str)
                row.status = "COMPLETED"
                row.updated_at = datetime.utcnow()
                await session.commit()
        except Exception as e:
            logger.error(f"❌ Failed to complete idempotency key {idempotency_key}: {e}")

    async def release(self, idempotency_key):
        """Release a still-in-progress reservation so the key can be retried.

        Deletes the key row only when it exists and its status is exactly
        ``"IN_PROGRESS"`` — a COMPLETED key is never removed, preserving the
        cached response. Intended for rolling back an abandoned or failed
        attempt. Failures are swallowed and logged, not raised.

        Args:
            idempotency_key: The key whose in-progress reservation to release.

        Returns:
            None.
        """
        try:
            async with self._session_factory() as session:
                row = await session.get(IdempotencyKeyORM, idempotency_key)
                if row and row.status == "IN_PROGRESS":
                    await session.delete(row)
                    await session.commit()
        except Exception as e:
            logger.error(f"❌ Failed to release idempotency key {idempotency_key}: {e}")
