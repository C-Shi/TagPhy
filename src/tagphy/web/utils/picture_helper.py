from typing import Any


class PictureHelper:
    def __init__(self, db: Any):
        self.db = db

    def get_pictures_for_tag(self, tag_id: int):
        """Get all pictures for a tag."""
        try:

            images_query = f"""
                SELECT i.*
                FROM images i
                JOIN image_tags it ON i.id = it.image_id
                WHERE it.tag_id = ?)
            """
            return self.db.query(images_query, (str(tag_id),))
        except ValueError as e:
            raise ValueError(f"Invalid Tag")

    def get_pictures_for_tags_flatted(self, tag_ids: list[int]):
        """Get all pictures for a list of tags flattened into a single list."""

        try:
            images_query = f"""
                SELECT i.*
                FROM images i
                JOIN image_tags it ON i.id = it.image_id
                WHERE it.tag_id IN ({",".join(["?"] * len(tag_ids))})
            """
            return self.db.query(images_query, [str(id) for id in tag_ids])
        except ValueError as e:
            raise ValueError(f"Invalid Tags")
