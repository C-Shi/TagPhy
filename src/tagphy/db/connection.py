from __future__ import annotations

import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tagphy import app_root

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
MIGRATION_RE = re.compile(r"^\d{3}_[a-z0-9_]+\.sql$")

_SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
)
"""


class SQLiteConnection:
    def __init__(
        self,
        db_path: str | Path | None = None,
        migrations_dir: str | Path | None = None,
    ):
        self.db_path = Path(db_path) if db_path else app_root() / "tagphy.db"
        self.migrations_dir = Path(migrations_dir) if migrations_dir else MIGRATIONS_DIR
        self.conn: sqlite3.Connection | None = None
        self.cursor: sqlite3.Cursor | None = None

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.db_path, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = DELETE")
        self.cursor = self.conn.cursor()

    def migrate(self) -> list[str]:
        if self.conn is None:
            self.connect()
        logger.info("Migrating database...")
        self._ensure_migrations_table()
        applied = self._applied_versions()
        discovered = self._discover_migrations()
        self._warn_orphan_versions(applied, discovered)
        pending = [p for p in discovered if p.name not in applied]
        for path in pending:
            self._apply_migration(path)

        self.disconnect()
        logger.info("Database migrated successfully")
        return [p.name for p in pending]

    def disconnect(self) -> None:
        if self.cursor is not None:
            self.cursor.close()
        if self.conn is not None:
            self.conn.close()
        self.cursor = None
        self.conn = None

    def _ensure_migrations_table(self) -> None:
        assert self.conn is not None
        self.conn.execute(_SCHEMA_MIGRATIONS_DDL)

    def _applied_versions(self) -> set[str]:
        assert self.conn is not None
        rows = self.conn.execute("SELECT version FROM schema_migrations").fetchall()
        return {row[0] for row in rows}

    def _discover_migrations(self) -> list[Path]:
        if not self.migrations_dir.is_dir():
            logger.warning("Migrations directory missing: %s", self.migrations_dir)
            return []

        discovered: list[Path] = []
        for path in sorted(self.migrations_dir.glob("*.sql")):
            if MIGRATION_RE.match(path.name):
                discovered.append(path)
            else:
                logger.warning(
                    "Ignoring migration file with unexpected name: %s",
                    path.name,
                )
        return discovered

    def _warn_orphan_versions(self, applied: set[str], discovered: list[Path]) -> None:
        discovered_names = {p.name for p in discovered}
        for version in sorted(applied - discovered_names):
            logger.warning(
                "Applied migration has no matching file: %s",
                version,
            )

    @staticmethod
    def _split_statements(sql: str) -> list[str]:
        statements: list[str] = []
        buf = ""
        for line in sql.splitlines(keepends=True):
            buf += line
            if sqlite3.complete_statement(buf):
                stmt = buf.strip()
                if stmt:
                    statements.append(stmt)
                buf = ""
        leftover = buf.strip()
        if leftover:
            raise ValueError(
                f"Incomplete SQL statement at end of migration: {leftover[:80]!r}"
            )
        return statements

    def _apply_migration(self, path: Path) -> None:
        assert self.conn is not None
        statements = self._split_statements(path.read_text(encoding="utf-8"))
        self.conn.execute("BEGIN")
        try:
            for stmt in statements:
                self.conn.execute(stmt)
            self.conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (
                    path.name,
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                ),
            )
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            logger.error("Migration failed, rolled back: %s", path.name)
            raise

    def transaction(self, func: Callable[[], Any]) -> Any:
        self.connect()
        self.conn.execute("BEGIN")
        try:
            result = func()
            self.conn.execute("COMMIT")
            return result
        except Exception:
            self.conn.execute("ROLLBACK")
            raise
        finally:
            self.disconnect()

    def insert(self, table: str, data: dict[str, Any]) -> int:
        query = f"INSERT INTO {table} ({', '.join(data.keys())}) VALUES ({', '.join(['?' for _ in data.keys()])})"
        self.cursor.execute(query, tuple(data.values()))
        return self.cursor.lastrowid
