"""Contract tests for NSFWPreCheck (mocked ONNX, no real weights)."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from tagphy.tools.nsfw_precheck import INPUT_SIZE, NSFWPreCheck, NSFWScreenError


def _write_jpeg(path, size: tuple[int, int] = (32, 32)):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, (128, 128, 128)).save(path, format="JPEG")
    return str(path)


def _checker(tmp_path) -> NSFWPreCheck:
    model = tmp_path / "nsfw.onnx"
    model.write_bytes(b"fake-onnx")
    return NSFWPreCheck(model_path=model)


def _session_with_probs(probs: list[float]) -> MagicMock:
    session = MagicMock()
    input_info = MagicMock()
    input_info.name = "input"
    session.get_inputs.return_value = [input_info]
    session.run.return_value = [np.array([probs], dtype=np.float32)]
    return session


class TestNSFWPreCheckFailClosed:
    def test_missing_model_raises_and_does_not_create_session(self, tmp_path):
        checker = NSFWPreCheck(model_path=tmp_path / "missing.onnx")
        image = _write_jpeg(tmp_path / "photo.jpg")

        with pytest.raises(NSFWScreenError, match="not found"):
            checker.screen(image)

        assert checker._session is None

    def test_unreadable_path_raises(self, tmp_path):
        checker = _checker(tmp_path)

        with pytest.raises(NSFWScreenError, match="Unreadable"):
            checker.screen(str(tmp_path / "missing.jpg"))

        assert checker._session is None


class TestNSFWPreCheckPreprocess:
    def test_tensor_is_nhwc_224_unit_interval(self, tmp_path):
        checker = _checker(tmp_path)
        image = _write_jpeg(tmp_path / "photo.jpg", size=(640, 480))

        tensor = checker._path_to_tensor(image)

        assert tensor.shape == (1, INPUT_SIZE, INPUT_SIZE, 3)
        assert tensor.dtype == np.float32
        assert float(tensor.min()) >= 0.0
        assert float(tensor.max()) <= 1.0


class TestNSFWPreCheckScores:
    def test_uses_raw_probabilities_without_softmax(self):
        checker = NSFWPreCheck(model_path="unused.onnx")
        raw = np.array([[0.05, 0.05, 0.10, 0.70, 0.10]], dtype=np.float32)

        scores = checker._scores(raw)

        assert scores["porn"] == pytest.approx(0.70)
        assert scores["sexy"] == pytest.approx(0.10)


class TestNSFWPreCheckVerdict:
    @patch("tagphy.tools.nsfw_precheck._create_inference_session")
    def test_high_porn_is_blocked(self, mock_session_cls, tmp_path):
        mock_session_cls.return_value = _session_with_probs(
            [0.01, 0.01, 0.02, 0.90, 0.06]
        )
        checker = _checker(tmp_path)
        image = _write_jpeg(tmp_path / "photo.jpg")

        assert checker.screen(image) == "blocked"

    @patch("tagphy.tools.nsfw_precheck._create_inference_session")
    def test_high_sexy_without_porn_is_clear(self, mock_session_cls, tmp_path):
        mock_session_cls.return_value = _session_with_probs(
            [0.02, 0.02, 0.06, 0.10, 0.80]
        )
        checker = _checker(tmp_path)
        image = _write_jpeg(tmp_path / "photo.jpg")

        assert checker.screen(image) == "clear"

    @patch("tagphy.tools.nsfw_precheck._create_inference_session")
    def test_sexy_with_high_porn_hentai_is_blocked(
        self, mock_session_cls, tmp_path
    ):
        mock_session_cls.return_value = _session_with_probs(
            [0.0, 0.40, 0.0, 0.40, 0.50]
        )
        checker = _checker(tmp_path)
        image = _write_jpeg(tmp_path / "photo.jpg")

        assert checker.screen(image) == "blocked"

    @patch("tagphy.tools.nsfw_precheck._create_inference_session")
    def test_high_hentai_is_blocked(self, mock_session_cls, tmp_path):
        mock_session_cls.return_value = _session_with_probs(
            [0.02, 0.90, 0.02, 0.03, 0.03]
        )
        checker = _checker(tmp_path)
        image = _write_jpeg(tmp_path / "photo.jpg")

        assert checker.screen(image) == "blocked"

    @patch("tagphy.tools.nsfw_precheck._create_inference_session")
    def test_high_neutral_is_clear(self, mock_session_cls, tmp_path):
        mock_session_cls.return_value = _session_with_probs(
            [0.02, 0.02, 0.90, 0.03, 0.03]
        )
        checker = _checker(tmp_path)
        image = _write_jpeg(tmp_path / "photo.jpg")

        assert checker.screen(image) == "clear"


class TestNSFWPreCheckLazySession:
    @patch("tagphy.tools.nsfw_precheck._create_inference_session")
    def test_second_screen_reuses_session(self, mock_session_cls, tmp_path):
        mock_session_cls.return_value = _session_with_probs(
            [0.02, 0.02, 0.90, 0.03, 0.03]
        )
        checker = _checker(tmp_path)
        image = _write_jpeg(tmp_path / "photo.jpg")

        assert checker.screen(image) == "clear"
        assert checker.screen(image) == "clear"
        mock_session_cls.assert_called_once()
