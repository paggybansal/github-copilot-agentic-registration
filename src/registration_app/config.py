"""Application configuration for the registration service.

Configuration values are sourced from environment variables so that no secret is ever
hardcoded in source control. See ``.env.example`` for the recognized variable names.
"""

from __future__ import annotations

import os

#: Default local SQLite path used only when ``REGISTRATION_DATABASE`` is not set.
DEFAULT_DATABASE_PATH = "instance/registration.db"

#: Comfortably above the sum of the approved maximum field lengths (FR-14), so a
#: legitimate submission is never rejected while an oversized request body is
#: rejected by Flask before it reaches validation (design-review decision ADD-6).
MAX_CONTENT_LENGTH_BYTES = 16 * 1024


class Config:
    """Base configuration used by the real (non-test) application."""

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "")
    DATABASE_PATH = os.environ.get("REGISTRATION_DATABASE", DEFAULT_DATABASE_PATH)
    WTF_CSRF_ENABLED = True
    TESTING = False

    # Hardcoded, not environment-controlled: design-review decision ADD-1 requires
    # DEBUG to be False in every non-test configuration so Flask never returns an
    # interactive traceback page that could expose internal details.
    DEBUG = False

    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_BYTES


# TestConfig.SECRET_KEY is an intentional, deterministic, public test-only value.
# It must only ever be applied explicitly by test fixtures (never selected through
# any environment variable or other externally reachable path).
class TestConfig(Config):
    """Configuration override used by the automated test suite.

    CSRF is disabled by default here so ordinary functional tests do not need to
    supply a token. Tests that specifically verify CSRF behavior must explicitly
    override ``WTF_CSRF_ENABLED=True`` (and a valid/invalid token), per the
    "tests may disable CSRF only through explicit test configuration" security rule.
    """

    TESTING = True
    WTF_CSRF_ENABLED = False

    # Deterministic, test-only value; never a real secret and never read from the
    # environment, so test runs do not depend on FLASK_SECRET_KEY being set.
    SECRET_KEY = "test-secret-key"  # noqa: S105
