"""Employee Performance report against hand-worked answers.

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import unittest
from datetime import date, datetime
from unittest import mock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core.database import Base
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import performance_report_service
from app.services.report_period import make_period
from tests.test_dashboard_service import make

TODAY = date(2026, 9, 20)
SEPTEMBER = make_period(date(2026, 9, 1), date(2026, 9, 30))


class EmployeePerformanceTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        db = self.db
        db.execute(text(
            "CREATE TABLE audit_log (id INTEGER PRIMARY KEY, entity_type TEXT, entity_id INTEGER, "
            "event_label TEXT, previous_value TEXT, new_value TEXT, reason TEXT, changed_by INTEGER, changed_at DATETIME)"
        ))
        layla = make(db, User, username="l", email="l@x.com", full_name="Layla")
        client = make(db, Client, company_name="Acme")
        project = make(db, Project, project_no="P1", project_name="Villa", client_id=client.id, engineer_id=layla.id)
        n = iter(range(100))

        def task(due, status):
            return make(db, Task, task_no=f"T{next(n)}", project_id=project.id, title="t", assigned_to=layla.id, due_date=due, status=status)

        def completed(t, at):
            db.execute(text(
                "INSERT INTO audit_log (entity_type, entity_id, event_label, new_value, changed_by, changed_at) "
                "VALUES ('TASK', :i, 'Status changed', 'Completed', 1, :at)"
            ), {"i": t.id, "at": at})

        completed(task(date(2026, 9, 10), "Completed"), datetime(2026, 9, 9, 8))    # on time
        completed(task(date(2026, 9, 5), "Completed"), datetime(2026, 9, 9, 8))     # 4 days late
        completed(task(date(2026, 9, 8), "Completed"), datetime(2026, 9, 14, 8))    # 6 days late
        task(date(2026, 9, 15), "Completed")                                         # no audit row: on time
        task(date(2026, 9, 12), "In Progress")                                       # overdue
        task(date(2026, 9, 25), "Pending")                                           # not due yet
        # Due in August, completed in September: throughput only.
        completed(task(date(2026, 8, 25), "Completed"), datetime(2026, 9, 2, 8))
        db.commit()

    def test_outcomes(self):
        with mock.patch.object(performance_report_service, "kuwait_today", return_value=TODAY):
            report = performance_report_service.employee_performance(self.db, SEPTEMBER)
        (layla,) = report["members"]
        self.assertEqual((layla["dueInPeriod"], layla["dueSoFar"]), (6, 5))
        self.assertEqual((layla["completedOnTime"], layla["completedLate"], layla["overdueOpen"], layla["notYetDue"]), (2, 2, 1, 1))
        self.assertEqual((layla["completionRate"], layla["onTimeRate"], layla["averageDaysLate"]), (80.0, 40.0, 5.0))
        self.assertEqual(layla["completedInPeriod"], 4)  # 3 audited in Sep + the August-due one
        self.assertEqual(report["totals"]["onTimeRate"], 40.0)


if __name__ == "__main__":
    unittest.main()
