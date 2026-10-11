"""In-memory provider (DATABASE_PROVIDER=inmemory) — no server, no persistence."""

import logging

from .base import DatabaseProvider
from ...repositories.inmemory_repositories import (
    InMemoryStore,
    InMemoryAuthTokenRepository,
    InMemoryAuthAuditRepository,
)

logger = logging.getLogger(__name__)


class InMemoryProvider(DatabaseProvider):
    """Volatile provider backed by in-process dictionaries.

    Selected via ``DATABASE_PROVIDER=inmemory``. It requires no external
    database server and keeps all data in a shared :class:`InMemoryStore`, so
    everything is lost when the process exits. Intended for tests and local
    development.
    """

    name = "inmemory"

    def __init__(self):
        """Create the backing store and wire up the in-memory repositories."""
        self._store = InMemoryStore()
        self._token_repo = InMemoryAuthTokenRepository(self._store)
        self._audit_repo = InMemoryAuthAuditRepository(self._store)

    async def init(self) -> None:
        """Log that the volatile in-memory backend is active. No schema to build."""
        logger.info("🗃️  Database provider: IN-MEMORY (data is not persisted).")

    async def dispose(self) -> None:
        """Clear all in-memory token and audit data held by the store."""
        self._store.tokens.clear()
        self._store.audit.clear()

    def token_repository(self):
        """Return the in-memory AuthTokenRepository implementation."""
        return self._token_repo

    def audit_repository(self):
        """Return the in-memory AuthAuditRepository implementation."""
        return self._audit_repo
