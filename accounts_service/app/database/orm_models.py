"""
SQLAlchemy ORM models — the single, portable schema used by every SQL provider
(sqlite / mysql / postgres / supabase). Uses PORTABLE column types so
`Base.metadata.create_all` provisions the same schema on any dialect:

  - Integer autoincrement primary keys (NOT BIGSERIAL / nextval / native sequence)
  - String(...) for gender / privilege / account_type (NOT a native ENUM type)
  - Numeric(15, 2) for money (mapped to Python Decimal end-to-end)
  - DateTime / Boolean for timestamps and flags
  - UNIQUE on account_number, aadhar_number and registration_no

The Postgres `account_number_seq` (START WITH 1000) is reproduced portably at the
application level: the repository assigns the next account number as
max(account_number)+1 with a floor of 1000. See the repositories.

This module is imported ONLY by the SQLAlchemy code paths, so providers that
don't use SQLAlchemy (e.g. inmemory) never import SQLAlchemy.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    Date,
    Numeric,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Account numbers start at 1000 (reproduces the old Postgres sequence floor).
ACCOUNT_NUMBER_START = 1000


class Base(DeclarativeBase):
    """Declarative base for all accounts-service ORM models."""


class AccountORM(Base):
    """Core account row shared by every account type.

    Holds the identity, money and lifecycle columns common to all accounts
    (surrogate PK plus the UNIQUE business ``account_number``, balance,
    privilege, bank metadata and activation flags). Type-specific fields live in
    the paired ``SavingsAccountDetailsORM`` / ``CurrentAccountDetailsORM`` rows.
    """

    __tablename__ = "accounts"

    # Surrogate PK (portable autoincrement). NOT the account number.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Business account number — app-assigned starting at 1000, kept UNIQUE.
    account_number: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
    )
    account_type: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    privilege: Mapped[str] = mapped_column(String(10), nullable=False)
    bank_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Global Digital Bank"
    )
    bank_branch: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Main Branch"
    )
    ifsc_code: Mapped[str] = mapped_column(
        String(20), nullable=False, default="GDB0000001"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    activated_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    closed_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class SavingsAccountDetailsORM(Base):
    """Savings-specific detail row, linked 1:1 to an account by account_number.

    Stores personal KYC fields for a SAVINGS account. Aadhaar is kept encrypted
    at rest (non-deterministic Fernet ciphertext) with a separate deterministic
    ``aadhar_hash`` blind index used for uniqueness and lookup.
    """

    __tablename__ = "savings_account_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.account_number", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    # Gender kept as a plain string (portable) rather than a native ENUM.
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    phone_no: Mapped[str] = mapped_column(String(20), nullable=False)
    # Aadhaar is stored ENCRYPTED at rest (Fernet ciphertext, non-deterministic),
    # so the column is widened and carries no unique constraint. Uniqueness and
    # lookup use aadhar_hash (a deterministic keyed blind index). Remediation H-4.
    aadhar_number: Mapped[str] = mapped_column(String(255), nullable=False)
    aadhar_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class CurrentAccountDetailsORM(Base):
    """Current-account detail row, linked 1:1 to an account by account_number.

    Stores business/company fields for a CURRENT account, including the UNIQUE
    company ``registration_no`` and an optional website.
    """

    __tablename__ = "current_account_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("accounts.account_number", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    registration_no: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


def account_to_dict(
    acc: "AccountORM",
    savings: "Optional[SavingsAccountDetailsORM]" = None,
    current: "Optional[CurrentAccountDetailsORM]" = None,
) -> dict:
    """Assemble the exact dict shape get_account() has always returned.

    Balance is exposed as a float to preserve the historical dict contract that
    services and the internal API already rely on (money is stored/compared as
    Decimal internally in the repositories)."""
    result = {
        "account_number": acc.account_number,
        "account_type": acc.account_type,
        "name": acc.name,
        "balance": float(acc.balance) if acc.balance is not None else 0.0,
        "privilege": acc.privilege,
        "is_active": acc.is_active,
        "activated_date": acc.activated_date,
        "closed_date": acc.closed_date,
        "bank_name": acc.bank_name,
        "bank_branch": acc.bank_branch,
        "ifsc_code": acc.ifsc_code,
    }
    if acc.account_type == "SAVINGS" and savings is not None:
        result["date_of_birth"] = (
            str(savings.date_of_birth) if savings.date_of_birth else None
        )
        result["gender"] = savings.gender
        result["phone_no"] = savings.phone_no
        # Decrypt the at-rest Aadhaar ciphertext (H-4). Fall back to the raw value
        # for any legacy/plaintext rows so reads never hard-fail.
        from app.utils.encryption import EncryptionManager
        try:
            result["aadhar_number"] = EncryptionManager.decrypt_data(savings.aadhar_number)
        except Exception:
            result["aadhar_number"] = savings.aadhar_number
    elif acc.account_type == "CURRENT" and current is not None:
        result["company_name"] = current.company_name
        result["registration_no"] = current.registration_no
        result["website"] = current.website
    return result
