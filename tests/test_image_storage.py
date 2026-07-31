"""Contract tests for Stage 2.3 / 4.3 storage."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tagphy.db.connection import SQLiteConnection
from tagphy.tools.image_storage import ImageStorage


WORKDIR = "/virtual/Photo_Tagged"
SOURCE = "/virtual/inbox/vacation.HEIC"
APP_ROOT = Path("/virtual")


def _storage(workdir: str = WORKDIR) -> ImageStorage:
    return ImageStorage(workdir=workdir, db=MagicMock())


def _patch_app_root():
    return patch(
        "tagphy.tools.image_storage.app_root",
        return_value=APP_ROOT,
    )


class TestStoreImageDestination:
    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_moves_to_year_folder_when_year_present(
        self, _exists, mock_makedirs, mock_move, _app_root
    ):
        storage = _storage()
        metadata = {"year": "2024", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        expected = f"{WORKDIR}/2024/vacation.HEIC"
        mock_makedirs.assert_called_once_with(f"{WORKDIR}/2024", exist_ok=True)
        mock_move.assert_called_once_with(SOURCE, expected)
        assert result["destination_path"] == expected
        assert result["metadata"] == metadata

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_moves_to_unknown_when_year_missing(
        self, _exists, mock_makedirs, mock_move, _app_root
    ):
        storage = _storage()
        metadata = {"year": None, "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        expected = f"{WORKDIR}/Unknown/vacation.HEIC"
        mock_makedirs.assert_called_once_with(
            f"{WORKDIR}/Unknown", exist_ok=True
        )
        mock_move.assert_called_once_with(SOURCE, expected)
        assert result["destination_path"] == expected


class TestStoreImageYearTag:
    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_appends_numeric_year_tag_from_metadata(
        self, _exists, _makedirs, _move, _app_root
    ):
        storage = _storage()
        metadata = {"year": "2025", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        assert "2025" in result["tags"]
        assert "year" not in result["tags"]
        assert "cat" in result["tags"]
        assert "balcony" in result["tags"]

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_does_not_append_year_tag_when_year_missing(
        self, _exists, _makedirs, _move, _app_root
    ):
        storage = _storage()
        metadata = {"year": None, "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        assert "Unknown" not in result["tags"]
        assert not any(
            isinstance(t, str) and t.isdigit() and len(t) == 4
            for t in result["tags"]
        )

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_does_not_append_location_as_tag(
        self, _exists, _makedirs, _move, _app_root
    ):
        storage = _storage()
        metadata = {"year": "2025", "location": "Calgary, CA"}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        assert "Calgary, CA" not in result["tags"]

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_year_folder_comes_from_metadata_not_vision_tags(
        self, _exists, mock_makedirs, mock_move, _app_root
    ):
        """Vision must never invent the year folder; metadata year wins."""
        storage = _storage()
        metadata = {"year": None, "location": None}
        tags = {"main_tag": "2020", "secondary_tag": "cat"}

        result = storage.store_image(SOURCE, metadata, tags)

        mock_makedirs.assert_called_once_with(
            f"{WORKDIR}/Unknown", exist_ok=True
        )
        assert result["destination_path"].startswith(f"{WORKDIR}/Unknown/")
        mock_move.assert_called_once()


class TestStoreImageFailures:
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=True)
    def test_existing_destination_does_not_move(
        self, _exists, mock_makedirs, mock_move
    ):
        storage = _storage()
        metadata = {"year": "2024", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        mock_move.assert_not_called()
        mock_makedirs.assert_not_called()
        assert "warning" in result or "error" in result

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_move_failure_propagates(
        self, _exists, _makedirs, mock_move, _app_root
    ):
        mock_move.side_effect = OSError("disk full")
        storage = _storage()
        metadata = {"year": "2024", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        with pytest.raises(OSError, match="disk full"):
            storage.store_image(SOURCE, metadata, tags)


class TestStoreImageDbWrite:
    def test_stores_relative_file_path_and_image_tags(
        self, tmp_path, isolate_app_root, monkeypatch
    ):
        monkeypatch.setenv("TAGPHY_ROOT", str(isolate_app_root))
        workdir = isolate_app_root / "Photo_Tagged"
        workdir.mkdir()
        source = isolate_app_root / "inbox"
        source.mkdir()
        photo = source / "vacation.HEIC"
        photo.write_bytes(b"fake")

        db = SQLiteConnection(db_path=isolate_app_root / "tagphy.db")
        db.migrate()
        storage = ImageStorage(workdir=str(workdir), db=db)

        result = storage.store_image(
            str(photo),
            {"year": "2025", "location": "Calgary, CA"},
            {"main_tag": "ukulele", "secondary_tag": "instrument"},
        )

        assert result["destination_path"] == str(workdir / "2025" / "vacation.HEIC")
        assert (workdir / "2025" / "vacation.HEIC").is_file()
        assert not photo.exists()

        db.connect()
        row = db.conn.execute(
            "SELECT file_path, year, location FROM images"
        ).fetchone()
        assert row["file_path"] == "Photo_Tagged/2025/vacation.HEIC"
        assert not row["file_path"].startswith("/")
        assert row["year"] == "2025"
        assert row["location"] == "Calgary, CA"

        tag_names = {
            r["name"]
            for r in db.conn.execute("SELECT name FROM tags").fetchall()
        }
        assert tag_names == {"ukulele", "instrument", "2025"}
        assert "Calgary, CA" not in tag_names

        join_count = db.conn.execute(
            "SELECT COUNT(*) FROM image_tags"
        ).fetchone()[0]
        assert join_count == 3
        db.disconnect()

    def test_reuses_existing_tag_across_images(
        self, tmp_path, isolate_app_root, monkeypatch
    ):
        monkeypatch.setenv("TAGPHY_ROOT", str(isolate_app_root))
        workdir = isolate_app_root / "Photo_Tagged"
        workdir.mkdir()
        inbox = isolate_app_root / "inbox"
        inbox.mkdir()
        a = inbox / "a.HEIC"
        b = inbox / "b.HEIC"
        a.write_bytes(b"a")
        b.write_bytes(b"b")

        db = SQLiteConnection(db_path=isolate_app_root / "tagphy.db")
        db.migrate()
        storage = ImageStorage(workdir=str(workdir), db=db)

        storage.store_image(
            str(a),
            {"year": "2025", "location": ""},
            {"main_tag": "ukulele", "secondary_tag": "instrument"},
        )
        storage.store_image(
            str(b),
            {"year": "2024", "location": ""},
            {"main_tag": "ukulele", "secondary_tag": "music"},
        )

        db.connect()
        ukulele_rows = db.conn.execute(
            "SELECT id FROM tags WHERE name = ?", ("ukulele",)
        ).fetchall()
        assert len(ukulele_rows) == 1

        tag_count = db.conn.execute("SELECT COUNT(*) FROM tags").fetchone()[0]
        # ukulele, instrument, 2025, music, 2024
        assert tag_count == 5

        image_tag_count = db.conn.execute(
            "SELECT COUNT(*) FROM image_tags"
        ).fetchone()[0]
        assert image_tag_count == 6  # 3 per image
        db.disconnect()


class TestFirstOrCreate:
    def test_returns_same_id_on_conflict(self, tmp_path):
        db = SQLiteConnection(db_path=tmp_path / "t.db")
        db.migrate()
        db.connect()
        db.conn.execute("BEGIN")
        try:
            first = db.first_or_create(
                "tags",
                {"name": "cat", "source": "vision"},
                conflict_columns="name",
            )
            second = db.first_or_create(
                "tags",
                {"name": "cat", "source": "metadata"},
                conflict_columns="name",
            )
            assert first == second
            row = db.conn.execute(
                "SELECT source, COUNT(*) AS n FROM tags WHERE name = 'cat'"
            ).fetchone()
            assert row["n"] == 1
            # First writer wins for non-conflict columns.
            assert row["source"] == "vision"
            db.conn.execute("COMMIT")
        except Exception:
            db.conn.execute("ROLLBACK")
            raise
        finally:
            db.disconnect()
