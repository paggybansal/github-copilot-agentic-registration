"""Per-request SQLite connection lifecycle for the registration service.

One ``sqlite3.Connection`` is opened lazily per application/request context and
stored on :data:`flask.g`. The schema is applied idempotently on first open, so
both test (``tmp_path``) databases and the real ``instance/`` database
self-initialize (architecture Section 5, Section 8; NFR-6, NFR-7, SEC-6).
"""

from __future__ import annotations

import sqlite3

from flask import Flask, current_app, g

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db() -> sqlite3.Connection:
    """Return the request-scoped SQLite connection, opening it on first use.

    The connection is stored on ``flask.g`` so repeated calls within the same
    application/request context reuse the same connection (NFR-7). The schema
    is applied (``CREATE TABLE IF NOT EXISTS``) every time a new connection is
    opened, which is safe to call multiple times (idempotent).
    """
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.execute(_SCHEMA)
        g.db.commit()
    return g.db


def close_db(exception: BaseException | None = None) -> None:
    """Close the request-scoped connection, if one was opened.

    Registered via ``app.teardown_appcontext`` so the connection is closed
    regardless of whether the request succeeded or failed.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app: Flask) -> None:
    """Register the teardown hook that closes the per-context connection."""
    app.teardown_appcontext(close_db)
