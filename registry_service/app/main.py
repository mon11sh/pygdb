"""
GDB Service Registry — standalone service for the Service Discovery pattern.

Services POST /register (and periodically /heartbeat); clients GET /resolve/{name}
to obtain a live instance URL (round-robin, TTL-expiring). The registry logic
lives in gdb_common.discovery so it stays shared and unit-tested.

Run:  uvicorn app.main:app --host 0.0.0.0 --port 8010
"""

from gdb_common import install_observability
from gdb_common.discovery import create_registry_app

app = create_registry_app()
install_observability(app)   # correlation id + security headers + JSON logs


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8010)
