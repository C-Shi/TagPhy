import logging, os, time
from logging import getLogger
from pathlib import Path
from typing import Callable

from PIL import Image
from tagphy import app_root
from tagphy.tools import GeminiVisionEngine, ImageMetadata, ImageStorage
from tagphy.db.connection import SQLiteConnection

logger = getLogger(__name__)

DEFAULT_OUTPUT_DIR_NAME = "Photo_Tagged"
BATCH_SIZE = 100
PROGRESS_INTERVAL = 10

# pillow-heif is registered at import time by tagphy.tools.image_metadata
IMAGE_EXTENSIONS = {
    ext.lower()
    for ext, fmt in Image.registered_extensions().items()
    if fmt in Image.OPEN
}


class ImageProcessingPipeline:
    """A pipeline for processing images in local drive.
    Stage:
     - Extract metadata from image
     - Intelligently tag the image
     - Move the image into processed folder
    """

    def __init__(self, workdir: str | Path | None = None):
        """Initialize the image processing pipeline.

        Args:
            workdir: The destination root directory to store the images.
        """

        self.db = SQLiteConnection()
        self.workdir = Path(workdir or (app_root() / DEFAULT_OUTPUT_DIR_NAME)).resolve()
        self.image_metadata = ImageMetadata()
        self.image_vision = GeminiVisionEngine(db=self.db)
        self.image_storage = ImageStorage(workdir=str(self.workdir), db=self.db)

    def validate_path(self, path: str | Path) -> bool:
        """Validate the path is a valid image or directory.

        Args:
            path: The path to validate.
        """
        target = Path(path).resolve()
        output_key = os.path.normcase(str(self.workdir))
        target_key = os.path.normcase(str(target))

        if target_key == output_key or target_key.startswith(output_key + os.sep):
            return False
        return True

    def run(
        self,
        path: str | Path,
        should_stop: Callable = lambda: False,
        on_progress: Callable | None = None,
    ):
        """Run the image processing pipeline on a single image or a directory of images.

        Args:
            path: The absolute path to the image or directory of images to process.
            should_stop: A callable that returns True if the pipeline should stop.
        """
        target = Path(path).resolve()

        if not self.validate_path(target):
            logger.error("Target is the output directory or inside it")
            if on_progress:
                on_progress(
                    {
                        "status": "fail",
                        "stage": "run",
                        "msg": "Target is the output directory or inside it",
                    }
                )
            return {
                "status": "fail",
                "stage": "run",
                "msg": "Target is the output directory or inside it",
            }

        if target.is_dir():
            return self._run_directory(target, should_stop, on_progress)

        # choose not to have on_progress for single image processing. If directly, handle inside _run_directory but outside of _run_single
        return self._run_single(str(path), should_stop)

    def _run_single(self, image_path: str, should_stop: Callable):
        """Run the image processing pipeline on single image.

        Args:
            image_path: The path to the image to process.
        """

        if should_stop():
            return

        try:
            metadata = self.image_metadata.extract_metadata(image_path)
        except Exception as e:
            return self._failure(image_path, "extract_metadata", e)
        try:
            vision_response = self.image_vision.tag_image(image_path)
        except Exception as e:
            return self._failure(image_path, "tag_image", e)
        try:
            return self.image_storage.store_image(image_path, metadata, vision_response)
        except Exception as e:
            return self._failure(image_path, "store_image", e)

    def _run_directory(
        self,
        directory_path: str | Path,
        should_stop: Callable,
        on_progress: Callable | None = None,
    ):
        """Walk a directory once, process each image, return aggregate counts."""
        counts = {
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }
        batch: list[Path] = []
        output_key = os.path.normcase(str(self.workdir))
        started_at = time.monotonic()

        logger.info(
            "Starting directory scan: path=%s output=%s",
            directory_path,
            self.workdir,
        )

        if on_progress:
            on_progress(
                {
                    "status": "start",
                    "stage": "run",
                    "msg": f"Starting directory scan: path={directory_path} output={self.workdir}",
                }
            )

        def process_batch(paths: list[Path]) -> None:
            for image_path in paths:
                if should_stop():
                    return
                counts["total"] += 1
                logger.info(
                    "Processing image %s: %s",
                    counts["total"],
                    image_path.name,
                )
                try:
                    result = self._run_single(str(image_path), should_stop)
                except Exception as e:
                    logger.error(
                        "Image Processing Pipeline unexpected error "
                        f"on {image_path}: {e}"
                    )
                    if on_progress:
                        on_progress(
                            {
                                "status": "fail",
                                "stage": "run",
                                "msg": f"Image Processing Pipeline unexpected error on {image_path}: {e}",
                            }
                        )
                    counts["failed"] += 1
                    continue

                if isinstance(result, dict) and result.get("status") == "fail":
                    counts["failed"] += 1
                elif isinstance(result, dict) and result.get("warning"):
                    counts["skipped"] += 1
                else:
                    counts["succeeded"] += 1

                if counts["total"] % PROGRESS_INTERVAL == 0:
                    elapsed = time.monotonic() - started_at
                    rate = counts["total"] / elapsed if elapsed > 0 else 0.0
                    logger.info(
                        "Progress: total=%s succeeded=%s failed=%s skipped=%s "
                        "elapsed=%.1fs rate=%.1f images/min",
                        counts["total"],
                        counts["succeeded"],
                        counts["failed"],
                        counts["skipped"],
                        elapsed,
                        rate * 60.0,
                    )
                    if on_progress:
                        on_progress(
                            {
                                "status": "progress",
                                "stage": "run",
                                "msg": f"Progress: total={counts['total']} succeeded={counts['succeeded']} failed={counts['failed']} skipped={counts['skipped']} elapsed={elapsed:.1f}s rate={rate * 60.0:.1f} images/min",
                            }
                        )

        walker = os.walk(
            directory_path,
            onerror=lambda err: logger.warning(f"Skipping unreadable directory: {err}"),
        )

        for dirpath, dirnames, filenames in walker:
            # Prune before descent: the output directory is never listed or entered.
            dirnames[:] = [
                d
                for d in sorted(dirnames)
                if os.path.normcase(str((Path(dirpath) / d).resolve())) != output_key
            ]
            for name in sorted(filenames):
                if Path(name).suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                batch.append(Path(dirpath) / name)
                if len(batch) >= BATCH_SIZE:
                    process_batch(batch)
                    batch.clear()
                if should_stop():
                    return

        if batch:
            process_batch(batch)
            if should_stop():
                return

        elapsed = time.monotonic() - started_at
        logger.info(
            "Directory scan complete: total=%s succeeded=%s failed=%s skipped=%s "
            "elapsed=%.1fs",
            counts["total"],
            counts["succeeded"],
            counts["failed"],
            counts["skipped"],
            elapsed,
        )
        if on_progress:
            on_progress(
                {
                    "status": "complete",
                    "stage": "run",
                    "msg": f"Directory scan complete: total={counts['total']} succeeded={counts['succeeded']} failed={counts['failed']} skipped={counts['skipped']} elapsed={elapsed:.1f}s",
                }
            )
        return counts

    def _failure(self, image_path: str | Path, stage: str, error: Exception):
        """Handle the failure of a stage.

        Args:
            stage: The stage that failed.
            error: The error that occurred.
        """

        try:
            relative_path = (
                Path(image_path).resolve().relative_to(app_root()).as_posix()
            )
        except Exception as e:
            logger.error(f"Image is outside of Drive at {image_path}. Skip logging")
            return {
                "status": "fail",
                "stage": stage,
                "image": Path(image_path).name,
                "error": "Image is outside of Drive",
            }
        file_name = Path(image_path).name

        logger.error(f"Image Processing Pipeline failed at {stage}: {error}")

        self.db.create_or_update(
            table="failure_log",
            data={
                "source_path": relative_path,
                "file_name": file_name,
                "stage": stage,
                "error_type": error.__class__.__name__,
                "error_message": f"Image Processing Pipeline failed at {stage}: {error}",
            },
            conflict_columns="source_path",
            operations={"attempts": "INCREMENT", "last_seen_at": "NOW"},
        )

        return {
            "status": "fail",
            "stage": stage,
            "image": file_name,
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    db = SQLiteConnection()
    db.migrate()
    pipeline = ImageProcessingPipeline()
    result = pipeline.run("/Users/cheng/Documents/Developer/TagPhy/dev/test")
    print(result)
