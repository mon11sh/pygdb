#!/usr/bin/env python3
"""
GDB — run the whole stack in Docker with ANY of the 5 database providers,
using one short word instead of long `-f` chains.

    python docker_up.py inmemory     # no DB, resets on stop (default, zero setup)
    python docker_up.py sqlite       # a .db file inside each service container
    python docker_up.py postgres     # bundled PostgreSQL container
    python docker_up.py mysql        # bundled MySQL container
    python docker_up.py supabase     # cloud Postgres (needs a .env — see below)

Extra flags are passed straight through to `docker compose up`, e.g.:
    python docker_up.py postgres -d          # run detached (in the background)
    python docker_up.py mysql --build        # force a rebuild

To STOP:  python docker_up.py down           # stops the stack
          python docker_up.py down -v         # stops AND wipes the DB volume

Supabase note: first copy  supabase.env.example → .env  and fill in your values.
Then open http://localhost:3000 and log in with  admin / Welcome@1.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BASE = "docker-compose.yml"

# provider -> extra override file layered on top of the base compose
OVERRIDES = {
    "inmemory": None,                     # base file already defaults to inmemory
    "sqlite":   "docker-compose.sqlite.yml",
    "postgres": "docker-compose.postgres.yml",
    "mysql":    "docker-compose.mysql.yml",
    "supabase": "docker-compose.supabase.yml",
}


def compose_files(provider: str) -> list[str]:
    files = ["-f", BASE]
    override = OVERRIDES[provider]
    if override:
        files += ["-f", override]
    return files


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    first = sys.argv[1].lower()

    # `down` convenience: stop the stack (pass -v to also drop volumes).
    if first == "down":
        cmd = ["docker", "compose", "-f", BASE, "down", *sys.argv[2:]]
        raise SystemExit(subprocess.call(cmd, cwd=ROOT))

    if first not in OVERRIDES:
        sys.exit(
            f"Unknown provider '{first}'.\n"
            f"Choose one of: {', '.join(OVERRIDES)}  (or 'down').\n\n{__doc__}"
        )

    if first == "supabase" and not (ROOT / ".env").exists():
        sys.exit(
            "Supabase needs your cloud credentials first:\n"
            "  1) copy  supabase.env.example  →  .env\n"
            "  2) fill in your Supabase connection values\n"
            "  3) re-run:  python docker_up.py supabase"
        )

    passthrough = sys.argv[2:]
    if "-d" not in passthrough and "--detach" not in passthrough:
        # default to --build so first run / code changes are picked up
        if "--build" not in passthrough:
            passthrough = ["--build", *passthrough]

    cmd = ["docker", "compose", *compose_files(first), "up", *passthrough]
    print("→", " ".join(cmd))
    print(f"   provider = {first}   |   open http://localhost:3000  (admin / Welcome@1)\n")
    raise SystemExit(subprocess.call(cmd, cwd=ROOT))


if __name__ == "__main__":
    main()
