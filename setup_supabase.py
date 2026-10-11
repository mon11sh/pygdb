#!/usr/bin/env python3
"""
GDB — Point ALL services at your Supabase database with ONE command.

Supabase is just a hosted PostgreSQL database. This writes the correct `.env`
file for every service so the whole app uses your Supabase database:
  - users / auth / accounts services  -> DATABASE_URL = your Supabase string
  - transactions service              -> DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME
  - the 4 mock services + frontend     -> copied as-is (they use no database)

All services share your single Supabase `postgres` database (their table names
never clash) and create their own tables + seed data automatically on first run.

HOW TO USE
----------
1) In Supabase: Project → "Connect" → choose "Session pooler" → copy the URI.
   It looks like:
   postgresql://postgres.abcdxyz:YOURPASSWORD@aws-0-xx.pooler.supabase.com:5432/postgres
2) Run (put the whole URI in quotes):
   python setup_supabase.py "postgresql://postgres.abcdxyz:YOURPASSWORD@aws-0-xx.pooler.supabase.com:5432/postgres"

TIP: use a Supabase database password made of ONLY letters and numbers, so the
URI has no special characters to worry about.
"""

import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

try:  # so emoji in the output never crash a Windows (cp1252) console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

URL_SERVICES = ["users_service", "auth_service", "accounts_service"]  # read DATABASE_URL
DBFIELD_SERVICES = ["transactions_service"]                            # read DB_* fields
NO_DB = ["aadhar_service", "company_crv_service", "notification_service",
         "central_payment_gateway_service", "frontend"]


def parse(conn: str):
    u = urlparse(conn.strip())
    if not u.hostname:
        raise SystemExit(
            "❌ That does not look like a connection URI.\n"
            "   Expected: postgresql://USER:PASSWORD@HOST:5432/postgres"
        )
    return {
        "user": unquote(u.username or "postgres"),
        "password": unquote(u.password or ""),
        "host": u.hostname,
        "port": str(u.port or 5432),
        "db": (u.path or "/postgres").lstrip("/") or "postgres",
    }


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
    # Append any override keys the example didn't already contain.
    for key, val in overrides.items():
        if key not in seen:
            out.append(f"{key}={val}")
    (service_dir / ".env").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"✅ [{service_dir.name}] .env written")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            'Usage:\n  python setup_supabase.py "postgresql://USER:PASSWORD@HOST:5432/postgres"'
        )

    root = Path(__file__).parent.resolve()
    raw_url = sys.argv[1].strip()
    p = parse(raw_url)

    print("=" * 62)
    print("🟢 GDB → Supabase setup")
    print(f"   host={p['host']}  port={p['port']}  db={p['db']}  user={p['user']}")
    print("=" * 62)

    for name in URL_SERVICES:
        write_env(root / name, {"DATABASE_PROVIDER": "supabase", "DATABASE_URL": raw_url})

    for name in DBFIELD_SERVICES:
        write_env(root / name, {
            "DATABASE_PROVIDER": "supabase",
            "DB_HOST": p["host"], "DB_PORT": p["port"],
            "DB_USER": p["user"], "DB_PASSWORD": p["password"], "DB_NAME": p["db"],
        })

    for name in NO_DB:
        write_env(root / name, {})  # copy example as-is

    print("=" * 62)
    print("🎉 All .env files updated for Supabase.")
    print("Next steps:")
    print("  1. python setup_venvs.py     (if you haven't installed deps yet)")
    print("  2. python run_all.py         (starts everything; tables auto-create)")
    print("  3. Open the frontend and log in:  admin / Welcome@1")
    print("=" * 62)


if __name__ == "__main__":
    main()
