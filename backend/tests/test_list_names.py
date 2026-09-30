"""List endpoints send each row's project name (resolved in one batched
query), so list pages don't have to download every project to label rows.

Standard library only. Run from the backend directory:
    venv/bin/python -m unittest discover -s tests
"""

import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core.database import Base
from app.models.client import Client
from app.models.document import ProjectDocument
from app.models.government import GovernmentSubmission
from app.models.message import MessageLogEntry
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from tests.test_dashboard_service import TODAY, make


class ListNamesTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        db = self.db
        user = make(db, User, full_name="Ahmed Rashid")
        self.user = user
        client = make(db, Client, company_name="Acme")
        self.project = make(db, Project, project_no="P1", project_name="Villa Salmiya", client_id=client.id, engineer_id=user.id)
        make(db, ProjectDocument, document_no="D1", project_id=self.project.id, title="Plan", uploaded_by=user.id, upload_date=TODAY)
        make(db, GovernmentSubmission, submission_no="SUB-1", project_id=self.project.id)
        make(db, MessageLogEntry, client_id=client.id, project_id=self.project.id, sent_at=datetime(2026, 9, 1))
        make(db, Task, task_no="T1", project_id=self.project.id, title="Draft", assigned_to=user.id, due_date=TODAY)
        db.commit()

    def test_documents(self):
        from app.api.documents import list_documents

        result = list_documents(None, None, None, None, None, 1, 25, db=self.db, _=None)
        self.assertEqual(result["items"][0].projectName, "Villa Salmiya")

    def test_submissions(self):
        from app.api.submissions import list_submissions

        (row,) = list_submissions(None, None, db=self.db, _=None)
        self.assertEqual((row.projectId, row.projectName), ("P1", "Villa Salmiya"))

    def test_message_log(self):
        from app.api.messages import list_log

        result = list_log(None, None, 1, 25, db=self.db, _=None)
        (row,) = result["items"]
        self.assertEqual(row.projectName, "Villa Salmiya")

    def test_tasks(self):
        from app.api.tasks import list_tasks

        result = list_tasks(None, None, None, None, None, None, 1, 25, db=self.db, _=None)
        row = result["items"][0]
        self.assertEqual((row.projectName, row.clientName, row.assignedTo), ("Villa Salmiya", "Acme", "Ahmed Rashid"))

    def test_projects_carry_client_name(self):
        from app.api.projects import _project_out, list_projects

        result = list_projects(
            clientId=None, status=None, stage=None, engineerId=None, search=None, sort=None, deleted=False,
            page=1, pageSize=25, db=self.db, _=None,
        )
        self.assertEqual(result["items"][0].clientName, "Acme")
        self.assertEqual(_project_out(self.db, self.project, "Ahmed Rashid").clientName, "Acme")

    def test_project_options(self):
        from app.api.projects import list_project_options

        self.assertEqual(list_project_options(db=self.db, _=None), [{"id": "P1", "name": "Villa Salmiya"}])


if __name__ == "__main__":
    unittest.main()
