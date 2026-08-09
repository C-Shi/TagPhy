"""Unit tests for FastAPI /api tag routes (mock TagHelper — no HTTP, no DB)."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

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
