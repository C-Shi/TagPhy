from shutil import move
import os
from typing import Any


class ImageStorage:
    def __init__(self, workdir: str, db: Any):
        """Initialize the image storage.

        Args:
            workdir: The destination root directory to store the images.
        """
        self.workdir = workdir
        self.db = db

    def store_image(
        self, image_path: str, metadata: dict[str, str], tags: dict[str, str]
    ) -> dict[str, Any]:
        year = metadata.get("year") or "Unknown"

        tags_db = [*tags.values()]

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
                # If duplicate file is found, return a warning only
                "warning": "File already exists. No action taken",
            }

        os.makedirs(destination_folder, exist_ok=True)

        try:
            self._update_db_record(destination_path, metadata, tags_db)
            move(image_path, destination_path)
            return {
                "destination_path": destination_path,
                "tags": tags_db,
                "metadata": metadata,
            }
        except Exception as e:
            self._log_file_move_error(image_path, destination_path, e)
            raise e

    def _update_db_record(
        self, destination_path: str, metadata: dict[str, str], tags: list[str]
    ):
        """Place holder for updating the database record."""

        def insert_record():
            # Write to image table
            self.db.insert(
                "images",
                {
                    "file_path": destination_path,
                    "file_name": os.path.basename(destination_path),
                    "year": metadata.get("year") or "",
                    "location": metadata.get("location") or "",
                },
            )
            # Write to tag table
            year = metadata.get("year")
            for tag in tags:
                self.db.insert(
                    "tags",
                    {
                        "name": tag,
                        "source": "metadata" if year == tag else "vision",
                    },
                )

        self.db.transaction(insert_record)

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
