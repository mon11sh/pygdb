"""
SQLAlchemy ORM models — the single, portable schema used by every SQL provider
(sqlite / mysql / postgres / supabase). Mirrors auth_schema.sql but with PORTABLE
column types so `Base.metadata.create_all` provisions the same schema on any
dialect:

  - UUID primary keys  -> String(36) storing an app-generated uuid4 string
    (avoids Postgres-only gen_random_uuid()).
  - BIGINT             -> Integer.
  - native ENUM        -> String (the action is validated in app code).
  - INET               -> String(45) (fits IPv4/IPv6 text form).
  - TIMESTAMPTZ        -> DateTime.

This module is imported ONLY by the SQLAlchemy code paths, so providers that
don't use SQLAlchemy (e.g. inmemory) never import SQLAlchemy.
"""

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..models.auth_models import AuthToken, AuthAuditLog


def _utcnow() -> datetime:
    """Return the current UTC time as a naive ``datetime``.

    Returns:
        The current UTC instant with its timezone info stripped, suitable for
        the ``TIMESTAMP WITHOUT TIME ZONE`` columns used by these models.
    """
    # NAIVE UTC on purpose: the DateTime columns are TIMESTAMP WITHOUT TIME ZONE,
    # and Postgres/asyncpg reject timezone-aware values in those columns.
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Declarative base for all auth-service ORM models."""


class AuthTokenORM(Base):
    """ORM mapping for the ``auth_tokens`` table.

    Persists issued JWT metadata (JTI, subject, issue/expiry times, revocation
    flag) so tokens can be looked up and revoked. Uses portable column types so
    the same schema materializes on sqlite, mysql, postgres, and supabase.
    """

    __tablename__ = "auth_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    login_id: Mapped[str] = mapped_column(String(255), nullable=False)
    token_jti: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)


class AuthAuditLogORM(Base):
    """ORM mapping for the ``auth_audit_logs`` table.

    Records an append-only audit trail of authentication events (login,
    logout, token issue/revoke, etc.) along with contextual metadata such as
    the reason, client IP address, and user agent. Portable column types keep
    the schema identical across every SQL dialect.
    """

    __tablename__ = "auth_audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    login_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    # Native ENUM (auth_action_enum) kept as a portable string.
    action: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # INET -> plain string.
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False, index=True)


def token_to_model(row: "AuthTokenORM") -> AuthToken:
    """Convert an AuthTokenORM row to the AuthToken dataclass the app expects."""
    return AuthToken(
        id=row.id,
        user_id=row.user_id,
        login_id=row.login_id,
        token_jti=row.token_jti,
        issued_at=row.issued_at,
        expires_at=row.expires_at,
        is_revoked=bool(row.is_revoked),
    )


def audit_to_model(row: "AuthAuditLogORM") -> AuthAuditLog:
    """Convert an AuthAuditLogORM row to the AuthAuditLog dataclass the app expects."""
    return AuthAuditLog(
        id=row.id,
        login_id=row.login_id,
        user_id=row.user_id,
        action=row.action,
        reason=row.reason,
        ip_address=row.ip_address,
        user_agent=row.user_agent,
        created_at=row.created_at,
    )
