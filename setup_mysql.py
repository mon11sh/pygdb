#!/usr/bin/env python3
"""
GDB — Point ALL services at a MySQL database with ONE command.

For MySQL, every service uses the SQLAlchemy path, so they all just need
DATABASE_PROVIDER=mysql + DATABASE_URL. All services share the SAME MySQL
database (their table names never clash) and create their own tables + seed
data automatically on first run.

HOW TO USE
----------
1) Have a MySQL server running and know: host, port (3306), user, password.
   Pick a database name (e.g. gdb) — it is created automatically if missing.
2) Run (put the whole URL in quotes):
   python setup_mysql.py "mysql://root:YOURPASSWORD@localhost:3306/gdb"

TIP: use a MySQL password made of ONLY letters and numbers, so the URL has no
special characters to worry about.
"""

import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

try:  # so emoji in the output never crash a Windows (cp1252) console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

DB_SERVICES = ["users_service", "auth_service", "accounts_service", "transactions_service"]
NO_DB = ["aadhar_service", "company_crv_service", "notification_service",
         "central_payment_gateway_service", "frontend"]


def validate(conn: str):
    u = urlparse(conn.strip())
    if not u.hostname or not (u.scheme or "").startswith("mysql"):
        raise SystemExit(
            "❌ That does not look like a MySQL URL.\n"
            "   Expected: mysql://USER:PASSWORD@HOST:3306/DBNAME"
        )
    db = (u.path or "").lstrip("/")
    if not db:
        raise SystemExit("❌ Please include a database name at the end, e.g. .../gdb")
    return {"host": u.hostname, "port": str(u.port or 3306),
            "user": unquote(u.username or "root"), "db": db}


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
    print(f"✅ [{service_dir.name}] .env written")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(
            'Usage:\n  python setup_mysql.py "mysql://USER:PASSWORD@HOST:3306/DBNAME"'
        )

    root = Path(__file__).parent.resolve()
    raw_url = sys.argv[1].strip()
    info = validate(raw_url)

    print("=" * 62)
    print("🐬 GDB → MySQL setup")
    print(f"   host={info['host']}  port={info['port']}  db={info['db']}  user={info['user']}")
    print("=" * 62)

    for name in DB_SERVICES:
        write_env(root / name, {"DATABASE_PROVIDER": "mysql", "DATABASE_URL": raw_url})

    for name in NO_DB:
        write_env(root / name, {})  # copy example as-is

    print("=" * 62)
    print("🎉 All .env files updated for MySQL.")
    print("Next steps:")
    print("  1. python setup_venvs.py     (installs aiomysql if missing)")
    print("  2. python run_all.py         (tables + seed auto-create)")
    print("  3. Open the frontend and log in:  admin / Welcome@1")
    print("=" * 62)


if __name__ == "__main__":
    main()
