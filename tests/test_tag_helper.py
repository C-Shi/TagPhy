"""Unit tests for TagHelper (MagicMock db only — no real SQLite)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tagphy.tools.db_operations import TagHelper

TAG_RESPONSE_KEYS = {"id", "name", "source", "photo_count", "children", "parents"}
TAG_PICTURE_RESPONSE_KEYS = {"id", "name", "source", "children", "parents"}
TAG_REF_KEYS = {"id", "name"}


def _query_side_effect_for_list(*_args, **_kwargs):
    """Route get_tags_with_details db.query calls by SQL content."""
    query = _args[0] if _args else ""
    sql = " ".join(str(query).split()).lower()

    if "group by t.id" in sql:
        return [
            {
                "id": 1,
                "name": "Cat",
                "source": "vision",
                "photo_count": 2,
            }
        ]
    if "descendants" in sql:
        return [{"id": 2, "name": "Meowy"}]
    if "ancestors" in sql:
        return [{"id": 10, "name": "Pet"}]
    if "child_count" in sql:
        return [{"child_count": 3}]
    return []


def _query_side_effect_for_pictures_ok(*_args, **_kwargs):
    query = _args[0] if _args else ""
    sql = " ".join(str(query).split()).lower()

    if "from tags where id" in sql:
        return [{"id": 1, "name": "Cat", "source": "vision"}]
    if "descendants" in sql:
        return [{"id": 2, "name": "Meowy"}]
    if "ancestors" in sql:
        return [{"id": 10, "name": "Pet"}]
    if "from images" in sql:
        return [
            {
                "id": 101,
                "file_path": "Photo_Tagged/2024/a.jpg",
                "file_name": "a.jpg",
                "year": "2024",
            }
        ]
    return []


class TestGetTagsWithDetails:
    def test_returns_tag_response_shape(self):
        db = MagicMock()
        db.query.side_effect = _query_side_effect_for_list
        helper = TagHelper(db=db)

        tags = helper.get_tags_with_details()

        assert len(tags) == 1
        tag = tags[0]
        assert TAG_RESPONSE_KEYS <= set(tag.keys())
        assert tag["id"] == 1
        assert tag["name"] == "Cat"
        assert tag["source"] == "vision"
        assert tag["photo_count"] == 5  # 2 direct + 3 descendant
        assert isinstance(tag["children"], list)
        assert isinstance(tag["parents"], list)
        assert tag["children"] == [{"id": 2, "name": "Meowy"}]
        assert tag["parents"] == [{"id": 10, "name": "Pet"}]
        assert TAG_REF_KEYS <= set(tag["children"][0].keys())
        assert TAG_REF_KEYS <= set(tag["parents"][0].keys())


class TestGetTagPictures:
    def test_valid_tag_id_returns_tag_picture_response(self):
        db = MagicMock()
        db.query.side_effect = _query_side_effect_for_pictures_ok
        helper = TagHelper(db=db)

        result = helper.get_tag_pictures(1)

        assert TAG_PICTURE_RESPONSE_KEYS <= set(result.keys())
        assert result["id"] == 1
        assert result["name"] == "Cat"
        assert result["source"] == "vision"
        assert result["children"] == [{"id": 2, "name": "Meowy"}]
        assert result["parents"] == [{"id": 10, "name": "Pet"}]

    @pytest.mark.parametrize("tag_id", [0, -1, None])
    def test_invalid_tag_id_raises_value_error(self, tag_id):
        db = MagicMock()
        helper = TagHelper(db=db)

        with pytest.raises(ValueError, match="Bad Request: Invalid Tag"):
            helper.get_tag_pictures(tag_id)

        db.query.assert_not_called()

    def test_unknown_tag_id_raises_value_error(self):
        db = MagicMock()
        db.query.return_value = []
        helper = TagHelper(db=db)

        with pytest.raises(ValueError, match="Bad Request: Invalid Tag"):
            helper.get_tag_pictures(999)
