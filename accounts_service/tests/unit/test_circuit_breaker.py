"""Circuit Breaker pattern tests (gdb_common.resilience)."""

import pytest

from gdb_common.resilience import BreakerState, CircuitBreaker, CircuitBreakerOpen


class _FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


async def _ok():
    return "ok"


async def _boom():
    raise RuntimeError("downstream failed")


async def test_opens_after_threshold_then_fails_fast():
    cb = CircuitBreaker("dep", failure_threshold=3, reset_timeout=10)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            await cb.call(_boom)
    assert cb.state is BreakerState.OPEN
    # Now calls short-circuit without invoking the callable.
    with pytest.raises(CircuitBreakerOpen):
        await cb.call(_ok)


async def test_half_open_after_cooldown_then_closes_on_success():
    clock = _FakeClock()
    cb = CircuitBreaker("dep", failure_threshold=2, reset_timeout=10, _clock=clock)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(_boom)
    assert cb.state is BreakerState.OPEN

    clock.now = 10.5  # cooldown elapsed
    assert cb.state is BreakerState.HALF_OPEN
    assert await cb.call(_ok) == "ok"  # trial call succeeds -> CLOSED
    assert cb.state is BreakerState.CLOSED


async def test_success_resets_failure_count():
    cb = CircuitBreaker("dep", failure_threshold=3)
    with pytest.raises(RuntimeError):
        await cb.call(_boom)
    await cb.call(_ok)  # resets the counter
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(_boom)
    assert cb.state is BreakerState.CLOSED  # 2 < threshold because it reset
