"""In-process CPU NSFW / intimate pre-check. Not a tagging engine."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image
from pillow_heif import register_heif_opener

from tagphy import app_root

register_heif_opener()

INPUT_SIZE = 224
LABELS = ("drawings", "hentai", "neutral", "porn", "sexy")
DEFAULT_MODEL_NAME = "nsfw_mobilenet2_224x224.onnx"


class NSFWScreenError(Exception):
    """Raised when the NSFW pre-check cannot complete (fail closed)."""


class NSFWPreCheck:
    def __init__(self, model_path: str | Path | None = None):
        self.model_path = (
            Path(model_path)
            if model_path
            else app_root() / "models" / DEFAULT_MODEL_NAME
        )
        self._session = None

    def screen(self, image_path: str) -> Literal["clear", "blocked"]:
        """Classify an image file. Matches GantMan predict.py preprocessing."""
        tensor = self._path_to_tensor(image_path)
        session = self._get_session()
        try:
            input_name = session.get_inputs()[0].name
            outputs = session.run(None, {input_name: tensor})
        except Exception as e:
            raise NSFWScreenError(f"ONNX inference failed: {e}") from e
        scores = self._scores(outputs[0])
        return self._rule(scores)

    def _rule(self, scores: dict[str, float]) -> Literal["clear", "blocked"]:
        category = max(scores, key=scores.get)
        # If highest score is porn or hentai, return blocked
        if category == "porn" or category == "hentai":
            return "blocked"
        # If highest score is neutral or drawings, return clear
        if category == "neutral" or category == "drawings":
            return "clear"
        # If highest score is sexy, check porn + hentai score
        if category == "sexy":
            porn_score = scores["porn"]
            hentai_score = scores["hentai"]
            drawings_score = scores["drawings"]
            neutral_score = scores["neutral"]
            sexy_score = scores["sexy"]

            if sexy_score > 0.85:
                # very confident sexy, not porn or hentai
                return "clear"
            if porn_score + hentai_score > drawings_score + neutral_score:
                return "blocked"
        return "clear"

    def _get_session(self):
        if self._session is not None:
            return self._session
        if not self.model_path.is_file():
            raise NSFWScreenError(f"NSFW model not found: {self.model_path}")
        try:
            self._session = _create_inference_session(self.model_path)
        except NSFWScreenError:
            raise
        except Exception as e:
            raise NSFWScreenError(f"Failed to load NSFW model: {e}") from e
        return self._session

    def _path_to_tensor(self, image_path: str) -> np.ndarray:
        """Keras load_img(path, target_size=(224, 224)) then img_to_array / 255.

        Stretch resize with nearest-neighbor (tf.keras default interpolation).
        NHWC float32 in [0, 1], batch dim added.
        """
        try:
            with Image.open(image_path) as img:
                rgb = img.convert("RGB").resize(
                    (INPUT_SIZE, INPUT_SIZE),
                    resample=Image.Resampling.NEAREST,
                )
                array = np.asarray(rgb, dtype=np.float32) / 255.0
        except Exception as e:
            raise NSFWScreenError(f"Unreadable image: {e}") from e
        return array[np.newaxis, ...]

    def _scores(self, raw: np.ndarray) -> dict[str, float]:
        """Map ONNX output to labels. GantMan already emits class probabilities."""
        vector = np.asarray(raw, dtype=np.float32).reshape(-1)
        if vector.size != len(LABELS):
            raise NSFWScreenError(f"Unexpected NSFW model output size: {vector.size}")
        return {label: float(vector[i]) for i, label in enumerate(LABELS)}


def _create_inference_session(model_path: Path):
    """Load an ONNX CPU session. Imported lazily so tests need not load the native lib."""
    import onnxruntime as ort

    return ort.InferenceSession(
        str(model_path),
        providers=["CPUExecutionProvider"],
    )


if __name__ == "__main__":
    nsfw_precheck = NSFWPreCheck()
    print(
        nsfw_precheck.screen(
            "/Users/cheng/Documents/Developer/TagPhy/dev/sexy_personal.jpeg"
        )
    )
