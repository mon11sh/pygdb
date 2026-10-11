"""
Service Discovery pattern (client-side discovery with a registry).

Instead of hard-coding peer URLs, services REGISTER themselves with a registry
and clients RESOLVE a logical name to a live instance (round-robin across healthy
instances, TTL-expiring stale ones). In production this would be Consul/Eureka;
here it's a small in-process ServiceRegistry that can also be exposed as an HTTP
service via `create_registry_app()`. `StaticResolver` is the config-based fallback.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional

from pydantic import BaseModel, Field


class Registration(BaseModel):
    """Registry register/heartbeat/deregister payload."""

    name: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    ttl: float = 30.0


@dataclass
class ServiceInstance:
    """A single registered instance of a service, with its TTL bookkeeping."""

    name: str
    url: str
    registered_at: float
    ttl: float

    def is_alive(self, now: float) -> bool:
        """Return True if the instance's TTL has not yet elapsed at `now`.

        Args:
            now: Current clock reading (same clock used at registration).

        Returns:
            True while the time since registration is within the TTL.
        """
        return (now - self.registered_at) <= self.ttl


class ServiceRegistry:
    """In-memory registry: register / heartbeat / TTL-expiry / round-robin resolve."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        """Initialize an empty registry.

        Args:
            clock: Monotonic time source, injectable for deterministic tests.
        """
        self._clock = clock
        self._services: Dict[str, List[ServiceInstance]] = {}
        self._rr: Dict[str, int] = {}

    def register(self, name: str, url: str, ttl: float = 30.0) -> None:
        """Register an instance URL under a service name (idempotent by URL).

        Re-registering an existing (name, url) refreshes its timestamp and TTL
        instead of creating a duplicate.

        Args:
            name: Logical service name.
            url: Base URL of the instance being registered.
            ttl: Seconds the registration stays alive without a heartbeat.
        """
        instances = self._services.setdefault(name, [])
        for inst in instances:
            if inst.url == url:  # refresh existing
                inst.registered_at = self._clock()
                inst.ttl = ttl
                return
        instances.append(ServiceInstance(name, url, self._clock(), ttl))

    def heartbeat(self, name: str, url: str) -> bool:
        """Refresh the TTL of an already-registered instance.

        Args:
            name: Logical service name.
            url: Base URL of the instance to refresh.

        Returns:
            True if a matching instance was found and refreshed, else False.
        """
        for inst in self._services.get(name, []):
            if inst.url == url:
                inst.registered_at = self._clock()
                return True
        return False

    def deregister(self, name: str, url: str) -> None:
        """Remove a specific instance URL from a service (no-op if absent).

        Args:
            name: Logical service name.
            url: Base URL of the instance to remove.
        """
        self._services[name] = [i for i in self._services.get(name, []) if i.url != url]

    def healthy(self, name: str) -> List[ServiceInstance]:
        """Return the currently-alive (non-expired) instances of a service.

        Args:
            name: Logical service name.

        Returns:
            List of instances whose TTL has not yet elapsed.
        """
        now = self._clock()
        return [i for i in self._services.get(name, []) if i.is_alive(now)]

    def resolve(self, name: str) -> Optional[str]:
        """Return one healthy instance URL, round-robining across instances."""
        instances = self.healthy(name)
        if not instances:
            return None
        idx = self._rr.get(name, 0) % len(instances)
        self._rr[name] = idx + 1
        return instances[idx].url

    def names(self) -> List[str]:
        """Return the names of services that currently have healthy instances."""
        return [n for n in self._services if self.healthy(n)]


class StaticResolver:
    """Config-based discovery: resolve a name from a static {name: url} map."""

    def __init__(self, mapping: Mapping[str, str]):
        """Store a copy of the static name -> URL mapping.

        Args:
            mapping: Service name to base URL map (copied defensively).
        """
        self._mapping = dict(mapping)

    def resolve(self, name: str) -> Optional[str]:
        """Return the configured URL for `name`, or None if not mapped.

        Args:
            name: Logical service name to resolve.

        Returns:
            The mapped base URL, or None when the name is unknown.
        """
        return self._mapping.get(name)


def create_registry_app():
    """Build a FastAPI app that exposes a ServiceRegistry over HTTP.

    Deployed as the standalone `registry_service`; imported here so the logic is
    unit-testable with any service venv that has FastAPI.
    """
    from fastapi import FastAPI, HTTPException

    registry = ServiceRegistry()
    app = FastAPI(title="GDB Service Registry", version="1.0.0")
    app.state.registry = registry

    @app.post("/register")
    async def register(reg: Registration):
        """Register (or refresh) a service instance from a request payload."""
        registry.register(reg.name, reg.url, reg.ttl)
        return {"status": "registered", "name": reg.name, "url": reg.url}

    @app.post("/heartbeat")
    async def heartbeat(reg: Registration):
        """Refresh an instance's TTL; 404 if it is not currently registered."""
        if not registry.heartbeat(reg.name, reg.url):
            raise HTTPException(status_code=404, detail="instance not registered")
        return {"status": "ok"}

    @app.delete("/register")
    async def deregister(reg: Registration):
        """Remove a service instance from the registry."""
        registry.deregister(reg.name, reg.url)
        return {"status": "deregistered"}

    @app.get("/resolve/{name}")
    async def resolve(name: str):
        """Resolve a service name to one healthy instance URL; 404 if none."""
        url = registry.resolve(name)
        if not url:
            raise HTTPException(status_code=404, detail=f"no healthy instance for '{name}'")
        return {"name": name, "url": url}

    @app.get("/services")
    async def services():
        """List all services with healthy instances mapped to their URLs."""
        return {n: [i.url for i in registry.healthy(n)] for n in registry.names()}

    @app.get("/health")
    async def health():
        """Liveness probe for the registry service itself."""
        return {"status": "healthy", "service": "service-registry"}

    return app
