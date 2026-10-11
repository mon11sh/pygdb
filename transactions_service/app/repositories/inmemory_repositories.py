"""
In-memory repository implementations (DATABASE_PROVIDER=inmemory).

Pure Python dicts/lists — no SQL engine, no external driver. Data lives only for
the process lifetime. Implements the same repository CONTRACTS as the asyncpg and
SQLAlchemy implementations, so services never know the difference.

Money is handled as Decimal end-to-end (mirrors the Numeric(15, 2) columns).
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from app.models.enums import TransactionType
from app.exceptions.database_exception import DatabaseException
from .transaction_repository import TransactionRepositoryInterface
from .transaction_log_repository import TransactionLogRepositoryInterface
from .transfer_limit_repository import TransferLimitRepositoryInterface
from .idempotency_repository import IdempotencyRepositoryInterface

logger = logging.getLogger(__name__)


class InMemoryStore:
    """Process-lifetime store shared by the in-memory repositories."""

    def __init__(self):
        """Initialize empty in-memory collections and id counters.

        Sets up the dicts/lists that back the fund transfers, transaction
        logs, transfer limits, and idempotency records, plus the monotonic
        sequence counters used to generate primary keys.
        """
        self.fund_transfers: Dict[int, Dict[str, Any]] = {}
        self.transaction_logs: List[Dict[str, Any]] = []
        self.transfer_limits: Dict[str, Dict[str, Any]] = {}
        self.idempotency: Dict[str, Dict[str, Any]] = {}
        self._transfer_seq = 0
        self._log_seq = 0

    def next_transfer_id(self) -> int:
        """Return the next auto-incrementing fund transfer id.

        Returns:
            int: A new, unique transfer id (increments on every call).
        """
        self._transfer_seq += 1
        return self._transfer_seq

    def next_log_id(self) -> int:
        """Return the next auto-incrementing transaction log id.

        Returns:
            int: A new, unique log id (increments on every call).
        """
        self._log_seq += 1
        return self._log_seq


def _as_decimal(value) -> Decimal:
    """Coerce a numeric value to a Decimal for money-safe arithmetic.

    Values that are already Decimal are returned unchanged; anything else is
    converted via its string form to avoid binary float rounding artifacts.

    Args:
        value: A Decimal, int, float, or str representing a monetary amount.

    Returns:
        Decimal: The value as a Decimal.
    """
    return value if isinstance(value, Decimal) else Decimal(str(value))


class InMemoryTransactionRepository(TransactionRepositoryInterface):
    """In-memory repository for fund transfer transactions.

    Stores fund transfer rows in the shared :class:`InMemoryStore`, providing
    the same contract as the persistent (asyncpg/SQLAlchemy) transaction
    repositories for use with ``DATABASE_PROVIDER=inmemory``.
    """

    def __init__(self, store: InMemoryStore):
        """Bind this repository to a shared in-memory store.

        Args:
            store (InMemoryStore): The process-lifetime store holding
                fund transfer data.
        """
        self._store = store

    async def create_transaction(self, from_account, to_account, amount,
                                 transaction_type, description=None):
        """Create a new fund transfer record and return its id.

        Args:
            from_account: Source account number.
            to_account: Destination account number.
            amount: Transfer amount (coerced to Decimal).
            transaction_type: The transaction type (accepted for interface
                parity; not persisted on the transfer row).
            description: Optional free-text description (unused here).

        Returns:
            int: The generated transaction id.
        """
        tid = self._store.next_transfer_id()
        now = datetime.utcnow()
        row = {
            "id": tid,
            "from_account": from_account,
            "to_account": to_account,
            "transfer_amount": _as_decimal(amount),
            "transfer_mode": "NEFT",
            "created_at": now,
            "updated_at": now,
        }
        self._store.fund_transfers[tid] = row
        logger.info(f"✅ Transaction {tid} created")
        return tid

    async def get_transaction(self, transaction_id):
        """Fetch a single transaction by id.

        Args:
            transaction_id: The transaction id to look up.

        Returns:
            Optional[Dict[str, Any]]: A copy of the transaction row, or
            ``None`` if no transaction matches.
        """
        row = self._store.fund_transfers.get(transaction_id)
        return dict(row) if row else None

    async def get_account_transactions(self, account_number, skip=0, limit=10, days=30):
        """Return an account's recent transactions, newest first, with a total.

        Includes transfers where the account is either sender or receiver
        within the trailing ``days`` window.

        Args:
            account_number: The account to filter transactions for.
            skip: Number of rows to skip for pagination.
            limit: Maximum number of rows to return.
            days: Size of the trailing time window in days.

        Returns:
            Tuple[List[Dict[str, Any]], int]: The page of transaction rows and
            the total count of matching rows before pagination.
        """
        from_date = datetime.utcnow() - timedelta(days=days)
        rows = [
            r for r in self._store.fund_transfers.values()
            if (r["from_account"] == account_number or r["to_account"] == account_number)
            and r["created_at"] >= from_date
        ]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        total = len(rows)
        return [dict(r) for r in rows[skip:skip + limit]], total

    async def update_transaction_status(self, transaction_id, error_message=None):
        """Touch a transaction's ``updated_at`` timestamp.

        Args:
            transaction_id: The transaction id to update.
            error_message: Optional error detail (accepted for interface
                parity; not stored on the in-memory row).

        Returns:
            bool: Always ``True``; a missing transaction is a no-op.
        """
        row = self._store.fund_transfers.get(transaction_id)
        if row:
            row["updated_at"] = datetime.utcnow()
        return True

    async def get_daily_transactions(self, account_number, date=None):
        """Return an account's transactions for a single calendar day.

        Includes transfers where the account is sender or receiver whose
        ``created_at`` falls within the given day, sorted newest first.

        Args:
            account_number: The account to filter transactions for.
            date: The day to report on; defaults to the current UTC day.

        Returns:
            List[Dict[str, Any]]: Matching transaction rows for that day.
        """
        if not date:
            date = datetime.utcnow()
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        rows = [
            r for r in self._store.fund_transfers.values()
            if (r["from_account"] == account_number or r["to_account"] == account_number)
            and start <= r["created_at"] < end
        ]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return [dict(r) for r in rows]


class InMemoryTransactionLogRepository(TransactionLogRepositoryInterface):
    """In-memory repository for transaction (audit) logs.

    Stores per-account transaction log rows (deposits, withdrawals, etc.) in
    the shared :class:`InMemoryStore`, mirroring the persistent transaction
    log repository contract for ``DATABASE_PROVIDER=inmemory``.
    """

    def __init__(self, store: InMemoryStore):
        """Bind this repository to a shared in-memory store.

        Args:
            store (InMemoryStore): The process-lifetime store holding
                transaction log data.
        """
        self._store = store

    async def log_to_database(self, account_number, amount, transaction_type,
                              reference_id=None, description=None):
        """Append a transaction log entry and return its id.

        Failures are swallowed and logged so that auditing never breaks the
        caller's flow.

        Args:
            account_number: The account the log entry belongs to.
            amount: The transaction amount (coerced to Decimal).
            transaction_type: A ``TransactionType`` enum whose ``.value`` is
                stored on the row.
            reference_id: Optional id linking the log to a transaction.
            description: Optional free-text description.

        Returns:
            Optional[int]: The generated log id, or ``None`` if logging failed.
        """
        try:
            log_id = self._store.next_log_id()
            now = datetime.utcnow()
            row = {
                "id": log_id,
                "account_number": account_number,
                "amount": _as_decimal(amount),
                "transaction_type": transaction_type.value,
                "reference_id": reference_id,
                "description": description,
                "mode": None,
                "status": "SUCCESS",
                "created_at": now,
                "updated_at": now,
            }
            self._store.transaction_logs.append(row)
            logger.info(
                f"✅ Logged {transaction_type.value} for account {account_number} "
                f"to store (ID: {log_id})"
            )
            return log_id
        except Exception as e:
            logger.error(f"❌ Failed to log to store: {str(e)}")
            return None

    async def get_logs_for_transaction(self, transaction_id):
        """Return all log entries referencing a given transaction.

        Args:
            transaction_id: The transaction id to match against each log's
                ``reference_id``.

        Returns:
            Dict[str, Any]: A mapping with the ``transaction_id`` and a
            ``logs`` list of matching entries, sorted newest first.
        """
        rows = [r for r in self._store.transaction_logs if r["reference_id"] == transaction_id]
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return {"transaction_id": transaction_id, "logs": [dict(r) for r in rows]}

    @staticmethod
    def _type_matches(row_type: str, wanted: str) -> bool:
        """Check whether a stored transaction type matches a requested filter.

        Treats ``WITHDRAW`` and ``WITHDRAWAL`` as equivalent so the two
        spellings match the same filter; all other types match exactly.

        Args:
            row_type (str): The transaction type stored on the log row.
            wanted (str): The requested transaction type to filter by.

        Returns:
            bool: ``True`` if the row's type satisfies the filter.
        """
        if wanted == "WITHDRAW":
            return row_type in ("WITHDRAW", "WITHDRAWAL")
        return row_type == wanted

    async def get_account_logs(self, account_number, skip=0, limit=10,
                               start_date=None, end_date=None, transaction_type=None,
                               sort_by="id", order="asc"):
        """Return a filtered, sorted, paginated page of an account's logs.

        Args:
            account_number: The account whose logs to return.
            skip: Number of rows to skip for pagination.
            limit: Maximum number of rows to return.
            start_date: Optional inclusive lower bound on ``created_at``.
            end_date: Optional inclusive upper bound on ``created_at``.
            transaction_type: Optional type filter; ``"ALL"`` (or falsy)
                disables filtering.
            sort_by: ``"id"`` to sort by log id, otherwise by ``created_at``.
            order: ``"asc"`` for ascending, anything else for descending.

        Returns:
            Tuple[List[Dict[str, Any]], int]: The page of log rows and the
            total count of matching rows before pagination.
        """
        rows = [r for r in self._store.transaction_logs if r["account_number"] == account_number]
        if transaction_type and transaction_type != "ALL":
            rows = [r for r in rows if self._type_matches(r["transaction_type"], transaction_type)]
        if start_date:
            rows = [r for r in rows if r["created_at"] >= start_date]
        if end_date:
            rows = [r for r in rows if r["created_at"] <= end_date]
        total = len(rows)
        key = (lambda r: r["id"]) if sort_by == "id" else (lambda r: r["created_at"])
        rows.sort(key=key, reverse=(order.lower() != "asc"))
        return [dict(r) for r in rows[skip:skip + limit]], total

    async def get_all_transactions(self, skip=0, limit=50, transaction_type=None,
                                   start_date=None, end_date=None, sort_by="id", order="asc"):
        """Return a unified, filtered feed of logs and transfers.

        Merges deposit/withdrawal entries from the transaction logs with
        fund transfer rows into a single normalized shape, applies type and
        date filters, then sorts and paginates the result.

        Args:
            skip: Number of rows to skip for pagination.
            limit: Maximum number of rows to return.
            transaction_type: Optional type filter (upper-cased); ``"ALL"``
                or falsy includes both logs and transfers.
            start_date: Optional inclusive lower bound on the timestamp.
            end_date: Optional inclusive upper bound on the timestamp.
            sort_by: ``"id"`` to sort by transaction id, otherwise by timestamp.
            order: ``"asc"`` for ascending, anything else for descending.

        Returns:
            List[Dict[str, Any]]: The paginated, normalized transaction feed.
        """
        if transaction_type:
            transaction_type = str(transaction_type).upper()
        combined: List[Dict[str, Any]] = []

        include_logs = (not transaction_type or transaction_type == "ALL"
                        or transaction_type in ("DEPOSIT", "WITHDRAW", "WITHDRAWAL"))
        include_transfers = (not transaction_type or transaction_type == "ALL"
                             or transaction_type == "TRANSFER")

        if include_logs:
            for r in self._store.transaction_logs:
                if r["transaction_type"] not in ("DEPOSIT", "WITHDRAW", "WITHDRAWAL"):
                    continue
                if transaction_type in ("DEPOSIT", "WITHDRAW", "WITHDRAWAL") and \
                        not self._type_matches(r["transaction_type"], transaction_type):
                    continue
                if start_date and r["created_at"] < start_date:
                    continue
                if end_date and r["created_at"] > end_date:
                    continue
                combined.append({
                    "transaction_id": r["id"],
                    "account_number": r["account_number"],
                    "from_account": None,
                    "to_account": None,
                    "amount": r["amount"],
                    "transaction_type": r["transaction_type"],
                    "mode": None,
                    "status": "SUCCESS",
                    "timestamp": r["created_at"],
                })

        if include_transfers:
            for r in self._store.fund_transfers.values():
                if start_date and r["created_at"] < start_date:
                    continue
                if end_date and r["created_at"] > end_date:
                    continue
                combined.append({
                    "transaction_id": r["id"],
                    "account_number": None,
                    "from_account": r["from_account"],
                    "to_account": r["to_account"],
                    "amount": r["transfer_amount"],
                    "transaction_type": "TRANSFER",
                    "mode": r["transfer_mode"],
                    "status": "SUCCESS",
                    "timestamp": r["created_at"],
                })

        key = (lambda r: r["transaction_id"]) if sort_by == "id" else (lambda r: r["timestamp"])
        combined.sort(key=key, reverse=(order.lower() != "asc"))
        return [dict(r) for r in combined[skip:skip + limit]]

    async def get_total_count(self, transaction_type=None, start_date=None, end_date=None):
        """Return the total number of transactions matching the given filters.

        Args:
            transaction_type: Optional type filter, as in
                :meth:`get_all_transactions`.
            start_date: Optional inclusive lower bound on the timestamp.
            end_date: Optional inclusive upper bound on the timestamp.

        Returns:
            int: The count of matching transactions across logs and transfers.
        """
        rows = await self.get_all_transactions(
            skip=0, limit=10**9, transaction_type=transaction_type,
            start_date=start_date, end_date=end_date,
        )
        return len(rows)

    async def delete_old_logs(self, days_to_keep=90):
        """Purge transaction logs older than a retention window.

        Args:
            days_to_keep: Number of trailing days of logs to retain; entries
                with ``created_at`` before the cutoff are dropped.

        Returns:
            bool: Always ``True`` once the purge completes.
        """
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        self._store.transaction_logs = [
            r for r in self._store.transaction_logs if r["created_at"] >= cutoff
        ]
        return True


class InMemoryTransferLimitRepository(TransferLimitRepositoryInterface):
    """In-memory repository for per-privilege transfer limit rules.

    Stores daily and per-transaction transfer limits keyed by privilege tier
    in the shared :class:`InMemoryStore`, and derives daily usage from the
    recorded fund transfers, mirroring the persistent repository contract.
    """

    def __init__(self, store: InMemoryStore):
        """Bind this repository to a shared in-memory store.

        Args:
            store (InMemoryStore): The process-lifetime store holding transfer
                limit rules and fund transfer data.
        """
        self._store = store

    async def get_transfer_rule(self, privilege):
        """Fetch the transfer limit rule for a privilege tier.

        Args:
            privilege: The privilege tier (case-insensitive) to look up.

        Returns:
            Optional[Dict[str, Any]]: A mapping with ``daily_limit``,
            ``transaction_limit`` (both floats), and ``created_at``, or
            ``None`` if no rule exists for the tier.
        """
        row = self._store.transfer_limits.get(str(privilege).upper())
        if not row:
            return None
        return {
            "daily_limit": float(row["daily_limit"]),
            "transaction_limit": float(row["per_transaction_limit"]),
            "created_at": row["created_at"],
        }

    async def create_transfer_rule(self, privilege, daily_limit, transaction_limit):
        """Create or update the transfer limit rule for a privilege tier.

        Upserts the rule keyed by upper-cased privilege, preserving the
        original ``created_at`` when the rule already exists.

        Args:
            privilege: The privilege tier (case-insensitive) to set limits for.
            daily_limit: The cumulative daily transfer cap (coerced to Decimal).
            transaction_limit: The per-transaction cap (coerced to Decimal).

        Returns:
            bool: Always ``True`` once the rule is stored.
        """
        key = str(privilege).upper()
        now = datetime.utcnow()
        existing = self._store.transfer_limits.get(key)
        self._store.transfer_limits[key] = {
            "privilege": key,
            "daily_limit": _as_decimal(daily_limit),
            "per_transaction_limit": _as_decimal(transaction_limit),
            "created_at": existing["created_at"] if existing else now,
            "updated_at": now,
        }
        return True

    async def get_daily_used_amount(self, account_number, date=None):
        """Sum the amount an account has sent as transfers on a given day.

        Args:
            account_number: The sending account to total transfers for.
            date: The calendar date to total; defaults to today's UTC date.

        Returns:
            Decimal: The total transferred amount for that day.

        Raises:
            DatabaseException: If the daily total cannot be computed.
        """
        try:
            if date is None:
                date = datetime.utcnow().date()
            total = Decimal("0")
            for r in self._store.fund_transfers.values():
                if r["from_account"] == account_number and r["created_at"].date() == date:
                    total += _as_decimal(r["transfer_amount"])
            logger.info(f"Daily used amount for account {account_number}: ₹{total}")
            return total
        except Exception as e:
            logger.error(f"Error getting daily used amount: {str(e)}")
            raise DatabaseException("Failed to read daily used amount")

    async def get_daily_transaction_count(self, account_number, date=None):
        """Count the transfers an account has sent on a given day.

        Args:
            account_number: The sending account to count transfers for.
            date: The calendar date to count; defaults to today's UTC date.

        Returns:
            int: The number of transfers sent that day.

        Raises:
            DatabaseException: If the daily count cannot be computed.
        """
        try:
            if date is None:
                date = datetime.utcnow().date()
            count = sum(
                1 for r in self._store.fund_transfers.values()
                if r["from_account"] == account_number and r["created_at"].date() == date
            )
            logger.info(f"Daily transaction count for account {account_number}: {count}")
            return count
        except Exception as e:
            logger.error(f"Error getting daily transaction count: {str(e)}")
            raise DatabaseException("Failed to read daily transaction count")


class InMemoryIdempotencyRepository(IdempotencyRepositoryInterface):
    """In-memory repository enforcing idempotency of money operations.

    Tracks idempotency keys and their lifecycle (IN_PROGRESS then COMPLETED)
    in the shared :class:`InMemoryStore`, allowing a request that carries an
    already-seen key to be safely replayed instead of executed twice. Mirrors
    the persistent idempotency repository contract.
    """

    def __init__(self, store: InMemoryStore):
        """Bind this repository to a shared in-memory store.

        Args:
            store (InMemoryStore): The process-lifetime store holding
                idempotency records.
        """
        self._store = store

    async def reserve(self, idempotency_key, operation):
        """Atomically claim an idempotency key for a new operation.

        If the key is unseen, it is recorded as ``IN_PROGRESS`` and the claim
        succeeds; if it already exists (in progress or completed), the claim
        fails so the caller must not execute the operation again.

        Args:
            idempotency_key: The client-supplied key uniquely identifying the
                operation.
            operation: A label describing the operation being reserved.

        Returns:
            bool: ``True`` if the key was newly claimed, ``False`` if it was
            already reserved.

        Raises:
            DatabaseException: If the reservation cannot be recorded.
        """
        try:
            if idempotency_key in self._store.idempotency:
                return False
            now = datetime.utcnow()
            self._store.idempotency[idempotency_key] = {
                "idempotency_key": idempotency_key,
                "operation": operation,
                "status": "IN_PROGRESS",
                "response_json": None,
                "created_at": now,
                "updated_at": now,
            }
            return True
        except Exception as e:
            logger.error(f"❌ Idempotency reserve failed for {idempotency_key}: {e}")
            raise DatabaseException("Failed to reserve idempotency key")

    async def get_completed_response(self, idempotency_key):
        """Return the stored result for a completed key, for safe replay.

        Used after a failed :meth:`reserve` to detect that the operation has
        already finished and to hand back its original response instead of
        re-executing it.

        Args:
            idempotency_key: The key whose completed response to fetch.

        Returns:
            Optional[Any]: The deserialized stored response if the key exists
            and is ``COMPLETED`` with a saved payload; otherwise ``None``
            (including on lookup error).
        """
        try:
            row = self._store.idempotency.get(idempotency_key)
            if row and row["status"] == "COMPLETED" and row["response_json"]:
                return json.loads(row["response_json"])
            return None
        except Exception as e:
            logger.error(f"❌ Idempotency lookup failed for {idempotency_key}: {e}")
            return None

    async def complete(self, idempotency_key, response):
        """Finalize a reserved key by storing its response for replay.

        Serializes the response to JSON and marks the key ``COMPLETED`` so
        subsequent requests with the same key can replay it via
        :meth:`get_completed_response`. A no-op if the key was never reserved.

        Args:
            idempotency_key: The reserved key to finalize.
            response: The operation result to serialize and store.
        """
        try:
            row = self._store.idempotency.get(idempotency_key)
            if row is None:
                return
            row["response_json"] = json.dumps(response, default=str)
            row["status"] = "COMPLETED"
            row["updated_at"] = datetime.utcnow()
        except Exception as e:
            logger.error(f"❌ Failed to complete idempotency key {idempotency_key}: {e}")

    async def release(self, idempotency_key):
        """Free an in-progress reservation so the key can be retried.

        Removes the record only if it is still ``IN_PROGRESS`` (e.g. the
        operation failed before completing), leaving completed keys intact.
        A no-op for unknown or already-completed keys.

        Args:
            idempotency_key: The reserved key to release.
        """
        try:
            row = self._store.idempotency.get(idempotency_key)
            if row and row["status"] == "IN_PROGRESS":
                del self._store.idempotency[idempotency_key]
        except Exception as e:
            logger.error(f"❌ Failed to release idempotency key {idempotency_key}: {e}")
