from google.genai import types, Client
import io
from PIL import Image
from pillow_heif import register_heif_opener
from dotenv import load_dotenv
from typing import Dict, Any
from abc import ABC, abstractmethod

load_dotenv()


class ImageVision(ABC):
    @abstractmethod
    def tag_image(self, image_path: str) -> Dict[str, Any]:
        pass

    @property
    def system_instruction(self) -> str:
        return """
            You tag photos for a searchable catalog. Return minimum of one, and maximum of three tags, and any needed tag_relations.

            Categories (most → least important). Use at most one tag per category, and at most three tags total:
            1. Subject — what the photo is mainly of
            2. Scene — where / setting
            3. Activity — what is happening
            4. Object — other clear things that are not the main subject
            5. People — social framing (portrait, group, family) only when that is the point; prefer Subject when both fit
            6. Time — lighting or time of day (sunset, night), never calendar values

            Tagging rules:
            - Tag from image content only, not filename or metadata.
            - Always tag the most obvious, significant content (usually Subject).
            - After having at least one tag, optionally add tags from context from other categories; omit if not 99% confident.
            - Prefer the most specific accurate noun (cat over animal).
            - English, one word, singular noun, lowercase — except established proper/tech forms (USA, iPhone, China).
            - Never use calendar values (2026, January, Monday).

            Catalog matching:
            - You will receive existing catalog tag names.
            - If a catalog tag accurately fits, you MUST reuse that exact string.
            - Invent a new tag only when no existing catalog tag fits.
            - Do not invent a near-synonym of a catalog tag when the catalog tag already fits.

            Tag relations (DAG growth):
            - For each returned tag, compare it to the existing catalog list.
            - If it has a clear hierarchical relationship with any catalog tag, add that parent/child pair to tag_relations.
            - Report the relationship even if that edge may already exist in the database.
            - Do not create relations between tags on the same image.
            - If the catalog is empty, or no returned tag relates to any catalog tag, return an empty tag_relations list.

            Example 1 — empty catalog
            Existing catalog tags: (none)
            Image: a cat on a balcony
            Output:
                {
                    "tags": ["cat", "balcony"],
                    "tag_relations": []
                }
            Why: no catalog tags exist, so there is nothing to relate to. Do not add "animal" as an another tag beside "cat".

            Example 2 — reuse catalog and still report relations
            Existing catalog tags: animal, cat, balcony
            Image: a cat on a balcony
            Output:
                {
                    "tags": ["cat", "balcony"],
                    "tag_relations": [
                        {"parent": "animal", "child": "cat"}
                    ]
                }
            Why: returned "cat" relates to catalog "animal", so emit that edge even if it may already exist. Do not put both "cat" and "animal" on the image. "balcony" has no hierarchy link, so no relation row for it.

            Example 3 — new tag linked up and down
            Existing catalog tags: human, father
            Image: a man
            Output:
                {
                    "tags": ["man"],
                    "tag_relations": [
                        {"parent": "human", "child": "man"},
                        {"parent": "man", "child": "father"}
                    ]
                }
            Why: returned "man" relates to existing "human" (parent) and "father" (child).
        """

    def get_image_thumbnail(self, image_path: str) -> bytes:
        with Image.open(image_path) as img:
            rgb = img.convert("RGB")
            rgb.thumbnail((1024, 1024))

            # create a byte buffer to store the image
            buffer = io.BytesIO()
            rgb.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()


class GeminiVisionEngine(ImageVision):
    def __init__(self, db: Any):
        register_heif_opener()
        self.db = db
        self.client = Client(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    initial_delay=1.0,
                    attempts=3,
                    http_status_codes=[408, 429, 500, 502, 503, 504],
                ),
                timeout=120_000,
            ),
        )
        super().__init__()

    def tag_image(self, image_path: str) -> Dict[str, Any]:
        image_buff = self.get_image_thumbnail(image_path)

        existing_tags = self.db.select(
            table="tags",
            columns=["name"],
            where={"source": "vision"},
        )

        tag_instructions = (
            f"Existing tags: {", ".join([tag['name'] for tag in existing_tags])}"
        )

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 3,
                    },
                    "tag_relations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "parent": {"type": "string"},
                                "child": {"type": "string"},
                            },
                            "required": ["parent", "child"],
                        },
                        "minItems": 0,
                        "maxItems": 6,
                    },
                },
                "required": ["tags", "tag_relations"],
            },
            system_instruction=self.system_instruction,
        )
        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[
                types.Part.from_bytes(data=image_buff, mime_type="image/jpeg"),
                types.Part.from_text(text=tag_instructions),
            ],
            config=config,
        )

        return response.parsed


if __name__ == "__main__":
    from tagphy.db import SQLiteConnection

    engine = GeminiVisionEngine(db=SQLiteConnection())
    response = engine.tag_image("/Users/cheng/Documents/Developer/TagPhy/dev/4.JPG")
    print(response)
