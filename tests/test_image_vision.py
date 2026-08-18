"""Contract tests for Stage 2.2 / 4.5 vision tagging."""

from abc import ABC
from unittest.mock import MagicMock, patch

import pytest

from tagphy.tools.image_vision import GeminiVisionEngine, ImageVision


def _vision_result(*tags: str, relations: list | None = None) -> dict:
    return {"tags": list(tags), "tag_relations": relations or []}


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
    def _engine_with_fake_client(self, existing_tags: list | None = None):
        with patch.object(GeminiVisionEngine, "__init__", lambda self, db=None: None):
            engine = GeminiVisionEngine(db=MagicMock())
        engine.client = MagicMock()
        engine.db = MagicMock()
        rows = [{"name": name} for name in (existing_tags or [])]
        engine.db.select.return_value = rows
        return engine

    def test_returns_parsed_tags_and_relations(self):
        engine = self._engine_with_fake_client()
        engine.get_image_thumbnail = MagicMock(return_value=b"jpeg-bytes")
        parsed = _vision_result(
            "cat",
            "balcony",
            relations=[{"parent": "animal", "child": "cat"}],
        )
        response = MagicMock()
        response.parsed = parsed
        engine.client.models.generate_content.return_value = response

        result = engine.tag_image("photo.jpg")

        assert result == parsed
        assert result["tags"] == ["cat", "balcony"]
        assert result["tag_relations"] == [{"parent": "animal", "child": "cat"}]

    def test_requests_structured_json_schema_image_and_catalog_text(self):
        engine = self._engine_with_fake_client(existing_tags=["animal", "cat"])
        engine.get_image_thumbnail = MagicMock(return_value=b"jpeg-bytes")
        response = MagicMock()
        response.parsed = _vision_result("cat")
        engine.client.models.generate_content.return_value = response

        engine.tag_image("photo.jpg")

        engine.db.select.assert_called_once_with(
            table="tags",
            columns=["name"],
            where={"source": "vision"},
        )
        kwargs = engine.client.models.generate_content.call_args.kwargs
        config = kwargs["config"]
        assert config.response_mime_type == "application/json"
        schema = config.response_schema
        assert "tags" in schema["properties"]
        assert "tag_relations" in schema["properties"]
        assert schema["properties"]["tags"]["minItems"] == 1
        assert schema["properties"]["tags"]["maxItems"] == 3
        assert set(schema["required"]) == {"tags", "tag_relations"}
        contents = kwargs["contents"]
        assert len(contents) == 2
        catalog_part = contents[1]
        assert "animal" in catalog_part.text
        assert "cat" in catalog_part.text

    def test_api_failure_propagates(self):
        engine = self._engine_with_fake_client()
        engine.get_image_thumbnail = MagicMock(return_value=b"jpeg-bytes")
        engine.client.models.generate_content.side_effect = RuntimeError(
            "api down"
        )

        with pytest.raises(RuntimeError, match="api down"):
            engine.tag_image("photo.jpg")

    def test_thumbnail_failure_propagates(self):
        engine = self._engine_with_fake_client()
        engine.get_image_thumbnail = MagicMock(
            side_effect=OSError("cannot open")
        )

        with pytest.raises(OSError, match="cannot open"):
            engine.tag_image("bad.jpg")
        engine.client.models.generate_content.assert_not_called()
