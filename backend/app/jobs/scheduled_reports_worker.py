"""Scheduled-report worker: one long-running process, one polling loop.

Started by the serviceos-scheduled-reports@<instance>.service systemd unit
(see deploy/systemd/) -- exactly one per instance, independent of how many
API workers run. Every POLL_INTERVAL_SECONDS it calls the existing
run_due_schedules(), which does all the real work: finding due schedules,
the per-schedule FOR UPDATE claim, advancing next_run_at before sending,
rendering, emailing and recording the outcome. That row lock still guards
against a duplicate send if a second worker is ever started by mistake.

Run by hand from the backend directory:
    venv/bin/python -m app.jobs.scheduled_reports_worker
Stop with Ctrl+C / SIGTERM: the cycle in progress finishes, then it exits.
"""

import logging
import signal
import sys
import threading

from app.core.database import SessionLocal
from app.jobs import configure_logging
from app.services.scheduled_report_service import run_due_schedules

logger = logging.getLogger("app.scheduler")

POLL_INTERVAL_SECONDS = 60

_stop = threading.Event()


def run_cycle() -> int:
    """One polling pass with its own session, always closed afterwards,
    so nothing is held open while the worker sleeps."""
    db = SessionLocal()
    try:
        return run_due_schedules(db)
    except Exception:
        logger.exception("Scheduled report run failed.")
        try:
            db.rollback()
        except Exception:
            # The connection itself may be what failed (database down).
            logger.exception("Rollback after a failed scheduled report run also failed.")
        return 0
    finally:
        db.close()


def _request_stop(signum: int, _frame: object) -> None:
    logger.info("Received %s; stopping after the current cycle.", signal.Signals(signum).name)
    _stop.set()


def main() -> int:
    configure_logging()
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    logger.info("Scheduled-report worker started (polling every %ds).", POLL_INTERVAL_SECONDS)
    while not _stop.is_set():
        try:
            sent = run_cycle()
            if sent:
                logger.info("Scheduled reports: sent %d report(s).", sent)
        except Exception:
            # run_cycle already handles failures; this only keeps a truly
            # unexpected error (e.g. closing a dead session) from ending
            # the loop.
            logger.exception("Unexpected error in scheduled-report worker cycle.")
        _stop.wait(POLL_INTERVAL_SECONDS)
    logger.info("Scheduled-report worker stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
