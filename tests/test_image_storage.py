"""Contract tests for Stage 2.3 / 4.3 / 4.5 storage (MagicMock db only)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
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


def _vision(*tags: str, relations: list | None = None) -> dict:
    return {"tags": list(tags), "tag_relations": relations or []}


def _db_for_tags(*, image_id: int = 101, tag_ids: list[int] | None = None):
    db = MagicMock()
    db.transaction.side_effect = _run_transaction_callback
    db.query.return_value = []
    db.select.return_value = []
    ids = tag_ids or [1, 2, 3]
    db.first_or_create.side_effect = list(ids)
    # image insert + one image_tags insert per tag id (+ optional edge inserts)
    db.insert.side_effect = [image_id] + [None] * (len(ids) + 4)
    return db


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
        embeded_text = np.array([0.1, 0.2, 0.3])

        result = storage.store_image(
            SOURCE, metadata, _vision("cat", "balcony"), embeded_text
        )

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
        embeded_text = np.array([0.1, 0.2, 0.3])

        result = storage.store_image(
            SOURCE, metadata, _vision("cat", "balcony"), embeded_text
        )

        expected = f"{WORKDIR}/Unknown/vacation.HEIC"
        mock_makedirs.assert_called_once_with(f"{WORKDIR}/Unknown", exist_ok=True)
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
        embeded_text = np.array([0.1, 0.2, 0.3])
        result = storage.store_image(
            SOURCE, metadata, _vision("cat", "balcony"), embeded_text
        )

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
        embeded_text = np.array([0.1, 0.2, 0.3])
        result = storage.store_image(
            SOURCE, metadata, _vision("cat", "balcony"), embeded_text
        )

        assert "Unknown" not in result["tags"]
        assert not any(
            isinstance(t, str) and t.isdigit() and len(t) == 4 for t in result["tags"]
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
        embeded_text = np.array([0.1, 0.2, 0.3])
        result = storage.store_image(
            SOURCE, metadata, _vision("cat", "balcony"), embeded_text
        )

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
        embeded_text = np.array([0.1, 0.2, 0.3])
        result = storage.store_image(
            SOURCE, metadata, _vision("2020", "cat"), embeded_text
        )

        mock_makedirs.assert_called_once_with(f"{WORKDIR}/Unknown", exist_ok=True)
        assert result["destination_path"].startswith(f"{WORKDIR}/Unknown/")
        mock_move.assert_called_once()

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_does_not_mutate_vision_tags_list(
        self, _exists, _makedirs, _move, _app_root
    ):
        storage = _storage()
        metadata = {"year": "2025", "location": None}
        vision_tags = ["cat"]
        vision = {"tags": vision_tags, "tag_relations": []}
        embeded_text = np.array([0.1, 0.2, 0.3])
        storage.store_image(SOURCE, metadata, vision, embeded_text)

        assert vision_tags == ["cat"]


class TestStoreImageFailures:
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=True)
    def test_existing_destination_does_not_move(
        self, _exists, mock_makedirs, mock_move
    ):
        storage = _storage()
        metadata = {"year": "2024", "location": None}
        embeded_text = np.array([0.1, 0.2, 0.3])

        result = storage.store_image(
            SOURCE, metadata, _vision("cat", "balcony"), embeded_text
        )

        mock_move.assert_not_called()
        mock_makedirs.assert_not_called()
        assert "warning" in result or "error" in result

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_move_failure_propagates(self, _exists, _makedirs, mock_move, _app_root):
        mock_move.side_effect = OSError("disk full")
        storage = _storage()
        metadata = {"year": "2024", "location": None}
        embeded_text = np.array([0.1, 0.2, 0.3])
        with pytest.raises(OSError, match="disk full"):
            storage.store_image(
                SOURCE, metadata, _vision("cat", "balcony"), embeded_text
            )


class TestStoreImageDbWrite:
    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_writes_relative_path_tags_and_image_tags_via_db_mock(
        self, _exists, _makedirs, _move, _app_root
    ):
        db = _db_for_tags(tag_ids=[1, 2, 3])
        storage = _storage(db=db)
        metadata = {"year": "2025", "location": "Calgary, CA"}
        embeded_text = np.array([0.1, 0.2, 0.3])
        storage.store_image(
            SOURCE, metadata, _vision("ukulele", "instrument"), embeded_text
        )

        db.transaction.assert_called_once()
        image_insert = db.insert.call_args_list[0]
        assert image_insert.args[0] == "images"
        assert image_insert.args[1]["file_path"] == "Photo_Tagged/2025/vacation.HEIC"
        assert not image_insert.args[1]["file_path"].startswith("/")
        assert image_insert.args[1]["year"] == "2025"
        assert image_insert.args[1]["location"] == "Calgary, CA"
        assert image_insert.args[1]["description_embedding"] == embeded_text.astype(
            np.float32
        ).tobytes()

        tag_names = [c.args[1]["name"] for c in db.first_or_create.call_args_list]
        assert tag_names == ["ukulele", "instrument", "2025"]
        assert all(
            c.kwargs.get("conflict_columns") == "name" or c.args[0] == "tags"
            for c in db.first_or_create.call_args_list
        )

        join_calls = [c for c in db.insert.call_args_list if c.args[0] == "image_tags"]
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
        db.query.return_value = []
        db.select.return_value = []
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
            _vision("ukulele", "instrument"),
            np.array([0.1, 0.2, 0.3]),
        )
        storage.store_image(
            "/virtual/inbox/b.HEIC",
            {"year": "2024", "location": ""},
            _vision("ukulele", "music"),
            np.array([0.1, 0.2, 0.3]),
        )

        ukulele_calls = [
            c
            for c in db.first_or_create.call_args_list
            if c.args[1]["name"] == "ukulele"
        ]
        assert len(ukulele_calls) == 2
        assert db.transaction.call_count == 2

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_persists_tag_relations_as_edges(
        self, _exists, _makedirs, _move, _app_root
    ):
        db = _db_for_tags(tag_ids=[1, 2, 3, 4, 1])
        storage = _storage(db=db)
        metadata = {"year": "2025", "location": ""}
        vision = _vision(
            "cat",
            "balcony",
            relations=[{"parent": "animal", "child": "cat"}],
        )
        embeded_text = np.array([0.1, 0.2, 0.3])
        storage.store_image(SOURCE, metadata, vision, embeded_text)

        edge_inserts = [c for c in db.insert.call_args_list if c.args[0] == "tag_edges"]
        assert len(edge_inserts) == 1
        assert edge_inserts[0].args[1] == {"parent_id": 4, "child_id": 1}
        relation_tag_names = [
            c.args[1]["name"]
            for c in db.first_or_create.call_args_list
            if c.args[1]["name"] in {"animal", "cat"}
        ]
        assert "animal" in relation_tag_names

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_skips_self_relation(self, _exists, _makedirs, _move, _app_root):
        db = _db_for_tags(tag_ids=[1, 2])
        storage = _storage(db=db)
        vision = _vision(
            "cat",
            relations=[{"parent": "cat", "child": "cat"}],
        )
        embeded_text = np.array([0.1, 0.2, 0.3])
        storage.store_image(
            SOURCE, {"year": None, "location": ""}, vision, embeded_text
        )

        assert not any(c.args[0] == "tag_edges" for c in db.insert.call_args_list)
        db.query.assert_not_called()

    @_patch_app_root()
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_skips_edge_when_cycle_detected(self, _exists, _makedirs, _move, _app_root):
        db = _db_for_tags(tag_ids=[1, 2, 2])
        db.query.return_value = [{"1": 1}]
        storage = _storage(db=db)
        vision = _vision(
            "animal",
            relations=[{"parent": "animal", "child": "cat"}],
        )
        embeded_text = np.array([0.1, 0.2, 0.3])
        storage.store_image(
            SOURCE, {"year": None, "location": ""}, vision, embeded_text
        )

        assert not any(c.args[0] == "tag_edges" for c in db.insert.call_args_list)
        db.query.assert_called_once()


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
                _vision("cat", "balcony"),
                np.array([0.1, 0.2, 0.3]),
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
                _vision("cat", "balcony"),
                np.array([0.1, 0.2, 0.3]),
            )

        db.delete.assert_not_called()
        mock_move.assert_not_called()
