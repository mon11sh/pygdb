#!/usr/bin/env python3
"""
GDB — Step 3: Launch all backend services (uvicorn) + the service registry
(:8010) + the API gateway (:8000) + the React frontend (npm run dev), each in
its OWN titled console window.

Each window is kept OPEN even if the service crashes on startup, so you can
READ the error (bad DB credentials, port already in use, missing package, ...)
instead of the window vanishing. The window title shows which service it is.

Prerequisites (run these first, once):
    1. Your database must be running/reachable with the creds in your .env files
       (each DB service auto-creates its database + tables + seed on startup).
    2. python setup_env.py / setup_supabase.py / setup_mysql.py   # write .env
    3. python setup_venvs.py                                       # venvs + npm install

Usage:
    python run_all.py              # start everything
    python run_all.py --reload     # start with auto-reload (heavier; handy while editing)

To STOP: close each service window (or press Ctrl+C in it).
IMPORTANT: fully close old windows before re-running, or a leftover process will
still hold the port and the new one will fail with "address already in use".
"""

import platform
import subprocess
import sys
import time
from pathlib import Path

try:  # so emoji in the output never crash a Windows (cp1252) console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# (service directory, port). Start order roughly follows dependencies.
SERVICES = [
    ("auth_service", 8004),  # Auth Service port
    ("users_service", 8003),  # Users Service port
    ("accounts_service", 8001),  # Accounts Service port
    ("aadhar_service", 8005),  # Aadhar Service port
    ("company_crv_service", 8006),  # Company CRV Service port
    ("notification_service", 8007),  # Notification Service port
    ("central_payment_gateway_service", 8008),  # Central Payment Gateway Service port
    ("transactions_service", 8002),  # Transactions Service port
    # microservice-pattern services (registry first, gateway last so backends exist)
    ("registry_service", 8010),  # Service Registry port
    ("central_gateway_service", 8000),  # Central Gateway Service port
]

IS_WIN = platform.system() == "Windows"
RELOAD = "--reload" in sys.argv


def venv_python_path(svc_venv: Path) -> Path:
    return svc_venv / ("Scripts/python.exe" if IS_WIN else "bin/python")


def launch(title: str, command: str, cwd: Path):
    """Open a NEW console window running `command` (a shell command relative to
    `cwd`), kept OPEN even if it exits/crashes so the error stays visible.
    `title` labels the window."""
    if IS_WIN:
        # cmd /k keeps the window open; `title` names it; `&` chains the two.
        full = f'cmd /k "title {title}  &  {command}"'
        return subprocess.Popen(full, cwd=str(cwd), creationflags=subprocess.CREATE_NEW_CONSOLE)
    # POSIX: run in the background (terminal-window handling varies by OS).
    return subprocess.Popen(command, cwd=str(cwd), shell=True)


def main():
    root = Path(__file__).parent.resolve()
    print("=" * 60)
    print("🚀 GDB — Starting all services" + (" (reload ON)" if RELOAD else ""))
    print("=" * 60)

    # Every backend needs its venv.
    missing = [name for name, _ in SERVICES
               if not venv_python_path(root / name / "venv").exists()]
    if missing:
        print("❌ Missing venv for: " + ", ".join(missing))
        print("   Run:  python setup_venvs.py   first.")
        sys.exit(1)

    py_rel = "venv\\Scripts\\python.exe" if IS_WIN else "venv/bin/python"

    # Backend services — each in its own titled, persistent window.
    for name, port in SERVICES:
        svc = root / name
        command = f"{py_rel} -m uvicorn app.main:app --host 0.0.0.0 --port {port}"
        if RELOAD:
            command += " --reload"
        print(f"▶️  [{name}]  http://localhost:{port}")
        launch(f"{name}:{port}", command, svc)
        time.sleep(2)  # stagger so DB auto-create / console spawns don't collide

    # Frontend (Vite dev server) — also kept open.
    frontend = root / "frontend"
    if (frontend / "package.json").exists():
        print("▶️  [frontend] npm run dev")
        launch("frontend", "npm run dev", frontend)

    print("=" * 60)
    print("✅ Launched. Each service is in its OWN window (named by service:port).")
    print("   A window that shows an error and stays open = that service failed —")
    print("   read the message (common: DB creds wrong, or port already in use).")
    print("   Swagger:  http://localhost:8001/api/v1/docs  (per service port)")
    print("   Frontend: the URL Vite prints (http://localhost:3000 or :5173)")
    print("   Login:    admin / Welcome@1")
    print("=" * 60)


if __name__ == "__main__":
    main()
