"""A small in-process cache for figures that everyone sees the same and
that may be a few seconds old (see api/dashboard.py).

Each API worker process keeps its own copy. When an entry expires and
several requests want it at once, one computes it and the others wait
for that answer instead of all running the same queries.
"""

import threading
import time
from collections.abc import Callable, Hashable
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: float):
        self.ttl_seconds = ttl_seconds
        self._entries: dict[Hashable, tuple[float, Any]] = {}
        self._locks: dict[Hashable, threading.Lock] = {}
        self._guard = threading.Lock()

    def _fresh(self, key: Hashable) -> tuple[bool, Any]:
        entry = self._entries.get(key)
        if entry is not None and time.monotonic() - entry[0] < self.ttl_seconds:
            return True, entry[1]
        return False, None

    def get_or_compute(self, key: Hashable, compute: Callable[[], Any]) -> Any:
        hit, value = self._fresh(key)
        if hit:
            return value
        with self._guard:
            lock = self._locks.setdefault(key, threading.Lock())
        with lock:
            hit, value = self._fresh(key)  # another request may have just filled it
            if hit:
                return value
            value = compute()  # an error is raised to the caller and nothing is kept
            now = time.monotonic()
            # Drop what has expired (e.g. yesterday's keys) so a long-running
            # worker doesn't accumulate them.
            for old in [k for k, (at, _) in self._entries.items() if now - at >= self.ttl_seconds]:
                self._entries.pop(old, None)
            self._entries[key] = (now, value)
            return value

    def clear(self) -> None:
        self._entries.clear()
