from shutil import move
import os
from pathlib import Path
from typing import Any

from tagphy import app_root


class ImageStorage:
    def __init__(self, workdir: str, db: Any):
        """Initialize the image storage.

        Args:
            workdir: The destination root directory to store the images.
            db: Database connection utility (SQLiteConnection).
        """
        self.workdir = workdir
        self.db = db

    def store_image(
        self, image_path: str, metadata: dict[str, str], tags: dict[str, str]
    ) -> dict[str, Any]:

        # A variable to track the stage of the image storage process. Mainly for catch where the error happens
        stage = "BEGIN"
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

        stage = "CREATE_DESTINATION_FOLDER"
        os.makedirs(destination_folder, exist_ok=True)

        try:
            stage = "DB_WRITE"
            image_id = self._update_db_record(destination_path, metadata, tags_db)
            stage = "FILE_MOVE"
            move(image_path, destination_path)
            stage = "DONE"
            return {
                "destination_path": destination_path,
                "tags": tags_db,
                "metadata": metadata,
            }
        except Exception as e:
            if stage == "FILE_MOVE":
                # IF stage is FILE_MOVE, image_id is guaranteed to be valid
                self.db.delete("images", {"id": image_id})
            raise e

    def _update_db_record(
        self, destination_path: str, metadata: dict[str, str], tags: list[str]
    ):
        """Write image, first-or-create tags, and image_tags join rows."""

        relative_path = (
            Path(destination_path).resolve().relative_to(app_root()).as_posix()
        )
        year = metadata.get("year") or ""

        def insert_record():
            image_id = self.db.insert(
                "images",
                {
                    "file_path": relative_path,
                    "file_name": os.path.basename(destination_path),
                    "year": year,
                    "location": metadata.get("location") or "",
                },
            )
            for tag in dict.fromkeys(tags):
                source = "metadata" if tag == year else "vision"
                tag_id = self.db.first_or_create(
                    "tags",
                    {"name": tag, "source": source},
                    conflict_columns="name",
                )
                self.db.insert(
                    "image_tags",
                    {
                        "image_id": image_id,
                        "tag_id": tag_id,
                        "source": source,
                    },
                )
            # return image_id to the caller to use for the next step
            return image_id

        return self.db.transaction(insert_record)
