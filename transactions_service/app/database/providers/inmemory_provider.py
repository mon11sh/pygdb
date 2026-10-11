"""In-memory provider (DATABASE_PROVIDER=inmemory) — no server, no persistence."""

import logging

from .base import DatabaseProvider
from ..seed_data import seed_transfer_limits, seed_sample_logs
from ...repositories.inmemory_repositories import (
    InMemoryStore,
    InMemoryTransactionRepository,
    InMemoryTransactionLogRepository,
    InMemoryTransferLimitRepository,
    InMemoryIdempotencyRepository,
)

logger = logging.getLogger(__name__)


class InMemoryProvider(DatabaseProvider):
    """Database provider backed by in-process dictionaries.

    Abstracts a fully in-memory store (no database server, no persistence),
    intended for tests and local runs. Wires up the four in-memory repositories
    over a shared :class:`InMemoryStore`.
    """

    name = "inmemory"

    def __init__(self):
        """Create the shared in-memory store and its four repositories."""
        self._store = InMemoryStore()
        self._txn_repo = InMemoryTransactionRepository(self._store)
        self._log_repo = InMemoryTransactionLogRepository(self._store)
        self._limit_repo = InMemoryTransferLimitRepository(self._store)
        self._idem_repo = InMemoryIdempotencyRepository(self._store)

    async def init(self) -> None:
        """Seed default transfer limits and sample logs if the store is empty."""
        logger.info("🗃️  Database provider: IN-MEMORY (data is not persisted).")
        if not self._store.transfer_limits:
            count = await seed_transfer_limits(self._limit_repo)
            logger.info(f"🌱 Seeded {count} transfer limits (in-memory).")
        if not self._store.transaction_logs:
            await seed_sample_logs(self._txn_repo, self._log_repo)
            logger.info("🌱 Seeded sample transaction logs (in-memory).")

    async def dispose(self) -> None:
        """Clear every in-memory collection, releasing all stored data."""
        self._store.fund_transfers.clear()
        self._store.transaction_logs.clear()
        self._store.transfer_limits.clear()
        self._store.idempotency.clear()

    def transaction_repository(self):
        """Return the in-memory transaction (fund_transfers) repository."""
        return self._txn_repo

    def transaction_log_repository(self):
        """Return the in-memory transaction log repository."""
        return self._log_repo

    def transfer_limit_repository(self):
        """Return the in-memory transfer limit repository."""
        return self._limit_repo

    def idempotency_repository(self):
        """Return the in-memory idempotency repository."""
        return self._idem_repo
