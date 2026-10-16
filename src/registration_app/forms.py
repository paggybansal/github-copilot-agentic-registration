"""CSRF boundary for the registration page (T8).

``RegistrationForm`` exists solely to carry Flask-WTF's CSRF token and the
raw field declarations; it defines no WTForms validators and enforces no
business rules. All business validation lives in ``validation.py`` instead,
so validation stays in a plain, dependency-free, directly unit-testable
module (architecture Section 2 "Forms (CSRF boundary)" and Section 14).
"""

from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField


class RegistrationForm(FlaskForm):
    """Raw field declarations only; no validators (business rules excluded)."""

    full_name = StringField("Full Name")
    email = StringField("Email")
    password = PasswordField("Password")
    confirm_password = PasswordField("Confirm Password")
