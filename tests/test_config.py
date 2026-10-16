"""Unit tests for the application configuration module (T1)."""

from __future__ import annotations

import importlib

import registration_app.config as config_module
from registration_app.config import Config, TestConfig


def test_config_reads_secret_key_from_environment(monkeypatch):
    # Arrange
    monkeypatch.setenv("FLASK_SECRET_KEY", "env-secret-value")

    # Act
    reloaded = importlib.reload(config_module)

    # Assert
    assert reloaded.Config.SECRET_KEY == "env-secret-value"  # noqa: S105

    # Cleanup: restore the module to its unset-environment state for later tests.
    monkeypatch.undo()
    importlib.reload(config_module)


def test_config_reads_database_path_from_environment(monkeypatch):
    # Arrange
    monkeypatch.setenv("REGISTRATION_DATABASE", "instance/custom.db")

    # Act
    reloaded = importlib.reload(config_module)

    # Assert
    assert reloaded.Config.DATABASE_PATH == "instance/custom.db"

    # Cleanup
    monkeypatch.undo()
    importlib.reload(config_module)


def test_config_has_safe_defaults_when_environment_variables_are_absent(monkeypatch):
    # Arrange
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.delenv("REGISTRATION_DATABASE", raising=False)

    # Act
    reloaded = importlib.reload(config_module)

    # Assert
    assert reloaded.Config.SECRET_KEY == ""
    assert reloaded.Config.DATABASE_PATH == "instance/registration.db"


def test_config_enforces_debug_false():
    # Assert
    assert Config.DEBUG is False


def test_config_enables_csrf_by_default():
    # Assert
    assert Config.WTF_CSRF_ENABLED is True


def test_config_sets_max_content_length():
    # Assert
    assert Config.MAX_CONTENT_LENGTH == 16 * 1024


def test_config_testing_flag_is_false_by_default():
    # Assert
    assert Config.TESTING is False


def test_test_config_enables_testing_flag():
    # Assert
    assert TestConfig.TESTING is True


def test_test_config_disables_csrf_by_default():
    # Assert
    assert TestConfig.WTF_CSRF_ENABLED is False


def test_test_config_inherits_debug_false():
    # Assert
    assert TestConfig.DEBUG is False


def test_test_config_has_deterministic_secret_key():
    # Assert
    assert TestConfig.SECRET_KEY == "test-secret-key"  # noqa: S105
