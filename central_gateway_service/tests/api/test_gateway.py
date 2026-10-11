"""API Gateway routing/proxy tests (httpx MockTransport backends)."""

import httpx
from fastapi.testclient import TestClient

from gdb_common import StaticResolver, RateLimiter
from app.main import build_gateway_app

RESOLVER = StaticResolver({
    "accounts": "http://accounts:8001",
    "auth": "http://auth:8004",
})


def _client(captured, status=200):
    def handler(request):
        captured.append(request)
        return httpx.Response(status, json={"ok": True})
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_routes_first_segment_to_backend_and_strips_it():
    captured = []
    app = build_gateway_app(resolver=RESOLVER, client=_client(captured))
    r = TestClient(app).get("/accounts/api/v1/accounts/101")
    assert r.status_code == 200
    assert str(captured[0].url).startswith("http://accounts:8001/api/v1/accounts/101")
    assert captured[0].method == "GET"


def test_forwards_method_query_and_body():
    captured = []
    app = build_gateway_app(resolver=RESOLVER, client=_client(captured))
    r = TestClient(app).post("/auth/api/v1/auth/login?foo=bar", json={"u": "admin"})
    assert r.status_code == 200
    req = captured[0]
    assert req.method == "POST"
    assert "auth:8004/api/v1/auth/login" in str(req.url)
    assert "foo=bar" in str(req.url)
    assert b'"u"' in req.content


def test_preserves_client_host_header():
    # Backends behind TrustedHostMiddleware must see the client's Host, not the
    # internal target host — otherwise they reject with 400 "Invalid host header".
    captured = []
    app = build_gateway_app(resolver=RESOLVER, client=_client(captured))
    TestClient(app).get("/accounts/api/v1/health", headers={"host": "localhost:8000"})
    assert captured[0].headers["host"] == "localhost:8000"


def test_unknown_service_returns_404():
    app = build_gateway_app(resolver=RESOLVER, client=_client([]))
    assert TestClient(app).get("/nope/x").status_code == 404


def test_status_code_passthrough():
    app = build_gateway_app(resolver=RESOLVER, client=_client([], status=418))
    assert TestClient(app).get("/accounts/x").status_code == 418


def test_health_endpoint():
    app = build_gateway_app(resolver=RESOLVER, client=_client([]))
    assert TestClient(app).get("/health").json()["status"] == "healthy"


def test_env_override_resolver(monkeypatch):
    # Default resolver picks up GATEWAY_<NAME>_URL overrides.
    monkeypatch.setenv("GATEWAY_ACCOUNTS_URL", "http://accounts-docker:8001")
    captured = []
    app = build_gateway_app(client=_client(captured))  # no explicit resolver
    TestClient(app).get("/accounts/ping")
    assert str(captured[0].url).startswith("http://accounts-docker:8001/ping")


def test_rate_limit_returns_429_after_capacity():
    # capacity 2, negligible refill during the test -> 3rd request is throttled.
    limiter = RateLimiter(capacity=2, refill_per_sec=0.0001)
    app = build_gateway_app(resolver=RESOLVER, client=_client([]), rate_limiter=limiter)
    c = TestClient(app)
    assert c.get("/accounts/x").status_code == 200
    assert c.get("/accounts/x").status_code == 200
    r = c.get("/accounts/x")
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


def test_rate_limit_exempts_health():
    limiter = RateLimiter(capacity=1, refill_per_sec=0.0001)
    app = build_gateway_app(resolver=RESOLVER, client=_client([]), rate_limiter=limiter)
    c = TestClient(app)
    for _ in range(5):
        assert c.get("/health").status_code == 200


def test_rate_limit_from_env_disabled_by_default():
    # No GATEWAY_RATE_LIMIT_PER_MIN -> no limiter attached, requests never 429.
    app = build_gateway_app(resolver=RESOLVER, client=_client([]))
    assert app.state.rate_limiter is None
    c = TestClient(app)
    for _ in range(10):
        assert c.get("/accounts/x").status_code == 200
