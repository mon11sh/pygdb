"""
Aadhaar encryption-at-rest tests (Enterprise remediation H-4).

Exercises the SQLAlchemy repository against a real SQLite file to prove:
- Aadhaar is stored as ciphertext (not plaintext) at rest,
- reads transparently decrypt back to the original value,
- uniqueness is enforced via the deterministic blind index (aadhar_hash).
"""

import sqlite3

import pytest

from app.database.providers.sqlalchemy_provider import SqlAlchemyProvider
from app.exceptions.account_exceptions import DuplicateConstraintError
from app.models.account import SavingsAccountCreate


def _savings(aadhar, phone, name="Enc Test"):
    return SavingsAccountCreate(
        name=name, pin="1234", date_of_birth="1990-01-01", gender="Male",
        phone_no=phone, aadhar_number=aadhar, initial_balance=2000,
    )


async def test_aadhaar_ciphertext_at_rest_and_decrypt_on_read(tmp_path):
    db = tmp_path / "enc.db"
    provider = SqlAlchemyProvider(f"sqlite+aiosqlite:///{db}", name="sqlite")
    await provider.init()
    repo = provider.account_repository()

    number = await repo.create_savings_account(_savings("999888777666", "9876500000"), "pinhash")

    # Read path transparently decrypts back to the original value.
    details = await repo.get_account(number)
    assert details["aadhar_number"] == "999888777666"
    await provider.dispose()

    # At rest it is ciphertext + a 64-char blind index, never the plaintext.
    conn = sqlite3.connect(db)
    raw_aadhar, raw_hash = conn.execute(
        "SELECT aadhar_number, aadhar_hash FROM savings_account_details WHERE account_number=?",
        (number,),
    ).fetchone()
    conn.close()
    assert raw_aadhar != "999888777666"
    assert len(raw_aadhar) > 20            # Fernet token
    assert raw_hash and len(raw_hash) == 64  # HMAC-SHA256 hex


async def test_duplicate_aadhaar_rejected_via_blind_index(tmp_path):
    db = tmp_path / "dup.db"
    provider = SqlAlchemyProvider(f"sqlite+aiosqlite:///{db}", name="sqlite")
    await provider.init()
    repo = provider.account_repository()

    await repo.create_savings_account(_savings("111222333444", "9876500001", "Holder One"), "h")
    with pytest.raises(DuplicateConstraintError):
        await repo.create_savings_account(_savings("111222333444", "9876500002", "Holder Two"), "h")
    await provider.dispose()
