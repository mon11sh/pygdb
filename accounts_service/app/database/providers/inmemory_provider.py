"""In-memory provider (DATABASE_PROVIDER=inmemory) — no server, no persistence."""

import logging

from .base import DatabaseProvider
from app.database.seed_data import seed_default_accounts
from app.repositories.inmemory_repositories import (
    InMemoryStore,
    InMemoryAccountRepository,
)

logger = logging.getLogger(__name__)


class InMemoryProvider(DatabaseProvider):
    """DatabaseProvider backed by a process-local store — no server, no persistence.

    Used for tests and quick local runs; it owns an ``InMemoryStore`` and the
    ``InMemoryAccountRepository`` built on top of it. All data is lost when the
    process exits or the provider is disposed.
    """

    name = "inmemory"

    def __init__(self):
        """Create the in-memory store and its account repository."""
        self._store = InMemoryStore()
        self._account_repo = InMemoryAccountRepository(self._store)

    async def init(self) -> None:
        """Seed the default accounts if the store is empty (no schema to create)."""
        logger.info("🗃️  Database provider: IN-MEMORY (data is not persisted).")
        if not await self._account_repo.get_all_accounts():
            count = await seed_default_accounts(self._account_repo)
            logger.info(f"🌱 Seeded {count} default accounts (in-memory).")

    async def dispose(self) -> None:
        """Clear the in-memory store, releasing all held data."""
        self._store.clear()

    def account_repository(self):
        """Return the in-memory AccountRepository."""
        return self._account_repo
