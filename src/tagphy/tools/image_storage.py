from shutil import move
import os
from typing import Any


class ImageStorage:
    def __init__(self, workdir: str):
        self.workdir = workdir

    def store_image(
        self, image_path: str, metadata: dict[str, str], tags: dict[str, str]
    ) -> dict[str, Any]:
        year = metadata.get("year") or "Unknown"
        location = metadata.get("location", None)

        tags_db = [*tags.values()]

        if metadata.get("location"):
            tags_db.append(location)
        if metadata.get("year"):
            tags_db.append(year)

        destination_folder = os.path.join(self.workdir, year)
        destination_path = os.path.join(
            self.workdir, year, os.path.basename(image_path)
        )

        if os.path.exists(destination_path):
            return {
                "destination_path": destination_path,
                "tags": tags_db,
                "metadata": metadata,
                "error": "File already exists",
            }

        os.makedirs(destination_folder, exist_ok=True)

        try:
            move(image_path, destination_path)
            self._update_db_record(destination_path, tags_db)
            return {
                "destination_path": destination_path,
                "tags": tags_db,
                "metadata": metadata,
            }
        except FileNotFoundError as e:
            self._log_file_move_error(image_path, destination_path, e)
            return {
                "error": e.strerror,
            }
        except Exception as e:
            self._log_file_move_error(image_path, destination_path, e)
            return {
                "error": e.message,
            }

    def _update_db_record(self, destination_path: str, tags: dict[str, str]):
        """Place holder for updating the database record."""
        pass

    def _log_file_move_error(
        self, image_path: str, destination_path: str, error: Exception
    ):
        pass


if __name__ == "__main__":
    image_storage = ImageStorage(
        workdir="/Users/cheng/Documents/Developer/TagPhy/Photo_Tagged"
    )
    result = image_storage.store_image(
        image_path="/Users/cheng/Documents/Developer/TagPhy/dev/4.JPG",
        metadata={
            "year": "2026",
            "location": "Calgary, CA",
        },
        tags={
            "main_tag": "baby",
            "secondary_tag": "infant",
        },
    )
    print(result)
