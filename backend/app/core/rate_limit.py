"""In-memory sliding-window rate limiter.

Deliberately stdlib-only (no Redis) to match this project's current
single-process deploy target. Login attempts already have their own
per-account lockout (see auth_service.py); this covers every other
endpoint, which today have no throttling at all.

Caveat: state is per-process. If this ever runs behind multiple
uvicorn/gunicorn workers or multiple instances, each process counts
independently, so the effective limit becomes (limit * worker_count).
Fine for a single-instance deploy; swap for a Redis-backed counter
before scaling out.
"""

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.exceptions import RateLimitError

# (max_requests, window_seconds). Generous enough not to bother normal
# usage (dashboards polling, paginated tables) while stopping scripted
# hammering of the API.
DEFAULT_LIMIT = 300
DEFAULT_WINDOW_SECONDS = 60


class SlidingWindowRateLimiter:
    def __init__(self, limit: int = DEFAULT_LIMIT, window_seconds: int = DEFAULT_WINDOW_SECONDS):
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        """Raises RateLimitError if `key` has exceeded the limit within
        the current window; otherwise records this hit."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= self.limit:
                raise RateLimitError()
            hits.append(now)
            self._maybe_sweep(cutoff)

    def _maybe_sweep(self, cutoff: float) -> None:
        # Keys are only ever added, so without this every distinct IP/user
        # ever seen would keep an (empty) deque forever. Sweeping is O(keys),
        # so only do it once the table has grown well past a normal working
        # set. Caller holds self._lock.
        if len(self._hits) < 10_000:
            return
        stale = [k for k, hits in self._hits.items() if not hits or hits[-1] < cutoff]
        for k in stale:
            del self._hits[k]


rate_limiter = SlidingWindowRateLimiter()
