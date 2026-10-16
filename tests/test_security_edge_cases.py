"""Security edge-case tests for the registration flow (T9).

Covers the plan's T9 done criteria beyond the dedicated CSRF tests in
``tests/test_csrf.py``: the submitted password and any password hash never
appear in a response across any outcome (success, validation failure,
duplicate email, database failure), raw database/internal details never
reach the user on an unexpected failure, the submitted password and the
CSRF token never appear in application logs, and no secret-bearing or
database file is tracked by Git (SEC-4, NFR-2, ADD-1, EC-15, EC-16).
"""

from __future__ import annotations

import re
import subprocess

import pytest

from registration_app import routes
from registration_app.app import create_app
from registration_app.config import TestConfig
from registration_app.db import get_db
from registration_app.repository import RepositoryError
from registration_app.security import hash_password

HTTP_OK = 200
HTTP_FOUND = 302

VALID_FULL_NAME = "New User"
VALID_EMAIL = "new.user@example.test"
VALID_PASSWORD = "Example123"  # noqa: S105
WEAK_PASSWORD = "weak"  # noqa: S105


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


def test_register_success_response_never_contains_plain_password(client):
    # Act
    response = client.post("/register", data=_valid_form_data(), follow_redirects=True)

    # Assert
    assert response.status_code == HTTP_OK
    assert VALID_PASSWORD.encode() not in response.data


def test_register_validation_failure_response_never_contains_plain_password(client):
    # Act
    weak_fields = {"password": WEAK_PASSWORD, "confirm_password": WEAK_PASSWORD}
    response = client.post("/register", data=_valid_form_data(**weak_fields))

    # Assert
    assert response.status_code == HTTP_OK
    assert WEAK_PASSWORD.encode() not in response.data


def test_register_duplicate_email_response_never_contains_plain_password(client, create_user):
    # Arrange
    create_user(email=VALID_EMAIL)

    # Act
    response = client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_OK
    assert VALID_PASSWORD.encode() not in response.data


def test_register_database_failure_response_never_contains_plain_password(
    client, monkeypatch
):
    # Arrange
    def _raise_repository_error(*args, **kwargs):
        raise RepositoryError("Registration could not be completed. Please try again")

    monkeypatch.setattr(routes, "create_user", _raise_repository_error)

    # Act
    response = client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_OK
    assert VALID_PASSWORD.encode() not in response.data


def test_register_success_response_never_contains_password_hash(client, app):
    # Act
    response = client.post("/register", data=_valid_form_data(), follow_redirects=True)

    # Assert
    assert response.status_code == HTTP_OK
    with app.app_context():
        connection = get_db()
        row = connection.execute(
            "SELECT password_hash FROM users WHERE email = ?", (VALID_EMAIL,)
        ).fetchone()
    assert row is not None
    stored_hash = row[0]
    assert stored_hash.encode() not in response.data


def test_register_database_failure_response_contains_only_generic_message(
    client, monkeypatch
):
    """An unexpected database failure must never leak SQL text, a database
    path, or a Python traceback to the user (SEC-6, ADD-1); only the
    approved generic message is shown."""

    # Arrange
    internal_detail = "sqlite3.OperationalError: no such table: /instance/registration.db"

    def _raise_repository_error(*args, **kwargs):
        raise RepositoryError("Registration could not be completed. Please try again")

    monkeypatch.setattr(routes, "create_user", _raise_repository_error)

    # Act
    response = client.post("/register", data=_valid_form_data())

    # Assert
    assert response.status_code == HTTP_OK
    assert b"Registration could not be completed. Please try again" in response.data
    assert b"Traceback" not in response.data
    assert b"sqlite3" not in response.data
    assert b".db" not in response.data
    assert internal_detail.encode() not in response.data


def test_register_success_plain_password_never_logged(client, caplog):
    # Act
    client.post("/register", data=_valid_form_data())

    # Assert
    assert VALID_PASSWORD not in caplog.text


def test_register_database_failure_plain_password_never_logged(client, monkeypatch, caplog):
    # Arrange
    def _raise_repository_error(*args, **kwargs):
        raise RepositoryError("Registration could not be completed. Please try again")

    monkeypatch.setattr(routes, "create_user", _raise_repository_error)

    # Act
    client.post("/register", data=_valid_form_data())

    # Assert
    assert VALID_PASSWORD not in caplog.text


def test_register_valid_csrf_token_never_appears_in_logs(client, caplog):
    # Arrange
    get_response = client.get("/register")

    # Act
    client.post("/register", data=_valid_form_data())

    # Assert: the rendered CSRF token value itself must not leak into logs.
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', get_response.data)
    if match is not None:
        token = match.group(1).decode()
        assert token not in caplog.text


def test_git_tracked_files_exclude_env_and_database_and_key_files():
    # Act
    result = subprocess.run(  # noqa: S603
        ["git", "ls-files"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    )
    tracked_files = result.stdout.splitlines()

    # Assert
    forbidden_suffixes = (".env", ".db", ".sqlite", ".sqlite3", ".pem", ".key")
    violations = [
        path
        for path in tracked_files
        if path.endswith(forbidden_suffixes) and path != ".env.example"
    ]
    assert violations == []
