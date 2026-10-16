"""Pure validation and normalization functions for registration input (T4).

This module has no Flask or database imports, so it can be unit-tested in
isolation and reused by the future registration route (architecture Section 7).

Every ``validate_*`` function returns a ``list[str]`` of field-specific error
messages: an empty list means the value is valid. This is the single
consistent return pattern used throughout the module.

Password and Confirm Password are never trimmed, normalized, logged, printed,
or otherwise modified anywhere in this module (FR-12; registration-security
skill: never log a submitted password).
"""

from __future__ import annotations

import re
import unicodedata

FULL_NAME_MAX_LENGTH = 100
EMAIL_MAX_LENGTH = 254
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

#: Practical email-format check: local-part@domain, with at least one `.` in
#: the domain and no whitespace anywhere (architecture Section 7, step 4).
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

ERROR_FULL_NAME_REQUIRED = "Full Name is required"
ERROR_FULL_NAME_CONTROL_CHARACTER = "Full Name may not contain control characters"
ERROR_FULL_NAME_TOO_LONG = f"Full Name must be at most {FULL_NAME_MAX_LENGTH} characters"
ERROR_EMAIL_REQUIRED = "Email is required"
ERROR_EMAIL_INVALID = "Enter a valid email address"
ERROR_EMAIL_TOO_LONG = f"Email must be at most {EMAIL_MAX_LENGTH} characters"
# The following are user-facing validation message strings, not secrets; the
# "PASSWORD" substring in each constant name is a false-positive trigger for
# ruff's S105 (hardcoded-password) check.
ERROR_PASSWORD_REQUIRED = "Password is required"  # noqa: S105
ERROR_PASSWORD_TOO_SHORT = f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
ERROR_PASSWORD_TOO_LONG = f"Password must be at most {PASSWORD_MAX_LENGTH} characters"
ERROR_PASSWORD_MISSING_UPPERCASE = "Password must contain at least one uppercase letter"  # noqa: S105
ERROR_PASSWORD_MISSING_LOWERCASE = "Password must contain at least one lowercase letter"  # noqa: S105
ERROR_PASSWORD_MISSING_DIGIT = "Password must contain at least one digit"  # noqa: S105
ERROR_CONFIRM_PASSWORD_REQUIRED = "Confirm Password is required"  # noqa: S105
ERROR_PASSWORDS_DO_NOT_MATCH = "Passwords do not match"


def normalize_full_name(full_name: str) -> str:
    """Trim leading and trailing whitespace from Full Name (FR-12)."""
    return full_name.strip()


def normalize_email(email: str) -> str:
    """Trim whitespace and lowercase Email (FR-12)."""
    return email.strip().lower()


def validate_full_name(normalized_full_name: str) -> list[str]:
    """Validate an already-trimmed Full Name value (FR-13, FR-14, ADD-4).

    Rejects an empty or whitespace-only value, rejects any Unicode category
    ``Cc`` (control character), and enforces the 100-character maximum.
    Unicode letters, spaces, hyphens, apostrophes, and other normal
    punctuation are accepted.
    """
    errors: list[str] = []

    if not normalized_full_name:
        errors.append(ERROR_FULL_NAME_REQUIRED)
        return errors

    if any(unicodedata.category(character) == "Cc" for character in normalized_full_name):
        errors.append(ERROR_FULL_NAME_CONTROL_CHARACTER)

    if len(normalized_full_name) > FULL_NAME_MAX_LENGTH:
        errors.append(ERROR_FULL_NAME_TOO_LONG)

    return errors


def validate_email(normalized_email: str) -> list[str]:
    """Validate an already-trimmed-and-lowercased Email value (FR-7, FR-14).

    Rejects an empty value, a value exceeding 254 characters, and a value
    that does not match a practical email format (missing ``@`` or domain).
    """
    errors: list[str] = []

    if not normalized_email:
        errors.append(ERROR_EMAIL_REQUIRED)
        return errors

    if len(normalized_email) > EMAIL_MAX_LENGTH:
        errors.append(ERROR_EMAIL_TOO_LONG)

    if not _EMAIL_PATTERN.match(normalized_email):
        errors.append(ERROR_EMAIL_INVALID)

    return errors


def validate_password(password: str) -> list[str]:
    """Validate Password without ever trimming or modifying it (FR-9, FR-14).

    Enforces an 8-128 character length and requires at least one uppercase
    letter, one lowercase letter, and one digit.
    """
    errors: list[str] = []

    if not password:
        errors.append(ERROR_PASSWORD_REQUIRED)
        return errors

    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(ERROR_PASSWORD_TOO_SHORT)

    if len(password) > PASSWORD_MAX_LENGTH:
        errors.append(ERROR_PASSWORD_TOO_LONG)

    if not any(character.isupper() for character in password):
        errors.append(ERROR_PASSWORD_MISSING_UPPERCASE)

    if not any(character.islower() for character in password):
        errors.append(ERROR_PASSWORD_MISSING_LOWERCASE)

    if not any(character.isdigit() for character in password):
        errors.append(ERROR_PASSWORD_MISSING_DIGIT)

    return errors


def validate_password_confirmation(password: str, confirm_password: str) -> list[str]:
    """Validate that Confirm Password is present and matches Password exactly (FR-8).

    Neither value is trimmed or modified.
    """
    errors: list[str] = []

    if not confirm_password:
        errors.append(ERROR_CONFIRM_PASSWORD_REQUIRED)
        return errors

    if confirm_password != password:
        errors.append(ERROR_PASSWORDS_DO_NOT_MATCH)

    return errors
