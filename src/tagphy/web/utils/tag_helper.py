from typing import Any


class TagHelper:
    def __init__(self, db: Any):
        self.db = db

    def get_tags_with_details(self):
        """Get all tags with their details."""

        # get image info and direct image count
        base_query = """
        SELECT t.id, t.name, t.source, count(it.image_id) as photo_count
        FROM tags t LEFT JOIN image_tags it ON t.id = it.tag_id
        GROUP BY t.id
        """
        tags = self.db.query(base_query)
        tags = [dict(tag) for tag in tags]

        children_query = """
            WITH RECURSIVE descendants(id) AS (
                SELECT e.child_id
                FROM tag_edges e
                WHERE e.parent_id = ?
                UNION
                SELECT e.child_id
                FROM tag_edges e
                JOIN descendants d ON e.parent_id = d.id
            )
            SELECT t.id, t.name
            FROM descendants d
            JOIN tags t ON t.id = d.id;
        """

        parents_query = """
            WITH RECURSIVE ancestors(id) AS (
                SELECT e.parent_id
                FROM tag_edges e
                WHERE e.child_id = ?
                UNION
                SELECT e.parent_id
                FROM tag_edges e
                JOIN ancestors a ON e.child_id = a.id
            )
            SELECT t.id, t.name
            FROM ancestors a
            JOIN tags t ON t.id = a.id;
        """

        for tag in tags:
            children = self.db.query(children_query, (tag["id"],))
            tag["children"] = [dict(child) for child in children]
            parents = self.db.query(parents_query, (tag["id"],))
            tag["parents"] = [dict(parent) for parent in parents]

            # get all descendants image count
            if len(tag["children"]) > 0:
                descendant_ids = [child["id"] for child in tag["children"]]
                child_image_count = self.db.query(
                    f"SELECT count(image_id) as child_count FROM image_tags WHERE tag_id IN ({",".join(["?"] * len(descendant_ids))})",
                    [str(id) for id in descendant_ids],
                )
                tag["photo_count"] += child_image_count[0]["child_count"]

        return tags

    def get_tag_pictures(self, tag_id: int):
        """Get all pictures for a tag."""

        if not tag_id or not isinstance(tag_id, int) or tag_id <= 0:
            raise ValueError("Bad Request: Invalid Tag")

        # get tag info
        tag_info = self.db.query(
            "SELECT id, name, source FROM tags WHERE id = ?", (tag_id,)
        )
        if not tag_info:
            raise ValueError("Bad Request: Invalid Tag")
        tag_pictures_response = dict(tag_info[0])

        # get all descendants tags
        children_query = """
            WITH RECURSIVE descendants(id) AS (
                SELECT e.child_id
                FROM tag_edges e
                WHERE e.parent_id = ?
                UNION
                SELECT e.child_id
                FROM tag_edges e
                JOIN descendants d ON e.parent_id = d.id
            )
            SELECT t.id, t.name
            FROM descendants d
            JOIN tags t ON t.id = d.id;
        """
        children = self.db.query(children_query, (tag_id,))
        tag_pictures_response["children"] = [dict(child) for child in children]

        # get all parent tags
        parents_query = """
            WITH RECURSIVE ancestors(id) AS (
                SELECT e.parent_id
                FROM tag_edges e
                WHERE e.child_id = ?
                UNION
                SELECT e.parent_id
                FROM tag_edges e
                JOIN ancestors a ON e.child_id = a.id
            )
            SELECT t.id, t.name
            FROM ancestors a
            JOIN tags t ON t.id = a.id;
        """
        parents = self.db.query(parents_query, (tag_id,))
        tag_pictures_response["parents"] = [dict(parent) for parent in parents]

        # get all direct and indirect images

        image_tag_ids = [child["id"] for child in tag_pictures_response["children"]]
        image_tag_ids.append(tag_id)

        images_query = f"""
            SELECT *
            FROM images i
            JOIN image_tags it ON i.id = it.image_id
            WHERE it.tag_id IN ({",".join(["?"] * len(image_tag_ids))})
        """
        images = self.db.query(images_query, [str(id) for id in image_tag_ids])
        tag_pictures_response["pictures"] = [dict(image) for image in images]

        return tag_pictures_response
