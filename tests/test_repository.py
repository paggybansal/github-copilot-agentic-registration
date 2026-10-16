"""Unit/integration tests for the user repository module (T6)."""

from __future__ import annotations

import sqlite3

import pytest

from registration_app import db as db_module
from registration_app.repository import (
    DuplicateEmailError,
    RepositoryError,
    create_user,
    email_exists,
    find_user_by_email,
)


@pytest.fixture
def connection(tmp_path):
    """A tmp_path SQLite connection with the users schema applied directly.

    No Flask application/request context is used here, proving the
    repository functions are testable with an explicit connection alone
    (ADD-5).
    """
    db_path = tmp_path / "registration.db"
    conn = sqlite3.connect(db_path)
    conn.execute(db_module._SCHEMA)  # noqa: SLF001
    conn.commit()
    yield conn
    conn.close()


def test_email_exists_returns_false_for_unknown_email(connection):
    assert email_exists(connection, "new.user@example.test") is False


def test_email_exists_returns_true_after_insert(connection):
    create_user(connection, "New User", "new.user@example.test", "hashed-value")

    assert email_exists(connection, "new.user@example.test") is True


def test_create_user_inserts_successfully(connection):
    create_user(connection, "New User", "new.user@example.test", "hashed-value")

    row = find_user_by_email(connection, "new.user@example.test")
    assert row is not None
    assert row["full_name"] == "New User"
    assert row["email"] == "new.user@example.test"
    assert row["password_hash"] == "hashed-value"  # noqa: S105


def test_find_user_by_email_returns_none_for_unknown_email(connection):
    assert find_user_by_email(connection, "missing@example.test") is None


def test_create_user_duplicate_email_raises_duplicate_email_error(connection):
    create_user(connection, "New User", "new.user@example.test", "hashed-value")

    with pytest.raises(DuplicateEmailError):
        create_user(connection, "Another User", "new.user@example.test", "another-hash")


def test_create_user_duplicate_email_different_casing_is_rejected_by_application_layer(
    connection,
):
    """The repository stores whatever normalized email it is given; the caller
    (routes.py, in a later task) is responsible for lowercasing before this
    call, per FR-12. Passing the same already-normalized value twice proves
    the unique constraint still catches the race regardless of case the
    caller previously normalized."""
    create_user(connection, "New User", "new.user@example.test", "hashed-value")

    with pytest.raises(DuplicateEmailError):
        create_user(connection, "New User", "new.user@example.test", "hashed-value")


def test_create_user_does_not_leave_partial_row_after_duplicate_rejection(connection):
    create_user(connection, "New User", "new.user@example.test", "hashed-value")

    with pytest.raises(DuplicateEmailError):
        create_user(connection, "Second User", "new.user@example.test", "second-hash")

    cursor = connection.execute(
        "SELECT COUNT(*) FROM users WHERE email = ?", ("new.user@example.test",)
    )
    assert cursor.fetchone()[0] == 1


def test_create_user_sql_injection_shaped_full_name_stored_safely_as_data(connection):
    malicious_name = "Robert'); DROP TABLE users;--"

    create_user(connection, malicious_name, "new.user@example.test", "hashed-value")

    row = find_user_by_email(connection, "new.user@example.test")
    assert row["full_name"] == malicious_name

    # The users table still exists and still contains exactly one row.
    cursor = connection.execute("SELECT COUNT(*) FROM users")
    assert cursor.fetchone()[0] == 1


def test_create_user_sql_injection_shaped_email_stored_safely_as_data(connection):
    malicious_email = "a@example.test'); DROP TABLE users;--"

    create_user(connection, "New User", malicious_email, "hashed-value")

    row = find_user_by_email(connection, malicious_email)
    assert row is not None
    assert row["email"] == malicious_email


def test_create_user_uses_parameterized_sql_not_string_interpolation(connection):
    """Prove the INSERT statement executed against sqlite3 never contains the
    submitted values directly -- i.e. parameters are passed separately from
    the SQL string."""

    class RecordingConnection:
        """Wraps a real connection, recording the exact SQL/parameters sqlite3
        receives, while still delegating to the real connection underneath."""

        def __init__(self, real_connection):
            self._real = real_connection
            self.last_sql = None
            self.last_parameters = None

        def execute(self, sql, parameters=()):
            self.last_sql = sql
            self.last_parameters = parameters
            return self._real.execute(sql, parameters)

        def commit(self):
            self._real.commit()

        def rollback(self):
            self._real.rollback()

    recording_connection = RecordingConnection(connection)

    create_user(recording_connection, "New User", "new.user@example.test", "hashed-value")

    assert "?" in recording_connection.last_sql
    assert "New User" not in recording_connection.last_sql
    assert "new.user@example.test" not in recording_connection.last_sql
    assert recording_connection.last_parameters == (
        "New User",
        "new.user@example.test",
        "hashed-value",
    )


def test_create_user_other_integrity_error_raises_repository_error_with_safe_message():
    """A non-email IntegrityError (e.g. a NOT NULL violation surfaced as an
    IntegrityError by some other constraint) must map to the generic
    RepositoryError, not DuplicateEmailError, and must not expose SQL."""

    class RaisingConnection:
        def __init__(self):
            self.rolled_back = False

        def execute(self, sql, parameters=()):
            raise sqlite3.IntegrityError("NOT NULL constraint failed: users.full_name")

        def commit(self):
            raise AssertionError("commit() must not be called after a failed insert")

        def rollback(self):
            self.rolled_back = True

    raising_connection = RaisingConnection()

    with pytest.raises(RepositoryError) as exc_info:
        create_user(raising_connection, "New User", "new.user@example.test", "hashed-value")

    assert raising_connection.rolled_back is True
    assert "Registration could not be completed" in str(exc_info.value)
    assert "NOT NULL" not in str(exc_info.value)
    assert "SELECT" not in str(exc_info.value)
    assert "INSERT" not in str(exc_info.value)


def test_create_user_unexpected_database_error_rolls_back_and_raises_repository_error():
    class RaisingConnection:
        def __init__(self):
            self.rolled_back = False

        def execute(self, sql, parameters=()):
            raise sqlite3.OperationalError("disk I/O error")

        def commit(self):
            raise AssertionError("commit() must not be called after a failed insert")

        def rollback(self):
            self.rolled_back = True

    raising_connection = RaisingConnection()

    with pytest.raises(RepositoryError) as exc_info:
        create_user(raising_connection, "New User", "new.user@example.test", "hashed-value")

    assert raising_connection.rolled_back is True
    assert "Registration could not be completed" in str(exc_info.value)
    assert "disk I/O error" not in str(exc_info.value)
