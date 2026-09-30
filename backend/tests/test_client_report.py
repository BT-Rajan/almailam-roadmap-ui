"""Client Projects report against hand-worked answers.

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import unittest
from datetime import date, datetime
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core.database import Base
from app.models.client import Client
from app.models.company import CompanySettings
from app.models.payment import FinancialAgreement, Payment, PaymentObligation
from app.models.project import Project
from app.models.user import User
from app.services import client_report_service
from app.services.report_period import make_period
from tests.test_dashboard_service import make

TODAY = date(2026, 9, 30)
SEPTEMBER = make_period(date(2026, 9, 1), date(2026, 9, 30))


class ClientPortfolioTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        db = self.db
        make(db, CompanySettings, id=1, currency="KWD")
        user = make(db, User, full_name="Layla")
        acme = make(db, Client, company_name="Acme", status="Active", created_at=datetime(2026, 9, 5))
        make(db, Client, company_name="Idle Co", status="Active", created_at=datetime(2025, 1, 1))

        def project(no, status, created):
            return make(db, Project, project_no=no, project_name=no, client_id=acme.id, engineer_id=user.id, status=status, created_at=created)

        villa = project("P1", "Active", datetime(2026, 9, 10))
        project("P2", "Completed", datetime(2025, 5, 1))
        tower = project("P3", "On Hold", datetime(2026, 2, 1))
        kwd = make(db, FinancialAgreement, project_id=villa.id, currency="KWD", stream="Design")
        usd = make(db, FinancialAgreement, project_id=tower.id, currency="USD", stream="Design")
        make(db, PaymentObligation, agreement_id=kwd.id, due_date=date(2026, 9, 1), amount_due=500, amount_received=200, sequence_number=1)
        make(db, PaymentObligation, agreement_id=kwd.id, due_date=date(2026, 12, 1), amount_due=300, amount_received=0, sequence_number=2)
        make(db, PaymentObligation, agreement_id=kwd.id, due_date=date(2026, 8, 1), amount_due=90, amount_received=0,
             sequence_number=3, manual_status="Waived")
        make(db, PaymentObligation, agreement_id=usd.id, due_date=date(2026, 8, 1), amount_due=999, amount_received=0, sequence_number=1)
        make(db, Payment, agreement_id=kwd.id, project_id=villa.id, amount_received=200, payment_date=date(2026, 9, 3),
             created_by=user.id, created_at=datetime(2026, 9, 3))
        make(db, Payment, agreement_id=usd.id, project_id=tower.id, amount_received=50, payment_date=date(2026, 9, 3),
             created_by=user.id, created_at=datetime(2026, 9, 3))
        db.commit()

    def report(self):
        with mock.patch.object(client_report_service, "kuwait_today", return_value=TODAY):
            return client_report_service.client_portfolio(self.db, SEPTEMBER)

    def test_client_rows(self):
        clients = {row["clientName"]: row for row in self.report()["clients"]}
        acme = clients["Acme"]
        self.assertEqual((acme["totalProjects"], acme["activeProjects"], acme["onHoldProjects"], acme["completedProjects"]), (3, 1, 1, 1))
        self.assertEqual((acme["newClient"], acme["newProjectsInPeriod"]), (True, 1))
        self.assertEqual((acme["receivedInPeriod"], acme["outstanding"], acme["overdue"]), (200.0, 600.0, 300.0))
        villa = next(p for p in acme["projects"] if p["projectNo"] == "P1")
        self.assertEqual((villa["outstanding"], villa["overdue"], villa["newInPeriod"]), (600.0, 300.0, True))
        self.assertEqual(clients["Idle Co"]["totalProjects"], 0)

    def test_totals(self):
        totals = self.report()["totals"]
        self.assertEqual((totals["clients"], totals["newClients"], totals["clientsWithoutProjects"]), (2, 1, 1))
        self.assertEqual((totals["projects"], totals["newProjects"]), (3, 1))
        self.assertEqual((totals["receivedInPeriod"], totals["outstanding"], totals["overdue"], totals["clientsWithOverdue"]), (200.0, 600.0, 300.0, 1))


if __name__ == "__main__":
    unittest.main()
