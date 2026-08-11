import io
import os
from typing import Any

from PIL import Image
from pillow_heif import register_heif_opener

from tagphy import app_root


# set default picture per page
_PAGINATION_DEFAULT_ = 25
register_heif_opener()


class PictureHelper:
    def __init__(self, db: Any, page_size: int = _PAGINATION_DEFAULT_):
        self.page_size = page_size
        self.db = db

    def get_pictures_for_tags_flatted(
        self,
        tag_ids: list[int | list[int]] = [],
        page: int = 1,
        logic: str = "AND",
    ):
        """
        Get all pictures for a list of tags flattened into a single list.

        Args:
            tag_ids: A list of tag IDs (for OR logic), or a list of lists of tag IDs (for AND logic)
            page: The page number
            logic: The logic to use for the query (AND or OR)
        """

        try:
            images_query = f"""
                SELECT DISTINCT i.*
                FROM images i
            """

            if len(tag_ids) > 0:
                if logic == "OR":
                    images_query += f"""
                        JOIN image_tags it ON i.id = it.image_id
                        WHERE it.tag_id IN ({",".join(["?"] * len(tag_ids))})
                    """

                    images_query += f"""
                        ORDER BY i.created_at DESC
                        LIMIT {self.page_size} OFFSET {(page - 1) * self.page_size}
                    """
                    return self.db.query(images_query, [str(id) for id in tag_ids])

                if logic == "AND":
                    images_query += f"""
                        JOIN image_tags it ON i.id = it.image_id
                        WHERE 
                    """

                    condition_query = []
                    for sublist in tag_ids:
                        x = ", ".join(["?" for _ in sublist])
                        per_condition_query = f"EXISTS (SELECT 1 FROM image_tags WHERE image_id = i.id AND tag_id IN ({x}))"
                        condition_query.append(per_condition_query)

                    images_query += " AND ".join(condition_query)
                    images_query += f"""
                        ORDER BY i.created_at DESC
                        LIMIT {self.page_size} OFFSET {(page - 1) * self.page_size}
                    """

                    return self.db.query(
                        images_query, [str(id) for sublist in tag_ids for id in sublist]
                    )

                raise ValueError(
                    "Invalid Tag Selection Logic Type. Must be 'OR' or 'AND' but got {logic}"
                )
            else:
                images_query += f"""
                        ORDER BY i.created_at DESC
                        LIMIT {self.page_size} OFFSET {(page - 1) * self.page_size}
                    """
                return self.db.query(images_query)

        except ValueError as e:
            if "Invalid Tag Selection Logic Type" in str(e):
                raise ValueError(str(e))
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
