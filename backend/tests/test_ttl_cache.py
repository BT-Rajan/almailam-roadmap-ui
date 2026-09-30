"""Dashboard figures are cached per API worker for a few seconds
(app/core/ttl_cache.py, api/dashboard.py).

Standard library only. Run from the backend directory:
    python -m unittest discover -s tests
"""

import threading
import time
import unittest
from datetime import date
import json
from unittest import mock

from app.api import dashboard as dashboard_api
from app.core import ttl_cache
from app.core.ttl_cache import TTLCache


class TTLCacheTest(unittest.TestCase):
    def setUp(self):
        self.clock = [100.0]
        patcher = mock.patch.object(ttl_cache.time, "monotonic", side_effect=lambda: self.clock[0])
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_reuses_until_it_expires(self):
        cache, calls = TTLCache(30), []
        compute = lambda: calls.append(1) or len(calls)  # noqa: E731
        self.assertEqual(cache.get_or_compute("k", compute), 1)
        self.clock[0] += 29
        self.assertEqual(cache.get_or_compute("k", compute), 1)
        self.clock[0] += 2
        self.assertEqual(cache.get_or_compute("k", compute), 2)

    def test_an_error_is_not_kept(self):
        cache = TTLCache(30)

        def fail():
            raise RuntimeError("database down")

        with self.assertRaises(RuntimeError):
            cache.get_or_compute("k", fail)
        self.assertEqual(cache.get_or_compute("k", lambda: "ok"), "ok")

    def test_expired_keys_are_dropped(self):
        cache = TTLCache(30)
        cache.get_or_compute("yesterday", lambda: 1)
        self.clock[0] += 31
        cache.get_or_compute("today", lambda: 2)
        self.assertEqual(set(cache._entries), {"today"})


class SingleFlightTest(unittest.TestCase):
    def test_many_requests_at_once_compute_once(self):
        cache, calls = TTLCache(30), []
        started = threading.Event()

        def slow():
            calls.append(1)
            started.set()
            time.sleep(0.2)
            return "figures"

        results = []
        threads = [threading.Thread(target=lambda: results.append(cache.get_or_compute("k", slow))) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(calls), 1)
        self.assertEqual(results, ["figures"] * 8)


class DashboardEndpointCacheTest(unittest.TestCase):
    def setUp(self):
        dashboard_api.cache.clear()
        self.addCleanup(dashboard_api.cache.clear)

    def test_a_tab_is_computed_once_per_day_within_the_window(self):
        today = [date(2026, 9, 30)]
        with mock.patch.object(dashboard_api, "kuwait_today", side_effect=lambda: today[0]), \
                mock.patch.object(dashboard_api.dashboard_service, "financials_tab", side_effect=lambda db: {"day": today[0]}) as tab:
            first = dashboard_api.financials_tab(db=None)
            again = dashboard_api.financials_tab(db=None)
            self.assertEqual(json.loads(first.body), {"day": "2026-09-30"})
            self.assertEqual(first.media_type, "application/json")
            self.assertIs(first.body, again.body)
            self.assertEqual(tab.call_count, 1)
            today[0] = date(2026, 10, 1)  # Kuwait midnight: new figures at once
            self.assertEqual(json.loads(dashboard_api.financials_tab(db=None).body), {"day": "2026-10-01"})
            self.assertEqual(tab.call_count, 2)


if __name__ == "__main__":
    unittest.main()
