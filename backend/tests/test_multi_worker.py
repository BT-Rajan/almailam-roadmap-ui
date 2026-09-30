"""The API runs as several worker processes (install.sh). Anything a
worker keeps in memory must not go stale when another worker changes
the database.

Standard library only. Run from the backend directory:
    python -m unittest discover -s tests
"""

import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.core.database import Base
from app.models.company import CompanySettings
from app.models.role import RoleDefinition, RolePermission
from app.services import company_service, role_service


class PermissionCacheTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        role_service._invalidate_cache()
        self.addCleanup(role_service._invalidate_cache)

    def _change_in_another_worker(self, role, module, can_view):
        """Writes straight to the database -- this process's cache isn't told."""
        row = (
            self.db.query(RolePermission)
            .join(RoleDefinition, RoleDefinition.id == RolePermission.role_id)
            .filter(RoleDefinition.role == role, RolePermission.module == module)
            .one()
        )
        row.can_view = can_view
        self.db.commit()

    def test_a_change_made_elsewhere_arrives_within_the_ttl(self):
        clock = [1000.0]
        with mock.patch.object(role_service.time, "monotonic", side_effect=lambda: clock[0]):
            self.assertTrue(role_service.has_permission(self.db, "Administrator", "Projects", "view"))
            self._change_in_another_worker("Administrator", "Projects", False)

            clock[0] += role_service.CACHE_TTL_SECONDS - 1
            self.assertTrue(role_service.has_permission(self.db, "Administrator", "Projects", "view"))  # cached

            clock[0] += 2
            self.assertFalse(role_service.has_permission(self.db, "Administrator", "Projects", "view"))  # re-read


class CompanySettingsFirstRunTest(unittest.TestCase):
    def test_losing_the_first_run_race_returns_the_winners_row(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        winner, loser = Session(engine), Session(engine)
        self.addCleanup(winner.close)
        self.addCleanup(loser.close)

        # The loser has already looked (no row) when the winner commits.
        real_query = loser.query
        looked = []

        def query(*args, **kwargs):
            result = real_query(*args, **kwargs)
            if not looked:
                looked.append(1)
                winner.add(CompanySettings(id=1, company_name="Winner"))
                winner.commit()
                return mock.Mock(filter=lambda *a: mock.Mock(first=lambda: None))
            return result

        with mock.patch.object(loser, "query", side_effect=query):
            settings = company_service.get_settings(loser)
        self.assertEqual(settings.company_name, "Winner")


if __name__ == "__main__":
    unittest.main()
