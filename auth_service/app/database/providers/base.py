"""
DatabaseProvider — the abstraction the rest of the app depends on.

A provider owns the storage backend (SQLAlchemy engine/session, or an in-memory
store) and hands out repositories. The application never knows which provider is
active; it only asks the provider for repositories.
"""

from abc import ABC, abstractmethod

from ...repositories.auth_token_repo import AuthTokenRepository
from ...repositories.auth_audit_repo import AuthAuditRepository


class DatabaseProvider(ABC):
    """Abstract database provider."""

    name: str = "unknown"

    @abstractmethod
    async def init(self) -> None:
        """Provision schema (if any). Called at startup."""

    @abstractmethod
    async def dispose(self) -> None:
        """Release resources. Called at shutdown."""

    @abstractmethod
    def token_repository(self) -> AuthTokenRepository:
        """Return the active AuthTokenRepository implementation."""

    @abstractmethod
    def audit_repository(self) -> AuthAuditRepository:
        """Return the active AuthAuditRepository implementation."""
