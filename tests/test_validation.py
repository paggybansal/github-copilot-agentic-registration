"""Unit tests for the validation and normalization module (T4)."""

from __future__ import annotations

from registration_app.validation import (
    EMAIL_MAX_LENGTH,
    ERROR_EMAIL_INVALID,
    ERROR_EMAIL_REQUIRED,
    ERROR_EMAIL_TOO_LONG,
    ERROR_FULL_NAME_CONTROL_CHARACTER,
    ERROR_FULL_NAME_REQUIRED,
    ERROR_FULL_NAME_TOO_LONG,
    ERROR_PASSWORD_MISSING_DIGIT,
    ERROR_PASSWORD_MISSING_LOWERCASE,
    ERROR_PASSWORD_MISSING_UPPERCASE,
    ERROR_PASSWORD_TOO_LONG,
    ERROR_PASSWORD_TOO_SHORT,
    ERROR_PASSWORDS_DO_NOT_MATCH,
    PASSWORD_MAX_LENGTH,
    normalize_email,
    normalize_full_name,
    validate_email,
    validate_full_name,
    validate_password,
    validate_password_confirmation,
)

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------


def test_normalize_email_mixed_case_returns_lowercase():
    assert normalize_email("New.User@Example.TEST") == "new.user@example.test"


def test_normalize_email_strips_leading_and_trailing_whitespace():
    assert normalize_email("  new.user@example.test  ") == "new.user@example.test"


def test_validate_email_valid_email_returns_no_errors():
    assert validate_email("new.user@example.test") == []


def test_validate_email_missing_at_returns_error():
    assert validate_email("new.userexample.test") == [ERROR_EMAIL_INVALID]


def test_validate_email_missing_domain_returns_error():
    assert validate_email("new.user@") == [ERROR_EMAIL_INVALID]


def test_validate_email_empty_returns_error():
    assert validate_email("") == [ERROR_EMAIL_REQUIRED]


def test_validate_email_exactly_254_characters_is_accepted():
    local_part = "a" * (EMAIL_MAX_LENGTH - len("@example.test"))
    email = f"{local_part}@example.test"
    assert len(email) == EMAIL_MAX_LENGTH
    assert validate_email(email) == []


def test_validate_email_255_characters_returns_length_error():
    local_part = "a" * (EMAIL_MAX_LENGTH + 1 - len("@example.test"))
    email = f"{local_part}@example.test"
    assert len(email) == EMAIL_MAX_LENGTH + 1
    assert ERROR_EMAIL_TOO_LONG in validate_email(email)


# ---------------------------------------------------------------------------
# Full name
# ---------------------------------------------------------------------------


def test_normalize_full_name_strips_leading_and_trailing_whitespace():
    assert normalize_full_name("  New User  ") == "New User"


def test_validate_full_name_valid_name_returns_no_errors():
    assert validate_full_name("New User") == []


def test_validate_full_name_unicode_characters_accepted():
    assert validate_full_name("Jos\u00e9 Mu\u00f1oz") == []


def test_validate_full_name_hyphens_and_apostrophes_accepted():
    assert validate_full_name("Mary-Jane O'Brien") == []


def test_validate_full_name_whitespace_only_rejected():
    # A whitespace-only value has already been trimmed to "" by
    # normalize_full_name before validation, so it is rejected as required.
    assert validate_full_name(normalize_full_name("   ")) == [ERROR_FULL_NAME_REQUIRED]


def test_validate_full_name_unicode_control_character_rejected():
    assert validate_full_name("New\x01User") == [ERROR_FULL_NAME_CONTROL_CHARACTER]


def test_validate_full_name_exactly_100_characters_is_accepted():
    name = "A" * 100
    assert validate_full_name(name) == []


def test_validate_full_name_101_characters_rejected():
    name = "A" * 101
    assert validate_full_name(name) == [ERROR_FULL_NAME_TOO_LONG]


def test_validate_full_name_empty_rejected():
    assert validate_full_name("") == [ERROR_FULL_NAME_REQUIRED]


# ---------------------------------------------------------------------------
# Password
# ---------------------------------------------------------------------------


def test_validate_password_valid_password_returns_no_errors():
    assert validate_password("Example123") == []


def test_validate_password_below_8_characters_returns_error():
    assert ERROR_PASSWORD_TOO_SHORT in validate_password("Exam1")


def test_validate_password_exactly_8_characters_is_accepted():
    assert validate_password("Exampl1A") == []


def test_validate_password_above_128_characters_returns_error():
    password = "Aa1" + "a" * 127  # 130 characters
    assert ERROR_PASSWORD_TOO_LONG in validate_password(password)


def test_validate_password_exactly_128_characters_is_accepted():
    password = "Aa1" + "a" * (PASSWORD_MAX_LENGTH - 3)
    assert len(password) == PASSWORD_MAX_LENGTH
    assert validate_password(password) == []


def test_validate_password_129_characters_returns_length_error():
    password = "Aa1" + "a" * (PASSWORD_MAX_LENGTH - 2)
    assert len(password) == PASSWORD_MAX_LENGTH + 1
    assert ERROR_PASSWORD_TOO_LONG in validate_password(password)


def test_validate_password_missing_uppercase_returns_error():
    assert ERROR_PASSWORD_MISSING_UPPERCASE in validate_password("example123")


def test_validate_password_missing_lowercase_returns_error():
    assert ERROR_PASSWORD_MISSING_LOWERCASE in validate_password("EXAMPLE123")


def test_validate_password_missing_number_returns_error():
    assert ERROR_PASSWORD_MISSING_DIGIT in validate_password("ExampleOnly")


def test_validate_password_is_never_modified_or_trimmed():
    # Arrange: a password with leading/trailing whitespace, which must be
    # preserved exactly -- validation must never trim or otherwise change it.
    submitted_password = "  Example123  "  # noqa: S105

    # Act
    validate_password(submitted_password)

    # Assert: the original string object/value is untouched by validation.
    assert submitted_password == "  Example123  "  # noqa: S105


# ---------------------------------------------------------------------------
# Password confirmation
# ---------------------------------------------------------------------------


def test_validate_password_confirmation_match_returns_no_errors():
    assert validate_password_confirmation("Example123", "Example123") == []


def test_validate_password_confirmation_mismatch_returns_error():
    assert validate_password_confirmation("Example123", "Different123") == [
        ERROR_PASSWORDS_DO_NOT_MATCH
    ]
