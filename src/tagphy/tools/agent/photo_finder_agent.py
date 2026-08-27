"""
Catalog tools for the Photo Finder agent:

1. get_all_tags — tag vocabulary for the LLM
2. get_candidate_tags — name → id + descendants
3. get_candidate_photos — pre-filter images by tags
4. rank_photos — embed prompt, cosine rank, return preview refs
"""

from typing import Literal

import numpy as np

from tagphy.db.connection import SQLiteConnection
from tagphy.tools.db_operations.tag_helper import TagHelper
from tagphy.tools.embedding import TextEmbedding

db = SQLiteConnection()
embedding_model = TextEmbedding()


def get_all_tags() -> list[dict]:
    """Get all tags from the database (id + name for the LLM)."""
    return [dict(row) for row in db.query("SELECT id, name FROM tags ORDER BY name")]


def get_candidate_tags(
    tag_names: list[str], logic: Literal["AND", "OR"] = "OR"
) -> list[int] | list[list[int]]:
    """Expand LLM-picked tag names to seed ids + descendant ids.

    Args:
        tag_names: Catalog tag names extracted from the prompt.
        logic: ``OR`` → flat ``list[int]`` (duplicates OK for SQL IN).
               ``AND`` → ``list[list[int]]`` (one group per seed).

    Returns:
        Tag ids ready for ``get_candidate_photos``.
    """
    seed_ids: list[int] = []
    for tag_name in tag_names:
        rows = db.select("tags", ["id"], where={"name": tag_name})
        if rows:
            seed_ids.append(int(rows[0]["id"]))

    tag_helper = TagHelper(db)

    if logic == "AND":
        groups: list[list[int]] = []
        for tag_id in seed_ids:
            child_ids = [
                int(child["id"]) for child in tag_helper.get_descendants_tags(tag_id)
            ]
            groups.append([tag_id, *child_ids])
        return groups

    tag_ids: list[int] = list(seed_ids)
    for tag_id in seed_ids:
        tag_ids.extend(
            int(child["id"]) for child in tag_helper.get_descendants_tags(tag_id)
        )
    return tag_ids


def get_candidate_photos(
    tag_ids: list[int] | list[list[int]] | None = None,
    logic: Literal["AND", "OR"] = "OR",
) -> list[dict]:
    """Pre-filter images by tag ids (call get_candidate_tags first for DAG expand).

    Args:
        tag_ids: Flat ids for OR, or list-of-lists for AND. Empty/None → all images.
        logic: AND or OR across tag groups.
    """
    if tag_ids is None:
        tag_ids = []

    images_query = """
        SELECT DISTINCT i.id, i.description, i.description_embedding
        FROM images i
    """

    if len(tag_ids) == 0:
        images_query += " ORDER BY i.created_at DESC"
        return [dict(row) for row in db.query(images_query)]

    if logic == "OR":
        images_query += f"""
            JOIN image_tags it ON i.id = it.image_id
            WHERE it.tag_id IN ({",".join(["?"] * len(tag_ids))})
        """
        return [
            dict(row)
            for row in db.query(images_query, [str(tid) for tid in tag_ids])
        ]

    if logic == "AND":
        images_query += """
            JOIN image_tags it ON i.id = it.image_id
            WHERE 
        """
        condition_query = []
        for sublist in tag_ids:
            x = ", ".join(["?" for _ in sublist])
            condition_query.append(
                f"EXISTS (SELECT 1 FROM image_tags WHERE image_id = i.id AND tag_id IN ({x}))"
            )
        images_query += " AND ".join(condition_query)
        return [
            dict(row)
            for row in db.query(
                images_query, [str(tid) for sublist in tag_ids for tid in sublist]
            )
        ]

    raise ValueError(
        f"Invalid Tag Selection Logic Type. Must be 'OR' or 'AND' but got {logic}"
    )


def rank_photos(
    description: str, photos: list[dict], limit: int = 5
) -> list[dict]:
    """Rank candidate photos by cosine similarity to the user description.

    Returns top ``limit`` items with id, description, preview_url, similarity.
    """
    vector_target = embedding_model.embed_text(description)

    scored: list[dict] = []
    for photo in photos:
        blob = photo.get("description_embedding")
        if blob is None:
            continue
        vec = np.frombuffer(blob, dtype=np.float32)
        scored.append(
            {
                "id": photo["id"],
                "description": photo.get("description") or "",
                "preview_url": f"/api/pictures/{photo['id']}/preview",
                "similarity": float(np.dot(vec, vector_target)),
            }
        )

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:limit]
