"""Gateway configuration: logical service name -> backend base URL.

Overridable per service via env var GATEWAY_<NAME>_URL (e.g. GATEWAY_ACCOUNTS_URL),
so the same image works for local (localhost ports) and Docker (compose DNS names).
"""

import os

# Logical service name -> default local backend base URL.
DEFAULT_BACKENDS = {
    "accounts": "http://localhost:8001",
    "transactions": "http://localhost:8002",
    "users": "http://localhost:8003",
    "auth": "http://localhost:8004",
    "aadhar": "http://localhost:8005",
    "company": "http://localhost:8006",
    "notification": "http://localhost:8007",
    "payment": "http://localhost:8008",
}


def backends_from_env(defaults=None):
    """Return {service: base_url}, applying GATEWAY_<NAME>_URL overrides."""
    backends = dict(defaults or DEFAULT_BACKENDS)
    for name in list(backends):
        override = os.getenv(f"GATEWAY_{name.upper()}_URL")
        if override:
            backends[name] = override.rstrip("/")
    return backends


def rate_limit_from_env():
    """Return (capacity, refill_per_sec) for the gateway limiter, or None if off.

    GATEWAY_RATE_LIMIT_PER_MIN=0 (default) disables limiting. When >0, the sustained
    rate is that many requests/minute per client IP; GATEWAY_RATE_BURST overrides
    the burst capacity (default: one minute's worth).
    """
    try:
        per_min = int(os.getenv("GATEWAY_RATE_LIMIT_PER_MIN", "0") or 0)
    except ValueError:
        per_min = 0
    if per_min <= 0:
        return None
    try:
        burst = int(os.getenv("GATEWAY_RATE_BURST", str(per_min)) or per_min)
    except ValueError:
        burst = per_min
    return max(1, burst), per_min / 60.0
