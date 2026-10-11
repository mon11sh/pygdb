"""
DatabaseProvider — the abstraction the rest of the app depends on.

A provider owns the storage backend (SQLAlchemy engine/session, or an in-memory
store) and hands out repositories. The application never knows which provider is
active; it only asks the provider for repositories.
"""

from abc import ABC, abstractmethod

from ...repositories.user_repository import UserRepository
from ...repositories.audit_repository import AuditRepository


class DatabaseProvider(ABC):
    """Abstract database provider."""

    name: str = "unknown"

    @abstractmethod
    async def init(self) -> None:
        """Provision schema (if any) and seed initial data. Called at startup."""

    @abstractmethod
    async def dispose(self) -> None:
        """Release resources. Called at shutdown."""

    @abstractmethod
    def user_repository(self) -> UserRepository:
        """Return the active UserRepository implementation."""

    @abstractmethod
    def audit_repository(self) -> AuditRepository:
        """Return the active AuditRepository implementation."""
