"""
Default seed users — shared by EVERY provider so there is zero duplicated seed
logic. Seeding goes through the repository's own create_user (which hashes the
password), so it behaves identically on sqlite / mysql / postgres / supabase /
inmemory.
"""

DEFAULT_PASSWORD = "Welcome@1"

# (username, login_id, role)
SEED_USERS = [
    ("Admin User", "admin", "ADMIN"),
    ("Sarah Johnson", "sarah.admin", "ADMIN"),
    ("John Doe", "john.doe", "TELLER"),
    ("Emily Davis", "emily.davis", "TELLER"),
    ("Teller User", "teller", "TELLER"),
    ("Manager User", "manager.manager", "MANAGER"),
    ("Jane Smith", "jane.smith", "MANAGER"),
    ("Michael Brown", "michael.brown", "MANAGER"),
    ("Alice Wilson", "alice.wilson", "MANAGER"),
    ("Bob Taylor", "bob.taylor", "MANAGER"),
]


async def seed_default_users(user_repo) -> int:
    """Seed default users via the repository (reuses create_user → same hashing
    and persistence path on every provider). Returns the number seeded."""
    for username, login_id, role in SEED_USERS:
        await user_repo.create_user(username, login_id, DEFAULT_PASSWORD, role)
    return len(SEED_USERS)
