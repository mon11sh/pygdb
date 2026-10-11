"""
Asyncpg provider — serves postgres / supabase (supabase *is* PostgreSQL).

Preserves the original asyncpg experience byte-for-byte: it bootstraps the shared
DatabaseConnection pool (best-effort CREATE DATABASE + schema + seed of
transfer_limits and sample logs) and hands out the raw-asyncpg repositories that
talk to that pool. Keeping this path unchanged means the existing service/repo
tests (which patch `app.repositories.*.database`) keep working.
"""

import logging

from .base import DatabaseProvider

logger = logging.getLogger(__name__)


class AsyncpgProvider(DatabaseProvider):
    """Database provider for the raw-asyncpg PostgreSQL path.

    Serves the ``postgres`` and ``supabase`` backends (both are PostgreSQL). It
    bootstraps and hands out the raw-asyncpg repositories that talk to the shared
    :class:`DatabaseConnection` pool, preserving the original asyncpg behaviour.
    """

    def __init__(self, name: str = "postgres"):
        """Instantiate the stateless asyncpg repositories.

        Args:
            name: Provider label (``"postgres"`` or ``"supabase"``).
        """
        self.name = name
        # Stateless repos that talk to the shared DatabaseConnection pool via the
        # module-global `database` symbol (patchable in tests).
        from ...repositories.transaction_repository import TransactionRepository
        from ...repositories.transaction_log_repository import TransactionLogRepository
        from ...repositories.transfer_limit_repository import TransferLimitRepository
        from ...repositories.idempotency_repository import IdempotencyRepository

        self._txn_repo = TransactionRepository()
        self._log_repo = TransactionLogRepository()
        self._limit_repo = TransferLimitRepository()
        self._idem_repo = IdempotencyRepository()

    async def init(self) -> None:
        """Bootstrap the shared asyncpg pool (schema + seed) at startup."""
        logger.info(f"🗄️  Database provider: asyncpg '{self.name}' (PostgreSQL).")
        from ..db import DatabaseConnection
        await DatabaseConnection.bootstrap_asyncpg()

    async def dispose(self) -> None:
        """Close the shared asyncpg connection pool at shutdown."""
        from ..db import DatabaseConnection
        await DatabaseConnection.close_pool()

    def transaction_repository(self):
        """Return the asyncpg transaction (fund_transfers) repository."""
        return self._txn_repo

    def transaction_log_repository(self):
        """Return the asyncpg transaction log repository."""
        return self._log_repo

    def transfer_limit_repository(self):
        """Return the asyncpg transfer limit repository."""
        return self._limit_repo

    def idempotency_repository(self):
        """Return the asyncpg idempotency repository."""
        return self._idem_repo
