"""Contract tests for Stage 2.3 / 4.3 / 4.4 storage (MagicMock db only)."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from tagphy.tools.image_storage import ImageStorage


WORKDIR = "/virtual/Photo_Tagged"
SOURCE = "/virtual/inbox/vacation.HEIC"
APP_ROOT = Path("/virtual")


def _storage(workdir: str = WORKDIR, db: MagicMock | None = None) -> ImageStorage:
    return ImageStorage(workdir=workdir, db=db if db is not None else MagicMock())


def _patch_app_root():
    return patch(
        "tagphy.tools.image_storage.app_root",
        return_value=APP_ROOT,
    )


def _run_transaction_callback(func):
    """MagicMock transaction side_effect: execute the callback like a real tx."""
    return func()


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
    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_writes_relative_path_tags_and_image_tags_via_db_mock(
        self, _exists, _makedirs, _move, _app_root
    ):
        db = MagicMock()
        db.transaction.side_effect = _run_transaction_callback
        db.insert.side_effect = [101, None, None, None]  # image id, then joins
        db.first_or_create.side_effect = [1, 2, 3]

        storage = _storage(db=db)
        metadata = {"year": "2025", "location": "Calgary, CA"}
        tags = {"main_tag": "ukulele", "secondary_tag": "instrument"}

        storage.store_image(SOURCE, metadata, tags)

        db.transaction.assert_called_once()
        image_insert = db.insert.call_args_list[0]
        assert image_insert.args[0] == "images"
        assert image_insert.args[1]["file_path"] == "Photo_Tagged/2025/vacation.HEIC"
        assert not image_insert.args[1]["file_path"].startswith("/")
        assert image_insert.args[1]["year"] == "2025"
        assert image_insert.args[1]["location"] == "Calgary, CA"

        tag_names = [
            c.args[1]["name"] for c in db.first_or_create.call_args_list
        ]
        assert tag_names == ["ukulele", "instrument", "2025"]
        assert all(
            c.kwargs.get("conflict_columns") == "name"
            or c.args[0] == "tags"
            for c in db.first_or_create.call_args_list
        )

        join_calls = [
            c for c in db.insert.call_args_list if c.args[0] == "image_tags"
        ]
        assert len(join_calls) == 3
        assert {c.args[1]["image_id"] for c in join_calls} == {101}

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_reuses_first_or_create_for_same_tag_across_images(
        self, _exists, _makedirs, _move, _app_root
    ):
        db = MagicMock()
        db.transaction.side_effect = _run_transaction_callback
        db.insert.side_effect = [
            1,
            None,
            None,
            None,
            2,
            None,
            None,
            None,
        ]
        db.first_or_create.side_effect = [10, 11, 12, 10, 13, 14]

        storage = _storage(db=db)
        storage.store_image(
            "/virtual/inbox/a.HEIC",
            {"year": "2025", "location": ""},
            {"main_tag": "ukulele", "secondary_tag": "instrument"},
        )
        storage.store_image(
            "/virtual/inbox/b.HEIC",
            {"year": "2024", "location": ""},
            {"main_tag": "ukulele", "secondary_tag": "music"},
        )

        ukulele_calls = [
            c
            for c in db.first_or_create.call_args_list
            if c.args[1]["name"] == "ukulele"
        ]
        assert len(ukulele_calls) == 2
        assert db.transaction.call_count == 2


class TestCompensatingDelete:
    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_deletes_image_row_when_move_fails_after_db_write(
        self, _exists, _makedirs, mock_move, _app_root
    ):
        db = MagicMock()
        db.transaction.return_value = 42
        mock_move.side_effect = OSError("disk full")
        storage = _storage(db=db)

        with pytest.raises(OSError, match="disk full"):
            storage.store_image(
                SOURCE,
                {"year": "2024", "location": None},
                {"main_tag": "cat", "secondary_tag": "balcony"},
            )

        db.delete.assert_called_once_with("images", {"id": 42})

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_no_delete_when_db_write_fails(
        self, _exists, _makedirs, mock_move, _app_root
    ):
        db = MagicMock()
        db.transaction.side_effect = RuntimeError("db down")
        storage = _storage(db=db)

        with pytest.raises(RuntimeError, match="db down"):
            storage.store_image(
                SOURCE,
                {"year": "2024", "location": None},
                {"main_tag": "cat", "secondary_tag": "balcony"},
            )

        db.delete.assert_not_called()
        mock_move.assert_not_called()
