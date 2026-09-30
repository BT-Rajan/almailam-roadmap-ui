"""Employee Activity report (and the activity service it shares with the
Activity Calendar) against hand-worked answers.

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import unittest
from datetime import date, datetime

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core.database import Base
from app.models.client import Client
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import activity_report_service, activity_service
from app.services.report_period import make_period
from tests.test_dashboard_service import make

SEPTEMBER = make_period(date(2026, 9, 1), date(2026, 9, 30))


class EmployeeActivityTest(unittest.TestCase):
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
        self.layla = make(db, User, username="layla", email="l@x.com", full_name="Layla")
        self.ahmed = make(db, User, username="ahmed", email="a@x.com", full_name="Ahmed")
        client = make(db, Client, company_name="Acme")
        p1 = make(db, Project, project_no="P1", project_name="Villa", client_id=client.id, engineer_id=self.layla.id)
        p2 = make(db, Project, project_no="P2", project_name="Tower", client_id=client.id, engineer_id=self.layla.id)
        t1 = make(db, Task, task_no="P1-001", project_id=p1.id, title="t", assigned_to=self.layla.id, due_date=date(2026, 9, 9))

        def log(entity_type, entity_id, label, user, at, new_value=None):
            db.execute(text(
                "INSERT INTO audit_log (entity_type, entity_id, event_label, new_value, changed_by, changed_at) "
                "VALUES (:t, :i, :l, :v, :u, :at)"
            ), {"t": entity_type, "i": entity_id, "l": label, "v": new_value, "u": user, "at": at})

        # 21:30 UTC on 31 Aug = 00:30 on 1 Sep in Kuwait -> in September.
        log("TASK", t1.id, "Task created", self.layla.id, datetime(2026, 8, 31, 21, 30))
        log("TASK", t1.id, "Status changed", self.layla.id, datetime(2026, 9, 2, 8), "Completed")
        log("PROJECT", p2.id, "Project deleted", self.layla.id, datetime(2026, 9, 2, 9))
        log("DOCUMENT", 1, "Document rejected", self.ahmed.id, datetime(2026, 9, 10, 8))
        log("PROJECT", p1.id, "Stage advanced", None, datetime(2026, 9, 11, 8))  # system
        # 21:30 UTC on 30 Sep = 1 Oct in Kuwait -> not September.
        log("TASK", t1.id, "Task updated", self.ahmed.id, datetime(2026, 9, 30, 21, 30))
        db.commit()

    def test_people_and_totals(self):
        report = activity_report_service.employee_activity(self.db, SEPTEMBER)
        members = {m["name"]: m for m in report["members"]}
        layla = members["Layla"]
        self.assertEqual((layla["actions"], layla["activeDays"], layla["projectsTouched"]), (3, 2, 2))
        self.assertEqual((layla["created"], layla["completed"], layla["deleted"], layla["rejected"]), (1, 1, 1, 0))
        self.assertEqual(layla["byArea"]["task"], 2)
        self.assertEqual((members["Ahmed"]["actions"], members["Ahmed"]["rejected"]), (1, 1))
        self.assertTrue(members["System"]["system"])
        self.assertEqual(report["members"][-1]["name"], "System")  # people first
        totals = report["totals"]
        self.assertEqual((totals["actions"], totals["systemActions"], totals["peopleActive"]), (4, 1, 2))
        self.assertEqual(sum(report["series"]["actions"]), 5)
        self.assertEqual(report["series"]["actions"][0], 3)  # week of 1 Sep: created, completed, deleted

    def test_one_person(self):
        report = activity_report_service.employee_activity(self.db, SEPTEMBER, self.ahmed.id)
        self.assertEqual([m["name"] for m in report["members"]], ["Ahmed"])

    def test_timestamps_are_explicit_utc_with_kuwait_day(self):
        rows = activity_service.get_filtered_activities(self.db, date(2026, 9, 1), date(2026, 9, 2))
        (created,) = [r for r in rows if r["description"] == "Task created"]
        self.assertEqual(created["timestamp"], "2026-08-31T21:30:00Z")
        self.assertEqual(created["kuwaitDate"], "2026-09-01")
        self.assertEqual(created["entityId"], "P1-001")

    def test_month_summary_groups_by_kuwait_day(self):
        days = {d["date"]: d for d in activity_service.get_month_activity(self.db, 2026, 9)}
        self.assertIn("2026-09-01", days)
        self.assertNotIn("2026-08-31", days)
        self.assertEqual(days["2026-09-02"]["deleted"], 1)


if __name__ == "__main__":
    unittest.main()
