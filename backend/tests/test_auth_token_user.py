"""Signing in and resuming a session return the user -- and what the app
needs to start (server date, branding, knowledgebase switch) -- with the
token, so starting the app is one round trip.

Standard library only. Run from the backend directory:
    python -m unittest discover -s tests
"""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

import app.main  # noqa: F401 -- registers every model on Base.metadata
from app.api import auth as auth_api
from app.core.database import Base
from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import LoginRequest
from tests.test_dashboard_service import make


def _request(cookie: str | None = None) -> Request:
    headers = [(b"cookie", f"refresh_token={cookie}".encode())] if cookie else []
    return Request({"type": "http", "method": "POST", "path": "/", "headers": headers, "client": ("127.0.0.1", 1)})


def _cookie(response: Response) -> str:
    header = response.headers["set-cookie"]
    return header.split("refresh_token=", 1)[1].split(";", 1)[0]


class TokenCarriesUserTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.addCleanup(self.db.close)
        self.user = make(
            self.db, User, username="ahmed@example.com", full_name="Ahmed Rashid", email="ahmed@example.com",
            password_hash=hash_password("correct horse"), role="Administrator", is_active=True,
        )
        self.db.commit()

    def test_login_and_refresh_return_the_user(self):
        response = Response()
        tokens = auth_api.login(
            LoginRequest(username="ahmed@example.com", password="correct horse"), _request(), response, self.db
        )
        self.assertTrue(tokens.access_token)
        self.assertEqual(tokens.user.name, "Ahmed Rashid")
        self.assertIsInstance(tokens.user.permissions, dict)

        again = Response()
        refreshed = auth_api.refresh(_request(_cookie(response)), again, self.db)
        self.assertEqual(refreshed.user.name, "Ahmed Rashid")
        # Same user shape GET /me sends.
        me = auth_api.me(self.user, self.db)
        self.assertEqual(refreshed.user.model_dump(), me.model_dump())
        # What the app needs to start comes along too.
        self.assertRegex(refreshed.session.serverTime.date, r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(refreshed.session.branding.brandColor)
        self.assertIsInstance(refreshed.session.knowledgeEnabled, bool)
        # And the refresh token is never in the body.
        self.assertNotIn("refresh_token", refreshed.model_dump())


    def test_knowledge_switch_is_false_without_access(self):
        from unittest import mock

        from app.services import ai_config_service

        config = mock.Mock(is_enabled=True)
        with mock.patch.object(ai_config_service, "get_configuration", return_value=(config, [])), \
                mock.patch("app.services.role_service.has_permission", side_effect=lambda db, role, module, action: role == "Administrator"):
            self.assertTrue(auth_api._session_bootstrap(self.db, self.user).knowledgeEnabled)
            self.user.role = "Viewer"
            self.assertFalse(auth_api._session_bootstrap(self.db, self.user).knowledgeEnabled)


if __name__ == "__main__":
    unittest.main()
