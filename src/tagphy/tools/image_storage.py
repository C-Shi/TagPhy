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

        self.db.transaction(insert_record)

    def _log_file_move_error(
        self, image_path: str, destination_path: str, error: Exception
    ):
        pass
