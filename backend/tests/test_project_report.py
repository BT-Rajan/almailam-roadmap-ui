"""Project Performance report: schedule health, tasks and per-stream money
for one project, against hand-worked answers.

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest import mock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core.database import Base
from app.models.client import Client
from app.models.payment import FinancialAgreement, Payment, PaymentObligation
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import project_report_service
from app.services.project_report_service import _schedule
from app.services.report_period import make_period
from tests.test_dashboard_service import make

TODAY = date(2026, 9, 30)
PERIOD = make_period(date(2026, 7, 1), date(2026, 9, 30))


def schedule(status="Active", progress=50, start=date(2026, 1, 1), target=date(2026, 12, 31)):
    project = SimpleNamespace(status=status, progress=progress, start_date=start, target_date=target)
    return _schedule(project, TODAY)


class ScheduleHealthTest(unittest.TestCase):
    def test_on_track_when_progress_keeps_up_with_time(self):
        # 272 of 364 days used = 74.7%; 60% progress is within 15 points.
        self.assertEqual(schedule(progress=60)["health"], "on-track")

    def test_at_risk_when_time_runs_ahead_of_progress(self):
        result = schedule(progress=50)
        self.assertEqual(result["timeElapsedPercent"], 74.7)
        self.assertEqual(result["health"], "at-risk")

    def test_late_after_the_target_date(self):
        result = schedule(progress=95, target=date(2026, 9, 1))
        self.assertEqual((result["health"], result["daysToTarget"]), ("late", -29))
        self.assertEqual(result["timeElapsedPercent"], 100.0)

    def test_status_wins_for_finished_or_paused_projects(self):
        self.assertEqual(schedule(status="Completed", target=date(2026, 9, 1))["health"], "completed")
        self.assertEqual(schedule(status="On Hold")["health"], "on-hold")

    def test_not_started_yet(self):
        result = schedule(progress=0, start=date(2026, 10, 10), target=date(2026, 12, 31))
        self.assertEqual((result["timeElapsedPercent"], result["health"]), (0.0, "on-track"))


class ProjectPerformanceTest(unittest.TestCase):
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
        user = make(db, User, full_name="Layla")
        client = make(db, Client, company_name="Acme")
        self.project = make(db, Project, project_no="P1", project_name="Villa", client_id=client.id, engineer_id=user.id,
                            status="Active", progress=40, start_date=date(2026, 1, 1), target_date=date(2026, 12, 31))
        other = make(db, Project, project_no="P2", project_name="Other", client_id=client.id, engineer_id=user.id)

        def task(no, due, status, project=self.project):
            return make(db, Task, task_no=no, project_id=project.id, title=no, assigned_to=user.id, due_date=due, status=status)

        done = task("T1", date(2026, 8, 10), "Completed")
        task("T2", date(2026, 9, 1), "Pending")        # overdue 29 days
        task("T3", date(2026, 9, 20), "In Progress")   # overdue 10 days
        task("T4", date(2026, 10, 20), "Pending")
        task("X1", date(2026, 9, 1), "Pending", other)  # another project: ignored
        db.execute(text(
            "INSERT INTO audit_log (entity_type, entity_id, event_label, new_value, changed_by, changed_at) "
            "VALUES ('TASK', :id, 'Status changed', 'Completed', 1, :at)"
        ), {"id": done.id, "at": datetime(2026, 8, 12, 9)})  # 2 days late

        design = make(db, FinancialAgreement, project_id=self.project.id, stream="Design", currency="KWD", contract_amount=1000)

        def obligation(due, amount_due, received, seq, manual=None):
            return make(db, PaymentObligation, agreement_id=design.id, due_date=due, amount_due=amount_due,
                        amount_received=received, sequence_number=seq, description=f"Instalment {seq}", manual_status=manual)

        obligation(date(2026, 6, 1), 400, 400, 1)     # paid, before the period
        obligation(date(2026, 8, 1), 300, 100, 2)     # billed in period, 200 overdue
        obligation(date(2026, 11, 1), 300, 0, 3)      # future, 300 pending
        obligation(date(2026, 9, 1), 50, 0, 4, "Waived")
        make(db, Payment, agreement_id=design.id, project_id=self.project.id, amount_received=400,
             payment_date=date(2026, 6, 2), created_by=user.id, created_at=datetime(2026, 6, 2))
        make(db, Payment, agreement_id=design.id, project_id=self.project.id, amount_received=100,
             payment_date=date(2026, 8, 3), created_by=user.id, created_at=datetime(2026, 8, 3))
        db.commit()

    def report(self):
        with mock.patch.object(project_report_service, "kuwait_today", return_value=TODAY):
            return project_report_service.project_performance(self.db, self.project, PERIOD)

    def test_tasks(self):
        tasks = self.report()["tasks"]
        self.assertEqual((tasks["total"], tasks["open"], tasks["overdue"]), (4, 3, 2))
        self.assertEqual((tasks["completedInPeriod"], tasks["onTimeRate"]), (1, 0.0))
        self.assertEqual([(t["taskNo"], t["daysLate"]) for t in tasks["overdueList"]], [("T2", 29), ("T3", 10)])

    def test_money(self):
        money = self.report()["money"]
        (stream,) = money["streams"]
        self.assertEqual(stream["received"], 500.0)
        self.assertEqual(stream["outstanding"], 500.0)   # 200 overdue + 300 pending; waived excluded
        self.assertEqual(stream["overdue"], 200.0)
        self.assertEqual(stream["receivedInPeriod"], 100.0)
        self.assertEqual(stream["billedInPeriod"], 300.0)
        self.assertEqual(money["cashFlow"]["categories"], ["Jul 2026", "Aug 2026", "Sep 2026"])
        self.assertEqual(money["cashFlow"]["received"], [0, 100.0, 0])
        self.assertEqual(money["cashFlow"]["billed"], [0, 300.0, 0])
        self.assertEqual([(u["description"], u["outstanding"], u["overdue"]) for u in money["upcoming"]],
                         [("Instalment 2", 200.0, True), ("Instalment 3", 300.0, False)])


if __name__ == "__main__":
    unittest.main()
