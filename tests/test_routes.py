"""Flask integration tests for the registration route (T8).

Covers every scenario in the ``python-test-standards`` skill's "Required
Flask integration tests" list, using the Flask test client against an app
built with a ``tmp_path`` SQLite database. Dedicated CSRF edge cases (invalid
token in depth, logging assertions beyond this file) are extended in T9;
this file still proves a missing token is rejected (HTTP 400), an invalid
token is rejected (HTTP 400), and a valid token is accepted, per T8's done
criteria.
"""

from __future__ import annotations

import re

import pytest

from registration_app import routes
from registration_app.app import create_app
from registration_app.config import TestConfig
from registration_app.db import get_db
from registration_app.repository import DuplicateEmailError, RepositoryError
from registration_app.security import hash_password

HTTP_OK = 200
HTTP_FOUND = 302
HTTP_BAD_REQUEST = 400
HTTP_PAYLOAD_TOO_LARGE = 413

VALID_FULL_NAME = "New User"
VALID_EMAIL = "new.user@example.test"
VALID_PASSWORD = "Example123"  # noqa: S105
WEAK_PASSWORD = "weak"  # noqa: S105
MISMATCHED_PASSWORD = "Different123"  # noqa: S105


def _valid_form_data(**overrides):
    data = {
        "full_name": VALID_FULL_NAME,
        "email": VALID_EMAIL,
        "password": VALID_PASSWORD,
        "confirm_password": VALID_PASSWORD,
    }
    data.update(overrides)
    return data


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "registration.db"

    class RouteTestConfig(TestConfig):
        DATABASE_PATH = str(db_path)

    return create_app(config_class=RouteTestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def create_user(app):
    """Insert a user directly (bypassing the route) for duplicate-email setup."""

    def _create_user(
        full_name="Existing User",
        email="existing.user@example.test",
        password=VALID_PASSWORD,
    ):
        with app.app_context():
            connection = get_db()
            connection.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (full_name, email.strip().lower(), hash_password(password)),
            )
            connection.commit()

    return _create_user


def _count_users(app) -> int:
    with app.app_context():
        connection = get_db()
        return connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def test_register_get_returns_200_and_renders_form(client):
    # Act
    response = client.get("/register")

    # Assert
    assert response.status_code == HTTP_OK
    assert b'name="full_name"' in response.data
    assert b'name="email"' in response.data
    assert b'name="password"' in response.data
    assert b'name="confirm_password"' in response.data


def test_register_post_valid_data_creates_user_and_redirects(client, app):
    # Act
    response = client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_FOUND
    assert response.headers["Location"].endswith("/register/success")
    assert _count_users(app) == 1

    with app.app_context():
        connection = get_db()
        row = connection.execute(
            "SELECT email, password_hash FROM users WHERE email = ?", (VALID_EMAIL,)
        ).fetchone()
    assert row is not None
    assert row[0] == VALID_EMAIL
    assert row[1] != VALID_PASSWORD
    assert hash_password(VALID_PASSWORD) != row[1]  # hashes are salted/non-deterministic


def test_register_post_redirect_followed_shows_success_message(client):
    # Act
    response = client.post("/register", data=_valid_form_data(), follow_redirects=True)

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Registration successful" in response.data


def test_register_success_page_get_without_prior_submission_returns_200(client):
    # Act
    response = client.get("/register/success")

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Registration successful" in response.data


def test_register_post_missing_fields_rerenders_with_errors_and_retains_values(client, app):
    # Act
    response = client.post(
        "/register",
        data={"full_name": "", "email": "", "password": "", "confirm_password": ""},
    )

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Full Name is required" in response.data
    assert b"Email is required" in response.data
    assert b"Password is required" in response.data
    assert _count_users(app) == 0


def test_register_post_invalid_email_rerenders_with_error(client, app):
    # Act
    response = client.post("/register", data=_valid_form_data(email="not-an-email"))

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Enter a valid email address" in response.data
    assert _count_users(app) == 0


def test_register_post_weak_password_rerenders_with_error(client, app):
    # Act
    weak_fields = {"password": WEAK_PASSWORD, "confirm_password": WEAK_PASSWORD}
    response = client.post("/register", data=_valid_form_data(**weak_fields))

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Password must be at least 8 characters" in response.data
    assert _count_users(app) == 0


def test_register_post_password_mismatch_rerenders_with_error(client, app):
    # Act
    response = client.post(
        "/register", data=_valid_form_data(confirm_password=MISMATCHED_PASSWORD)
    )

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Passwords do not match" in response.data
    assert _count_users(app) == 0


def test_register_post_validation_failure_retains_full_name_and_email_but_not_passwords(
    client,
):
    # Act
    weak_fields = {"password": WEAK_PASSWORD, "confirm_password": WEAK_PASSWORD}
    response = client.post("/register", data=_valid_form_data(**weak_fields))

    # Assert
    assert response.status_code == HTTP_OK
    assert VALID_FULL_NAME.encode() in response.data
    assert VALID_EMAIL.encode() in response.data
    assert b'name="password"\n            value=""' in response.data
    assert b'name="confirm_password"\n            value=""' in response.data
    assert b"weak" not in response.data


def test_register_post_xss_shaped_full_name_escaped_in_rerendered_form(client):
    # Arrange
    malicious_name = '<script>alert("registration-xss-test")</script>'

    # Act
    weak_fields = {"password": WEAK_PASSWORD, "confirm_password": WEAK_PASSWORD}
    response = client.post(
        "/register", data=_valid_form_data(full_name=malicious_name, **weak_fields)
    )

    # Assert
    assert response.status_code == HTTP_OK
    assert b"<script>alert" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_register_post_sql_injection_shaped_input_handled_as_data(client, app):
    # Arrange
    injection_name = "Robert'); DROP TABLE users;--"

    # Act
    response = client.post("/register", data=_valid_form_data(full_name=injection_name))

    # Assert
    assert response.status_code == HTTP_FOUND
    with app.app_context():
        connection = get_db()
        row = connection.execute(
            "SELECT full_name FROM users WHERE email = ?", (VALID_EMAIL,)
        ).fetchone()
    assert row[0] == injection_name
    assert _count_users(app) == 1


def test_register_post_duplicate_email_same_case_rejects_second_user(client, app, create_user):
    # Arrange
    create_user(email=VALID_EMAIL)

    # Act
    response = client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_OK
    assert b"An account with this email already exists" in response.data
    assert _count_users(app) == 1


def test_register_post_duplicate_email_different_case_rejects_second_user(client, app, create_user):
    # Arrange
    create_user(email="new.user@example.test")

    # Act
    response = client.post("/register", data=_valid_form_data(email="NEW.USER@EXAMPLE.TEST"))

    # Assert
    assert response.status_code == HTTP_OK
    assert b"An account with this email already exists" in response.data
    assert _count_users(app) == 1


def test_register_post_database_error_returns_generic_message(client, app, monkeypatch):
    # Arrange
    def _raise_repository_error(*args, **kwargs):
        raise RepositoryError("Registration could not be completed. Please try again")

    monkeypatch.setattr(routes, "create_user", _raise_repository_error)

    # Act
    response = client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Registration could not be completed. Please try again" in response.data
    assert _count_users(app) == 0
    assert VALID_PASSWORD.encode() not in response.data


def test_register_post_duplicate_email_race_returns_duplicate_message(client, app, monkeypatch):
    # Arrange: simulate the concurrent-insert race where create_user itself
    # raises DuplicateEmailError (rather than email_exists() catching it first).
    def _raise_duplicate(*args, **kwargs):
        raise DuplicateEmailError("An account with this email already exists")

    monkeypatch.setattr(routes, "create_user", _raise_duplicate)

    # Act
    response = client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_OK
    assert b"An account with this email already exists" in response.data
    assert _count_users(app) == 0


def test_register_post_valid_data_plain_password_absent_from_response(client):
    # Act
    response = client.post("/register", data=_valid_form_data(), follow_redirects=True)

    # Assert
    assert VALID_PASSWORD.encode() not in response.data


def test_register_post_valid_data_plain_password_absent_from_logs(client, caplog):
    # Act
    client.post("/register", data=_valid_form_data())

    # Assert
    assert VALID_PASSWORD not in caplog.text


def test_register_post_oversized_request_body_rejected(client, app):
    # Arrange: well beyond Config.MAX_CONTENT_LENGTH (16 KiB) and any approved
    # field maximum, so Flask rejects the request body before routing.
    oversized_name = "A" * (32 * 1024)

    # Act
    response = client.post("/register", data=_valid_form_data(full_name=oversized_name))

    # Assert
    assert response.status_code == HTTP_PAYLOAD_TOO_LARGE
    assert _count_users(app) == 0


def _extract_csrf_token(html: bytes) -> str:
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert match is not None, "csrf_token field not found in rendered form"
    return match.group(1).decode()


@pytest.fixture
def csrf_app(tmp_path):
    """A real-CSRF-enabled app, since the default TestConfig disables CSRF."""
    db_path = tmp_path / "registration.db"

    class CsrfEnabledTestConfig(TestConfig):
        DATABASE_PATH = str(db_path)
        WTF_CSRF_ENABLED = True

    return create_app(config_class=CsrfEnabledTestConfig)


@pytest.fixture
def csrf_client(csrf_app):
    return csrf_app.test_client()


def test_register_post_missing_csrf_token_rejected(csrf_client):
    # Act: POST without any csrf_token field at all.
    response = csrf_client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_BAD_REQUEST


def test_register_post_invalid_csrf_token_rejected(csrf_client):
    # Arrange
    get_response = csrf_client.get("/register")
    assert get_response.status_code == HTTP_OK

    # Act
    response = csrf_client.post(
        "/register", data=_valid_form_data(csrf_token="not-a-real-token")  # noqa: S106
    )

    # Assert
    assert response.status_code == HTTP_BAD_REQUEST


def test_register_post_valid_csrf_token_accepted(csrf_client):
    # Arrange
    get_response = csrf_client.get("/register")
    token = _extract_csrf_token(get_response.data)

    # Act
    response = csrf_client.post(
        "/register", data=_valid_form_data(csrf_token=token)
    )

    # Assert
    assert response.status_code == HTTP_FOUND
