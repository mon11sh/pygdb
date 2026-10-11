"""
SQLAlchemy ORM models — the single, portable schema used by every SQL provider
(sqlite / mysql / postgres / supabase). Uses portable column types (Integer
autoincrement instead of BIGSERIAL/nextval, String instead of native ENUM) so
`Base.metadata.create_all` provisions the same schema on any dialect.

This module is imported ONLY by the SQLAlchemy code paths, so providers that
don't use SQLAlchemy (e.g. inmemory) never import SQLAlchemy.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all users-service ORM models."""


class UserORM(Base):
    """ORM mapping for the ``users`` table (account credentials and role/status)."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    login_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Role kept as a plain string (portable) rather than a native ENUM type.
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="MANAGER")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class AuditLogORM(Base):
    """ORM mapping for the ``user_audit_logs`` table (user-management audit trail)."""

    __tablename__ = "user_audit_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    old_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


def user_to_dict(u: "UserORM", include_password: bool = False) -> dict:
    """Convert a UserORM row to the plain dict shape the services expect."""
    data = {
        "user_id": u.user_id,
        "username": u.username,
        "login_id": u.login_id,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at,
        "updated_at": u.updated_at,
    }
    if include_password:
        data["password"] = u.password
    return data
