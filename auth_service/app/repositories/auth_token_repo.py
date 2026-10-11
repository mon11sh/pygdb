"""
Authentication Token Repository — provider-agnostic data-access CONTRACT.

This is the stable public interface the services (and the test-suite) depend on.
It contains no SQL and no database driver: every method simply forwards to the
concrete repository owned by the ACTIVE database provider (chosen at runtime from
settings.DATABASE_PROVIDER).

Concrete implementations live in:
  - repositories.sqlalchemy_repositories.SqlAlchemyAuthTokenRepository
        -> sqlite / mysql / postgres / supabase
  - repositories.inmemory_repositories.InMemoryAuthTokenRepository
        -> inmemory

The module path, class name, static method signatures and return shapes are kept
UNCHANGED so `app.services` and tests that import / patch
`AuthTokenRepository.<method>` keep working exactly as before.

Author: GDB Architecture Team
"""

import logging
from abc import ABC
from datetime import datetime
from typing import Optional

from app.models.auth_models import AuthToken


logger = logging.getLogger(__name__)


def _repo():
    """Return the active AuthTokenRepository implementation from the provider.

    Imported lazily so selecting a non-SQL provider (or merely importing this
    module) never loads SQLAlchemy.
    """
    from app.database.connection import get_provider
    return get_provider().token_repository()


class AuthTokenRepository(ABC):
    """Abstract, database-agnostic repository for auth_tokens.

    The bodies below route to the active provider's concrete implementation, so
    the rest of the app depends only on this contract and never on a specific
    database. Concrete subclasses (SqlAlchemy/InMemory) override each method.
    """

    @staticmethod
    async def create_token(
        user_id: str,
        login_id: str,
        token_jti: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> str:
        """Create a new token record. Returns the token ID (UUID string)."""
        return await _repo().create_token(
            user_id, login_id, token_jti, issued_at, expires_at
        )

    @staticmethod
    async def get_token_by_jti(token_jti: str) -> Optional[AuthToken]:
        """Retrieve a token by JWT ID. Returns an AuthToken or None."""
        return await _repo().get_token_by_jti(token_jti)

    @staticmethod
    async def get_token_by_id(token_id: str) -> Optional[AuthToken]:
        """Retrieve a token by token ID. Returns an AuthToken or None."""
        return await _repo().get_token_by_id(token_id)

    @staticmethod
    async def revoke_token(token_jti: str) -> bool:
        """Revoke a token. Returns True on success."""
        return await _repo().revoke_token(token_jti)

    @staticmethod
    async def is_token_revoked(token_jti: str) -> bool:
        """Return True if the token is revoked (False if unknown/active)."""
        return await _repo().is_token_revoked(token_jti)

    @staticmethod
    async def get_user_tokens(user_id: str) -> list:
        """Return all tokens for a user as a list of AuthToken (newest first)."""
        return await _repo().get_user_tokens(user_id)
