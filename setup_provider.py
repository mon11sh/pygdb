#!/usr/bin/env python3
"""
GDB — Switch ALL services to a no-server database provider with ONE command.

Use this for the providers that need NO connection string:
    python setup_provider.py sqlite     # each service gets its own local .db file
    python setup_provider.py inmemory   # pure RAM, nothing persisted

(For MySQL use setup_mysql.py, for Supabase setup_supabase.py, and for a local
PostgreSQL / pgAdmin use setup_env.py <password> <user>.)

It sets DATABASE_PROVIDER and CLEARS DATABASE_URL for every DB service (so any
leftover MySQL/Supabase URL is ignored), and leaves the 4 mock services +
frontend untouched.
"""

import sys
from pathlib import Path

try:  # so emoji in the output never crash a Windows (cp1252) console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DB_SERVICES = ["users_service", "auth_service", "accounts_service", "transactions_service"]
NO_DB = ["aadhar_service", "company_crv_service", "notification_service",
         "central_payment_gateway_service", "frontend"]
ALLOWED = {"sqlite", "inmemory"}


def write_env(service_dir: Path, overrides: dict):
    example = service_dir / ".env.example"
    if not example.exists():
        print(f"⚠️  [{service_dir.name}] no .env.example — skipped")
        return
    lines = example.read_text(encoding="utf-8").splitlines()
    seen = set()
    out = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else None
        if key in overrides:
            out.append(f"{key}={overrides[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, val in overrides.items():
        if key not in seen:
            out.append(f"{key}={val}")
    (service_dir / ".env").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"✅ [{service_dir.name}] .env → {overrides.get('DATABASE_PROVIDER', '(no db)')}")


def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() not in ALLOWED:
        raise SystemExit("Usage:\n  python setup_provider.py sqlite\n  python setup_provider.py inmemory")

    provider = sys.argv[1].lower()
    root = Path(__file__).parent.resolve()

    print("=" * 60)
    print(f"🗃️  GDB → {provider.upper()} (no server needed)")
    print("=" * 60)

    for name in DB_SERVICES:
        # Clear DATABASE_URL so a leftover MySQL/Supabase URL is never reused.
        write_env(root / name, {"DATABASE_PROVIDER": provider, "DATABASE_URL": ""})

    for name in NO_DB:
        write_env(root / name, {})  # copy example as-is

    print("=" * 60)
    print(f"🎉 All services set to {provider}.")
    if provider == "sqlite":
        print("Each service creates its own file (users_service/gdb_users.db, etc.).")
    else:
        print("Data lives only in memory and resets every restart.")
    print("Next:  python run_all.py     (then log in: admin / Welcome@1)")
    print("=" * 60)


if __name__ == "__main__":
    main()
