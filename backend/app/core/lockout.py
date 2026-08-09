"""In-memory attempt-count lockout, keyed by an arbitrary string.

Same shape as auth_service.py's per-user lockout (N failures -> locked
for M minutes) but for callers that don't have a persistent account row
to store failed_login_attempts/locked_until on -- e.g. the customer
portal's mobile-number verification, which is keyed by project instead
of a user account.

Deliberately stdlib-only and per-process, same trade-off and same
caveat as core/rate_limit.py: fine for a single-instance deploy, would
need a shared (Redis/DB) store before running multiple workers.
"""

import time
from threading import Lock

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_LOCKOUT_SECONDS = 15 * 60


class LockoutTracker:
    def __init__(self, max_attempts: int = DEFAULT_MAX_ATTEMPTS, lockout_seconds: int = DEFAULT_LOCKOUT_SECONDS):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        # key -> (failed_count, locked_until_monotonic | None)
        self._state: dict[str, tuple[int, float | None]] = {}
        self._lock = Lock()

    def seconds_locked(self, key: str) -> float:
        """> 0 if `key` is currently locked out (and for how much longer); 0 otherwise."""
        with self._lock:
            _, locked_until = self._state.get(key, (0, None))
            if locked_until is None:
                return 0
            remaining = locked_until - time.monotonic()
            return remaining if remaining > 0 else 0

    def register_failure(self, key: str) -> None:
        with self._lock:
            count, locked_until = self._state.get(key, (0, None))
            count += 1
            if count >= self.max_attempts:
                locked_until = time.monotonic() + self.lockout_seconds
            self._state[key] = (count, locked_until)

    def register_success(self, key: str) -> None:
        with self._lock:
            self._state.pop(key, None)
