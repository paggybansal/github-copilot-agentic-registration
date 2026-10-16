"""User repository for the registration service (T6).

Functions receive an explicit ``sqlite3.Connection`` parameter rather than
calling ``db.get_db()`` internally (architecture Section 8, ADD-5), so they
can be unit-tested directly against a ``tmp_path`` connection without a Flask
application/request context.

All SQL is parameterized; no password, password hash, SQL text, or database
path ever appears in a log message or exception (SEC-2, SEC-3, SEC-6).
"""

from __future__ import annotations

import sqlite3


class DuplicateEmailError(Exception):
    """Raised when an insert fails because the normalized email already exists.

    Covers the concurrent-insert race condition: ``email_exists()`` found no
    row, but a competing request committed the same email first, so the
    SQLite ``UNIQUE`` constraint on ``email`` raised ``sqlite3.IntegrityError``
    (ADD-2, EC-12, EC-13).
    """


class RepositoryError(Exception):
    """Raised for any unexpected database failure during a write.

    The message is always a static, domain-safe string; it never contains
    SQL text, a database path, or any other internal detail (SEC-6, EC-14).
    """


def email_exists(connection: sqlite3.Connection, normalized_email: str) -> bool:
    """Return ``True`` if a user with ``normalized_email`` already exists."""
    cursor = connection.execute(
        "SELECT 1 FROM users WHERE email = ? LIMIT 1",
        (normalized_email,),
    )
    return cursor.fetchone() is not None


def find_user_by_email(
    connection: sqlite3.Connection, normalized_email: str
) -> sqlite3.Row | None:
    """Return the full user row for ``normalized_email``, or ``None``.

    Read-only test/verification-support helper (architecture Revision 2); not
    called by any production route, since login/authentication is out of
    scope for this story.
    """
    connection.row_factory = sqlite3.Row
    cursor = connection.execute(
        "SELECT id, full_name, email, password_hash, created_at FROM users WHERE email = ?",
        (normalized_email,),
    )
    return cursor.fetchone()


def create_user(
    connection: sqlite3.Connection,
    full_name: str,
    normalized_email: str,
    password_hash: str,
) -> None:
    """Insert a new user row, committing on success.

    Raises ``DuplicateEmailError`` if the insert violates the ``email``
    ``UNIQUE`` constraint (including the concurrent-insert race), and
    ``RepositoryError`` for any other database failure, after rolling back.
    """
    try:
        connection.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
            (full_name, normalized_email, password_hash),
        )
        connection.commit()
    except sqlite3.IntegrityError as exc:
        connection.rollback()
        if "email" in str(exc).lower():
            raise DuplicateEmailError(
                "An account with this email already exists"
            ) from exc
        raise RepositoryError(
            "Registration could not be completed. Please try again"
        ) from exc
    except sqlite3.Error as exc:
        connection.rollback()
        raise RepositoryError(
            "Registration could not be completed. Please try again"
        ) from exc
