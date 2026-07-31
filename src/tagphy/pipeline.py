import logging, os, time
from logging import getLogger
from pathlib import Path

from PIL import Image
from tagphy import app_root
from tagphy.tools import GeminiVisionEngine, ImageMetadata, ImageStorage

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
        self.workdir = Path(workdir or (app_root() / DEFAULT_OUTPUT_DIR_NAME)).resolve()
        self.image_metadata = ImageMetadata()
        self.image_vision = GeminiVisionEngine()
        self.image_storage = ImageStorage(workdir=str(self.workdir))

    def run(self, path: str | Path):
        """Run the image processing pipeline on a single image or a directory of images.

        Args:
            path: The path to the image or directory of images to process.
        """
        target = Path(path).resolve()
        output_key = os.path.normcase(str(self.workdir))
        target_key = os.path.normcase(str(target))

        if target_key == output_key or target_key.startswith(output_key + os.sep):
            return self._failure(
                path,
                "validate_path",
                ValueError("Target is the output directory or inside it"),
            )

        if target.is_dir():
            return self._run_directory(target)
        return self._run_single(str(path))

    def _run_single(self, image_path: str):
        """Run the image processing pipeline on single image.

        Args:
            image_path: The path to the image to process.
        """

        try:
            metadata = self.image_metadata.extract_metadata(image_path)
        except Exception as e:
            return self._failure(image_path, "extract_metadata", e)
        try:
            tags = self.image_vision.tag_image(image_path)
        except Exception as e:
            return self._failure(image_path, "tag_image", e)
        try:
            return self.image_storage.store_image(image_path, metadata, tags)
        except Exception as e:
            return self._failure(image_path, "store_image", e)

    def _run_directory(self, directory_path: str | Path):
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

        def process_batch(paths: list[Path]) -> None:
            for image_path in paths:
                counts["total"] += 1
                logger.info(
                    "Processing image %s: %s",
                    counts["total"],
                    image_path.name,
                )
                try:
                    result = self._run_single(str(image_path))
                except Exception as e:
                    logger.error(
                        "Image Processing Pipeline unexpected error "
                        f"on {image_path}: {e}"
                    )
                    counts["failed"] += 1
                    continue

                if isinstance(result, dict) and result.get("success") == "fail":
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

        if batch:
            process_batch(batch)

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
        return counts

    def _failure(self, image_path: str | Path, stage: str, error: Exception):
        """Handle the failure of a stage.

        Args:
            stage: The stage that failed.
            error: The error that occurred.
        """

        file_name = Path(image_path).name

        logger.error(f"Image Processing Pipeline failed at {stage}: {error}")

        return {
            "success": "fail",
            "stage": stage,
            "image": file_name,
        }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    pipeline = ImageProcessingPipeline()
    result = pipeline.run("/Users/cheng/Documents/Developer/TagPhy/dev")
    print(result)
