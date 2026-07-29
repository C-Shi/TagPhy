"""Contract tests for Stage 2.3 storage."""

from unittest.mock import patch

import pytest

from tagphy.tools.image_storage import ImageStorage


WORKDIR = "/virtual/Photo_Tagged"
SOURCE = "/virtual/inbox/vacation.HEIC"


class TestStoreImageDestination:
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_moves_to_year_folder_when_year_present(
        self, _exists, mock_makedirs, mock_move
    ):
        storage = ImageStorage(workdir=WORKDIR)
        metadata = {"year": "2024", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        expected = f"{WORKDIR}/2024/vacation.HEIC"
        mock_makedirs.assert_called_once_with(f"{WORKDIR}/2024", exist_ok=True)
        mock_move.assert_called_once_with(SOURCE, expected)
        assert result["destination_path"] == expected
        assert result["metadata"] == metadata

    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_moves_to_unknown_when_year_missing(
        self, _exists, mock_makedirs, mock_move
    ):
        storage = ImageStorage(workdir=WORKDIR)
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
    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_appends_numeric_year_tag_from_metadata(
        self, _exists, _makedirs, _move
    ):
        storage = ImageStorage(workdir=WORKDIR)
        metadata = {"year": "2025", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        assert "2025" in result["tags"]
        assert "year" not in result["tags"]
        assert "cat" in result["tags"]
        assert "balcony" in result["tags"]

    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_does_not_append_year_tag_when_year_missing(
        self, _exists, _makedirs, _move
    ):
        storage = ImageStorage(workdir=WORKDIR)
        metadata = {"year": None, "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        assert "Unknown" not in result["tags"]
        assert not any(
            isinstance(t, str) and t.isdigit() and len(t) == 4
            for t in result["tags"]
        )

    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_year_folder_comes_from_metadata_not_vision_tags(
        self, _exists, mock_makedirs, mock_move
    ):
        """Vision must never invent the year folder; metadata year wins."""
        storage = ImageStorage(workdir=WORKDIR)
        metadata = {"year": None, "location": None}
        # Vision incorrectly emitting a year-like string must not choose folder.
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
        storage = ImageStorage(workdir=WORKDIR)
        metadata = {"year": "2024", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        result = storage.store_image(SOURCE, metadata, tags)

        mock_move.assert_not_called()
        mock_makedirs.assert_not_called()
        assert "warning" in result or "error" in result

    @patch("tagphy.tools.image_storage.move")
    @patch("tagphy.tools.image_storage.os.makedirs")
    @patch("tagphy.tools.image_storage.os.path.exists", return_value=False)
    def test_move_failure_propagates(self, _exists, _makedirs, mock_move):
        mock_move.side_effect = OSError("disk full")
        storage = ImageStorage(workdir=WORKDIR)
        metadata = {"year": "2024", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}

        with pytest.raises(OSError, match="disk full"):
            storage.store_image(SOURCE, metadata, tags)
