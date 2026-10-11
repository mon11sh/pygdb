#!/usr/bin/env python3
"""
GDB — Step 1: Create local .env files for every service + frontend.

Generates a `.env` in each of the 8 backend services and the frontend by copying
that service's `.env.example` and injecting YOUR local Postgres credentials.

The four "mock" services (aadhar, company, notification, payment) and the frontend
have no DB config, so their .env is copied verbatim.

Usage:
    python setup_env.py                    # uses the defaults below
    python setup_env.py <password>         # override just the DB password
    python setup_env.py <password> <user> <host> <port>

Only Postgres user/password/host/port are injected; database NAMES are left as the
service defaults (gdb_accounts_db, gdb_auth_db, ...), which the services auto-create.
"""

import re
import sys
from pathlib import Path

try:  # so emoji in the output never crash a Windows (cp1252) console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---------------------------------------------------------------------------
# EDIT THESE to match your local PostgreSQL, or pass them as CLI args.
# ---------------------------------------------------------------------------
DB_USER = "postgres"
DB_PASSWORD = "postgres"   # <-- your local Postgres password
DB_HOST = "localhost"
DB_PORT = "5432"
# ---------------------------------------------------------------------------

# Allow CLI overrides: setup_env.py <password> [user] [host] [port]
if len(sys.argv) >= 2:
    DB_PASSWORD = sys.argv[1]
if len(sys.argv) >= 3:
    DB_USER = sys.argv[2]
if len(sys.argv) >= 4:
    DB_HOST = sys.argv[3]
if len(sys.argv) >= 5:
    DB_PORT = sys.argv[4]

TARGETS = [
    "accounts_service",
    "transactions_service",
    "users_service",
    "auth_service",
    "aadhar_service",
    "company_crv_service",
    "notification_service",
    "central_payment_gateway_service",
    "frontend",
]


def transform(line: str) -> str:
    """Inject DB credentials into a single .env line, leaving everything else alone."""
    s = line.rstrip("\n")

    # accounts style: DATABASE_URL=postgresql://user:password@host:port/dbname
    if s.startswith("DATABASE_URL="):
        return re.sub(
            r"postgresql://[^/]+/",
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/",
            s,
        )

    # transactions style: DB_USER / DB_PASSWORD / DB_HOST / DB_PORT
    # auth & users style:  DATABASE_USER / DATABASE_PASSWORD
    replacements = {
        "DB_USER=": f"DB_USER={DB_USER}",
        "DB_PASSWORD=": f"DB_PASSWORD={DB_PASSWORD}",
        "DB_HOST=": f"DB_HOST={DB_HOST}",
        "DB_PORT=": f"DB_PORT={DB_PORT}",
        "DATABASE_USER=": f"DATABASE_USER={DB_USER}",
        "DATABASE_PASSWORD=": f"DATABASE_PASSWORD={DB_PASSWORD}",
    }
    for prefix, replacement in replacements.items():
        if s.startswith(prefix):
            return replacement
    return s


def main():
    root = Path(__file__).parent.resolve()
    print("=" * 60)
    print("📝 GDB — Creating .env files")
    print(f"   DB: {DB_USER}:***@{DB_HOST}:{DB_PORT}")
    print("=" * 60)

    created = 0
    for name in TARGETS:
        svc = root / name
        example = svc / ".env.example"
        env = svc / ".env"
        if not example.exists():
            print(f"⚠️  [{name}] no .env.example — skipped")
            continue
        lines = example.read_text(encoding="utf-8").splitlines()
        content = "\n".join(transform(l) for l in lines) + "\n"
        # Write UTF-8 without BOM so python-dotenv / Vite parse the first key correctly.
        env.write_text(content, encoding="utf-8")
        print(f"✅ [{name}] wrote {env.relative_to(root)}")
        created += 1

    print("=" * 60)
    print(f"🎉 Done: {created}/{len(TARGETS)} .env files written.")
    print("Next: python setup_venvs.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
