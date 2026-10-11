"""
User Repository — provider-agnostic data-access CONTRACT.

This is the interface every database provider implements. It contains no SQL
and no database driver, so services and dependency-injection depend only on this
abstraction and never on a concrete database.

Concrete implementations (selected by the database provider factory based on
DATABASE_PROVIDER) live in:
  - sqlalchemy_user_repository.SqlAlchemyUserRepository  → sqlite / mysql / postgres / supabase
  - inmemory_user_repository.InMemoryUserRepository       → inmemory

The public method signatures and return shapes below are the exact contract the
existing services already rely on (dicts, password included only where noted),
so no service or route code changes.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class UserRepository(ABC):
    """Abstract, database-agnostic repository for users."""

    @abstractmethod
    async def create_user(
        self, username: str, login_id: str, password: str, role: str = "MANAGER"
    ) -> Dict[str, Any]:
        """Create a user (password is hashed by the implementation). Returns the
        created user WITHOUT the password field."""

    @abstractmethod
    async def get_user_by_login_id(self, login_id: str) -> Optional[Dict[str, Any]]:
        """Return the user (INCLUDING the password hash) or None."""

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return the user (INCLUDING the password hash) or None."""

    @abstractmethod
    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update the given fields (password re-hashed if provided). Returns the
        updated user INCLUDING the password hash, or None."""

    @abstractmethod
    async def inactivate_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Set is_active=False. Returns the user WITHOUT the password field."""

    @abstractmethod
    async def activate_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Set is_active=True. Returns the user WITHOUT the password field."""

    @abstractmethod
    async def count_active_admins(self) -> int:
        """Number of currently active ADMIN users."""

    @abstractmethod
    async def get_all_users(self) -> List[Dict[str, Any]]:
        """All users (WITHOUT password), newest first."""
