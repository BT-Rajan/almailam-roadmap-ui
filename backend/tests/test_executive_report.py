"""Executive Summary figures for a chosen period, checked against a small
hand-built data set whose answers are worked out by hand below.

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
from app.core.exceptions import ValidationAppError
from app.models.client import Client
from app.models.company import CompanySettings
from app.models.payment import FinancialAgreement, Payment, PaymentObligation, Refund
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import executive_report_service
from app.services.report_period import buckets, make_period
from tests.test_dashboard_service import make

TODAY = date(2026, 9, 30)
SEPTEMBER = make_period(date(2026, 9, 1), date(2026, 9, 30))


class ExecutiveSummaryTest(unittest.TestCase):
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
        make(db, CompanySettings, id=1, currency="KWD")
        user = make(db, User, full_name="Ahmed")
        client = make(db, Client, company_name="Acme", created_at=datetime(2026, 9, 3, 9))
        make(db, Client, company_name="Old", created_at=datetime(2026, 8, 1, 9))

        def project(no, created_at, status="Active"):
            return make(db, Project, project_no=no, project_name=no, client_id=client.id, engineer_id=user.id,
                        status=status, created_at=created_at)

        # 21:30 UTC on 31 Aug is 00:30 on 1 Sep in Kuwait -> September.
        p1 = project("P1", datetime(2026, 8, 31, 21, 30))
        project("P2", datetime(2026, 9, 2, 10))
        # 22:00 UTC on 30 Sep is already 1 Oct in Kuwait -> not September.
        project("P3", datetime(2026, 9, 30, 22))
        done = project("P4", datetime(2026, 1, 5), status="Completed")
        project("P5", datetime(2026, 1, 5), status="On Hold")

        kwd = make(db, FinancialAgreement, project_id=p1.id, currency="KWD", stream="Design")
        usd = make(db, FinancialAgreement, project_id=done.id, currency="USD", stream="Supervision")

        def payment(agreement, amount, day):
            return make(db, Payment, agreement_id=agreement.id, project_id=agreement.project_id, amount_received=amount,
                        payment_date=day, created_by=user.id, created_at=datetime(2026, 9, 1))

        payment(kwd, 100, date(2026, 9, 5))
        payment(kwd, 40, date(2026, 8, 31))   # before the period
        payment(usd, 999, date(2026, 9, 6))   # other currency
        make(db, Refund, agreement_id=kwd.id, obligation_id=1, refund_amount=10, refund_date=date(2026, 9, 20),
             authorising_user=user.id)

        def obligation(agreement, due, amount_due, amount_received, manual_status=None, seq=1):
            return make(db, PaymentObligation, agreement_id=agreement.id, due_date=due, amount_due=amount_due,
                        amount_received=amount_received, manual_status=manual_status, sequence_number=seq)

        obligation(kwd, date(2026, 9, 10), 200, 150)                   # billed in Sep, 50 overdue
        obligation(kwd, date(2026, 10, 10), 300, 0, seq=2)            # future: outstanding, not overdue
        obligation(kwd, date(2026, 9, 15), 500, 0, "Cancelled", seq=3)  # ignored everywhere
        obligation(usd, date(2026, 9, 12), 700, 0)                     # other currency

        def task(no, due, status):
            return make(db, Task, task_no=no, project_id=p1.id, title=no, assigned_to=user.id, due_date=due, status=status)

        on_time = task("T1", date(2026, 9, 20), "Completed")
        late = task("T2", date(2026, 9, 10), "Completed")
        reopened = task("T3", date(2026, 9, 10), "In Progress")
        task("T4", date(2026, 9, 1), "Pending")     # open, overdue
        task("T5", date(2026, 10, 5), "Pending")    # open, not overdue

        def completed(entity_type, entity_id, at):
            db.execute(text(
                "INSERT INTO audit_log (entity_type, entity_id, event_label, new_value, changed_by, changed_at) "
                "VALUES (:t, :i, 'Status changed', 'Completed', 1, :at)"
            ), {"t": entity_type, "i": entity_id, "at": at})

        completed("TASK", on_time.id, datetime(2026, 9, 15, 8))
        completed("TASK", late.id, datetime(2026, 9, 12, 8))
        completed("TASK", reopened.id, datetime(2026, 9, 9, 8))
        completed("PROJECT", done.id, datetime(2026, 9, 25, 8))
        db.commit()

    def summary(self):
        with mock.patch.object(executive_report_service, "kuwait_today", return_value=TODAY):
            return executive_report_service.executive_summary(self.db, SEPTEMBER)

    def test_period_flows(self):
        kpis = self.summary()["kpis"]
        self.assertEqual(kpis["newProjects"], 2)          # P1 (Kuwait 1 Sep) and P2; not P3
        self.assertEqual(kpis["projectsCompleted"], 1)
        self.assertEqual(kpis["newClients"], 1)
        self.assertEqual(kpis["activeProjectsNow"], 3)
        self.assertEqual(kpis["onHoldProjectsNow"], 1)

    def test_money_in_company_currency_only(self):
        kpis = self.summary()["kpis"]
        self.assertEqual(kpis["cashReceived"], 100.0)
        self.assertEqual(kpis["refunded"], 10.0)
        self.assertEqual(kpis["netCash"], 90.0)
        self.assertEqual(kpis["billed"], 200.0)
        self.assertEqual(kpis["collectedOfBilled"], 150.0)
        self.assertEqual(kpis["collectionRate"], 75.0)
        self.assertEqual(kpis["outstandingNow"], 350.0)   # 50 + 300
        self.assertEqual(kpis["overdueNow"], 50.0)

    def test_delivery(self):
        kpis = self.summary()["kpis"]
        self.assertEqual(kpis["tasksCompleted"], 2)       # reopened T3 doesn't count
        self.assertEqual(kpis["tasksOnTimeRate"], 50.0)
        self.assertEqual(kpis["openTasksNow"], 3)         # T3, T4, T5
        self.assertEqual(kpis["overdueTasksNow"], 2)      # T3 and T4 (due before 30 Sep)

    def test_charts_are_bucketed_by_week_for_a_month(self):
        result = self.summary()
        self.assertEqual(result["cashFlow"]["categories"], ["1 Sep", "8 Sep", "15 Sep", "22 Sep", "29 Sep"])
        self.assertEqual(result["cashFlow"]["received"], [100.0, 0, 0, 0, 0])
        self.assertEqual(result["cashFlow"]["billed"], [0, 200.0, 0, 0, 0])
        self.assertEqual(result["projectFlow"]["started"], [2, 0, 0, 0, 0])
        self.assertEqual(result["projectFlow"]["completed"], [0, 0, 0, 1, 0])
        self.assertEqual(result["topClients"], [{"clientName": "Acme", "received": 100.0, "payments": 1}])


class PeriodTest(unittest.TestCase):
    def test_validation(self):
        with self.assertRaises(ValidationAppError):
            make_period(date(2026, 9, 2), date(2026, 9, 1))
        with self.assertRaises(ValidationAppError):
            make_period(date(1026, 1, 1), date(2026, 1, 1))

    def test_bucket_sizes(self):
        self.assertEqual(len(buckets(make_period(date(2026, 1, 1), date(2026, 12, 31)))), 12)
        yearly = buckets(make_period(date(2020, 3, 1), date(2026, 9, 30)))
        self.assertEqual([b.label for b in yearly][:2], ["2020", "2021"])
        self.assertEqual(yearly[0].start, date(2020, 3, 1))   # clipped to the period
        months = buckets(make_period(date(2026, 1, 15), date(2026, 4, 10)))
        self.assertEqual((months[0].start, months[-1].end), (date(2026, 1, 15), date(2026, 4, 10)))

    def test_utc_bounds_are_kuwait_midnight(self):
        self.assertEqual(SEPTEMBER.utc_start, datetime(2026, 8, 31, 21))
        self.assertEqual(SEPTEMBER.utc_end_exclusive, datetime(2026, 9, 30, 21))


if __name__ == "__main__":
    unittest.main()
