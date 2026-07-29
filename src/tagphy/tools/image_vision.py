from google.genai import types, Client
import io
from PIL import Image
from pillow_heif import register_heif_opener
from dotenv import load_dotenv
from typing import Dict
from abc import ABC, abstractmethod

load_dotenv()


class ImageVision(ABC):
    @abstractmethod
    def tagging_image(self, image_path: str) -> Dict[str, str]:
        pass


class GeminiVisionEngine(ImageVision):
    def __init__(self):
        register_heif_opener()
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

    def _get_image_thumbnail(self, image_path: str) -> bytes:
        with Image.open(image_path) as img:
            rgb = img.convert("RGB")
            rgb.thumbnail((1024, 1024))

            # create a byte buffer to store the image
            buffer = io.BytesIO()
            rgb.save(buffer, format="JPEG", quality=85)
            return buffer.getvalue()

    def tagging_image(self, image_path: str) -> Dict[str, str]:
        image_buff = self._get_image_thumbnail(image_path)

        system_instruction = """
            You are a helpful assistant that tags images with a main tag and a secondary tag.
            The main tag is the most important tag for the image.
            The secondary tag is a secondary tag for the image.
            The tags will eventually be used to categories and classify images

            Rules:
            - You always tag the image based on content, not file name or meta data
            - The tag should be specific enough to identify and associate the image with the correct content (eg: cat or pet, rather than just animal)
            - The tag should be generic enough so that it can be used to group similar images together (eg: cat or pet, rather than Ragdoll or Siamese)
            - Only tag if you are 99% confient about the content. Do not invent or guess the content. If you are not sure, do not tag.
            - The tag should be in English, one word, singlar noun and lowercase.
            - Each tag should be unique and not overlap with each other (eg: do not tag both "cat" and "animal")

            Tie Breaker:
            - If there are multiple tags that are equally valid, choose one that is more close to a human lifestyle (eg: "cat" is more likely than "animal")

            Exception:
            - If the word belongs to Acrynon, or specialized words that natually present as Capitalized, do not force it to lowercase. (eg: USA, iPhone, China)
            - Do not use Time or Date in the tag (eg: no 2026, July, etc)
        """

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "object",
                "properties": {
                    "main_tag": {"type": "string"},
                    "secondary_tag": {"type": "string"},
                },
                "required": ["main_tag", "secondary_tag"],
            },
            system_instruction=system_instruction,
        )
        response = self.client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[types.Part.from_bytes(data=image_buff, mime_type="image/jpeg")],
            config=config,
        )

        return response.parsed


if __name__ == "__main__":
    engine = GeminiVisionEngine()
    response = engine.tagging_image(
        "/Users/cheng/Documents/Developer/TagPhy/dev/5.HEIC"
    )
    print(response)
