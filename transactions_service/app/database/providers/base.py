"""
DatabaseProvider — the abstraction the rest of the app depends on.

A provider owns the storage backend (asyncpg pool, SQLAlchemy engine/session, or
an in-memory store) and hands out the four transactions repositories. The
application never knows which provider is active; it only asks the provider for
repositories.
"""

from abc import ABC, abstractmethod

from ...repositories.transaction_repository import TransactionRepositoryInterface
from ...repositories.transaction_log_repository import TransactionLogRepositoryInterface
from ...repositories.transfer_limit_repository import TransferLimitRepositoryInterface
from ...repositories.idempotency_repository import IdempotencyRepositoryInterface


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
    def transaction_repository(self) -> TransactionRepositoryInterface:
        """Return the active TransactionRepository (fund_transfers)."""

    @abstractmethod
    def transaction_log_repository(self) -> TransactionLogRepositoryInterface:
        """Return the active TransactionLogRepository."""

    @abstractmethod
    def transfer_limit_repository(self) -> TransferLimitRepositoryInterface:
        """Return the active TransferLimitRepository."""

    @abstractmethod
    def idempotency_repository(self) -> IdempotencyRepositoryInterface:
        """Return the active IdempotencyRepository."""
