"""Contract tests for Stage 2.4 pipeline orchestration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from tagphy.pipeline import ImageProcessingPipeline


def _pipeline_with_mocks():
    """Build a pipeline without constructing a real Gemini Client."""
    with (
        patch("tagphy.pipeline.ImageMetadata") as Meta,
        patch("tagphy.pipeline.GeminiVisionEngine") as Vision,
        patch("tagphy.pipeline.ImageStorage") as Storage,
    ):
        meta = MagicMock()
        vision = MagicMock()
        storage = MagicMock()
        Meta.return_value = meta
        Vision.return_value = vision
        Storage.return_value = storage
        pipeline = ImageProcessingPipeline(workdir="/virtual/Photo_Tagged")
    pipeline.image_metadata = meta
    pipeline.image_vision = vision
    pipeline.image_storage = storage
    return pipeline, meta, vision, storage


class TestPipelineSuccess:
    def test_runs_metadata_then_vision_then_storage(self):
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        path = "/virtual/inbox/photo.jpg"
        metadata = {"year": "2024", "location": None}
        tags = {"main_tag": "cat", "secondary_tag": "balcony"}
        stored = {
            "destination_path": "/virtual/Photo_Tagged/2024/photo.jpg",
            "tags": ["cat", "balcony", "2024"],
            "metadata": metadata,
        }
        meta.extract_metadata.return_value = metadata
        vision.tag_image.return_value = tags
        storage.store_image.return_value = stored

        result = pipeline.run(path)

        meta.extract_metadata.assert_called_once_with(path)
        vision.tag_image.assert_called_once_with(path)
        storage.store_image.assert_called_once_with(path, metadata, tags)
        assert result == stored

    def test_passes_metadata_and_vision_outputs_to_storage(self):
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        path = "relative/shot.HEIC"
        metadata = {"year": "2022", "location": "Calgary, CA"}
        tags = {"main_tag": "dog", "secondary_tag": "park"}
        meta.extract_metadata.return_value = metadata
        vision.tag_image.return_value = tags
        storage.store_image.return_value = {"ok": True}

        pipeline.run(path)

        args = storage.store_image.call_args.args
        assert args[0] == path
        assert args[1] is metadata
        assert args[2] is tags


class TestPipelineHardStop:
    def test_metadata_failure_skips_vision_and_storage(self):
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        path = "/virtual/inbox/broken.jpg"
        meta.extract_metadata.side_effect = ValueError("bad exif")

        result = pipeline.run(path)

        assert result["success"] == "fail"
        assert result["stage"] == "extract_metadata"
        assert result["image"] == "broken.jpg"
        vision.tag_image.assert_not_called()
        storage.store_image.assert_not_called()

    def test_vision_failure_skips_storage(self):
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        path = "/virtual/inbox/photo.jpg"
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.side_effect = RuntimeError("gemini timeout")

        result = pipeline.run(path)

        assert result["success"] == "fail"
        assert result["stage"] == "tag_image"
        assert result["image"] == "photo.jpg"
        storage.store_image.assert_not_called()

    def test_storage_failure_returns_failure_entry(self):
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        path = "/virtual/inbox/photo.jpg"
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.side_effect = OSError("move failed")

        result = pipeline.run(path)

        assert result["success"] == "fail"
        assert result["stage"] == "store_image"
        assert result["image"] == "photo.jpg"


class TestPipelinePathRouting:
    def test_directory_path_does_not_invoke_single_image_tools(self):
        """Stage 2 only requires single-file processing; directory is Stage 3."""
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        directory = Path("/virtual/inbox")

        with patch.object(Path, "is_dir", return_value=True):
            result = pipeline.run(directory)

        meta.extract_metadata.assert_not_called()
        vision.tag_image.assert_not_called()
        storage.store_image.assert_not_called()
        # Stage 3 stub: no multi-file semantics invented yet.
        assert result is None
