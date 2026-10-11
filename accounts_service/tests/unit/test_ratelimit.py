"""Token-bucket RateLimiter tests (gdb_common.ratelimit)."""

import pytest

from gdb_common.ratelimit import RateLimiter


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_allows_up_to_capacity_then_denies():
    rl = RateLimiter(capacity=3, refill_per_sec=1.0, clock=_Clock())
    assert all(rl.check("k")[0] for _ in range(3))
    ok, retry = rl.check("k")
    assert not ok and retry > 0


def test_refill_over_time():
    clk = _Clock()
    rl = RateLimiter(capacity=1, refill_per_sec=1.0, clock=clk)
    assert rl.check("k")[0] is True
    assert rl.check("k")[0] is False
    clk.t = 1.0  # one second -> one token refilled
    assert rl.check("k")[0] is True


def test_keys_are_independent():
    rl = RateLimiter(capacity=1, refill_per_sec=0.001)
    assert rl.check("a")[0] is True
    assert rl.check("b")[0] is True   # different client unaffected
    assert rl.check("a")[0] is False  # a is now empty


def test_retry_after_reflects_refill_rate():
    rl = RateLimiter(capacity=1, refill_per_sec=2.0, clock=_Clock())  # 2 tokens/sec
    rl.check("k")                     # spend the only token
    ok, retry = rl.check("k")
    assert not ok
    assert abs(retry - 0.5) < 1e-9    # 1 token at 2/sec == 0.5s


def test_reset_refills_immediately():
    rl = RateLimiter(capacity=1, refill_per_sec=0.001)
    rl.check("k")
    assert rl.check("k")[0] is False
    rl.reset("k")
    assert rl.check("k")[0] is True


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        RateLimiter(capacity=0, refill_per_sec=1.0)
    with pytest.raises(ValueError):
        RateLimiter(capacity=1, refill_per_sec=0.0)
