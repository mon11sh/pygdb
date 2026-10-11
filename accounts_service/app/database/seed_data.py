"""
Default seed accounts — shared by EVERY provider so there is zero duplicated seed
logic. Seeding goes through the repository's own create_* methods (which persist
via the active backend), so it behaves identically on sqlite / mysql / postgres /
supabase / inmemory.
"""

import bcrypt

DEFAULT_PIN = "1234"


def _pin_hash() -> str:
    """Return a bcrypt hash of the default PIN (cost factor 12) for seeded accounts."""
    return bcrypt.hashpw(DEFAULT_PIN.encode("utf-8"), bcrypt.gensalt(12)).decode("utf-8")


async def seed_default_accounts(account_repo) -> int:
    """Seed the two default accounts via the repository (reuses the same create
    path on every provider). Returns the number of accounts seeded."""
    from app.models.account import SavingsAccountCreate, CurrentAccountCreate

    pin_hash = _pin_hash()

    savings = SavingsAccountCreate(
        name="John Doe",
        pin=DEFAULT_PIN,
        date_of_birth="1990-01-01",
        gender="Male",
        phone_no="9876543210",
        aadhar_number="123456789012",
        privilege="GOLD",
        initial_balance=50000.0,
    )
    await account_repo.create_savings_account(savings, pin_hash)

    current = CurrentAccountCreate(
        name="System Admin",
        pin=DEFAULT_PIN,
        company_name="Admin Tech Corp",
        registration_no="U12345MH2020PTC123456",
        website="admintech.com",
        privilege="PREMIUM",
    )
    await account_repo.create_current_account(current, pin_hash)

    return 2
