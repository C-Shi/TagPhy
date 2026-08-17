"""Durable app settings in SQLite (config PK, value TEXT)."""

from __future__ import annotations

from typing import Any

from tagphy.db.connection import SQLiteConnection

DEFAULTS = {"privacy_pre_check": "true"}


def _as_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


class SettingsStore:
    def __init__(self, db: SQLiteConnection):
        self.db = db

    def _ensure_defaults(self) -> None:
        for config, value in DEFAULTS.items():
            self.db.query(
                "INSERT INTO settings (config, value) VALUES (?, ?) "
                "ON CONFLICT(config) DO NOTHING",
                (config, value),
            )

    def load(self) -> dict[str, str]:
        """Return all settings. Seed any missing DEFAULTS rows, then persist."""
        self._ensure_defaults()
        rows = self.db.query("SELECT config, value FROM settings")
        return {row["config"]: row["value"] for row in rows}

    def get(self, config: str) -> str:
        self._ensure_defaults()
        rows = self.db.select(
            table="settings",
            columns=["value"],
            where={"config": config},
        )
        if not rows:
            raise KeyError(config)
        return rows[0]["value"]

    def set(self, config: str, value: Any) -> dict[str, str]:
        if not config or not str(config).strip():
            raise ValueError("config must be a non-empty string")
        stored = _as_value(value)
        if stored == "":
            raise ValueError("value must be a non-empty string")
        self.db.create_or_update(
            table="settings",
            data={"config": config, "value": stored},
            conflict_columns="config",
            operations={},
        )
        return self.load()

    def privacy_pre_check_enabled(self) -> bool:
        """True unless the stored value is exactly 'false' (fail closed)."""
        try:
            return self.get("privacy_pre_check") != "false"
        except KeyError:
            return True
