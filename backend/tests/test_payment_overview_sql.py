"""payment_service.agreements_overview computes balances in SQL; it must
give exactly what the Python rules (payment_calculations.get_financial_summary)
give, on randomised instalments covering every case: unpaid, part-paid,
fully paid, overpaid, due today / before / after, waived and cancelled.

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import random
import unittest
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core import payment_calculations as calc
from app.core.database import Base
from app.models.client import Client
from app.models.payment import FinancialAgreement, PaymentObligation
from app.models.project import Project
from app.models.user import User
from app.services import payment_service
from tests.test_dashboard_service import TODAY, make


class PaymentOverviewSqlTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        for target in ("app.services.payment_service.kuwait_today", "app.core.payment_calculations.kuwait_today"):
            patcher = mock.patch(target, return_value=TODAY)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_matches_python_rules_on_random_data(self):
        rng = random.Random(7)
        db = self.db
        user = make(db, User, full_name="A")
        client = make(db, Client, company_name="Acme")
        for p in range(8):
            project = make(db, Project, project_no=f"P{p}", project_name=f"Project {p}", client_id=client.id, engineer_id=user.id)
            for stream in ("Design", "Supervision"):
                agreement = make(db, FinancialAgreement, project_id=project.id, stream=stream,
                                 contract_amount=Decimal(rng.choice(["1000", "2500.50", "0"])), currency="KWD")
                for seq in rng.sample(range(1, 12), rng.randint(0, 9)):  # gaps / empty schedules too
                    due = Decimal(rng.choice(["100", "250.25", "0", "999.99"]))
                    received = rng.choice([Decimal("0"), due, due / 2, due + 10])
                    make(db, PaymentObligation, agreement_id=agreement.id, sequence_number=seq, description=f"#{seq}",
                         amount_due=due, amount_received=received.quantize(Decimal("0.01")),
                         due_date=TODAY + timedelta(days=rng.choice([-40, -1, 0, 1, 30])),
                         manual_status=rng.choice([None, None, None, "Waived", "Cancelled"]))
        db.commit()

        overview = payment_service.agreements_overview(db)
        rows = {row["id"]: row for row in overview["rows"]}
        expected_totals = {key: Decimal("0") for key in ("contractAmount", "totalReceived", "totalPending", "totalOverdue")}
        for agreement in db.query(FinancialAgreement).all():
            obligations = db.query(PaymentObligation).filter(PaymentObligation.agreement_id == agreement.id).order_by(PaymentObligation.id).all()
            want = calc.get_financial_summary(agreement, obligations)
            got = rows[str(agreement.id)]
            for key in expected_totals:
                expected_totals[key] += Decimal(str(want[key]))
                self.assertAlmostEqual(got[key], float(want[key]), places=2, msg=f"{key} agreement {agreement.id}")
            nxt = want["nextPaymentObligation"]
            if nxt is None:
                self.assertIsNone(got["nextPaymentDueDate"], agreement.id)
            else:
                self.assertEqual(got["nextPaymentDueDate"], nxt.due_date.isoformat())
                self.assertAlmostEqual(got["nextPaymentAmount"], float(nxt.amount_due - nxt.amount_received), places=2)
            self.assertEqual(got["nextPaymentIsOverdue"], bool(want["nextPaymentIsOverdue"]), agreement.id)
        for key, value in expected_totals.items():
            self.assertAlmostEqual(overview["totals"][key], float(value), places=2, msg=key)


if __name__ == "__main__":
    unittest.main()
