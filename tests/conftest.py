"""Shared fixtures for TagPhy contract tests."""

import pytest


@pytest.fixture(autouse=True)
def isolate_app_root(tmp_path, monkeypatch):
    """Point app_root() at a throwaway directory for every test.

    Safety net only: unit tests must not open real SQLite. If something
    accidentally constructs SQLiteConnection(), this keeps writes out of the
    repository working tree. Prefer MagicMock for all db interactions.
    """
    sandbox = tmp_path / "app_root"
    sandbox.mkdir(exist_ok=True)
    monkeypatch.setenv("TAGPHY_ROOT", str(sandbox))
    return sandbox
