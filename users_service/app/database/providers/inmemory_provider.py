"""In-memory provider (DATABASE_PROVIDER=inmemory) — no server, no persistence."""

import logging

from .base import DatabaseProvider
from ..seed_data import seed_default_users
from ...repositories.inmemory_repositories import (
    InMemoryStore,
    InMemoryUserRepository,
    InMemoryAuditRepository,
)

logger = logging.getLogger(__name__)


class InMemoryProvider(DatabaseProvider):
    """DatabaseProvider backed by process-lifetime in-memory stores (no server)."""

    name = "inmemory"

    def __init__(self):
        """Create the in-memory store and its user/audit repositories."""
        self._store = InMemoryStore()
        self._user_repo = InMemoryUserRepository(self._store)
        self._audit_repo = InMemoryAuditRepository(self._store)

    async def init(self) -> None:
        """Seed default users on first startup if the store is empty."""
        logger.info("🗃️  Database provider: IN-MEMORY (data is not persisted).")
        if not await self._user_repo.get_all_users():
            count = await seed_default_users(self._user_repo)
            logger.info(f"🌱 Seeded {count} default users (in-memory).")

    async def dispose(self) -> None:
        """Clear the in-memory user and audit collections."""
        self._store.users.clear()
        self._store.audit.clear()

    def user_repository(self):
        """Return the in-memory UserRepository."""
        return self._user_repo

    def audit_repository(self):
        """Return the in-memory AuditRepository."""
        return self._audit_repo
