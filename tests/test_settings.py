"""SettingsStore: SQLite config/value map (uses a real temp DB)."""

from __future__ import annotations

import pytest

from tagphy.db.connection import SQLiteConnection
from tagphy.web.utils.settings import SettingsStore


@pytest.fixture
def store(tmp_path):
    db = SQLiteConnection(db_path=tmp_path / "tagphy.db")
    db.migrate()
    return SettingsStore(db)


class TestSettingsStore:
    def test_migrate_seeds_privacy_pre_check_true(self, store):
        data = store.load()
        assert data["privacy_pre_check"] == "true"
        assert store.privacy_pre_check_enabled() is True

    def test_set_overwrites_and_reload_matches(self, store):
        store.set("privacy_pre_check", "false")
        assert store.get("privacy_pre_check") == "false"
        assert store.load()["privacy_pre_check"] == "false"
        assert store.privacy_pre_check_enabled() is False

    def test_load_fills_missing_default_key(self, store):
        store.db.delete("settings", {"config": "privacy_pre_check"})
        data = store.load()
        assert data["privacy_pre_check"] == "true"

    def test_privacy_pre_check_enabled_fail_closed(self, store):
        store.set("privacy_pre_check", "yes")
        assert store.privacy_pre_check_enabled() is True
        store.set("privacy_pre_check", "false")
        assert store.privacy_pre_check_enabled() is False

    def test_set_rejects_empty_value(self, store):
        with pytest.raises(ValueError, match="non-empty"):
            store.set("privacy_pre_check", "")

    def test_set_allows_extra_keys(self, store):
        data = store.set("custom_flag", "on")
        assert data["custom_flag"] == "on"
        assert data["privacy_pre_check"] == "true"
