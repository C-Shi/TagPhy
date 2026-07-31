"""Shared fixtures for TagPhy contract tests."""

import pytest


@pytest.fixture(autouse=True)
def isolate_app_root(tmp_path, monkeypatch):
    """Point app_root() at a throwaway directory for every test.

    Without this, SQLiteConnection and ImageProcessingPipeline fall back to the
    real repository root, so a test that forgets to pass an explicit path would
    create tagphy.db or Photo_Tagged/ in the working tree.
    """
    sandbox = tmp_path / "app_root"
    sandbox.mkdir(exist_ok=True)
    monkeypatch.setenv("TAGPHY_ROOT", str(sandbox))
    return sandbox
