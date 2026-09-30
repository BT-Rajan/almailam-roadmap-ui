"""What install.sh relies on to refuse a bad deploy: the schema check
(scripts/check_schema.py) and the health endpoint.

Standard library only. Run from the backend directory:
    python -m unittest discover -s tests
"""

import unittest
from unittest import mock

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

import app.main as main
from app.core.database import Base
from scripts.check_schema import missing_schema


class SchemaCheckTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def test_a_complete_database_passes(self):
        self.assertEqual(missing_schema(self.engine), [])

    def test_names_a_missing_column_and_table(self):
        with self.engine.begin() as connection:
            connection.execute(text("DROP INDEX IF EXISTS idx_clients_mobile_digits"))
            connection.execute(text("ALTER TABLE clients DROP COLUMN mobile_digits"))
            connection.execute(text("DROP TABLE message_attachments"))
        missing = missing_schema(self.engine)
        self.assertIn("column clients.mobile_digits", missing)
        self.assertIn("table message_attachments", missing)


class HealthCheckTest(unittest.TestCase):
    def test_reports_ok_when_the_database_answers(self):
        engine = create_engine("sqlite://")
        with mock.patch.object(main, "engine", engine):
            self.assertEqual(main.health_check()["status"], "ok")

    def test_503_when_the_database_is_unreachable(self):
        broken = mock.Mock(connect=mock.Mock(side_effect=OperationalError("SELECT 1", {}, Exception("down"))))
        with mock.patch.object(main, "engine", broken):
            self.assertEqual(main.health_check().status_code, 503)


if __name__ == "__main__":
    unittest.main()
