"""
This module contains the logic for finding photos based on the prompt. Photo Finder Agent will use it to:

- Get possible tags from the prompt
"""

from typing import Literal
import numpy as np
from tagphy.db.connection import SQLiteConnection
from tagphy.tools import TextEmbedding
from tagphy.tools.db_operations.tag_helper import TagHelper
from tagphy.tools.db_operations.picture_helper import PictureHelper
from tagphy.tools.embedding import TextEmbedding

db = SQLiteConnection()
embedding_model = TextEmbedding()


def get_all_tags() -> list[str]:
    """Get all tags from the database."""
    return db.select("tags", ["id", "name"])


def get_candidate_tags(
    tag_names: list[str], logic: Literal["AND", "OR"] = "OR"
) -> list[str]:
    """Get possible tags from the tag names.

    Args:
        tag_names: A list of unique, non-related tags that was extracted from prompt

    Returns:
        A list of possible tags.
    """

    tag_list = []

    tag_helper = TagHelper(db)

    for tag_name in tag_names:
        sublist = tag_helper.get_descendants_tags(tag_name)
        if logic == "OR":
            tag_list.extend(sublist)
        elif logic == "AND":
            tag_list.extend([sublist])

    tag_list = list(set(tag_list))

    return tag_list


def get_candidate_photos(
    tag_ids: list[int | list[int]] = [], logic: Literal["AND", "OR"] = "OR"
) -> list[dict]:
    """
    Get all pictures for a list of tags. This method will query for tag_ids passed ONLY. To include children tags, call recursive tag retrieval before passing in tag_ids

    Args:
        tag_ids: A list of tag IDs (for OR logic), or a list of lists of tag IDs (for AND logic)
        logic: The logic to use for the query (AND or OR)
    """

    try:
        images_query = f"""
            SELECT DISTINCT i.id, i.description_embedding
            FROM images i
        """

        if len(tag_ids) > 0:
            if logic == "OR":
                images_query += f"""
                    JOIN image_tags it ON i.id = it.image_id
                    WHERE it.tag_id IN ({",".join(["?"] * len(tag_ids))})
                """
                return db.query(images_query, [str(id) for id in tag_ids])

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
                return db.query(
                    images_query, [str(id) for sublist in tag_ids for id in sublist]
                )
        else:
            images_query += "ORDER BY i.created_at DESC"
            return db.query(images_query)

    except ValueError as e:
        if "Invalid Tag Selection Logic Type" in str(e):
            raise ValueError(str(e))
        raise ValueError(f"Invalid Tags")


def rank_photos(description: str, photos: list[str], limit: int = 5) -> list[dict]:
    """Rank photos based on the description and tags."""

    vectors_generator = (
        {
            "id": photo["id"],
            "vector": np.frombuffer(photo["description_embedding"], dtype=np.float32),
        }
        for photo in photos
    )

    vector_target = embedding_model.embed_text(description)

    similarity_generator = (
        {"id": vector["id"], "similarity": np.dot(vector["vector"], vector_target)}
        for vector in vectors_generator
    )

    return sorted(similarity_generator, key=lambda x: x["similarity"], reverse=True)[
        :limit
    ]


if __name__ == "__main__":
    photos = get_candidate_photos()

    ranked_photos = rank_photos(
        "My wife hold our son while sitting on a brown sofa.",
        photos,
    )
    print(ranked_photos)
