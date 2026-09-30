"""Dashboard figures are computed in the database (dashboard_service), not
by shipping every row to the browser. Seeds an in-memory SQLite database
and checks each tab's numbers and lists.

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import unittest
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from unittest import mock

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core.database import Base
from app.models.client import Client
from app.models.contract import Contract
from app.models.document import ProjectDocument
from app.models.payment import FinancialAgreement, PaymentObligation
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services import dashboard_service

TODAY = date(2026, 9, 30)


def _filler(column):
    """A valid value for a required column the test doesn't care about."""
    if column.type.__class__.__name__ == "Enum":
        return column.type.enums[0]
    python_type = column.type.python_type
    if python_type is str:
        return "x"
    if python_type in (int, float, Decimal):
        return 1
    if python_type is bool:
        return False
    if python_type is date:
        return TODAY
    if python_type is datetime:
        return datetime.combine(TODAY, time())
    if python_type is time:
        return time(17, 0)
    return None


def make(db: Session, model, **values):
    for column in inspect(model).columns:
        if column.primary_key or column.name in values or column.nullable:
            continue
        if column.default is not None or column.server_default is not None:
            continue
        values[column.name] = _filler(column)
    row = model(**values)
    db.add(row)
    db.flush()
    return row


class DashboardServiceTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        for target in ("app.services.dashboard_service.kuwait_today", "app.core.payment_calculations.kuwait_today"):
            patcher = mock.patch(target, return_value=TODAY)
            patcher.start()
            self.addCleanup(patcher.stop)

        db = self.db
        self.user = make(db, User, full_name="Ahmed Rashid")
        self.acme = make(db, Client, company_name="Acme", status="Active", onboarding_state="Ready")
        make(db, Client, company_name="Beta", status="Active", onboarding_state="Documents Required")
        make(db, Client, company_name="Gone", status="Inactive", onboarding_state="Ready")
        make(db, Client, company_name="Deleted", status="Active", onboarding_state="Ready", deleted_at=datetime(2026, 1, 1))

        def project(no, status, **extra):
            return make(
                db, Project, project_no=no, project_name=f"Project {no}", client_id=self.acme.id,
                engineer_id=self.user.id, status=status, **extra,
            )

        self.villa = project("P1", "Active")
        project("P2", "On Hold")
        self.done = project("P3", "Completed")
        project("P4", "Active", deleted_at=datetime(2026, 1, 1))

        def task(no, due, status="Pending", **extra):
            return make(
                db, Task, task_no=no, project_id=self.villa.id, title=f"Task {no}", assigned_to=self.user.id,
                due_date=due, status=status, **extra,
            )

        task("T-overdue", TODAY - timedelta(days=3))
        task("T-soon", TODAY + timedelta(days=5))
        task("T-later", TODAY + timedelta(days=30))
        task("T-done", TODAY - timedelta(days=10), status="Completed")
        task("T-deleted", TODAY + timedelta(days=1), deleted_at=datetime(2026, 1, 1))

        make(db, ProjectDocument, document_no="D1", project_id=self.villa.id, title="Old plan",
             uploaded_by=self.user.id, upload_date=TODAY - timedelta(days=9), file_size_bytes=2048)
        make(db, ProjectDocument, document_no="D2", project_id=self.villa.id, title="New plan",
             uploaded_by=self.user.id, upload_date=TODAY - timedelta(days=1))

        def contract(no, project_row, status, expiry):
            return make(db, Contract, contract_no=no, project_id=project_row.id, status=status, expiry_date=expiry)

        contract("C-soon", self.villa, "Signed", TODAY + timedelta(days=5))
        contract("C-lapsed", self.villa, "Active", TODAY - timedelta(days=2))
        contract("C-lapsed-done", self.done, "Signed", TODAY - timedelta(days=2))  # project Completed -> fine
        contract("C-draft", self.villa, "Draft", TODAY + timedelta(days=1))  # not in force
        contract("C-far", self.villa, "Signed", TODAY + timedelta(days=60))

        agreement = make(db, FinancialAgreement, project_id=self.villa.id, contract_amount=Decimal("1000"), currency="KWD")

        def obligation(seq, due, amount, received=0, manual_status=None):
            make(db, PaymentObligation, agreement_id=agreement.id, sequence_number=seq, description=f"#{seq}",
                 due_date=due, amount_due=Decimal(amount), amount_received=Decimal(received), manual_status=manual_status)

        obligation(1, TODAY - timedelta(days=10), "300", received="100")  # 200 overdue
        obligation(2, TODAY + timedelta(days=10), "400")  # 400 pending
        obligation(3, TODAY - timedelta(days=5), "300", manual_status="Waived")  # neither
        db.commit()

    def test_clients_tab(self):
        result = dashboard_service.clients_tab(self.db)
        self.assertEqual((result["total"], result["active"], result["inactive"], result["onboarding"]), (3, 2, 1, 1))
        self.assertEqual(len(result["recentClients"]), 3)
        self.assertEqual(result["recentClients"][0]["id"][:4], "CLT-")

    def test_projects_tab(self):
        result = dashboard_service.projects_tab(self.db)
        self.assertEqual((result["total"], result["active"], result["onHold"]), (3, 1, 1))
        self.assertEqual([p["id"] for p in result["recentProjects"]], ["P3", "P2", "P1"])  # newest first, no deleted
        self.assertEqual(result["recentProjects"][0]["client"], "Acme")
        self.assertEqual(result["pendingTasksTotal"], 3)
        self.assertEqual([t["id"] for t in result["pendingTasks"]], ["T-overdue", "T-soon", "T-later"])
        self.assertEqual(result["pendingTasks"][0]["project"], "Project P1")
        self.assertEqual(result["pendingTasks"][0]["assignee"], "Ahmed Rashid")
        self.assertEqual([d["name"] for d in result["recentDocuments"]], ["New plan", "Old plan"])
        self.assertEqual(result["recentDocuments"][1]["size"], "2.0 KB")

    def test_deadlines_tab(self):
        result = dashboard_service.deadlines_tab(self.db)
        self.assertEqual(result["overdueTasks"], 1)
        self.assertEqual([t["id"] for t in result["upcomingDeadlines"]], ["T-soon"])  # within 14 days
        self.assertEqual([c["contractNo"] for c in result["contractsExpiringSoon"]], ["C-soon"])
        self.assertEqual([c["contractNo"] for c in result["contractsNotRenewed"]], ["C-lapsed"])

    def test_financials_tab(self):
        result = dashboard_service.financials_tab(self.db)
        self.assertEqual(result["totalOverdue"], 200.0)
        self.assertEqual(result["totalPending"], 400.0)
        self.assertEqual(len(result["overdueAgreements"]), 1)
        row = result["overdueAgreements"][0]
        self.assertEqual((row["projectId"], row["client"], row["overdueAmount"]), ("P1", "Acme", 200.0))

    def test_queries_do_not_grow_with_rows(self):
        """Each tab is a fixed number of queries -- nothing per row."""
        from sqlalchemy import event

        def count(fn):
            calls = []
            listener = lambda *args: calls.append(1)  # noqa: E731
            event.listen(self.db.get_bind(), "before_cursor_execute", listener)
            try:
                fn(self.db)
            finally:
                event.remove(self.db.get_bind(), "before_cursor_execute", listener)
            return len(calls)

        before = {name: count(getattr(dashboard_service, name)) for name in ("projects_tab", "deadlines_tab", "financials_tab")}
        for i in range(20):
            make(self.db, Task, task_no=f"T-x{i}", project_id=self.villa.id, title="x", assigned_to=self.user.id,
                 due_date=TODAY + timedelta(days=2), status="Pending")
        self.db.commit()
        after = {name: count(getattr(dashboard_service, name)) for name in before}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
