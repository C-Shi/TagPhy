from typing import Any


class TagHelper:
    def __init__(self, db: Any):
        self.db = db

    def get_tags_with_details(self):
        """Get all tags with their details."""

        base_query = """
        SELECT t.id, t.name, t.source, count(t.id) as photo_count
        FROM tags t LEFT JOIN image_tags it ON t.id = it.tag_id
        GROUP BY t.id
        """
        tags = self.db.query(base_query)
        tags = [dict(tag) for tag in tags]

        children_query = """
        SELECT t.id, t.name FROM tag_edges te 
        JOIN tags t ON te.child_id = t.id WHERE te.parent_id = ?
        """

        for tag in tags:
            children = self.db.query(children_query, (tag["id"],))
            tag["children"] = list(children)
        return tags
