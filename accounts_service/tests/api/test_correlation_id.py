"""
Correlation-ID middleware tests (Enterprise remediation Phase 2, observability).

Every response carries an X-Correlation-ID; an inbound one is honoured so a
single id can be traced across services.
"""

from fastapi.testclient import TestClient

from app.main import app


# base_url sets an allowed Host (accounts uses TrustedHostMiddleware).
def test_correlation_id_minted_when_absent():
    with TestClient(app, base_url="http://localhost") as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        cid = resp.headers.get("X-Correlation-ID")
        assert cid and len(cid) >= 8


def test_correlation_id_echoed_when_provided():
    with TestClient(app, base_url="http://localhost") as client:
        resp = client.get("/health", headers={"X-Correlation-ID": "cid-abc-123"})
        assert resp.status_code == 200
        assert resp.headers.get("X-Correlation-ID") == "cid-abc-123"
