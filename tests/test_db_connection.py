"""Pure / no-IO checks for SQLiteConnection construction helpers.

Live SQLite (connect, migrate, execute) is intentionally not unit-tested here.
Callers (pipeline, storage) assert against MagicMock db methods instead.
"""

from __future__ import annotations

import pytest

from tagphy.db.connection import MIGRATIONS_DIR, SQLiteConnection


class TestSplitStatements:
    def test_splits_complete_statements(self):
        sql = "CREATE TABLE a (id INTEGER);\nCREATE TABLE b (id INTEGER);\n"
        stmts = SQLiteConnection._split_statements(sql)
        assert len(stmts) == 2
        assert stmts[0].startswith("CREATE TABLE a")
        assert stmts[1].startswith("CREATE TABLE b")

    def test_incomplete_statement_raises(self):
        with pytest.raises(ValueError, match="Incomplete SQL"):
            SQLiteConnection._split_statements("CREATE TABLE a (id INTEGER")


class TestPathConstruction:
    def test_explicit_db_path(self, tmp_path):
        path = tmp_path / "custom.db"
        db = SQLiteConnection(db_path=path)
        assert db.db_path == path
        assert db.conn is None

    def test_default_db_path_uses_tagphy_root(self, isolate_app_root):
        db = SQLiteConnection()
        assert db.db_path == isolate_app_root / "tagphy.db"
        assert db.conn is None

    def test_default_migrations_dir_is_packaged_dir(self, isolate_app_root):
        db = SQLiteConnection()
        assert db.migrations_dir == MIGRATIONS_DIR
        assert db.conn is None
