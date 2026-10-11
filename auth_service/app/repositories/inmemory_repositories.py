"""
In-memory repository implementations (DATABASE_PROVIDER=inmemory).

Pure Python dicts/lists — no SQL engine, no external driver. Data lives only for
the process lifetime. Implements the same AuthTokenRepository / AuthAuditRepository
contracts as the SQL implementations, so services never know the difference.
"""

import uuid
import logging
from datetime import datetime, UTC
from typing import Optional, List, Dict

from app.models.auth_models import AuthToken, AuthAuditLog
from app.exceptions.auth_exceptions import DatabaseException
from .auth_token_repo import AuthTokenRepository
from .auth_audit_repo import AuthAuditRepository


logger = logging.getLogger(__name__)


class InMemoryStore:
    """Process-lifetime store shared by the in-memory auth repositories."""

    def __init__(self):
        """Initialize empty in-memory token and audit collections."""
        self.tokens: Dict[str, AuthToken] = {}   # keyed by token id (UUID str)
        self.audit: List[AuthAuditLog] = []


def _to_int_user_id(user_id) -> int:
    """Coerce a user identifier to int.

    Args:
        user_id: User identifier of any type convertible to int.

    Returns:
        The user id as an int.

    Raises:
        DatabaseException: If the value cannot be converted to an int.
    """
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise DatabaseException(f"Invalid user_id format: {user_id}")


class InMemoryAuthTokenRepository(AuthTokenRepository):
    """In-memory implementation of the auth token repository contract.

    Stores AuthToken records in a shared InMemoryStore for the process lifetime.
    """

    def __init__(self, store: InMemoryStore):
        """Bind this repository to a shared in-memory store.

        Args:
            store: The InMemoryStore holding the token/audit collections.
        """
        self._store = store

    async def create_token(self, user_id, login_id, token_jti, issued_at, expires_at):
        """Create and store a new token record.

        Args:
            user_id: Owner user identifier (coerced to int).
            login_id: Login identifier the token was issued for.
            token_jti: JWT ID (unique token identifier).
            issued_at: Token issuance timestamp.
            expires_at: Token expiry timestamp.

        Returns:
            The generated token ID (UUID string).
        """
        token_id = str(uuid.uuid4())
        token = AuthToken(
            id=token_id,
            user_id=_to_int_user_id(user_id),
            login_id=login_id,
            token_jti=token_jti,
            issued_at=issued_at,
            expires_at=expires_at,
            is_revoked=False,
        )
        self._store.tokens[token_id] = token
        logger.info(f"Created auth token {token_id} for user {user_id}")
        return token_id

    async def get_token_by_jti(self, token_jti):
        """Find a token by its JWT ID.

        Args:
            token_jti: The JWT ID to look up.

        Returns:
            The matching AuthToken, or None if not found.
        """
        for token in self._store.tokens.values():
            if token.token_jti == token_jti:
                return token
        return None

    async def get_token_by_id(self, token_id):
        """Find a token by its token ID.

        Args:
            token_id: The token ID (UUID string) to look up.

        Returns:
            The matching AuthToken, or None if not found.
        """
        return self._store.tokens.get(token_id)

    async def revoke_token(self, token_jti):
        """Mark any token(s) with the given JWT ID as revoked.

        Args:
            token_jti: The JWT ID of the token to revoke.

        Returns:
            True (always) once the operation completes.
        """
        for token in self._store.tokens.values():
            if token.token_jti == token_jti:
                token.is_revoked = True
        logger.info(f"Revoked token {token_jti}")
        return True

    async def is_token_revoked(self, token_jti):
        """Report whether a token is revoked.

        Args:
            token_jti: The JWT ID to check.

        Returns:
            True if a matching token is revoked; False if active or unknown.
        """
        for token in self._store.tokens.values():
            if token.token_jti == token_jti:
                return token.is_revoked is True
        return False

    async def get_user_tokens(self, user_id):
        """Return all tokens owned by a user, newest first.

        Args:
            user_id: Owner user identifier (coerced to int).

        Returns:
            A list of AuthToken ordered by issued_at descending.
        """
        uid = _to_int_user_id(user_id)
        tokens = [t for t in self._store.tokens.values() if t.user_id == uid]
        tokens.sort(key=lambda t: t.issued_at, reverse=True)
        return tokens


class InMemoryAuthAuditRepository(AuthAuditRepository):
    """In-memory implementation of the auth audit log repository contract.

    Appends AuthAuditLog entries to a shared InMemoryStore for the process
    lifetime.
    """

    def __init__(self, store: InMemoryStore):
        """Bind this repository to a shared in-memory store.

        Args:
            store: The InMemoryStore holding the token/audit collections.
        """
        self._store = store

    async def log_login_attempt(
        self, login_id, user_id, action, reason=None, ip_address=None, user_agent=None
    ):
        """Append an audit log entry for a login attempt.

        Args:
            login_id: Login identifier the attempt was made for.
            user_id: Associated user id (coerced to int; invalid values stored
                as None).
            action: Audit action, e.g. LOGIN_SUCCESS or LOGIN_FAILURE.
            reason: Optional human-readable reason (typically for failures).
            ip_address: Optional client IP address.
            user_agent: Optional client user agent string.

        Returns:
            The generated audit log ID (UUID string).
        """
        log_id = str(uuid.uuid4())
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid user_id format for audit: {user_id}")
                user_id_int = None
        entry = AuthAuditLog(
            id=log_id,
            login_id=login_id,
            user_id=user_id_int,
            action=action,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(UTC),
        )
        self._store.audit.append(entry)
        logger.info(f"Audit: {action} for {login_id} (user_id: {user_id}) from {ip_address}")
        return log_id

    async def log_login_success(self, login_id, user_id, ip_address=None, user_agent=None):
        """Record a successful login as a LOGIN_SUCCESS audit entry.

        Args:
            login_id: Login identifier that authenticated.
            user_id: Associated user id.
            ip_address: Optional client IP address.
            user_agent: Optional client user agent string.

        Returns:
            The generated audit log ID (UUID string).
        """
        return await self.log_login_attempt(
            login_id=login_id, user_id=user_id, action="LOGIN_SUCCESS",
            reason=None, ip_address=ip_address, user_agent=user_agent,
        )

    async def log_login_failure(self, login_id, user_id, reason, ip_address=None, user_agent=None):
        """Record a failed login as a LOGIN_FAILURE audit entry.

        Args:
            login_id: Login identifier that failed to authenticate.
            user_id: Associated user id, if known (may be None).
            reason: Human-readable failure reason.
            ip_address: Optional client IP address.
            user_agent: Optional client user agent string.

        Returns:
            The generated audit log ID (UUID string).
        """
        return await self.log_login_attempt(
            login_id=login_id, user_id=user_id, action="LOGIN_FAILURE",
            reason=reason, ip_address=ip_address, user_agent=user_agent,
        )

    async def get_audit_log(self, log_id):
        """Retrieve a single audit log entry by its ID.

        Args:
            log_id: The audit log ID (UUID string).

        Returns:
            The matching AuthAuditLog, or None if not found.
        """
        for entry in self._store.audit:
            if entry.id == log_id:
                return entry
        return None

    async def get_user_audit_logs(self, user_id, limit=100):
        """Return recent audit logs for a user, newest first.

        Args:
            user_id: User identifier (coerced to int when possible).
            limit: Maximum number of entries to return.

        Returns:
            A list of AuthAuditLog ordered by created_at descending.
        """
        uid = None
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            uid = user_id
        rows = [e for e in self._store.audit if e.user_id == uid]
        rows.sort(key=lambda e: e.created_at, reverse=True)
        return rows[:limit]

    async def get_login_id_audit_logs(self, login_id, limit=100):
        """Return recent audit logs for a login id, newest first.

        Args:
            login_id: Login identifier to filter by.
            limit: Maximum number of entries to return.

        Returns:
            A list of AuthAuditLog ordered by created_at descending.
        """
        rows = [e for e in self._store.audit if e.login_id == login_id]
        rows.sort(key=lambda e: e.created_at, reverse=True)
        return rows[:limit]
