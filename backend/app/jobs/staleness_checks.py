"""Daily staleness/reminder checks, as a one-shot process.

Started once a day by the serviceos-staleness-checks@<instance>.timer
systemd unit (see deploy/systemd/); exits when done. Previously this ran
inside the FastAPI process on an in-process timer -- once per API worker, and
immediately on every startup.

Run by hand from the backend directory:
    venv/bin/python -m app.jobs.staleness_checks
"""

import logging
import sys

from app.core.database import SessionLocal
from app.jobs import configure_logging
from app.services.client_service import check_and_notify_stale_onboarding
from app.services.payment_service import check_and_notify_payment_reminders
from app.services.project_service import (
    check_and_notify_overdue_projects,
    check_and_notify_stale_projects,
    check_and_notify_unpaid_completed_projects,
    check_and_start_supervision_tasks,
)
from app.services.quotation_service import check_and_expire_quotations

logger = logging.getLogger("app.scheduler")

# (check, success message, failure message) -- the same messages the
# in-process scheduler logged, in the same order.
CHECKS = [
    (check_and_notify_stale_projects, "Stale-project check: notified %d project(s).", "Stale-project check failed."),
    (check_and_notify_stale_onboarding, "Stale-onboarding check: notified %d client(s).", "Stale-onboarding check failed."),
    (check_and_notify_payment_reminders, "Payment-reminder check: sent %d reminder(s).", "Payment-reminder check failed."),
    (
        check_and_notify_unpaid_completed_projects,
        "Unpaid-completed-project check: notified %d project(s).",
        "Unpaid-completed-project check failed.",
    ),
    (check_and_notify_overdue_projects, "Overdue-project check: notified %d project(s).", "Overdue-project check failed."),
    (check_and_expire_quotations, "Quotation-expiry check: expired %d quotation(s).", "Quotation-expiry check failed."),
    (
        check_and_start_supervision_tasks,
        "Supervision-task-start check: started %d task(s).",
        "Supervision-task-start check failed.",
    ),
]


def run() -> int:
    """Runs every check with one session. Each check has its own
    try/except, so a failure in one doesn't prevent the rest from
    running. Returns how many checks failed."""
    failures = 0
    db = SessionLocal()
    try:
        for check, success_message, failure_message in CHECKS:
            try:
                count = check(db)
                if count:
                    logger.info(success_message, count)
            except Exception:
                logger.exception(failure_message)
                db.rollback()
                failures += 1
    finally:
        db.close()
    return failures


def main() -> int:
    configure_logging()
    failures = run()
    # Non-zero exit marks the run failed in `systemctl status` / the
    # journal; the checks that succeeded have already committed.
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
