"""Lifecycle tests for the standalone background jobs (app/jobs/).

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

BACKEND_DIR = Path(__file__).resolve().parent.parent


class ApiOwnsNoSchedulerTest(unittest.TestCase):
    def test_app_imports_and_starts_without_a_scheduler(self):
        from fastapi.testclient import TestClient

        from sqlalchemy import create_engine

        from app.main import app

        self.assertNotIn("apscheduler", sys.modules)
        # /api/health pings the database; an in-memory one stands in for it.
        with mock.patch("app.core.database.SessionLocal") as session_factory, \
                mock.patch("app.main.engine", create_engine("sqlite://")):
            with TestClient(app) as client:  # runs startup/shutdown
                self.assertEqual(client.get("/api/health").status_code, 200)
        session_factory.assert_not_called()  # startup no longer runs any job


class ScheduledReportsWorkerCycleTest(unittest.TestCase):
    def setUp(self):
        from app.jobs import scheduled_reports_worker

        self.worker = scheduled_reports_worker
        self.session = mock.MagicMock()
        patcher = mock.patch.object(scheduled_reports_worker, "SessionLocal", return_value=self.session)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_closes_its_session_after_a_cycle(self):
        with mock.patch.object(self.worker, "run_due_schedules", return_value=2):
            self.assertEqual(self.worker.run_cycle(), 2)
        self.session.close.assert_called_once()

    def test_failed_cycle_rolls_back_and_closes(self):
        with mock.patch.object(self.worker, "run_due_schedules", side_effect=RuntimeError("db down")):
            with self.assertLogs("app.scheduler", "ERROR"):
                self.assertEqual(self.worker.run_cycle(), 0)
        self.session.rollback.assert_called_once()
        self.session.close.assert_called_once()

    def test_failed_rollback_still_closes_and_does_not_raise(self):
        self.session.rollback.side_effect = RuntimeError("connection lost")
        with mock.patch.object(self.worker, "run_due_schedules", side_effect=RuntimeError("db down")):
            with self.assertLogs("app.scheduler", "ERROR"):
                self.worker.run_cycle()
        self.session.close.assert_called_once()


class ScheduledReportsWorkerProcessTest(unittest.TestCase):
    """The real process: the database is unreachable, so every cycle fails.
    It must keep running, then exit cleanly on SIGTERM."""

    def test_survives_database_errors_and_stops_on_sigterm(self):
        env = {**os.environ, "DB_HOST": "127.0.0.1", "DB_PORT": "1", "PYTHONUNBUFFERED": "1"}
        proc = subprocess.Popen(
            [sys.executable, "-m", "app.jobs.scheduled_reports_worker"],
            cwd=BACKEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            time.sleep(4)  # first cycle runs and fails against the dead DB
            self.assertIsNone(proc.poll(), "worker exited after a database error")
            proc.send_signal(signal.SIGTERM)
            output, _ = proc.communicate(timeout=15)
        finally:
            if proc.poll() is None:
                proc.kill()
        self.assertEqual(proc.returncode, 0, output)
        self.assertIn("Scheduled report run failed.", output)
        self.assertIn("Received SIGTERM", output)
        self.assertIn("Scheduled-report worker stopped.", output)


class StalenessChecksTest(unittest.TestCase):
    def test_one_failing_check_does_not_stop_the_rest(self):
        from app.jobs import staleness_checks

        calls = []

        def ok(name):
            def check(db):
                calls.append(name)
                return 0

            return check

        def broken(db):
            calls.append("broken")
            raise RuntimeError("boom")

        checks = [(ok("first"), "%d", "first failed"), (broken, "%d", "broken failed"), (ok("last"), "%d", "last failed")]
        session = mock.MagicMock()
        with (
            mock.patch.object(staleness_checks, "CHECKS", checks),
            mock.patch.object(staleness_checks, "SessionLocal", return_value=session),
            self.assertLogs("app.scheduler", "ERROR"),
        ):
            self.assertEqual(staleness_checks.run(), 1)
        self.assertEqual(calls, ["first", "broken", "last"])
        session.rollback.assert_called_once()
        session.close.assert_called_once()

    def test_session_is_closed_even_on_an_unexpected_interrupt(self):
        from app.jobs import staleness_checks

        def interrupted(db):
            raise KeyboardInterrupt

        session = mock.MagicMock()
        with (
            mock.patch.object(staleness_checks, "CHECKS", [(interrupted, "%d", "x")]),
            mock.patch.object(staleness_checks, "SessionLocal", return_value=session),
        ):
            with self.assertRaises(KeyboardInterrupt):
                staleness_checks.run()
        session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
