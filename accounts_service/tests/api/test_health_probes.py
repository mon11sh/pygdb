"""Liveness/readiness probe tests (Enterprise remediation Phase 2)."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_live_ready_all_200():
    with TestClient(app, base_url="http://localhost") as client:
        assert client.get("/health").status_code == 200
        assert client.get("/live").json() == {"status": "alive"}
        assert client.get("/ready").json() == {"status": "ready"}
