"""Contract tests for Stage 2.4 / 3.1 / 4.4 pipeline orchestration (no real SQLite)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from tagphy.pipeline import BATCH_SIZE, PROGRESS_INTERVAL, ImageProcessingPipeline

APP_ROOT = Path("/virtual")


def _pipeline_with_mocks(workdir="/virtual/Photo_Tagged"):
    """Build a pipeline without real Gemini client or SQLiteConnection."""
    db = MagicMock()
    with (
        patch("tagphy.pipeline.ImageMetadata") as Meta,
        patch("tagphy.pipeline.GeminiVisionEngine") as Vision,
        patch("tagphy.pipeline.ImageStorage") as Storage,
        patch("tagphy.pipeline.SQLiteConnection", return_value=db),
    ):
        meta = MagicMock()
        vision = MagicMock()
        storage = MagicMock()
        Meta.return_value = meta
        Vision.return_value = vision
        Storage.return_value = storage
        pipeline = ImageProcessingPipeline(workdir=workdir)
    pipeline.image_metadata = meta
    pipeline.image_vision = vision
    pipeline.image_storage = storage
    pipeline.db = db
    return pipeline, meta, vision, storage


def _touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")
    return path


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

        assert result["status"] == "fail"
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

        assert result["status"] == "fail"
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

        assert result["status"] == "fail"
        assert result["stage"] == "store_image"
        assert result["image"] == "photo.jpg"


class TestFailureLogWrite:
    @patch("tagphy.pipeline.app_root", return_value=APP_ROOT)
    def test_on_root_failure_upserts_failure_log(self, _app_root):
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        path = "/virtual/inbox/broken.jpg"
        err = ValueError("bad exif")
        meta.extract_metadata.side_effect = err

        result = pipeline.run(path)

        assert result["status"] == "fail"
        pipeline.db.create_or_update.assert_called_once()
        kwargs = pipeline.db.create_or_update.call_args.kwargs
        assert kwargs["table"] == "failure_log"
        assert kwargs["conflict_columns"] == "source_path"
        assert kwargs["operations"] == {
            "attempts": "INCREMENT",
            "last_seen_at": "NOW",
        }
        assert kwargs["data"]["source_path"] == "inbox/broken.jpg"
        assert kwargs["data"]["file_name"] == "broken.jpg"
        assert kwargs["data"]["stage"] == "extract_metadata"
        assert kwargs["data"]["error_type"] == "ValueError"

    @patch("tagphy.pipeline.app_root", return_value=APP_ROOT)
    def test_off_root_failure_skips_failure_log(self, _app_root):
        pipeline, meta, vision, storage = _pipeline_with_mocks()
        path = "/other/drive/broken.jpg"
        meta.extract_metadata.side_effect = ValueError("bad exif")

        result = pipeline.run(path)

        assert result["status"] == "fail"
        assert result["stage"] == "extract_metadata"
        pipeline.db.create_or_update.assert_not_called()


class TestDirectoryScan:
    def test_nested_images_processed_exactly_once(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "all_photo"
        a = _touch(scan_root / "New" / "a.jpg")
        b = _touch(scan_root / "New" / "nested" / "b.PNG")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        result = pipeline.run(scan_root)

        assert result == {
            "total": 2,
            "succeeded": 2,
            "failed": 0,
            "skipped": 0,
        }
        called = {
            Path(c.args[0]).resolve() for c in meta.extract_metadata.call_args_list
        }
        assert called == {a.resolve(), b.resolve()}
        assert meta.extract_metadata.call_count == 2

    def test_mixed_extensions_accepted_unsupported_ignored(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        kept = [
            _touch(scan_root / "one.jpg"),
            _touch(scan_root / "two.JPG"),
            _touch(scan_root / "three.HEIC"),
            _touch(scan_root / "four.png"),
        ]
        _touch(scan_root / "notes.txt")
        _touch(scan_root / "clip.mp4")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": None, "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        result = pipeline.run(scan_root)

        assert result["total"] == 4
        assert result["succeeded"] == 4
        called = {
            Path(c.args[0]).resolve() for c in meta.extract_metadata.call_args_list
        }
        assert called == {p.resolve() for p in kept}

    def test_prunes_output_dir_sibling_under_scan_root(self, tmp_path):
        scan_root = tmp_path / "all_photo"
        workdir = scan_root / "Photo_Tagged"
        new_img = _touch(scan_root / "New" / "IMG_001.JPG")
        _touch(workdir / "2024" / "old.jpg")
        _touch(workdir / "2024" / "deep" / "older.HEIC")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        result = pipeline.run(scan_root)

        assert result["total"] == 1
        assert result["succeeded"] == 1
        assert meta.extract_metadata.call_count == 1
        assert (
            Path(meta.extract_metadata.call_args.args[0]).resolve() == new_img.resolve()
        )
        for call in meta.extract_metadata.call_args_list:
            assert "Photo_Tagged" not in Path(call.args[0]).parts

    def test_prunes_output_dir_nested_deeper_than_scan_root(self, tmp_path):
        scan_root = tmp_path / "all_photo"
        workdir = scan_root / "a" / "b" / "Photo_Tagged"
        keep = _touch(scan_root / "keep.jpg")
        _touch(workdir / "nested" / "skip.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        result = pipeline.run(scan_root)

        assert result["total"] == 1
        assert Path(meta.extract_metadata.call_args.args[0]).resolve() == keep.resolve()

    def test_rejects_target_equal_to_workdir(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        workdir.mkdir()
        _touch(workdir / "inside.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)

        result = pipeline.run(workdir)

        assert result["status"] == "fail"
        assert result["stage"] == "run"
        meta.extract_metadata.assert_not_called()
        vision.tag_image.assert_not_called()
        storage.store_image.assert_not_called()

    def test_rejects_target_inside_workdir(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        nested = workdir / "2024"
        nested.mkdir(parents=True)
        _touch(nested / "inside.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)

        result = pipeline.run(nested)

        assert result["status"] == "fail"
        assert result["stage"] == "run"
        meta.extract_metadata.assert_not_called()
        storage.store_image.assert_not_called()

    def test_one_failure_does_not_stop_later_images(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        first = _touch(scan_root / "a.jpg")
        second = _touch(scan_root / "b.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)

        def metadata_side_effect(path):
            if Path(path).name == "a.jpg":
                raise ValueError("bad exif")
            return {"year": "2024", "location": None}

        meta.extract_metadata.side_effect = metadata_side_effect
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        result = pipeline.run(scan_root)

        assert result == {
            "total": 2,
            "succeeded": 1,
            "failed": 1,
            "skipped": 0,
        }
        called = [Path(c.args[0]).name for c in meta.extract_metadata.call_args_list]
        assert called == [first.name, second.name] or set(called) == {
            first.name,
            second.name,
        }

    def test_unexpected_exception_does_not_abort_run(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        _touch(scan_root / "a.jpg")
        _touch(scan_root / "b.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        pipeline._run_single = MagicMock(
            side_effect=[
                RuntimeError("boom"),
                {"destination_path": "ok"},
            ]
        )

        result = pipeline.run(scan_root)

        assert result["total"] == 2
        assert result["failed"] == 1
        assert result["succeeded"] == 1
        assert pipeline._run_single.call_count == 2

    def test_storage_warning_counts_as_skipped(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        _touch(scan_root / "dup.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {
            "destination_path": "x",
            "warning": "File already exists. No action taken",
        }

        result = pipeline.run(scan_root)

        assert result == {
            "total": 1,
            "succeeded": 0,
            "failed": 0,
            "skipped": 1,
        }

    def test_empty_directory_returns_zero_counts(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "empty"
        scan_root.mkdir()

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)

        result = pipeline.run(scan_root)

        assert result == {
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }
        assert set(result) == {"total", "succeeded", "failed", "skipped"}
        meta.extract_metadata.assert_not_called()

    def test_return_has_only_aggregate_counters(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        _touch(scan_root / "a.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        result = pipeline.run(scan_root)

        assert set(result.keys()) == {"total", "succeeded", "failed", "skipped"}
        assert "results" not in result

    def test_batch_boundary_processes_all_images_once(self, tmp_path):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        count = BATCH_SIZE + 3
        for i in range(count):
            _touch(scan_root / f"img_{i:04d}.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        result = pipeline.run(scan_root)

        assert result["total"] == count
        assert result["succeeded"] == count
        assert meta.extract_metadata.call_count == count


class TestDirectoryScanProgress:
    def test_logs_scan_start_with_directory_name(self, tmp_path, caplog):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        scan_root.mkdir()

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)

        with caplog.at_level("INFO", logger="tagphy.pipeline"):
            pipeline.run(scan_root)

        assert any(
            "Starting directory scan" in record.message and "inbox" in record.message
            for record in caplog.records
        )

    def test_logs_heartbeat_for_each_image(self, tmp_path, caplog):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        _touch(scan_root / "alpha.jpg")
        _touch(scan_root / "beta.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        with caplog.at_level("INFO", logger="tagphy.pipeline"):
            pipeline.run(scan_root)

        messages = [record.message for record in caplog.records]
        assert any("Processing image" in m and "alpha.jpg" in m for m in messages)
        assert any("Processing image" in m and "beta.jpg" in m for m in messages)

    def test_logs_aggregate_progress_every_interval(self, tmp_path, caplog):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        for i in range(PROGRESS_INTERVAL + 1):
            _touch(scan_root / f"img_{i:02d}.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)
        meta.extract_metadata.return_value = {"year": "2024", "location": None}
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        with caplog.at_level("INFO", logger="tagphy.pipeline"):
            pipeline.run(scan_root)

        assert any("Progress:" in record.message for record in caplog.records)

    def test_logs_final_summary_matching_counts(self, tmp_path, caplog):
        workdir = tmp_path / "Photo_Tagged"
        scan_root = tmp_path / "inbox"
        _touch(scan_root / "ok.jpg")
        _touch(scan_root / "bad.jpg")

        pipeline, meta, vision, storage = _pipeline_with_mocks(workdir=workdir)

        def metadata_side_effect(path):
            if Path(path).name == "bad.jpg":
                raise ValueError("bad exif")
            return {"year": "2024", "location": None}

        meta.extract_metadata.side_effect = metadata_side_effect
        vision.tag_image.return_value = {
            "main_tag": "cat",
            "secondary_tag": "balcony",
        }
        storage.store_image.return_value = {"destination_path": "ok"}

        with caplog.at_level("INFO", logger="tagphy.pipeline"):
            result = pipeline.run(scan_root)

        summary = next(
            record.message
            for record in caplog.records
            if "Directory scan complete" in record.message
        )
        assert f"total={result['total']}" in summary
        assert f"succeeded={result['succeeded']}" in summary
        assert f"failed={result['failed']}" in summary
        assert f"skipped={result['skipped']}" in summary
        assert set(result.keys()) == {"total", "succeeded", "failed", "skipped"}
