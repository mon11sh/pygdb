"""
GDB API Gateway — the single entry point (API Gateway pattern).

Clients call the gateway once; it routes each request to the right backend
microservice, centralising cross-cutting concerns (CORS, correlation-id
propagation, a single public port) instead of repeating them in every service.

Routing is path-based: the FIRST path segment is the logical service name and the
remainder is forwarded verbatim to that backend.

    GET /accounts/api/v1/accounts/101   ->  http://accounts-backend/api/v1/accounts/101
    POST /auth/api/v1/auth/login        ->  http://auth-backend/api/v1/auth/login

Backends are located through the Service Discovery resolver (StaticResolver by
default, backed by config / env; swappable for the live ServiceRegistry).

Run:  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import math

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gdb_common import install_observability, StaticResolver, RateLimiter

from app.config import backends_from_env, rate_limit_from_env

# Hop-by-hop headers must not be forwarded through a proxy (RFC 7230 §6.1).
_HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length",
}


def build_gateway_app(resolver=None, client: httpx.AsyncClient | None = None,
                      timeout: float = 30.0, rate_limiter: RateLimiter | None = None) -> FastAPI:
    """Build the gateway app.

    resolver: anything with .resolve(name) -> base_url | None (defaults to a
        StaticResolver over config/env). client: injectable httpx.AsyncClient
        (tests pass one backed by a MockTransport). rate_limiter: an explicit
        RateLimiter; when omitted, one is built from env (disabled by default).
    """
    resolver = resolver or StaticResolver(backends_from_env())
    if rate_limiter is None:
        cfg = rate_limit_from_env()
        if cfg is not None:
            rate_limiter = RateLimiter(capacity=cfg[0], refill_per_sec=cfg[1])

    app = FastAPI(title="GDB API Gateway", version="1.0.0")
    app.state.resolver = resolver
    app.state.client = client  # None -> create per-request
    app.state.rate_limiter = rate_limiter

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    if rate_limiter is not None:
        @app.middleware("http")
        async def _rate_limit(request: Request, call_next):
            """Apply per-client-IP token-bucket rate limiting.

            Health checks and CORS preflight are exempt; over-limit requests get
            a 429 with a Retry-After header instead of being proxied.
            """
            # Exempt health checks and CORS preflight from limiting.
            if request.method == "OPTIONS" or request.url.path == "/health":
                return await call_next(request)
            key = request.client.host if request.client else "unknown"
            allowed, retry_after = rate_limiter.check(key)
            if not allowed:
                return JSONResponse(
                    {"detail": "rate limit exceeded"},
                    status_code=429,
                    headers={"Retry-After": str(max(1, math.ceil(retry_after)))},
                )
            return await call_next(request)

    @app.get("/health")
    async def health():
        """Liveness probe for the gateway itself (does not check backends)."""
        return {"status": "healthy", "service": "api-gateway"}

    @app.api_route(
        "/{service}/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def proxy(service: str, path: str, request: Request):
        """Reverse-proxy a request to the resolved backend for `service`.

        Resolves the first path segment to a backend base URL, forwards the
        method, remaining path, query string, headers (minus hop-by-hop, with
        the client Host preserved), and body, then relays the backend response.

        Args:
            service: Logical service name (first path segment).
            path: Remainder of the path forwarded verbatim to the backend.
            request: The inbound request being proxied.

        Returns:
            The backend's Response, or a 404 when the service is unknown/
            unavailable and a 502 when the backend is unreachable.
        """
        base = resolver.resolve(service)
        if base is None:
            return Response(
                content=f'{{"detail":"unknown or unavailable service \'{service}\'"}}',
                status_code=404, media_type="application/json",
            )

        url = f"{base.rstrip('/')}/{path}"
        fwd_headers = {k: v for k, v in request.headers.items()
                       if k.lower() not in _HOP_BY_HOP}
        # Preserve the client's Host so a backend behind TrustedHostMiddleware
        # still sees an allowed host (standard reverse-proxy behavior). Without
        # this, httpx would set Host to the internal target (e.g. accounts-service)
        # and the backend rejects it with 400 "Invalid host header".
        incoming_host = request.headers.get("host")
        if incoming_host:
            fwd_headers["host"] = incoming_host
        body = await request.body()

        own_client = app.state.client is None
        active = app.state.client or httpx.AsyncClient(timeout=timeout)
        try:
            upstream = await active.request(
                request.method, url,
                params=dict(request.query_params),
                content=body, headers=fwd_headers,
            )
        except httpx.RequestError as exc:
            return Response(
                content=f'{{"detail":"backend \'{service}\' unreachable: {exc.__class__.__name__}"}}',
                status_code=502, media_type="application/json",
            )
        finally:
            if own_client:
                await active.aclose()

        resp_headers = {k: v for k, v in upstream.headers.items()
                        if k.lower() not in _HOP_BY_HOP}
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=resp_headers,
            media_type=upstream.headers.get("content-type"),
        )

    return app


app = build_gateway_app()
install_observability(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
