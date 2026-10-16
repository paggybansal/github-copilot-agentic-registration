"""Unit tests for the password-hashing helper module (T5)."""

from __future__ import annotations

from registration_app.security import hash_password, verify_password


def test_hash_password_returns_hash_different_from_plain_password():
    # Arrange
    password = "Example123"  # noqa: S105

    # Act
    password_hash = hash_password(password)

    # Assert
    assert password_hash != password
    assert isinstance(password_hash, str)
    assert len(password_hash) > 0


def test_verify_password_returns_true_for_correct_password():
    # Arrange
    password = "Example123"  # noqa: S105
    password_hash = hash_password(password)

    # Act / Assert
    assert verify_password(password_hash, password) is True


def test_verify_password_returns_false_for_incorrect_password():
    # Arrange
    password_hash = hash_password("Example123")

    # Act / Assert
    assert verify_password(password_hash, "WrongPassword1") is False


def test_hash_password_empty_password_does_not_crash():
    # Act
    password_hash = hash_password("")

    # Assert
    assert isinstance(password_hash, str)
    assert len(password_hash) > 0


def test_verify_password_empty_candidate_does_not_crash():
    # Arrange
    password_hash = hash_password("Example123")

    # Act / Assert
    assert verify_password(password_hash, "") is False


def test_verify_password_malformed_hash_does_not_crash():
    # Act / Assert: an invalid/malformed hash string returns False rather
    # than raising, so the helper never crashes on unexpected stored input.
    assert verify_password("not-a-real-hash", "Example123") is False


def test_hash_password_never_appears_literally_in_its_own_output():
    # Arrange
    password = "Example123"  # noqa: S105

    # Act
    password_hash = hash_password(password)

    # Assert: the plain password never appears verbatim inside the hash.
    assert password not in password_hash


def test_verify_password_failure_raises_no_exception_containing_password(caplog):
    # Arrange
    password = "Example123"  # noqa: S105
    password_hash = hash_password(password)

    # Act
    result = verify_password(password_hash, "WrongPassword1")

    # Assert: no exception was raised or logged, and nothing resembling the
    # submitted password was written to the log.
    assert result is False
    assert password not in caplog.text
    assert "WrongPassword1" not in caplog.text
