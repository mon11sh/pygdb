"""
Token-bucket rate limiter (in-process).

Each key (e.g. a client IP) gets a bucket that holds up to `capacity` tokens and
refills at `refill_per_sec`. Each request spends one token; when the bucket is
empty the request is denied and `retry_after` says how long until one token is
available. Bursts up to `capacity` are allowed; the sustained rate is
`refill_per_sec`.

    limiter = RateLimiter(capacity=100, refill_per_sec=100/60)  # 100/min, burst 100
    ok, retry_after = limiter.check(client_ip)
    if not ok:
        return 429, {"Retry-After": ceil(retry_after)}

The clock is injectable so behaviour is deterministic in tests.
"""

from __future__ import annotations

import time
from typing import Callable, Dict, Tuple


class RateLimiter:
    """Token-bucket rate limiter keyed by an arbitrary string (e.g. a client IP).

    Each key gets its own bucket holding up to ``capacity`` tokens that refill at
    ``refill_per_sec``; each allowed request spends one token.
    """

    def __init__(
        self,
        capacity: int,
        refill_per_sec: float,
        clock: Callable[[], float] = time.monotonic,
    ):
        """Configure the bucket capacity and refill rate.

        Args:
            capacity: Maximum tokens a bucket holds (the allowed burst size).
            refill_per_sec: Sustained rate at which tokens replenish per second.
            clock: Monotonic time source, injectable for deterministic tests.

        Raises:
            ValueError: If ``capacity`` < 1 or ``refill_per_sec`` <= 0.
        """
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        if refill_per_sec <= 0:
            raise ValueError("refill_per_sec must be > 0")
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self._clock = clock
        self._buckets: Dict[str, Tuple[float, float]] = {}  # key -> (tokens, last_ts)

    def check(self, key: str) -> Tuple[bool, float]:
        """Spend one token for `key`. Returns (allowed, retry_after_seconds)."""
        now = self._clock()
        tokens, last = self._buckets.get(key, (float(self.capacity), now))

        # Refill for the elapsed time, capped at capacity.
        tokens = min(self.capacity, tokens + (now - last) * self.refill_per_sec)

        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, now)
            return True, 0.0

        # Not enough for one token — deny and report the wait.
        retry_after = (1.0 - tokens) / self.refill_per_sec
        self._buckets[key] = (tokens, now)
        return False, retry_after

    def reset(self, key: str | None = None) -> None:
        """Clear one key (or all) — handy for tests and admin flushes."""
        if key is None:
            self._buckets.clear()
        else:
            self._buckets.pop(key, None)
