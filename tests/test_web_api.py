"""Unit tests for FastAPI /api tag routes (mock TagHelper — no HTTP, no DB)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from tagphy.tools.db_operations import RecordNotFoundError
from tagphy.web import api


def _run(coro):
    return asyncio.run(coro)


class TestTagsRoute:
    def test_calls_get_tags_with_details(self):
        mock_helper = MagicMock()
        sample = [
            {
                "id": 1,
                "name": "Cat",
                "source": "vision",
                "photo_count": 5,
                "children": [],
                "parents": [],
            }
        ]
        mock_helper.get_tags_with_details.return_value = sample

        with patch.object(api, "tag_helper", mock_helper):
            result = _run(api.tag_info())

        mock_helper.get_tags_with_details.assert_called_once_with()
        assert result == sample


class TestPictureRoute:
    def test_valid_picture_id_calls_get_picture(self):
        mock_helper = MagicMock()
        image_sample = {
            "id": 101,
            "name": "Cat",
            "source": "vision",
        }
        tag_sample = [{"id": 1, "name": "Cat"}]
        mock_helper.get_picture.return_value = image_sample
        mock_helper.get_tags_for_picture.return_value = tag_sample
        with (
            patch.object(api, "picture_helper", mock_helper),
            patch.object(api, "tag_helper", mock_helper),
        ):
            result = _run(api.get_picture(101))

        mock_helper.get_picture.assert_called_once_with(101)
        mock_helper.get_tags_for_picture.assert_called_once_with(101)
        assert result == {**image_sample, "tags": tag_sample}

    def test_no_record_error_raises_http_400(self):
        mock_helper = MagicMock()
        mock_helper.get_picture.side_effect = RecordNotFoundError("images")

        with (
            patch.object(api, "picture_helper", mock_helper),
            patch.object(api, "tag_helper", mock_helper),
        ):
            with pytest.raises(HTTPException) as exc_info:
                _run(api.get_picture(101))

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Record not found in table: images"


class TestTagPicturesRoute:
    def test_valid_tag_id_calls_get_tag_pictures(self):
        mock_helper = MagicMock()
        sample = {
            "id": 7,
            "name": "Cat",
            "source": "vision",
            "children": [],
            "parents": [],
            "pictures": [{"id": 101}],
        }
        mock_helper.get_tag_pictures.return_value = sample

        with patch.object(api, "tag_helper", mock_helper):
            result = _run(api.get_tag(7))

        mock_helper.get_tag_pictures.assert_called_once_with(7)
        assert result == sample

    def test_value_error_raises_http_400(self):
        mock_helper = MagicMock()
        mock_helper.get_tag_pictures.side_effect = ValueError(
            "Bad Request: Invalid Tag"
        )

        with patch.object(api, "tag_helper", mock_helper):
            with pytest.raises(HTTPException) as exc_info:
                _run(api.get_tag(999))

        mock_helper.get_tag_pictures.assert_called_once_with(999)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Bad Request: Invalid Tag"


class TestSettingsRoute:
    def test_get_settings_returns_store_map(self):
        mock_store = MagicMock()
        mock_store.load.return_value = {"privacy_pre_check": "true"}
        with patch.object(api, "settings_store", mock_store):
            result = _run(api.get_settings())
        mock_store.load.assert_called_once_with()
        assert result == {"privacy_pre_check": "true"}

    def test_put_setting_calls_set(self):
        mock_store = MagicMock()
        mock_store.set.return_value = {"privacy_pre_check": "false"}
        with patch.object(api, "settings_store", mock_store):
            result = _run(api.update_setting("privacy_pre_check", {"value": "false"}))
        mock_store.set.assert_called_once_with("privacy_pre_check", "false")
        assert result["privacy_pre_check"] == "false"

    def test_put_empty_value_raises_http_400(self):
        mock_store = MagicMock()
        mock_store.set.side_effect = ValueError("value must be a non-empty string")
        with patch.object(api, "settings_store", mock_store):
            with pytest.raises(HTTPException) as exc_info:
                _run(api.update_setting("privacy_pre_check", {"value": ""}))
        assert exc_info.value.status_code == 400
