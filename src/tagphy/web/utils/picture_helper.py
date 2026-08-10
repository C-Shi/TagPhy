import io
import os
from typing import Any

from PIL import Image

from tagphy import app_root


# set default picture per page
_PAGINATION_DEFAULT_ = 25


class PictureHelper:
    def __init__(self, db: Any, page_size: int = _PAGINATION_DEFAULT_):
        self.page_size = page_size
        self.db = db

    def get_pictures_for_tags_flatted(self, tag_ids: list[int] = [], page: int = 1):
        """Get all pictures for a list of tags flattened into a single list."""

        try:
            images_query = f"""
                SELECT i.*
                FROM images i
            """

            if len(tag_ids) > 0:
                images_query += f"""
                    JOIN image_tags it ON i.id = it.image_id
                    WHERE it.tag_id IN ({",".join(["?"] * len(tag_ids))})
                """

            images_query += f"""
                ORDER BY i.id DESC
                LIMIT {self.page_size} OFFSET {(page - 1) * self.page_size}
            """

            return self.db.query(images_query, [str(id) for id in tag_ids])
        except ValueError as e:
            raise ValueError(f"Invalid Tags")

    def get_picture_preview(self, picture_id: int) -> tuple[bytes, str]:

        try:
            picture = self.db.select(
                "images", ["file_name", "file_path"], {"id": picture_id}
            )[0]

            image_path = os.path.join(app_root(), picture["file_path"])

            with Image.open(image_path) as img:
                rgb = img.convert("RGB")
                rgb.thumbnail((320, 320))

                # create a byte buffer to store the image
                buffer = io.BytesIO()
                rgb.save(buffer, format="JPEG", quality=85)
                alt = picture["file_name"]
            return (buffer.getvalue(), alt)
        except Exception as e:
            raise Exception(f"Failed to get picture preview: {e}")
