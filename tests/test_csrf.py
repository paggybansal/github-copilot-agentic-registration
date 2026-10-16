"""Dedicated CSRF-protection tests for POST /register (T9).

T8 already proved a baseline missing-token-rejected / valid-token-accepted
case in ``tests/test_routes.py``. This file adds the deeper cases required
by the plan's T9 done criteria: an invalid (tampered) token, an expired
token, and confirmation that CSRF uses the *real* configuration
(``WTF_CSRF_ENABLED=True``), not the test-default override.
"""

from __future__ import annotations

import re
import time

import pytest

from registration_app.app import create_app
from registration_app.config import Config, TestConfig

HTTP_OK = 200
HTTP_FOUND = 302
HTTP_BAD_REQUEST = 400

VALID_FULL_NAME = "New User"
VALID_EMAIL = "new.user@example.test"
VALID_PASSWORD = "Example123"  # noqa: S105


def _valid_form_data(**overrides):
    data = {
        "full_name": VALID_FULL_NAME,
        "email": VALID_EMAIL,
        "password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    }
    data.update(overrides)
    return data


def _extract_csrf_token(html: bytes) -> str:
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert match is not None, "csrf_token field not found in rendered form"
    return match.group(1).decode()


@pytest.fixture
def csrf_app(tmp_path):
    """A real-CSRF-enabled app; the default TestConfig disables CSRF for
    ordinary functional tests, so CSRF-specific tests must opt back in
    explicitly (the only approved way to disable CSRF is test configuration;
    these tests prove the real, enabled behavior instead)."""
    db_path = tmp_path / "registration.db"

    class CsrfEnabledTestConfig(TestConfig):
        DATABASE_PATH = str(db_path)
        WTF_CSRF_ENABLED = True

    return create_app(config_class=CsrfEnabledTestConfig)


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


def test_csrf_is_enabled_in_real_non_test_configuration():
    # Assert: the real application configuration never disables CSRF; only
    # an explicit test configuration override may do so (SEC-4).
    assert Config.WTF_CSRF_ENABLED is True


def test_register_post_valid_csrf_token_accepted(csrf_client):
    # Arrange
    get_response = csrf_client.get("/register")
    token = _extract_csrf_token(get_response.data)

    # Act
    response = csrf_client.post("/register", data=_valid_form_data(csrf_token=token))

    # Assert
    assert response.status_code == HTTP_FOUND


def test_register_post_missing_csrf_token_rejected(csrf_client):
    # Act: no csrf_token field present at all.
    response = csrf_client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_BAD_REQUEST


def test_register_post_tampered_csrf_token_rejected(csrf_client):
    # Arrange
    get_response = csrf_client.get("/register")
    token = _extract_csrf_token(get_response.data)
    tampered_token = token[:-1] + ("a" if token[-1] != "a" else "b")

    # Act
    response = csrf_client.post(
        "/register", data=_valid_form_data(csrf_token=tampered_token)
    )

    # Assert
    assert response.status_code == HTTP_BAD_REQUEST


def test_register_post_malformed_csrf_token_rejected(csrf_client):
    # Act: a well-formed-looking but entirely fabricated token value.
    response = csrf_client.post(
        "/register", data=_valid_form_data(csrf_token="not-a-real-token")  # noqa: S106
    )

    # Assert
    assert response.status_code == HTTP_BAD_REQUEST


def test_register_post_expired_csrf_token_rejected(tmp_path):
    # Arrange: a short CSRF time limit so a token issued just before the
    # limit elapses is provably expired, without relying on the production
    # default (1 hour).
    db_path = tmp_path / "registration.db"

    class ShortLivedCsrfConfig(TestConfig):
        DATABASE_PATH = str(db_path)
        WTF_CSRF_ENABLED = True
        WTF_CSRF_TIME_LIMIT = 1

    app = create_app(config_class=ShortLivedCsrfConfig)
    client = app.test_client()
    get_response = client.get("/register")
    token = _extract_csrf_token(get_response.data)

    time.sleep(2.0)

    # Act
    response = client.post("/register", data=_valid_form_data(csrf_token=token))

    # Assert
    assert response.status_code == HTTP_BAD_REQUEST


def test_register_get_does_not_require_csrf_token(csrf_client):
    # Act
    response = csrf_client.get("/register")

    # Assert: CSRF protection applies to state-changing POSTs, not GET.
    assert response.status_code == HTTP_OK
