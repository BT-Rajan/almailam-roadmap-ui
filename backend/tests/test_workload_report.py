"""Team Workload report against hand-worked answers.

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
from app.services import workload_report_service
from app.services.report_period import make_period
from tests.test_dashboard_service import make

TODAY = date(2026, 9, 30)
SEPTEMBER = make_period(date(2026, 9, 1), date(2026, 9, 30))


class TeamWorkloadTest(unittest.TestCase):
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
        layla = make(db, User, username="layla", email="l@x.com", full_name="Layla", role="Engineer", is_active=True)
        make(db, User, username="idle", email="i@x.com", full_name="Idle Engineer", role="Engineer", is_active=True)
        manager = make(db, User, username="pm", email="p@x.com", full_name="Manager", role="Project Manager", is_active=True)
        gone = make(db, User, username="gone", email="g@x.com", full_name="Left Company", role="Engineer", is_active=False)
        make(db, User, username="viewer", email="v@x.com", full_name="Viewer", role="Viewer", is_active=True)
        client = make(db, Client, company_name="Acme")
        project = make(db, Project, project_no="P1", project_name="Villa", client_id=client.id, engineer_id=layla.id, status="Active")
        n = iter(range(100))

        def task(user, due, status="Pending"):
            return make(db, Task, task_no=f"T{next(n)}", project_id=project.id, title="t", assigned_to=user.id, due_date=due, status=status)

        task(layla, date(2026, 9, 10))                  # overdue 20 days
        task(layla, date(2026, 9, 25), "In Progress")   # overdue 5 days
        task(layla, date(2026, 10, 3))                  # due soon
        task(layla, date(2026, 11, 30), "In Progress")  # later
        task(manager, date(2026, 10, 20))
        task(gone, date(2026, 9, 1))                    # stranded, overdue
        on_time = task(layla, date(2026, 9, 20), "Completed")
        late = task(manager, date(2026, 9, 5), "Completed")
        for done, at in ((on_time, datetime(2026, 9, 18, 8)), (late, datetime(2026, 9, 7, 8))):
            db.execute(text(
                "INSERT INTO audit_log (entity_type, entity_id, event_label, new_value, changed_by, changed_at) "
                "VALUES ('TASK', :id, 'Status changed', 'Completed', 1, :at)"
            ), {"id": done.id, "at": at})
        db.commit()

    def report(self):
        with mock.patch.object(workload_report_service, "kuwait_today", return_value=TODAY):
            return workload_report_service.team_workload(self.db, SEPTEMBER)

    def test_members(self):
        members = {m["name"]: m for m in self.report()["members"]}
        self.assertEqual(set(members), {"Layla", "Idle Engineer", "Manager", "Left Company"})  # no Viewer
        layla = members["Layla"]
        self.assertEqual(
            (layla["openTasks"], layla["overdueTasks"], layla["dueSoonTasks"], layla["laterTasks"], layla["notStartedTasks"]),
            (4, 2, 1, 1, 2),
        )
        self.assertEqual((layla["oldestOverdueDays"], layla["activeProjects"]), (20, 1))
        self.assertEqual((layla["completedInPeriod"], layla["onTimeRate"]), (1, 100.0))
        self.assertEqual((members["Manager"]["completedInPeriod"], members["Manager"]["onTimeRate"]), (1, 0.0))
        self.assertEqual(members["Idle Engineer"]["openTasks"], 0)
        self.assertTrue(members["Left Company"]["inactive"])
        self.assertEqual(self.report()["members"][0]["name"], "Layla")  # heaviest first

    def test_totals(self):
        totals = self.report()["totals"]
        self.assertEqual((totals["openTasks"], totals["overdueTasks"], totals["dueSoonTasks"]), (6, 3, 1))
        self.assertEqual(totals["overdueShare"], 50.0)
        self.assertEqual((totals["completedInPeriod"], totals["onTimeRate"]), (2, 50.0))
        self.assertEqual(totals["strandedTasks"], 1)
        self.assertEqual((totals["people"], totals["peopleWithOpenWork"], totals["peopleWithOverdue"]), (4, 3, 2))


if __name__ == "__main__":
    unittest.main()
