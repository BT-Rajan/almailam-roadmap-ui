"""Payment Ledger: refunds appear as negative rows; projections split
overdue from upcoming.

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
from app.models.payment import FinancialAgreement, Payment, PaymentObligation, Refund
from app.models.project import Project
from app.models.user import User
from app.services import report_service
from tests.test_dashboard_service import make


class PaymentLedgerTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        db = self.db
        user = make(db, User, full_name="Layla")
        client = make(db, Client, company_name="Acme")
        project = make(db, Project, project_no="P1", project_name="Villa", client_id=client.id, engineer_id=user.id)
        agreement = make(db, FinancialAgreement, project_id=project.id, currency="KWD", stream="Design")
        paid = make(db, PaymentObligation, agreement_id=agreement.id, due_date=date(2026, 8, 1), amount_due=500, amount_received=500, sequence_number=1)
        make(db, PaymentObligation, agreement_id=agreement.id, due_date=date(2026, 9, 10), amount_due=300, amount_received=100, sequence_number=2)
        make(db, PaymentObligation, agreement_id=agreement.id, due_date=date(2026, 11, 1), amount_due=200, amount_received=0, sequence_number=3)
        make(db, Payment, agreement_id=agreement.id, project_id=project.id, amount_received=500, payment_date=date(2026, 8, 2),
             payer="Acme", created_by=user.id, created_at=datetime(2026, 8, 2))
        make(db, Payment, agreement_id=agreement.id, project_id=project.id, amount_received=100, payment_date=date(2026, 9, 12),
             payer="Acme", created_by=user.id, created_at=datetime(2026, 9, 12))
        make(db, Refund, agreement_id=agreement.id, obligation_id=paid.id, refund_amount=50, refund_date=date(2026, 9, 20),
             reason="Overpaid", authorising_user=user.id)
        db.commit()

    def test_refunds_are_negative_rows_in_the_period(self):
        rows = report_service.payment_ledger(self.db, start_date=date(2026, 9, 1), end_date=date(2026, 9, 30))
        self.assertEqual([(r["entryType"], r["amount"]) for r in rows], [("Refund", -50.0), ("Payment", 100.0)])
        self.assertEqual(rows[0]["reference"], "Overpaid")
        self.assertEqual(sum(r["amount"] for r in rows), 50.0)

    def test_projections_split_overdue(self):
        with mock.patch.object(report_service, "kuwait_today", return_value=date(2026, 9, 30)):
            months = {m["month"]: m for m in report_service.payment_projections(self.db)["byMonth"]}
        self.assertEqual((months["2026-09"]["amount"], months["2026-09"]["overdue"]), (200.0, 200.0))
        self.assertEqual((months["2026-11"]["amount"], months["2026-11"]["overdue"]), (200.0, 0.0))
        self.assertNotIn("2026-08", months)  # fully paid


if __name__ == "__main__":
    unittest.main()
