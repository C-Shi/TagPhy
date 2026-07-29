"""Contract tests for Stage 2.2 vision tagging."""

from abc import ABC
from unittest.mock import MagicMock, patch

import pytest

from tagphy.tools.image_vision import GeminiVisionEngine, ImageVision


class TestImageVisionInterface:
    def test_image_vision_is_abstract_swap_point(self):
        assert issubclass(ImageVision, ABC)

        class Incomplete(ImageVision):
            pass

        with pytest.raises(TypeError):
            Incomplete()

    def test_concrete_engine_implements_tag_image(self):
        assert hasattr(GeminiVisionEngine, "tag_image")
        assert callable(GeminiVisionEngine.tag_image)


class TestGeminiVisionEngine:
    def _engine_with_fake_client(self):
        with patch.object(GeminiVisionEngine, "__init__", lambda self: None):
            engine = GeminiVisionEngine()
        engine.client = MagicMock()
        return engine

    def test_returns_parsed_main_and_secondary_tags(self):
        engine = self._engine_with_fake_client()
        engine._get_image_thumbnail = MagicMock(return_value=b"jpeg-bytes")
        parsed = {"main_tag": "cat", "secondary_tag": "balcony"}
        response = MagicMock()
        response.parsed = parsed
        engine.client.models.generate_content.return_value = response

        result = engine.tag_image("photo.jpg")

        assert result == parsed
        assert result["main_tag"] == "cat"
        assert result["secondary_tag"] == "balcony"

    def test_requests_structured_json_schema_and_jpeg_bytes(self):
        engine = self._engine_with_fake_client()
        engine._get_image_thumbnail = MagicMock(return_value=b"jpeg-bytes")
        response = MagicMock()
        response.parsed = {"main_tag": "dog", "secondary_tag": "park"}
        engine.client.models.generate_content.return_value = response

        engine.tag_image("photo.jpg")

        kwargs = engine.client.models.generate_content.call_args.kwargs
        config = kwargs["config"]
        assert config.response_mime_type == "application/json"
        schema = config.response_schema
        assert "main_tag" in schema["properties"]
        assert "secondary_tag" in schema["properties"]
        assert set(schema["required"]) == {"main_tag", "secondary_tag"}
        contents = kwargs["contents"]
        assert len(contents) == 1

    def test_api_failure_propagates(self):
        engine = self._engine_with_fake_client()
        engine._get_image_thumbnail = MagicMock(return_value=b"jpeg-bytes")
        engine.client.models.generate_content.side_effect = RuntimeError(
            "api down"
        )

        with pytest.raises(RuntimeError, match="api down"):
            engine.tag_image("photo.jpg")

    def test_thumbnail_failure_propagates(self):
        engine = self._engine_with_fake_client()
        engine._get_image_thumbnail = MagicMock(
            side_effect=OSError("cannot open")
        )

        with pytest.raises(OSError, match="cannot open"):
            engine.tag_image("bad.jpg")
        engine.client.models.generate_content.assert_not_called()
