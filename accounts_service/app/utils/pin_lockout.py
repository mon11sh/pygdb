"""
Accounts Service - PIN Brute-Force Lockout

Lightweight in-memory failed-attempt counter with time-based lockout for the
PIN-verify path.

NOTE: State is held in a module-level dict and is therefore PER-PROCESS. It is
intentionally simple and not shared across workers/replicas. For a multi-process
or multi-instance deployment this must be backed by a shared store (e.g. Redis).
A threading.Lock guards the dict so it is safe within a single process even under
a threaded server.

Policy: after MAX_FAILURES consecutive failures an account_number is locked for
LOCKOUT_SECONDS. A successful verification (or a natural lock expiry) resets the
counter.

Author: GDB Architecture Team
"""

import threading
import time
from typing import Dict, Tuple

# Tunable policy
MAX_FAILURES = 5          # consecutive failures before lockout
LOCKOUT_SECONDS = 15 * 60  # 15 minutes

# account_number -> (fail_count, locked_until_epoch_seconds)
_attempts: Dict[int, Tuple[int, float]] = {}
_lock = threading.Lock()


class AccountLockedError(Exception):
    """Raised when an account is currently locked out due to failed PIN attempts."""

    def __init__(self, account_number: int, retry_after_seconds: int):
        """Build the lockout error with retry guidance.

        Args:
            account_number: The account that is currently locked out.
            retry_after_seconds: Seconds the caller should wait before the
                lock expires and a retry is permitted.
        """
        self.account_number = account_number
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Account {account_number} is temporarily locked due to too many "
            f"failed PIN attempts. Try again in {retry_after_seconds} seconds."
        )


def check_locked(account_number: int) -> None:
    """
    Raise AccountLockedError if the account is currently locked.

    Call this BEFORE attempting PIN verification. If the existing lock has
    already expired it is cleared and the account is treated as unlocked.
    """
    now = time.time()
    with _lock:
        entry = _attempts.get(account_number)
        if not entry:
            return
        fail_count, locked_until = entry
        if locked_until and now < locked_until:
            raise AccountLockedError(
                account_number,
                retry_after_seconds=int(locked_until - now) + 1,
            )
        if locked_until and now >= locked_until:
            # Lock expired -> reset so the user gets a fresh set of attempts.
            _attempts.pop(account_number, None)


def is_locked(account_number: int) -> bool:
    """Non-raising convenience check for the current lock state."""
    try:
        check_locked(account_number)
        return False
    except AccountLockedError:
        return True


def record_failure(account_number: int) -> None:
    """
    Record a failed PIN attempt. Locks the account once MAX_FAILURES
    consecutive failures are reached.
    """
    now = time.time()
    with _lock:
        fail_count, locked_until = _attempts.get(account_number, (0, 0.0))
        # If a prior lock has expired, start counting fresh.
        if locked_until and now >= locked_until:
            fail_count = 0
            locked_until = 0.0
        fail_count += 1
        if fail_count >= MAX_FAILURES:
            locked_until = now + LOCKOUT_SECONDS
        _attempts[account_number] = (fail_count, locked_until)


def record_success(account_number: int) -> None:
    """Clear the failed-attempt counter after a successful verification."""
    with _lock:
        _attempts.pop(account_number, None)


def reset(account_number: int = None) -> None:
    """Test/maintenance helper: clear one account's state, or all if None."""
    with _lock:
        if account_number is None:
            _attempts.clear()
        else:
            _attempts.pop(account_number, None)
