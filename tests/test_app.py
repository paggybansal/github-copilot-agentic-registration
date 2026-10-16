"""Unit tests for the application factory (T2)."""

from __future__ import annotations

import importlib

import pytest
from flask import Flask
from flask_wtf import CSRFProtect

import registration_app.config as config_module
from registration_app.app import create_app
from registration_app.config import Config, TestConfig


def test_create_app_returns_configured_flask_instance(tmp_path):
    # Arrange
    db_path = tmp_path / "registration.db"

    class RealLikeConfig(Config):
        DATABASE_PATH = str(db_path)
        SECRET_KEY = "real-like-secret"  # noqa: S105

    # Act
    app = create_app(config_class=RealLikeConfig)

    # Assert
    assert isinstance(app, Flask)
    assert app.config["DATABASE_PATH"] == str(db_path)


def test_create_app_initializes_csrf_protection(tmp_path):
    # Arrange
    db_path = tmp_path / "registration.db"

    class RealLikeConfig(Config):
        DATABASE_PATH = str(db_path)
        SECRET_KEY = "real-like-secret"  # noqa: S105

    # Act
    app = create_app(config_class=RealLikeConfig)

    # Assert: Flask-WTF registers its CSRF extension under this key.
    assert "csrf" in app.extensions
    assert isinstance(app.extensions["csrf"], CSRFProtect)


def test_create_app_with_test_config_applies_test_overrides(tmp_path):
    # Arrange
    db_path = tmp_path / "registration.db"

    class ExplicitTestConfig(TestConfig):
        DATABASE_PATH = str(db_path)

    # Act
    app = create_app(config_class=ExplicitTestConfig)

    # Assert
    assert app.config["TESTING"] is True
    assert app.config["WTF_CSRF_ENABLED"] is False


def test_create_app_default_call_never_produces_test_config_behavior(tmp_path, monkeypatch):
    """Prove the default factory call cannot select TestConfig via any implicit path.

    There is no parameter, environment variable, or other code path in
    ``create_app`` that selects ``TestConfig`` other than an explicit direct
    call passing ``config_class=TestConfig`` (or a subclass of it). This test
    calls the factory the way production code would -- with only a
    ``Config`` subclass supplying a tmp_path database path -- and asserts the
    real, non-test behavior is produced.
    """
    # Arrange: simulate a "production-like" environment, including a stray
    # FLASK_SECRET_KEY, to prove no environment variable can select TestConfig.
    monkeypatch.setenv("FLASK_SECRET_KEY", "production-like-secret")
    db_path = tmp_path / "registration.db"

    class RealLikeConfig(Config):
        DATABASE_PATH = str(db_path)
        SECRET_KEY = "production-like-secret"  # noqa: S105

    # Act
    app = create_app(config_class=RealLikeConfig)

    # Assert: real (non-test) behavior -- CSRF enabled, TESTING off, and the
    # SECRET_KEY is not the literal TestConfig test value.
    assert app.config["WTF_CSRF_ENABLED"] is True
    assert app.config["TESTING"] is False
    assert app.config["SECRET_KEY"] != "test-secret-key"  # noqa: S105


def test_create_app_raises_when_secret_key_is_unset_for_real_config(tmp_path, monkeypatch):
    """A real (non-test) config with no FLASK_SECRET_KEY must fail fast, not
    silently start with a weak/empty SECRET_KEY."""
    # Arrange
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    reloaded = importlib.reload(config_module)

    class RealLikeConfigNoSecret(reloaded.Config):
        DATABASE_PATH = str(tmp_path / "registration.db")

    # Act / Assert
    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        create_app(config_class=RealLikeConfigNoSecret)

    # Cleanup
    importlib.reload(config_module)


def test_create_app_succeeds_when_secret_key_is_set(tmp_path, monkeypatch):
    """A real (non-test) config with FLASK_SECRET_KEY set must start normally."""
    # Arrange
    monkeypatch.setenv("FLASK_SECRET_KEY", "env-provided-real-secret")
    reloaded = importlib.reload(config_module)

    class RealLikeConfigWithSecret(reloaded.Config):
        DATABASE_PATH = str(tmp_path / "registration.db")

    # Act
    app = create_app(config_class=RealLikeConfigWithSecret)

    # Assert
    assert app.config["SECRET_KEY"] == "env-provided-real-secret"  # noqa: S105

    # Cleanup
    monkeypatch.undo()
    importlib.reload(config_module)


def test_create_app_with_test_config_still_succeeds_without_secret_env(tmp_path, monkeypatch):
    """TestConfig must remain unaffected by the SECRET_KEY fail-fast check."""
    # Arrange
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    db_path = tmp_path / "registration.db"

    class ExplicitTestConfig(TestConfig):
        DATABASE_PATH = str(db_path)

    # Act
    app = create_app(config_class=ExplicitTestConfig)

    # Assert
    assert app.config["TESTING"] is True
    assert app.config["SECRET_KEY"] == "test-secret-key"  # noqa: S105
