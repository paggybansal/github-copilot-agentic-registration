"""Password-hashing helper for the registration service (T5).

Thin wrapper around Werkzeug's own password-hashing primitives. No custom
cryptography is implemented here, and Werkzeug's hashing defaults are never
overridden (FR-3, SEC-1).

Neither function ever logs, prints, or includes a password or a password hash
in an exception message; both simply return their result or propagate a
``TypeError`` for a non-string input, as Werkzeug itself raises.
"""

from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Return a secure hash of ``password`` using Werkzeug's default algorithm."""
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Return ``True`` if ``password`` matches ``password_hash``, else ``False``."""
    return check_password_hash(password_hash, password)
