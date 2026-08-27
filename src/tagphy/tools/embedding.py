from pathlib import Path
import numpy as np
from tagphy import app_root
from tokenizers import Tokenizer


class TextEmbedding:
    def __init__(self):
        self.model_dir = app_root() / "models" / "all-MiniLM-L6-v2-onnx"
        self._session = None

    def embed_text(self, text: str) -> np.ndarray:
        tok = Tokenizer.from_file(str(self.model_dir / "tokenizer.json"))
        tok.enable_truncation(max_length=256)
        tok.enable_padding(length=256)  # or pad to batch max

        encoded = tok.encode(text)
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        token_type_ids = np.zeros_like(input_ids, dtype=np.int64)
        ort_inputs = {
            "input_ids": input_ids.astype(np.int64),
            "attention_mask": attention_mask.astype(np.int64),
            "token_type_ids": token_type_ids.astype(np.int64),
        }
        out = self._get_session().run(None, ort_inputs)[0]
        # already pooled (+ often already normalized)
        mask = attention_mask.astype(np.float32)[..., None]  # (1, seq, 1)
        summed = (out * mask).sum(axis=1)  # (1, 384)
        counts = np.clip(mask.sum(axis=1), 1e-9, None)
        vec = (summed / counts)[0]  # (384,)
        vec = vec / np.linalg.norm(vec)
        n = np.linalg.norm(vec)
        if n > 0:
            vec = vec / n
        return vec

    def _get_session(self):
        if self._session is not None:
            return self._session
        self._session = _create_inference_session(self.model_dir / "model.onnx")
        return self._session


def _create_inference_session(model_path: Path):
    """Load an ONNX CPU session. Imported lazily so tests need not load the native lib."""
    import onnxruntime as ort

    return ort.InferenceSession(
        str(model_path),
        providers=["CPUExecutionProvider"],
    )


if __name__ == "__main__":
    embedding = TextEmbedding()
    a = embedding.embed_text("An orange cat playing a toy in a room")
    b = embedding.embed_text("A cat in my living room floor")
    c = embedding.embed_text("how are you")
    print(a @ b)  # should be clearly higher
    print(a @ c)  # should be clearly lower
