#!/usr/bin/env python3
"""
GDB — Step 2: Create per-service virtual environments and install requirements,
then install the frontend's npm packages.

Smart flow (only installs when needed):

  For each backend service:
    - venv NOT created yet     -> create venv, then pip install -r requirements.txt
    - venv already created     -> check if requirements.txt is already satisfied
                                    * satisfied     -> skip (fast, nothing to do)
                                    * NOT satisfied -> pip install the missing ones

  Frontend:
    - node_modules missing     -> npm install
    - node_modules present     -> skip

Why per-service venvs (not one shared): services pin DIFFERENT dependency
versions (e.g. auth needs pydantic 2.5.0 while accounts pins 2.4.2), so one
shared environment would conflict.

You do NOT need to "activate" anything manually — this script installs directly
into each venv, and run_all.py launches each service with its own venv's Python.

Usage:
    python setup_venvs.py            # only installs what's missing
    python setup_venvs.py --force    # reinstall requirements even if satisfied
"""

import os
import subprocess
import sys
from pathlib import Path

try:  # so emoji in the output never crash a Windows (cp1252) console
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SERVICES = [
    "accounts_service",
    "transactions_service",
    "users_service",
    "auth_service",
    "aadhar_service",
    "company_crv_service",
    "notification_service",
    "central_payment_gateway_service",
    "registry_service",          # Service Discovery pattern (:8010)
    "central_gateway_service",   # API Gateway pattern (:8000)
]

FORCE = "--force" in sys.argv

# Runs INSIDE a venv's python: is every requirement installed (and == pins matched)?
# Exit 0 = all satisfied; exit 1 = something missing (and prints what).
CHECK_CODE = r"""
import sys, re
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError

missing = []
for raw in open(sys.argv[1], encoding="utf-8"):
    line = raw.split("#", 1)[0].strip()
    if not line or line.startswith("-"):
        continue
    m = re.match(r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?\s*(==|>=|<=|~=|!=|>|<)?\s*([A-Za-z0-9_.\-*]+)?", line)
    if not m:
        continue
    name, op, want = m.group(1), m.group(3), m.group(4)
    try:
        have = version(name)
    except PackageNotFoundError:
        missing.append(line)
        continue
    if op == "==" and want and have != want:
        missing.append(f"{line} (installed: {have})")

if missing:
    print("Missing / mismatched:")
    for x in missing:
        print("   - " + x)
    sys.exit(1)
sys.exit(0)
"""


def venv_python(venv_dir: Path) -> Path:
    """Path to the venv's python executable (Windows vs POSIX)."""
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def requirements_satisfied(py: Path, req: Path) -> bool:
    """Ask the venv's own Python whether requirements.txt is fully installed."""
    result = subprocess.run(
        [str(py), "-c", CHECK_CODE, str(req)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 and result.stdout.strip():
        print(result.stdout.rstrip())
    return result.returncode == 0


def pip_install(py: Path, req: Path):
    subprocess.check_call([str(py), "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
    # Run pip FROM the service directory so relative editable paths in
    # requirements.txt (e.g. `-e ../libs/gdb_common`) resolve correctly.
    subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(req)], cwd=str(req.parent))


def main():
    root = Path(__file__).parent.resolve()
    print("=" * 62)
    print("🐍 GDB — venvs + requirements" + ("  (--force reinstall)" if FORCE else ""))
    print("=" * 62)

    ok = 0
    for name in SERVICES:
        svc = root / name
        req = svc / "requirements.txt"
        venv = svc / "venv"
        py = venv_python(venv)
        if not req.exists():
            print(f"⚠️  [{name}] no requirements.txt — skipped")
            continue

        try:
            if not py.exists():
                # --- venv NOT created: create it, then install ---
                print(f"\n📦 [{name}] creating venv ...")
                subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
                print(f"⬇️  [{name}] installing requirements ...")
                pip_install(py, req)
                print(f"✅ [{name}] ready (fresh install)")
            else:
                # --- venv exists: check, install only if needed ---
                if not FORCE and requirements_satisfied(py, req):
                    print(f"✅ [{name}] requirements already installed — skipping")
                else:
                    reason = "forced" if FORCE else "missing packages"
                    print(f"\n⬇️  [{name}] installing requirements ({reason}) ...")
                    pip_install(py, req)
                    print(f"✅ [{name}] ready (updated)")
            ok += 1
        except subprocess.CalledProcessError as e:
            print(f"❌ [{name}] failed: {e}")

    # --- Frontend: install node modules only if missing ---
    frontend = root / "frontend"
    if (frontend / "package.json").exists():
        if not FORCE and (frontend / "node_modules").exists():
            print("\n✅ [frontend] node_modules already present — skipping")
        else:
            print("\n📦 [frontend] npm install ...")
            try:
                subprocess.check_call("npm install", shell=True, cwd=str(frontend))
                print("✅ [frontend] node_modules ready")
            except subprocess.CalledProcessError as e:
                print(f"❌ [frontend] npm install failed: {e}")
                print("💡 Run 'npm install' manually inside the frontend folder.")

    print("\n" + "=" * 62)
    print(f"🎉 Backend services ready: {ok}/{len(SERVICES)}")
    print("Next: make sure your database is reachable, then: python run_all.py")
    print("=" * 62)


if __name__ == "__main__":
    main()
