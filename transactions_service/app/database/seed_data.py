"""
Default seed data — shared by EVERY provider so there is zero duplicated seed
logic. Seeding goes through the repositories themselves, so it behaves
identically on sqlite / mysql / postgres / supabase / inmemory.

Mirrors what the original asyncpg db.py seeded:
  - transfer_limits rows for PREMIUM / GOLD / SILVER (daily_limit, per_transaction_limit)
  - a minimal, equivalent set of sample transaction logs / a fund transfer
"""

from decimal import Decimal

from app.models.enums import TransactionType

# (privilege, daily_limit, per_transaction_limit)
SEED_TRANSFER_LIMITS = [
    ("PREMIUM", Decimal("100000.00"), Decimal("50000.00")),
    ("GOLD", Decimal("50000.00"), Decimal("25000.00")),
    ("SILVER", Decimal("25000.00"), Decimal("12500.00")),
]


async def seed_transfer_limits(limit_repo) -> int:
    """Seed default transfer_limits rows (idempotent via upsert). Returns count."""
    for privilege, daily_limit, per_txn in SEED_TRANSFER_LIMITS:
        await limit_repo.create_transfer_rule(privilege, daily_limit, per_txn)
    return len(SEED_TRANSFER_LIMITS)


async def seed_sample_logs(transaction_repo, log_repo) -> None:
    """Seed a minimal, equivalent set of sample activity, matching the original
    db.py seed (a deposit, a transfer and its two logging legs)."""
    # Deposit to 1001
    await log_repo.log_to_database(
        account_number=1001,
        amount=Decimal("60000.00"),
        transaction_type=TransactionType.DEPOSIT,
        reference_id=None,
        description="Initial deposit",
    )

    # Transfer from 1002 to 1001
    transfer_id = await transaction_repo.create_transaction(
        from_account=1002,
        to_account=1001,
        amount=Decimal("10000.00"),
        transaction_type=TransactionType.TRANSFER,
        description="Fund Transfer to 1001",
    )

    # Debit log for 1002, credit log for 1001
    await log_repo.log_to_database(
        account_number=1002,
        amount=Decimal("10000.00"),
        transaction_type=TransactionType.TRANSFER,
        reference_id=transfer_id,
        description="Fund Transfer to 1001",
    )
    await log_repo.log_to_database(
        account_number=1001,
        amount=Decimal("10000.00"),
        transaction_type=TransactionType.TRANSFER,
        reference_id=transfer_id,
        description="Fund Transfer from 1002",
    )
