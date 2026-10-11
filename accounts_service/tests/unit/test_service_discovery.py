"""Service Discovery pattern tests (gdb_common.discovery)."""

from fastapi.testclient import TestClient

from gdb_common.discovery import ServiceRegistry, StaticResolver, create_registry_app


class _Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_round_robin_across_instances():
    reg = ServiceRegistry()
    reg.register("accounts", "http://a:8001")
    reg.register("accounts", "http://b:8001")
    got = {reg.resolve("accounts") for _ in range(4)}
    assert got == {"http://a:8001", "http://b:8001"}


def test_ttl_expiry_and_heartbeat():
    clock = _Clock()
    reg = ServiceRegistry(clock=clock)
    reg.register("svc", "http://x", ttl=10)
    assert reg.resolve("svc") == "http://x"
    clock.now = 11  # past ttl
    assert reg.resolve("svc") is None
    # heartbeat brings it back
    reg.heartbeat("svc", "http://x")
    assert reg.resolve("svc") == "http://x"


def test_deregister_removes_instance():
    reg = ServiceRegistry()
    reg.register("svc", "http://x")
    reg.deregister("svc", "http://x")
    assert reg.resolve("svc") is None


def test_static_resolver_fallback():
    resolver = StaticResolver({"accounts": "http://localhost:8001"})
    assert resolver.resolve("accounts") == "http://localhost:8001"
    assert resolver.resolve("unknown") is None


def test_registry_http_app():
    client = TestClient(create_registry_app())
    assert client.post("/register", json={"name": "accounts", "url": "http://a:8001"}).status_code == 200
    r = client.get("/resolve/accounts")
    assert r.status_code == 200 and r.json()["url"] == "http://a:8001"
    assert client.get("/services").json() == {"accounts": ["http://a:8001"]}
    assert client.get("/resolve/missing").status_code == 404
    assert client.request("DELETE", "/register", json={"name": "accounts", "url": "http://a:8001"}).status_code == 200
    assert client.get("/resolve/accounts").status_code == 404
