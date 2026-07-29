from pathlib import Path
from tagphy.tools import ImageMetadata, ImageStorage, GeminiVisionEngine
from logging import getLogger

logger = getLogger(__name__)


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
        self.workdir = workdir
        self.image_metadata = ImageMetadata()
        self.image_vision = GeminiVisionEngine()

        destination_dir = workdir or (Path.cwd() / "Photo_Tagged")
        self.image_storage = ImageStorage(workdir=destination_dir)

    def run(self, path: str | Path):
        """Run the image processing pipeline on a single image or a directory of images.

        Args:
            path: The path to the image or directory of images to process.
        """
        if Path(path).is_dir():
            return self._run_directory(path)
        return self._run_single(path)

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

    def _run_directory(self, directory_path: str):
        pass

    def _failure(self, image_path: str, stage: str, error: Exception):
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
    pipeline = ImageProcessingPipeline()
    result = pipeline.run("/Users/cheng/Documents/Developer/TagPhy/dev/5.HEIC")
    print(result)
