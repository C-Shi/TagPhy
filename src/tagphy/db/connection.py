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
        """Open a SQLite connection and apply connection PRAGMAs."""
        self.conn = sqlite3.connect(self.db_path, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = DELETE")
        self.cursor = self.conn.cursor()

    def _ensure_connection(self) -> bool:
        """Open the connection if needed.

        Returns:
            True if this call opened the connection (caller must disconnect).
            False if a connection was already open (caller must leave it open).
        """
        if self.conn is None:
            self.connect()
            return True
        return False

    def migrate(self) -> list[str]:
        """Apply pending migrations and return their filenames."""
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
        """Close the cursor and connection, if open."""
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
        """Run ``func`` inside BEGIN/COMMIT (ROLLBACK on error).

        Always disconnects when finished. Safe to call helpers like
        ``insert`` / ``first_or_create`` inside ``func`` (they will reuse
        this connection and not close it). Do not nest ``transaction``
        calls — the inner one would disconnect before the outer finishes.

        Args:
            func: Zero-arg callable that performs DB work.

        Returns:
            Whatever ``func`` returns.
        """
        self._ensure_connection()
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

    def select(
        self, table: str, columns: list[str], where: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Select rows from a table with conditions to precisely query by column.

        Args:
            table: Table name.
            columns: List of column names.
            where: Dictionary of column names and values.
        """
        opened = self._ensure_connection()
        assert self.cursor is not None

        try:
            query = f"SELECT {', '.join(columns)} FROM {table} WHERE {' AND '.join(f'{k} = ?' for k in where.keys())}"
            self.cursor.execute(query, tuple(where.values()))
            return self.cursor.fetchall()
        finally:
            if opened:
                self.disconnect()

    def insert(self, table: str, data: dict[str, Any]) -> int:
        """Insert one row.

        Opens a connection if needed and closes it only when this call
        opened it (so it can run inside ``transaction``).

        Args:
            table: Table name.
            data: Column → value map for the INSERT.

        Returns:
            ``lastrowid`` of the inserted row.
        """
        opened = self._ensure_connection()
        assert self.cursor is not None

        try:
            query = (
                f"INSERT INTO {table} ({', '.join(data.keys())}) "
                f"VALUES ({', '.join(['?' for _ in data.keys()])})"
            )
            self.cursor.execute(query, tuple(data.values()))
            return self.cursor.lastrowid
        finally:
            if opened:
                self.disconnect()

    def delete(self, table: str, data: dict[str, Any]) -> None:
        """Delete rows matching all key/value pairs in ``data`` (AND).

        Prefer identifying rows by primary key (e.g. ``{"id": image_id}``).

        Opens/closes the connection the same way as ``insert``.
        """
        opened = self._ensure_connection()
        assert self.cursor is not None

        try:
            query = f"DELETE FROM {table} WHERE {' AND '.join(f'{k} = ?' for k in data.keys())}"
            self.cursor.execute(query, tuple(data.values()))
        finally:
            if opened:
                self.disconnect()

    def query(
        self, query: str, params: tuple[Any, ...] | dict[str, Any] = []
    ) -> list[dict[str, Any]]:
        opened = self._ensure_connection()
        assert self.cursor is not None

        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        finally:
            if opened:
                self.disconnect()

    def first_or_create(
        self,
        table: str,
        data: dict[str, Any],
        *,
        conflict_columns: str | list[str],
        id_column: str = "id",
    ) -> int:
        """Insert a row, or return the existing id on unique conflict.

        ``conflict_columns`` must be keys in ``data`` and match a UNIQUE / PK
        target. On conflict, existing non-key columns are left unchanged
        (first writer wins).

        Opens/closes the connection the same way as ``insert``.
        """
        opened = self._ensure_connection()
        assert self.cursor is not None

        try:
            cols = list(data.keys())
            conflict = (
                [conflict_columns]
                if isinstance(conflict_columns, str)
                else list(conflict_columns)
            )
            missing = [c for c in conflict if c not in data]
            if missing:
                raise ValueError(f"conflict_columns not present in data: {missing}")

            placeholders = ", ".join("?" for _ in cols)
            conflict_list = ", ".join(conflict)
            self.cursor.execute(
                f"INSERT INTO {table} ({', '.join(cols)}) "
                f"VALUES ({placeholders}) "
                f"ON CONFLICT({conflict_list}) DO NOTHING",
                tuple(data[c] for c in cols),
            )
            where = " AND ".join(f"{c} = ?" for c in conflict)
            row = self.cursor.execute(
                f"SELECT {id_column} FROM {table} WHERE {where}",
                tuple(data[c] for c in conflict),
            ).fetchone()
            if row is None:
                raise RuntimeError(
                    f"first_or_create failed to find row in {table} "
                    f"after insert/conflict on {conflict}"
                )
            return int(row[id_column])
        finally:
            if opened:
                self.disconnect()

    def create_or_update(
        self,
        table: str,
        data: dict[str, Any],
        conflict_columns: str | list[str],
        operations: dict[str, str],
    ) -> int:
        """Insert a row, or update it on unique conflict (upsert).

        ``data`` is the INSERT payload. ``conflict_columns`` must match a
        UNIQUE / PK target (string or list).

        ``operations`` maps column → conflict-only action:
            - ``INCREMENT`` / ``DECREMENT``: mutate the existing row value
            - ``IGNORE``: leave the existing value unchanged
            - ``NOW``: set ``CURRENT_TIMESTAMP``

        Columns present in ``data`` but omitted from ``operations`` are
        replaced with the new insert values (``excluded.col``). Columns may
        appear only in ``operations`` (e.g. counters/timestamps that use
        table defaults on first insert).

        Opens/closes the connection the same way as ``insert``.

        Returns:
            SQLite ``lastrowid`` after the statement (reliable for inserts;
            do not rely on it to identify an updated row).
        """
        opened = self._ensure_connection()
        assert self.cursor is not None

        if isinstance(conflict_columns, str):
            conflict_columns = [conflict_columns]

        try:
            on_conflict_columns = []
            for column, operation in operations.items():
                if operation == "INCREMENT":
                    on_conflict_columns.append(f"{column} = {column} + 1")
                elif operation == "DECREMENT":
                    on_conflict_columns.append(f"{column} = {column} - 1")
                elif operation == "IGNORE":
                    pass
                elif operation == "NOW":
                    on_conflict_columns.append(f"{column} = CURRENT_TIMESTAMP")
                else:
                    raise ValueError(f"Invalid operation: {operation}")

            # Columns in data with no explicit op: overwrite from the insert row.
            for column in data.keys():
                if column not in operations.keys():
                    on_conflict_columns.append(f"{column} = excluded.{column}")

            query = (
                f"INSERT INTO {table} ({', '.join(data.keys())}) "
                f"VALUES ({', '.join(['?' for _ in data.keys()])}) "
                f"ON CONFLICT({', '.join(conflict_columns)}) DO UPDATE SET {', '.join(on_conflict_columns)}"
            )

            self.cursor.execute(query, tuple(data.values()))
            return self.cursor.lastrowid
        finally:
            if opened:
                self.disconnect()
