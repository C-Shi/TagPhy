"""Unit tests for BrowseHelper (no HTTP, no Gemini)."""

from pathlib import Path

import pytest

from tagphy.web.utils.browse_helper import BrowseHelper


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


class TestBrowseHelper:
    def test_lists_dirs_and_image_files_only(self, tmp_path: Path):
        _touch(tmp_path / "inbox" / "a.jpg")
        _touch(tmp_path / "inbox" / "notes.txt")
        (tmp_path / "dev").mkdir()

        helper = BrowseHelper(root=tmp_path)
        result = helper.list_directory("")

        names = {e["name"]: e["type"] for e in result["entries"]}
        assert names["dev"] == "dir"
        assert names["inbox"] == "dir"
        assert "notes.txt" not in names
        assert result["current"] == tmp_path.resolve().as_posix()

    def test_lists_images_inside_folder(self, tmp_path: Path):
        jpg = _touch(tmp_path / "inbox" / "shot.JPG")
        _touch(tmp_path / "inbox" / "readme.md")

        helper = BrowseHelper(root=tmp_path)
        result = helper.list_directory(str(tmp_path / "inbox"))

        assert result["parent"] == tmp_path.resolve().as_posix()
        assert result["entries"] == [
            {
                "name": "shot.JPG",
                "type": "file",
                "path": jpg.resolve().as_posix(),
            }
        ]

    def test_hides_photo_tagged(self, tmp_path: Path):
        (tmp_path / "Photo_Tagged").mkdir()
        (tmp_path / "keep").mkdir()

        helper = BrowseHelper(root=tmp_path)
        result = helper.list_directory("")

        names = [e["name"] for e in result["entries"]]
        assert "keep" in names
        assert "Photo_Tagged" not in names

    def test_rejects_browsing_inside_photo_tagged(self, tmp_path: Path):
        tagged = tmp_path / "Photo_Tagged" / "2024"
        tagged.mkdir(parents=True)

        helper = BrowseHelper(root=tmp_path)
        with pytest.raises(ValueError, match="output directory"):
            helper.list_directory(str(tagged))

    def test_relative_path_is_joined_to_root(self, tmp_path: Path):
        nested = tmp_path / "dev" / "test"
        nested.mkdir(parents=True)

        helper = BrowseHelper(root=tmp_path)
        result = helper.list_directory("dev/test")

        assert result["current"] == nested.resolve().as_posix()
        assert result["parent"] == (tmp_path / "dev").resolve().as_posix()
