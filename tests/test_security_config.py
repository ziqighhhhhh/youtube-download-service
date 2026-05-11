import importlib

import pytest


def reload_config(monkeypatch, **env):
    for key in (
        "DEBUG",
        "SECRET_KEY",
        "ADMIN_PASSWORD",
        "VIDEOS_PER_CHARGE",
        "MAX_CONCURRENT_TASKS",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    import config

    return importlib.reload(config)


def test_production_requires_strong_secret_key(monkeypatch):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        reload_config(monkeypatch, DEBUG="false", SECRET_KEY="dev-secret-key-change-me")


def test_production_requires_non_default_admin_password(monkeypatch):
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        reload_config(
            monkeypatch,
            DEBUG="false",
            SECRET_KEY="a-secure-secret-key-with-enough-length",
            ADMIN_PASSWORD="admin123",
        )


def test_positive_integer_config_validation(monkeypatch):
    with pytest.raises(RuntimeError, match="VIDEOS_PER_CHARGE"):
        reload_config(monkeypatch, VIDEOS_PER_CHARGE="0")
