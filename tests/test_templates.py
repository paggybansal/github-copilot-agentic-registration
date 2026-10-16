"""Template-rendering tests for the base layout, registration, and success
templates (T7).

``routes.py`` does not exist yet (T8), so these tests call ``render_template``
directly inside an app/request context with a stub context dict, per the
plan's T7 done criteria.
"""

from __future__ import annotations

from flask import render_template

from registration_app.app import create_app
from registration_app.config import Config


def _make_app(tmp_path):
    db_path = tmp_path / "registration.db"

    class RealLikeConfig(Config):
        DATABASE_PATH = str(db_path)
        SECRET_KEY = "real-like-secret"  # noqa: S105

    return create_app(config_class=RealLikeConfig)


def test_register_template_renders_csrf_hidden_field(tmp_path):
    app = _make_app(tmp_path)

    with app.test_request_context("/register"):
        html = render_template(
            "register.html", full_name="", email="", errors={}
        )

    assert '<input type="hidden" name="csrf_token" value="' in html


def test_register_template_password_fields_render_empty(tmp_path):
    app = _make_app(tmp_path)

    with app.test_request_context("/register"):
        html = render_template(
            "register.html", full_name="", email="", errors={}
        )

    assert 'id="password"' in html
    assert 'name="password"\n            value=""' in html
    assert 'id="confirm_password"' in html
    assert 'name="confirm_password"\n            value=""' in html


def test_register_template_retains_full_name_and_email_on_redisplay(tmp_path):
    app = _make_app(tmp_path)

    with app.test_request_context("/register"):
        html = render_template(
            "register.html",
            full_name="New User",
            email="new.user@example.test",
            errors={},
        )

    assert 'value="New User"' in html
    assert 'value="new.user@example.test"' in html


def test_register_template_renders_field_specific_errors(tmp_path):
    app = _make_app(tmp_path)

    with app.test_request_context("/register"):
        html = render_template(
            "register.html",
            full_name="",
            email="",
            errors={"email": ["Enter a valid email address"]},
        )

    assert "Enter a valid email address" in html
    assert 'id="email-errors"' in html


def test_register_template_escapes_xss_shaped_full_name(tmp_path):
    app = _make_app(tmp_path)
    malicious_name = '<script>alert("registration-xss-test")</script>'

    with app.test_request_context("/register"):
        html = render_template(
            "register.html", full_name=malicious_name, email="", errors={}
        )

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_registration_success_template_renders_success_message(tmp_path):
    app = _make_app(tmp_path)

    with app.test_request_context("/register/success"):
        html = render_template("registration_success.html")

    assert "Registration successful" in html


def test_registration_success_template_contains_no_submitted_data(tmp_path):
    app = _make_app(tmp_path)

    with app.test_request_context("/register/success"):
        html = render_template("registration_success.html")

    assert "New User" not in html
    assert "new.user@example.test" not in html
    assert "Example123" not in html
    assert "password" not in html.lower()
