# Global Digital Bank (GDB) — Microservices Platform

A training-grade full-stack banking application: **8 FastAPI microservices** + a
**React (Vite)** frontend, runnable against **five databases** (SQLite, In-Memory,
PostgreSQL, MySQL, Supabase) with **zero code changes** via a provider/factory
abstraction.

> **Login:** `admin` / `Welcome@1`

## Services & ports
| Service | Port | Role |
|---|---|---|
| accounts | 8001 | account lifecycle, balances, PIN |
| transactions | 8002 | transfers, deposits, limits, idempotency |
| users | 8003 | platform users, RBAC |
| auth | 8004 | login, JWT issuance |
| aadhar (mock) | 8005 | KYC verification stub |
| company (mock) | 8006 | company registration stub |
| notification (mock) | 8007 | notifications stub |
| payment gateway (mock) | 8008 | payment rail stub |
| frontend | 3000 | React web app |

## Run it

### Local (Python + Node)
```bash
python setup_venvs.py                 # per-service venvs + npm install (once)
python setup_provider.py sqlite       # or: inmemory | (setup_env.py PW postgres) | setup_mysql.py … | setup_supabase.py …
python run_all.py                     # starts all services + frontend
```

### Docker (one command)
```bash
python docker_up.py inmemory          # or: sqlite | postgres | mysql | supabase
# open http://localhost:3000
```

## Documentation
- **Setup (local)** → `STUDENT_SETUP_MANUAL.html`
- **Setup (Docker)** → `DOCKER_SETUP_MANUAL.html`
- **Codebase architecture** → `CODEBASE_ARCHITECTURE_GUIDE.html`
- **Enterprise audit** → `ENTERPRISE_AUDIT_REPORT.html`
- **Remediation plan** → `ENTERPRISE_REMEDIATION_PLAN.md`

## Architecture (per stateful service)
```
app/
  api/          # HTTP routes (thin controllers)
  services/     # business logic
  repositories/ # data access (interface + impls)
  database/     # providers (factory) + ORM models
  models/       # Pydantic DTOs
  dependencies/ # DI wiring
  integration/  # inter-service HTTP clients
  exceptions/   # typed errors
  config/       # settings (pydantic-settings)
```

## Configuration
Each service reads a local `.env` (see `.env.example`). Select the database with
`DATABASE_PROVIDER=sqlite|inmemory|postgres|mysql|supabase`.

> **Security note:** default JWT / internal-API-key values in `.env.example` are
> **development placeholders**. Production configuration must be injected at
> deploy time (secrets manager / K8s Secrets) — never committed. See the
> remediation plan.

## Testing
```bash
cd <service> && DATABASE_PROVIDER=inmemory venv/Scripts/python -m pytest -q
```

## License
Internal training material.
