"""
Resilience primitives for inter-service calls (Circuit Breaker pattern).

A circuit breaker stops a service from hammering a failing dependency: after N
consecutive failures it "opens" and fails fast for a cooldown, then "half-opens"
to test recovery with a single trial call before closing again.

    breaker = CircuitBreaker("accounts", failure_threshold=5, reset_timeout=30)
    result = await breaker.call(lambda: client.get(url))   # async callable
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class BreakerState(str, Enum):
    """The three states of the circuit breaker's lifecycle."""

    CLOSED = "closed"       # normal — calls pass through
    OPEN = "open"           # tripped — calls fail fast
    HALF_OPEN = "half_open"  # cooldown elapsed — allow one trial call


class CircuitBreakerOpen(Exception):
    """Raised when a call is rejected because the breaker is OPEN."""

    def __init__(self, name: str):
        """Record which breaker rejected the call.

        Args:
            name: Name of the breaker that is OPEN.
        """
        super().__init__(f"Circuit breaker '{name}' is OPEN — failing fast")
        self.name = name


class CircuitBreaker:
    """A minimal async circuit breaker (per downstream dependency)."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: float = 30.0,
        _clock: Callable[[], float] = time.monotonic,
    ):
        """Configure the breaker's failure threshold and cooldown.

        Args:
            name: Identifier for the downstream dependency (used in errors).
            failure_threshold: Consecutive failures that trip the breaker OPEN.
            reset_timeout: Seconds to stay OPEN before allowing a trial call.
            _clock: Monotonic time source, injectable for deterministic tests.
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._clock = _clock
        self._failures = 0
        self._state = BreakerState.CLOSED
        self._opened_at = 0.0

    @property
    def state(self) -> BreakerState:
        """Current breaker state, auto-transitioning OPEN -> HALF_OPEN on cooldown."""
        # Auto-transition OPEN -> HALF_OPEN once the cooldown has elapsed.
        if self._state is BreakerState.OPEN and (self._clock() - self._opened_at) >= self.reset_timeout:
            self._state = BreakerState.HALF_OPEN
        return self._state

    def _record_success(self) -> None:
        """Reset the failure count and close the breaker after a good call."""
        self._failures = 0
        self._state = BreakerState.CLOSED

    def _record_failure(self) -> None:
        """Count a failure and trip the breaker OPEN once the threshold is hit."""
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._state = BreakerState.OPEN
            self._opened_at = self._clock()

    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        """Run the async callable through the breaker.

        Fails fast with CircuitBreakerOpen when OPEN; a trial call in HALF_OPEN
        closes the breaker on success or re-opens it on failure.
        """
        if self.state is BreakerState.OPEN:
            raise CircuitBreakerOpen(self.name)
        try:
            result = await func()
        except Exception:
            self._record_failure()
            raise
        else:
            self._record_success()
            return result
