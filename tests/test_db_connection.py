"""Contract tests for SQLiteConnection and the migration runner."""

from __future__ import annotations

import logging
import shutil
import sqlite3
from pathlib import Path

import pytest

from tagphy.db.connection import MIGRATIONS_DIR, SQLiteConnection

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "schema_migrations",
    "images",
    "tags",
    "image_tags",
    "tag_edges",
    "failure_log",
}


def _conn(tmp_path: Path, migrations_dir: Path | None = None) -> SQLiteConnection:
    return SQLiteConnection(
        db_path=tmp_path / "tagphy.db",
        migrations_dir=migrations_dir or MIGRATIONS_DIR,
    )


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


class TestFreshMigrate:
    def test_creates_all_tables_and_returns_version(self, tmp_path):
        db = _conn(tmp_path)
        applied = db.migrate()

        assert applied == ["001_create_table.sql"]
        assert EXPECTED_TABLES.issubset(_table_names(db.conn))
        db.disconnect()

    def test_records_applied_at(self, tmp_path):
        db = _conn(tmp_path)
        db.migrate()

        row = db.conn.execute(
            "SELECT version, applied_at FROM schema_migrations"
        ).fetchone()
        assert row["version"] == "001_create_table.sql"
        assert row["applied_at"]
        db.disconnect()

    def test_second_call_is_noop(self, tmp_path):
        db = _conn(tmp_path)
        first = db.migrate()
        second = db.migrate()

        assert first == ["001_create_table.sql"]
        assert second == []
        count = db.conn.execute(
            "SELECT COUNT(*) FROM schema_migrations"
        ).fetchone()[0]
        assert count == 1
        db.disconnect()


class TestOrderingAndPartialApply:
    def test_applies_pending_file_in_order(self, tmp_path):
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        shutil.copy(MIGRATIONS_DIR / "001_create_table.sql", migrations / "001_create_table.sql")
        (migrations / "002_add_note.sql").write_text(
            "ALTER TABLE images ADD COLUMN note TEXT;\n",
            encoding="utf-8",
        )

        db = _conn(tmp_path, migrations_dir=migrations)
        first = db.migrate()
        assert first == ["001_create_table.sql", "002_add_note.sql"]

        # Simulate a database that already applied 001 only.
        db.disconnect()
        fresh = tmp_path / "partial.db"
        partial = SQLiteConnection(db_path=fresh, migrations_dir=migrations)
        partial.connect()
        partial._ensure_migrations_table()
        partial.conn.execute(
            "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
            ("001_create_table.sql", "2026-01-01T00:00:00+00:00"),
        )
        # Apply only the first file's DDL so 002 has a table to alter.
        for stmt in SQLiteConnection._split_statements(
            (migrations / "001_create_table.sql").read_text(encoding="utf-8")
        ):
            partial.conn.execute(stmt)

        pending = partial.migrate()
        assert pending == ["002_add_note.sql"]
        cols = {
            row[1]
            for row in partial.conn.execute("PRAGMA table_info(images)").fetchall()
        }
        assert "note" in cols
        versions = {
            row[0]
            for row in partial.conn.execute(
                "SELECT version FROM schema_migrations"
            ).fetchall()
        }
        assert versions == {"001_create_table.sql", "002_add_note.sql"}
        partial.disconnect()


class TestRollback:
    def test_failed_migration_rolls_back(self, tmp_path):
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        (migrations / "001_bad.sql").write_text(
            "CREATE TABLE keep_me (id INTEGER);\n"
            "CREATE TABLE ((((invalid;\n",
            encoding="utf-8",
        )

        db = _conn(tmp_path, migrations_dir=migrations)
        with pytest.raises(sqlite3.Error):
            db.migrate()

        assert "keep_me" not in _table_names(db.conn)
        versions = db.conn.execute(
            "SELECT version FROM schema_migrations"
        ).fetchall()
        assert versions == []
        db.disconnect()


class TestDiscoveryWarnings:
    def test_ignores_badly_named_files(self, tmp_path, caplog):
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        shutil.copy(MIGRATIONS_DIR / "001_create_table.sql", migrations / "001_create_table.sql")
        (migrations / "notes.sql").write_text(
            "CREATE TABLE should_not_exist (id INTEGER);\n",
            encoding="utf-8",
        )

        db = _conn(tmp_path, migrations_dir=migrations)
        with caplog.at_level(logging.WARNING, logger="tagphy.db.connection"):
            applied = db.migrate()

        assert applied == ["001_create_table.sql"]
        assert "should_not_exist" not in _table_names(db.conn)
        assert any("notes.sql" in r.message for r in caplog.records)
        db.disconnect()


class TestPragmasAndConstraints:
    def test_foreign_keys_enabled(self, tmp_path):
        db = _conn(tmp_path)
        db.connect()
        assert db.conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        db.disconnect()

    def test_year_nullable_and_file_path_unique(self, tmp_path):
        db = _conn(tmp_path)
        db.migrate()

        db.conn.execute(
            "INSERT INTO images (file_path, file_name, year, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Photo_Tagged/Unknown/a.jpg", "a.jpg", None, "t", "t"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.conn.execute(
                "INSERT INTO images (file_path, file_name, year, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("Photo_Tagged/Unknown/a.jpg", "a.jpg", None, "t", "t"),
            )
        db.disconnect()

    def test_delete_image_cascades_image_tags(self, tmp_path):
        db = _conn(tmp_path)
        db.migrate()

        db.conn.execute(
            "INSERT INTO images (file_path, file_name, year, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Photo_Tagged/2024/a.jpg", "a.jpg", "2024", "t", "t"),
        )
        db.conn.execute(
            "INSERT INTO tags (name, source, created_at) VALUES (?, ?, ?)",
            ("cat", "vision", "t"),
        )
        db.conn.execute(
            "INSERT INTO image_tags (image_id, tag_id, created_at) VALUES (?, ?, ?)",
            (1, 1, "t"),
        )
        db.conn.execute("DELETE FROM images WHERE id = 1")

        count = db.conn.execute("SELECT COUNT(*) FROM image_tags").fetchone()[0]
        assert count == 0
        db.disconnect()

    def test_self_edge_rejected(self, tmp_path):
        db = _conn(tmp_path)
        db.migrate()
        db.conn.execute(
            "INSERT INTO tags (name, source, created_at) VALUES (?, ?, ?)",
            ("cat", "vision", "t"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db.conn.execute(
                "INSERT INTO tag_edges (parent_id, child_id) VALUES (?, ?)",
                (1, 1),
            )
        db.disconnect()

    def test_descendant_cte_chain_and_diamond(self, tmp_path):
        db = _conn(tmp_path)
        db.migrate()

        for name in ("animal", "pet", "mammal", "cat", "Meowy"):
            db.conn.execute(
                "INSERT INTO tags (name, source, created_at) VALUES (?, ?, ?)",
                (name, "vision", "t"),
            )
        # ids: 1 animal, 2 pet, 3 mammal, 4 cat, 5 Meowy
        edges = [
            (1, 2),  # animal -> pet
            (1, 3),  # animal -> mammal
            (2, 4),  # pet -> cat
            (3, 4),  # mammal -> cat  (diamond)
            (4, 5),  # cat -> Meowy
        ]
        for parent_id, child_id in edges:
            db.conn.execute(
                "INSERT INTO tag_edges (parent_id, child_id) VALUES (?, ?)",
                (parent_id, child_id),
            )

        db.conn.execute(
            "INSERT INTO images (file_path, file_name, year, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Photo_Tagged/2024/meowy.jpg", "meowy.jpg", "2024", "t", "t"),
        )
        db.conn.execute(
            "INSERT INTO image_tags (image_id, tag_id, created_at) VALUES (?, ?, ?)",
            (1, 5, "t"),
        )

        rows = db.conn.execute(
            """
            WITH RECURSIVE descendants(id) AS (
                SELECT ?
                UNION
                SELECT e.child_id
                FROM tag_edges e
                JOIN descendants d ON e.parent_id = d.id
            )
            SELECT DISTINCT i.file_path
            FROM images i
            JOIN image_tags it ON it.image_id = i.id
            WHERE it.tag_id IN (SELECT id FROM descendants)
            """,
            (1,),  # animal
        ).fetchall()

        assert [row[0] for row in rows] == ["Photo_Tagged/2024/meowy.jpg"]

        # Diamond must not duplicate descendant ids.
        ids = [
            row[0]
            for row in db.conn.execute(
                """
                WITH RECURSIVE descendants(id) AS (
                    SELECT ?
                    UNION
                    SELECT e.child_id
                    FROM tag_edges e
                    JOIN descendants d ON e.parent_id = d.id
                )
                SELECT id FROM descendants ORDER BY id
                """,
                (1,),
            ).fetchall()
        ]
        assert ids == [1, 2, 3, 4, 5]
        db.disconnect()


class TestAppRootDefault:
    def test_default_db_path_uses_tagphy_root(self, isolate_app_root):
        db = SQLiteConnection()
        assert db.db_path == isolate_app_root / "tagphy.db"

    def test_default_migrations_dir_is_packaged_dir(self, isolate_app_root):
        db = SQLiteConnection()
        assert db.migrations_dir == MIGRATIONS_DIR

    def test_migrate_writes_only_under_sandboxed_root(self, isolate_app_root):
        db = SQLiteConnection()
        db.migrate()
        db.disconnect()

        assert (isolate_app_root / "tagphy.db").is_file()
        assert not (REPO_ROOT / "tagphy.db").exists()
