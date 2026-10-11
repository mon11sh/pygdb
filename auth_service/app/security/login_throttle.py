"""
Lightweight in-memory login throttle / lockout.

Tracks failed login attempts per identifier and locks the identifier out for a
cooldown period after too many consecutive failures. This is a defensive
measure against credential-stuffing / brute-force attacks.

IMPORTANT: This state lives in a plain module-level dict and is therefore
PER-PROCESS ONLY. It is not shared across workers/replicas and is lost on
restart. A production deployment MUST back this with a shared store (e.g.
Redis) so limits are enforced globally.

Author: GDB Architecture Team
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Tunables
MAX_FAILURES = 5           # consecutive failures before lockout
LOCKOUT_MINUTES = 15       # how long an identifier stays locked

# login_id -> (fail_count, locked_until)
# locked_until is None when not locked.
_attempts: Dict[str, Tuple[int, "datetime | None"]] = {}


def is_locked(login_id: str) -> bool:
    """Return True if the identifier is currently locked out."""
    entry = _attempts.get(login_id)
    if not entry:
        return False

    _fail_count, locked_until = entry
    if locked_until is None:
        return False

    if datetime.now(UTC) >= locked_until:
        # Lock has expired; clear it so the caller starts fresh.
        _attempts.pop(login_id, None)
        return False

    return True


def record_failure(login_id: str) -> None:
    """Record a failed login attempt, locking the identifier past the threshold."""
    fail_count, _locked_until = _attempts.get(login_id, (0, None))
    fail_count += 1

    if fail_count >= MAX_FAILURES:
        locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_MINUTES)
        _attempts[login_id] = (fail_count, locked_until)
        logger.warning(
            f"Login locked out for '{login_id}' after {fail_count} failures "
            f"until {locked_until.isoformat()}"
        )
    else:
        _attempts[login_id] = (fail_count, None)


def record_success(login_id: str) -> None:
    """Reset the counter for an identifier after a successful login."""
    _attempts.pop(login_id, None)


def reset(login_id: str) -> None:
    """Explicitly clear any state for an identifier (test/admin helper)."""
    _attempts.pop(login_id, None)


def clear_all() -> None:
    """Clear all throttle state (primarily for tests)."""
    _attempts.clear()
