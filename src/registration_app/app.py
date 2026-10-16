"""Application factory for the registration service.

``create_app`` builds a configured :class:`flask.Flask` instance from an
explicit configuration class, initializes CSRF protection (DR-3), wires up
the per-request database connection lifecycle, and registers the
registration blueprint (T8).
"""

from __future__ import annotations

from flask import Flask
from flask_wtf import CSRFProtect

from registration_app import db
from registration_app.config import Config
from registration_app.routes import bp as registration_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    """Build and configure the Flask application.

    ``config_class`` defaults to the real, non-test :class:`Config`. There is
    no environment variable, request header, or other externally reachable
    mechanism that selects ``TestConfig`` instead: a caller must explicitly
    pass ``config_class=TestConfig`` (as test fixtures do) for test behavior
    to be applied.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Fail fast: a real (non-test) configuration must never start with an
    # empty/predictable SECRET_KEY (SEC-8). TestConfig is exempt because it
    # sets TESTING=True and supplies its own deterministic test-only secret.
    if not app.config.get("SECRET_KEY") and not app.config.get("TESTING", False):
        raise RuntimeError(
            "FLASK_SECRET_KEY is not set. Refusing to start the application with an "
            "empty SECRET_KEY. Set the FLASK_SECRET_KEY environment variable."
        )

    CSRFProtect(app)
    db.init_app(app)
    app.register_blueprint(registration_bp)

    return app
