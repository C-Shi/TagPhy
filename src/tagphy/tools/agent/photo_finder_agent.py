"""
Catalog tools for the Photo Finder agent:

1. get_all_tags — tag vocabulary for the LLM
2. get_candidate_tags — name → id + descendants
3. get_candidate_photos_ids — pre-filter images by tags
4. rank_photos — embed prompt, cosine rank, return fixed search_results schema
"""

from __future__ import annotations

from typing import Any, Iterable, Literal

import numpy as np

from tagphy.db.connection import SQLiteConnection
from tagphy.tools.db_operations.tag_helper import TagHelper
from tagphy.tools.embedding import TextEmbedding

db = SQLiteConnection()
embedding_model = TextEmbedding()

# Fixed payload when presenting matches (UI: kind == search_results → gallery).
SEARCH_RESULTS_TYPE = "search_results"
RANK_TOOL_NAME = "tool_rank_photos"


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
        Tag ids ready for ``get_candidate_photos_ids``.
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


def get_candidate_photos_ids(
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
        SELECT DISTINCT i.id
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
            dict(row) for row in db.query(images_query, [str(tid) for tid in tag_ids])
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


def rank_photos(description: str, photos_ids: list[int], limit: int = 5) -> dict:
    """Rank candidate photos by cosine similarity to the user description.

    Always returns a fixed envelope for the UI (not free-form LLM text)::

        {
          "type": "search_results",
          "query": "<description used>",
          "items": [
            {"id", "description", "preview_url", "similarity"},
            ...
          ],
        }

    ``preview_url`` is ready for ``<img src=...>`` (same path as Library preview).
    """
    vector_target = embedding_model.embed_text(description)

    scored: list[dict] = []
    for photo_id in photos_ids:
        details = db.select(
            "images",
            ["id", "description", "description_embedding"],
            where={"id": photo_id},
        )
        if not details:
            continue
        row = details[0]
        blob = row["description_embedding"]
        if blob is None:
            continue
        vec = np.frombuffer(blob, dtype=np.float32)
        scored.append(
            {
                "id": row["id"],
                "description": row["description"],
                "preview_url": f"/api/pictures/{row['id']}/preview",
                "similarity": float(np.dot(vec, vector_target)),
            }
        )

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return {
        "type": SEARCH_RESULTS_TYPE,
        "query": description,
        "items": scored[:limit],
    }


def extract_photo_finder_turn(events: Iterable[Any]) -> dict:
    """Classify one Runner turn for UI: gallery payload vs free-text chat.

    Walk ADK events from ``runner.run_async`` (or collect them first). Prefer the
    structured tool result over whatever the model says in prose.

    Returns::

        {
          "kind": "search_results" | "chat",
          "message": str | None,   # clarify / decline / short caption
          "results": dict | None,  # fixed schema when kind == search_results
        }

    UI: if ``kind == "search_results"``, render ``results["items"]`` thumbnails via
    ``preview_url``; still show ``message`` if present. Otherwise show ``message`` only.
    """
    results: dict | None = None
    message: str | None = None

    for event in events:
        get_responses = getattr(event, "get_function_responses", None)
        if callable(get_responses):
            for fr in get_responses() or []:
                name = getattr(fr, "name", None)
                resp = getattr(fr, "response", None)
                if name != RANK_TOOL_NAME or not isinstance(resp, dict):
                    continue
                # Direct tool return, or ADK wrap under "result"
                if resp.get("type") == SEARCH_RESULTS_TYPE:
                    results = resp
                elif isinstance(resp.get("result"), dict) and resp["result"].get(
                    "type"
                ) == SEARCH_RESULTS_TYPE:
                    results = resp["result"]

        is_final = getattr(event, "is_final_response", None)
        content = getattr(event, "content", None)
        if callable(is_final) and is_final() and content is not None:
            for part in getattr(content, "parts", None) or []:
                text = getattr(part, "text", None)
                if text:
                    message = text
                    break

    if results is not None:
        return {"kind": SEARCH_RESULTS_TYPE, "message": message, "results": results}
    return {"kind": "chat", "message": message, "results": None}
