"""
SQLAlchemy repository implementations — one code path that runs on every SQL
provider: sqlite / mysql / postgres / supabase. The active engine/session is
supplied by the SQLAlchemy database provider; the SQL below is dialect-neutral
(no Postgres-only $n / RETURNING / gen_random_uuid / ON CONFLICT / INET).

Portability notes vs. the original asyncpg code:
  - UUID ids are generated in Python (uuid4 string) instead of gen_random_uuid().
  - RETURNING is not used; the id we return is the one we generated.
  - asyncpg.UniqueViolationError -> SQLAlchemy IntegrityError.

Imported ONLY when a SQL provider is selected, so non-SQL setups never load
SQLAlchemy.
"""

import uuid
import logging
from datetime import timezone
from typing import Optional, List

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError


def _naive_utc(dt):
    """Drop tzinfo so timezone-aware datetimes fit the TIMESTAMP WITHOUT TIME ZONE
    columns (Postgres/asyncpg reject aware values there). None passes through."""
    if dt is not None and getattr(dt, "tzinfo", None) is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

from app.models.auth_models import AuthToken, AuthAuditLog
from app.exceptions.auth_exceptions import DatabaseException
from .auth_token_repo import AuthTokenRepository
from .auth_audit_repo import AuthAuditRepository
from ..database.orm_models import (
    AuthTokenORM,
    AuthAuditLogORM,
    token_to_model,
    audit_to_model,
)


logger = logging.getLogger(__name__)


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


class SqlAlchemyAuthTokenRepository(AuthTokenRepository):
    """SQLAlchemy implementation of the auth token repository contract.

    Runs on any configured SQL provider (sqlite/mysql/postgres/supabase) using
    dialect-neutral SQL. Each method opens a session from the bound
    session_factory and maps ORM rows back to AuthToken domain models.
    """

    def __init__(self, session_factory):
        """Store the async session factory bound to the active engine.

        Args:
            session_factory: async_sessionmaker bound to the active engine.
        """
        # session_factory: async_sessionmaker bound to the active engine.
        self._session_factory = session_factory

    async def create_token(self, user_id, login_id, token_jti, issued_at, expires_at):
        """Insert a new token row.

        Args:
            user_id: Owner user identifier (coerced to int).
            login_id: Login identifier the token was issued for.
            token_jti: JWT ID (unique token identifier).
            issued_at: Token issuance timestamp (stored as naive UTC).
            expires_at: Token expiry timestamp (stored as naive UTC).

        Returns:
            The generated token ID (UUID string).

        Raises:
            DatabaseException: On integrity violation or any insert failure.
        """
        token_id = str(uuid.uuid4())
        user_id_int = _to_int_user_id(user_id)
        try:
            async with self._session_factory() as session:
                session.add(AuthTokenORM(
                    id=token_id,
                    user_id=user_id_int,
                    login_id=login_id,
                    token_jti=token_jti,
                    issued_at=_naive_utc(issued_at),
                    expires_at=_naive_utc(expires_at),
                    is_revoked=False,
                ))
                await session.commit()
            logger.info(f"Created auth token {token_id} for user {user_id}")
            return token_id
        except IntegrityError as e:
            logger.error(f"Failed to create token (integrity): {str(e)}")
            raise DatabaseException(f"Failed to create token: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create token: {str(e)}")
            raise DatabaseException(f"Failed to create token: {str(e)}")

    async def get_token_by_jti(self, token_jti):
        """Fetch a token by its JWT ID.

        Args:
            token_jti: The JWT ID to look up.

        Returns:
            The matching AuthToken, or None if not found.

        Raises:
            DatabaseException: On any query failure.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AuthTokenORM).where(AuthTokenORM.token_jti == token_jti)
                )
                row = result.scalar_one_or_none()
                return token_to_model(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get token by JTI: {str(e)}")
            raise DatabaseException(f"Failed to get token: {str(e)}")

    async def get_token_by_id(self, token_id):
        """Fetch a token by its primary key ID.

        Args:
            token_id: The token primary key (UUID string) to look up.

        Returns:
            The matching AuthToken, or None if not found.

        Raises:
            DatabaseException: On any query failure.
        """
        try:
            async with self._session_factory() as session:
                row = await session.get(AuthTokenORM, token_id)
                return token_to_model(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get token by ID: {str(e)}")
            raise DatabaseException(f"Failed to get token: {str(e)}")

    async def revoke_token(self, token_jti):
        """Mark the token with the given JWT ID as revoked.

        Args:
            token_jti: The JWT ID of the token to revoke.

        Returns:
            True once the revocation has been committed.

        Raises:
            DatabaseException: On any update failure.
        """
        try:
            async with self._session_factory() as session:
                await session.execute(
                    update(AuthTokenORM)
                    .where(AuthTokenORM.token_jti == token_jti)
                    .values(is_revoked=True)
                )
                await session.commit()
            logger.info(f"Revoked token {token_jti}")
            return True
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            raise DatabaseException(f"Failed to revoke token: {str(e)}")

    async def is_token_revoked(self, token_jti):
        """Report whether the token with the given JWT ID is revoked.

        Args:
            token_jti: The JWT ID of the token to check.

        Returns:
            True if the token exists and is flagged revoked; False otherwise
            (including when no matching token exists).

        Raises:
            DatabaseException: On any query failure.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AuthTokenORM.is_revoked).where(
                        AuthTokenORM.token_jti == token_jti
                    )
                )
                value = result.scalar_one_or_none()
                return value is True
        except Exception as e:
            logger.error(f"Failed to check if token is revoked: {str(e)}")
            raise DatabaseException(f"Failed to check token status: {str(e)}")

    async def get_user_tokens(self, user_id):
        """List all tokens issued to a user, newest first.

        Args:
            user_id: Owner user identifier (coerced to int).

        Returns:
            A list of AuthToken models ordered by issuance time descending.

        Raises:
            DatabaseException: On invalid user_id or any query failure.
        """
        try:
            uid = _to_int_user_id(user_id)
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AuthTokenORM)
                    .where(AuthTokenORM.user_id == uid)
                    .order_by(AuthTokenORM.issued_at.desc())
                )
                return [token_to_model(r) for r in result.scalars().all()]
        except DatabaseException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user tokens: {str(e)}")
            raise DatabaseException(f"Failed to get tokens: {str(e)}")


class SqlAlchemyAuthAuditRepository(AuthAuditRepository):
    """SQLAlchemy implementation of the auth audit-log repository contract.

    Persists login attempt records (success/failure) and exposes queries over
    the audit trail. Runs on any configured SQL provider using dialect-neutral
    SQL, opening a session from the bound session_factory per operation.
    """

    def __init__(self, session_factory):
        """Store the async session factory bound to the active engine.

        Args:
            session_factory: async_sessionmaker bound to the active engine.
        """
        self._session_factory = session_factory

    async def log_login_attempt(
        self, login_id, user_id, action, reason=None, ip_address=None, user_agent=None
    ):
        """Persist a single audit-log entry for a login attempt.

        A fresh UUID id is generated in Python. The user_id is best-effort
        coerced to int; an unconvertible value is logged as a warning and
        stored as NULL rather than failing the write.

        Args:
            login_id: Login identifier the attempt was made against.
            user_id: Resolved user identifier, or falsy/None if unknown.
            action: Audit action label (e.g. "LOGIN_SUCCESS", "LOGIN_FAILURE").
            reason: Optional human-readable reason (typically for failures).
            ip_address: Optional client IP address.
            user_agent: Optional client user-agent string.

        Returns:
            The generated audit-log ID (UUID string).

        Raises:
            DatabaseException: On any insert failure.
        """
        log_id = str(uuid.uuid4())
        user_id_int = None
        if user_id:
            try:
                user_id_int = int(user_id)
            except (ValueError, TypeError):
                logger.warning(f"Invalid user_id format for audit: {user_id}")
                user_id_int = None
        try:
            async with self._session_factory() as session:
                session.add(AuthAuditLogORM(
                    id=log_id,
                    login_id=login_id,
                    user_id=user_id_int,
                    action=action,
                    reason=reason,
                    ip_address=ip_address,
                    user_agent=user_agent,
                ))
                await session.commit()
            logger.info(f"Audit: {action} for {login_id} (user_id: {user_id}) from {ip_address}")
            return log_id
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            raise DatabaseException(f"Failed to create audit log: {str(e)}")

    async def log_login_success(self, login_id, user_id, ip_address=None, user_agent=None):
        """Record a successful login as a "LOGIN_SUCCESS" audit entry.

        Args:
            login_id: Login identifier that authenticated successfully.
            user_id: Resolved user identifier.
            ip_address: Optional client IP address.
            user_agent: Optional client user-agent string.

        Returns:
            The generated audit-log ID (UUID string).

        Raises:
            DatabaseException: On any insert failure.
        """
        return await self.log_login_attempt(
            login_id=login_id, user_id=user_id, action="LOGIN_SUCCESS",
            reason=None, ip_address=ip_address, user_agent=user_agent,
        )

    async def log_login_failure(self, login_id, user_id, reason, ip_address=None, user_agent=None):
        """Record a failed login as a "LOGIN_FAILURE" audit entry.

        Args:
            login_id: Login identifier that failed to authenticate.
            user_id: Resolved user identifier, or None if unknown.
            reason: Human-readable failure reason.
            ip_address: Optional client IP address.
            user_agent: Optional client user-agent string.

        Returns:
            The generated audit-log ID (UUID string).

        Raises:
            DatabaseException: On any insert failure.
        """
        return await self.log_login_attempt(
            login_id=login_id, user_id=user_id, action="LOGIN_FAILURE",
            reason=reason, ip_address=ip_address, user_agent=user_agent,
        )

    async def get_audit_log(self, log_id):
        """Fetch a single audit-log entry by its ID.

        Args:
            log_id: The audit-log primary key (UUID string) to look up.

        Returns:
            The matching AuthAuditLog, or None if not found.

        Raises:
            DatabaseException: On any query failure.
        """
        try:
            async with self._session_factory() as session:
                row = await session.get(AuthAuditLogORM, log_id)
                return audit_to_model(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get audit log: {str(e)}")
            raise DatabaseException(f"Failed to get audit log: {str(e)}")

    async def get_user_audit_logs(self, user_id, limit=100):
        """List audit-log entries for a user, newest first.

        The user_id is best-effort coerced to int; an unconvertible value
        becomes None, matching rows whose user_id is NULL.

        Args:
            user_id: User identifier to filter by.
            limit: Maximum number of entries to return (default 100).

        Returns:
            A list of AuthAuditLog models ordered by creation time descending.

        Raises:
            DatabaseException: On any query failure.
        """
        try:
            uid = int(user_id)
        except (ValueError, TypeError):
            uid = None
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AuthAuditLogORM)
                    .where(AuthAuditLogORM.user_id == uid)
                    .order_by(AuthAuditLogORM.created_at.desc())
                    .limit(limit)
                )
                return [audit_to_model(r) for r in result.scalars().all()]
        except Exception as e:
            logger.error(f"Failed to get user audit logs: {str(e)}")
            raise DatabaseException(f"Failed to get audit logs: {str(e)}")

    async def get_login_id_audit_logs(self, login_id, limit=100):
        """List audit-log entries for a login identifier, newest first.

        Args:
            login_id: Login identifier to filter by.
            limit: Maximum number of entries to return (default 100).

        Returns:
            A list of AuthAuditLog models ordered by creation time descending.

        Raises:
            DatabaseException: On any query failure.
        """
        try:
            async with self._session_factory() as session:
                result = await session.execute(
                    select(AuthAuditLogORM)
                    .where(AuthAuditLogORM.login_id == login_id)
                    .order_by(AuthAuditLogORM.created_at.desc())
                    .limit(limit)
                )
                return [audit_to_model(r) for r in result.scalars().all()]
        except Exception as e:
            logger.error(f"Failed to get login_id audit logs: {str(e)}")
            raise DatabaseException(f"Failed to get audit logs: {str(e)}")
