"""Registration route handlers (T8).

Orchestrates CSRF validation (``RegistrationForm``), business validation
(``validation.py``), password hashing (``security.py``), and persistence
(``repository.py``) for GET/POST ``/register`` and GET ``/register/success``
(architecture Section 2, Section 7).

The plain password and any password hash are never passed into a template
context, a log message, or an exception message anywhere in this module
(SEC-1, SEC-7, FR-6).
"""

from __future__ import annotations

from flask import Blueprint, redirect, render_template, url_for

from registration_app import validation
from registration_app.db import get_db
from registration_app.forms import RegistrationForm
from registration_app.repository import (
    DuplicateEmailError,
    RepositoryError,
    create_user,
)
from registration_app.security import hash_password

bp = Blueprint("registration", __name__)

#: Approved user-facing messages (requirements Section "Approved messages").
DUPLICATE_EMAIL_MESSAGE = "An account with this email already exists"
DATABASE_ERROR_MESSAGE = "Registration could not be completed. Please try again"


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Render the registration form (GET) or process a submission (POST).

    A POST with a missing/invalid CSRF token never reaches this view body:
    Flask-WTF's ``CSRFProtect`` extension aborts the request with HTTP 400
    before routing (DR-3), so ``form.validate_on_submit()`` returning
    ``False`` here only happens on a plain GET request.
    """
    form = RegistrationForm()

    if form.validate_on_submit():
        return _process_submission(form)

    return render_template(
        "register.html", form=form, full_name="", email="", errors={}
    )


def _process_submission(form: RegistrationForm):
    """Normalize, validate, and (on success) persist a registration submission."""
    full_name = validation.normalize_full_name(form.full_name.data or "")
    email = validation.normalize_email(form.email.data or "")
    password = form.password.data or ""
    confirm_password = form.confirm_password.data or ""

    errors = _collect_validation_errors(full_name, email, password, confirm_password)
    if errors:
        return render_template(
            "register.html", form=form, full_name=full_name, email=email, errors=errors
        ), 200

    password_hash = hash_password(password)
    connection = get_db()

    try:
        create_user(connection, full_name, email, password_hash)
    except DuplicateEmailError:
        return render_template(
            "register.html",
            form=form,
            full_name=full_name,
            email=email,
            errors={"email": [DUPLICATE_EMAIL_MESSAGE]},
        ), 200
    except RepositoryError:
        return render_template(
            "register.html",
            form=form,
            full_name=full_name,
            email=email,
            errors={"general": [DATABASE_ERROR_MESSAGE]},
        ), 200

    return redirect(url_for("registration.registration_success"))


def _collect_validation_errors(
    full_name: str, email: str, password: str, confirm_password: str
) -> dict[str, list[str]]:
    """Run all T4 validation functions and collect errors by field name."""
    errors: dict[str, list[str]] = {}

    full_name_errors = validation.validate_full_name(full_name)
    if full_name_errors:
        errors["full_name"] = full_name_errors

    email_errors = validation.validate_email(email)
    if email_errors:
        errors["email"] = email_errors

    password_errors = validation.validate_password(password)
    if password_errors:
        errors["password"] = password_errors

    confirm_password_errors = validation.validate_password_confirmation(
        password, confirm_password
    )
    if confirm_password_errors:
        errors["confirm_password"] = confirm_password_errors

    return errors


@bp.route("/register/success", methods=["GET"])
def registration_success():
    """Render the success page only; no submitted data is passed in (FR-16)."""
    return render_template("registration_success.html")
