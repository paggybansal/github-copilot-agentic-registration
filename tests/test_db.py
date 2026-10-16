"""Unit tests for the SQLite schema and per-request connection lifecycle (T2)."""

from __future__ import annotations

import sqlite3

from registration_app.app import create_app
from registration_app.config import Config
from registration_app.db import get_db


def _make_app(tmp_path):
    db_path = tmp_path / "registration.db"

    class RealLikeConfig(Config):
        DATABASE_PATH = str(db_path)
        SECRET_KEY = "real-like-secret"  # noqa: S105

    return create_app(config_class=RealLikeConfig)


def test_get_db_creates_users_table_idempotently(tmp_path):
    app = _make_app(tmp_path)

    with app.app_context():
        # Act: open the connection twice within the same context to prove the
        # same connection is reused (NFR-7).
        connection = get_db()
        connection_again = get_db()

        cursor = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        table = cursor.fetchone()

    with app.app_context():
        # Act: a fresh context against the same database file proves schema
        # creation is safe to repeat (idempotent).
        connection_second_context = get_db()
        cursor = connection_second_context.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        table_second_context = cursor.fetchone()

    # Assert
    assert table is not None
    assert table_second_context is not None
    assert connection is connection_again


def test_get_db_users_table_has_required_columns(tmp_path):
    app = _make_app(tmp_path)

    with app.app_context():
        connection = get_db()
        cursor = connection.execute("PRAGMA table_info(users)")
        columns = {row[1] for row in cursor.fetchall()}

    # Assert
    assert columns == {"id", "full_name", "email", "password_hash", "created_at"}


def test_get_db_enforces_unique_email_constraint(tmp_path):
    app = _make_app(tmp_path)

    with app.app_context():
        connection = get_db()
        connection.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
            ("Ada Lovelace", "ada@example.com", "hashed-value"),
        )
        connection.commit()

        # Act / Assert: a second insert with the same email violates UNIQUE.
        raised = False
        try:
            connection.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                ("Ada L.", "ada@example.com", "another-hashed-value"),
            )
            connection.commit()
        except sqlite3.IntegrityError:
            raised = True

        assert raised is True


def test_close_db_closes_connection_on_teardown(tmp_path):
    app = _make_app(tmp_path)

    with app.app_context():
        connection = get_db()

    # Act / Assert: after the context exits, teardown closed the connection,
    # so any further use raises sqlite3.ProgrammingError.
    raised = False
    try:
        connection.execute("SELECT 1")
    except sqlite3.ProgrammingError:
        raised = True

    assert raised is True
