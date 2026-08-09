from typing import Any

# set default picture per page
_PAGINATION_DEFAULT_ = 25


class PictureHelper:
    def __init__(self, db: Any, page_size: int = _PAGINATION_DEFAULT_):
        self.page_size = page_size
        self.db = db

    def get_pictures_for_tags_flatted(self, tag_ids: list[int], page: int = 1):
        """Get all pictures for a list of tags flattened into a single list."""

        try:
            images_query = f"""
                SELECT i.*
                FROM images i
                JOIN image_tags it ON i.id = it.image_id
                WHERE it.tag_id IN ({",".join(["?"] * len(tag_ids))})
                ORDER BY i.id DESC
                LIMIT {self.page_size} OFFSET {(page - 1) * self.page_size}
            """
            return self.db.query(images_query, [str(id) for id in tag_ids])
        except ValueError as e:
            raise ValueError(f"Invalid Tags")
