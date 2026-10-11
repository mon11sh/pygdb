"""
SQLAlchemy ORM models — the single, portable schema used by every SQL provider
(sqlite / mysql / postgres / supabase). Uses portable column types (Integer
autoincrement instead of BIGSERIAL/nextval, String instead of native ENUM,
Numeric(15, 2) for money mapped to Python Decimal) so
`Base.metadata.create_all` provisions the same schema on any dialect.

This module is imported ONLY by the SQLAlchemy code paths, so providers that
don't use SQLAlchemy (e.g. inmemory / asyncpg) never import SQLAlchemy.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Numeric, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all transactions-service ORM models."""


class FundTransferORM(Base):
    """ORM model for the ``fund_transfers`` table.

    Records a single fund transfer between two accounts (source, destination,
    amount, mode) along with creation/update timestamps.
    """

    __tablename__ = "fund_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_account: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    to_account: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    transfer_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    transfer_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class TransactionLoggingORM(Base):
    """ORM model for the ``transaction_logging`` table.

    Immutable audit log of per-account monetary activity (deposits, withdrawals
    and both legs of a transfer), capturing amount, type, optional reference to
    the originating transfer, description, mode and status.
    """

    __tablename__ = "transaction_logging"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class TransferLimitORM(Base):
    """ORM model for the ``transfer_limits`` table.

    Maps an account privilege tier (e.g. PREMIUM / GOLD / SILVER) to its daily
    and per-transaction transfer ceilings, keyed by privilege.
    """

    __tablename__ = "transfer_limits"

    privilege: Mapped[str] = mapped_column(String(20), primary_key=True)
    daily_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    per_transaction_limit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class IdempotencyKeyORM(Base):
    """ORM model for the ``idempotency_keys`` table.

    Persists an idempotency key per operation so a retried request replays the
    stored response instead of re-executing, tracking the operation, its status
    and the cached response JSON.
    """

    __tablename__ = "idempotency_keys"

    idempotency_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="IN_PROGRESS")
    response_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
