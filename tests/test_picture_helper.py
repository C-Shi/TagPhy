"""Unit tests for PictureHelper (MagicMock db + patched file/PIL — no real I/O)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tagphy.tools.db_operations import PictureHelper, RecordNotFoundError

TAG_A = 1
TAG_B = 2
TAG_C = 3

P1 = {
    "id": 101,
    "file_name": "p1.jpg",
    "file_path": "Photo_Tagged/2024/p1.jpg",
    "year": "2024",
}
P2 = {
    "id": 102,
    "file_name": "p2.jpg",
    "file_path": "Photo_Tagged/2024/p2.jpg",
    "year": "2024",
}
P3 = {
    "id": 103,
    "file_name": "p3.jpg",
    "file_path": "Photo_Tagged/2024/p3.jpg",
    "year": "2024",
}


def _normalize_sql(query: str) -> str:
    return " ".join(str(query).split()).lower()


class TestGetPicturePreview:
    def test_success_returns_buffer_and_filename(self):
        db = MagicMock()
        db.select.return_value = [
            {"file_name": "a.jpg", "file_path": "Photo_Tagged/2024/a.jpg"}
        ]
        helper = PictureHelper(db=db)

        mock_rgb = MagicMock()
        mock_img = MagicMock()
        mock_img.convert.return_value = mock_rgb

        def fake_save(buffer, format=None, quality=None):
            buffer.write(b"jpeg-bytes")

        mock_rgb.save.side_effect = fake_save

        with (
            patch(
                "tagphy.tools.db_operations.picture_helper.app_root",
                return_value="/fake/root",
            ),
            patch(
                "tagphy.tools.db_operations.picture_helper.Image.open",
                return_value=MagicMock(
                    __enter__=MagicMock(return_value=mock_img),
                    __exit__=MagicMock(return_value=False),
                ),
            ),
        ):
            buffer, alt = helper.get_picture_preview(42)

        assert buffer == b"jpeg-bytes"
        assert alt == "a.jpg"
        db.select.assert_called_once_with(
            "images", ["file_name", "file_path"], {"id": 42}
        )
        mock_img.convert.assert_called_once_with("RGB")
        mock_rgb.thumbnail.assert_called_once_with((320, 320))

    def test_failure_wraps_message(self):
        db = MagicMock()
        db.select.side_effect = RuntimeError("missing row")
        helper = PictureHelper(db=db)

        with pytest.raises(Exception, match=r"^Failed to get picture preview: ") as exc:
            helper.get_picture_preview(999)

        assert "missing row" in str(exc.value)


class TestGetPicturesForTags:
    def test_no_tag_ids_returns_all(self):
        db = MagicMock()
        db.query.return_value = [P1, P2, P3]
        helper = PictureHelper(db=db)

        result = helper.get_pictures_for_tags(tag_ids=[])

        assert result == [P1, P2, P3]
        sql = _normalize_sql(db.query.call_args[0][0])
        assert "from images i" in sql
        assert "exists" not in sql
        assert "tag_id in" not in sql
        assert "order by i.created_at desc" in sql
        assert "limit" in sql
        # empty tag list: query called with SQL only (no bind params) or empty params
        assert len(db.query.call_args[0]) == 1 or db.query.call_args[0][1] == []

    def test_and_a_and_c_returns_p1(self):
        db = MagicMock()
        db.query.return_value = [P1]
        helper = PictureHelper(db=db)

        result = helper.get_pictures_for_tags(tag_ids=[[TAG_A], [TAG_C]], logic="AND")

        assert result == [P1]
        sql = _normalize_sql(db.query.call_args[0][0])
        assert sql.count("exists") == 2
        assert " and " in sql
        params = db.query.call_args[0][1]
        assert params == [str(TAG_A), str(TAG_C)]

    def test_and_b_and_c_returns_empty(self):
        db = MagicMock()
        db.query.return_value = []
        helper = PictureHelper(db=db)

        result = helper.get_pictures_for_tags(tag_ids=[[TAG_B], [TAG_C]], logic="AND")

        assert result == []
        sql = _normalize_sql(db.query.call_args[0][0])
        assert sql.count("exists") == 2
        params = db.query.call_args[0][1]
        assert params == [str(TAG_B), str(TAG_C)]

    def test_or_expanded_ids_returns_all(self):
        """OR with caller-expanded ids (A ∪ descendants ∪ C) → all three pictures."""
        db = MagicMock()
        db.query.return_value = [P1, P2, P3]
        helper = PictureHelper(db=db)

        result = helper.get_pictures_for_tags(tag_ids=[TAG_A, TAG_B, TAG_C], logic="OR")

        assert result == [P1, P2, P3]
        sql = _normalize_sql(db.query.call_args[0][0])
        assert "join image_tags" in sql
        assert "tag_id in (?,?,?)" in sql
        assert "exists" not in sql
        params = db.query.call_args[0][1]
        assert params == [str(TAG_A), str(TAG_B), str(TAG_C)]

    def test_invalid_logic_raises(self):
        db = MagicMock()
        helper = PictureHelper(db=db)

        with pytest.raises(
            ValueError,
            match=(
                r"Invalid Tag Selection Logic Type\. "
                r"Must be 'OR' or 'AND' but got Other"
            ),
        ):
            helper.get_pictures_for_tags(tag_ids=[TAG_A], logic="Other")

        db.query.assert_not_called()


class TestGetPicture:
    def test_success_returns_picture(self):
        db = MagicMock()
        db.select.return_value = [P1]
        helper = PictureHelper(db=db)

        result = helper.get_picture(101)

        assert result == P1
        db.select.assert_called_once_with("images", ["*"], {"id": 101})

    def test_failure_wraps_message(self):
        db = MagicMock()
        db.select.side_effect = RecordNotFoundError("images")
        helper = PictureHelper(db=db)

        with pytest.raises(
            RecordNotFoundError, match="Record not found in table: images"
        ) as exc:
            helper.get_picture(999)

        assert "Record not found in table: images" in str(exc.value)
