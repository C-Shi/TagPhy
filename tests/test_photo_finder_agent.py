"""Unit tests for Photo Finder catalog tools (mocked db + embedding — no ONNX/SQLite)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tagphy.tools.agent import photo_finder_agent as pfa


def _vec(*vals: float) -> bytes:
    return np.asarray(vals, dtype=np.float32).tobytes()


def _normalize_sql(query: str) -> str:
    return " ".join(str(query).split()).lower()


class TestGetAllTags:
    def test_returns_id_and_name_rows(self):
        mock_db = MagicMock()
        mock_db.query.return_value = [
            {"id": 1, "name": "cat"},
            {"id": 2, "name": "sofa"},
        ]
        with patch.object(pfa, "db", mock_db):
            result = pfa.get_all_tags()

        assert result == [{"id": 1, "name": "cat"}, {"id": 2, "name": "sofa"}]
        sql = _normalize_sql(mock_db.query.call_args[0][0])
        assert "from tags" in sql


class TestGetCandidateTags:
    def test_or_includes_seed_and_descendant_ids(self):
        mock_db = MagicMock()
        mock_db.select.side_effect = [
            [{"id": 10}],  # cat
            [{"id": 20}],  # sofa
        ]
        mock_helper = MagicMock()
        mock_helper.get_descendants_tags.side_effect = [
            [{"id": 11, "name": "kitten"}],
            [{"id": 21, "name": "couch"}],
        ]

        with (
            patch.object(pfa, "db", mock_db),
            patch.object(pfa, "TagHelper", return_value=mock_helper),
        ):
            result = pfa.get_candidate_tags(["cat", "sofa"], logic="OR")

        assert result == [10, 20, 11, 21]
        mock_helper.get_descendants_tags.assert_any_call(10)
        mock_helper.get_descendants_tags.assert_any_call(20)

    def test_and_returns_one_group_per_seed(self):
        mock_db = MagicMock()
        mock_db.select.side_effect = [
            [{"id": 10}],
            [{"id": 20}],
        ]
        mock_helper = MagicMock()
        mock_helper.get_descendants_tags.side_effect = [
            [{"id": 11, "name": "kitten"}],
            [],
        ]

        with (
            patch.object(pfa, "db", mock_db),
            patch.object(pfa, "TagHelper", return_value=mock_helper),
        ):
            result = pfa.get_candidate_tags(["cat", "sofa"], logic="AND")

        assert result == [[10, 11], [20]]

    def test_skips_unknown_tag_names(self):
        mock_db = MagicMock()
        mock_db.select.side_effect = [
            [{"id": 10}],
            [],  # unknown
        ]
        mock_helper = MagicMock()
        mock_helper.get_descendants_tags.return_value = []

        with (
            patch.object(pfa, "db", mock_db),
            patch.object(pfa, "TagHelper", return_value=mock_helper),
        ):
            result = pfa.get_candidate_tags(["cat", "not-a-tag"], logic="OR")

        assert result == [10]
        mock_helper.get_descendants_tags.assert_called_once_with(10)


class TestGetCandidatePhotos:
    def test_or_filters_by_tag_ids(self):
        mock_db = MagicMock()
        mock_db.query.return_value = [
            {"id": 101, "description": "A cat", "description_embedding": _vec(1, 0)},
        ]

        with patch.object(pfa, "db", mock_db):
            result = pfa.get_candidate_photos([10, 11], logic="OR")

        assert len(result) == 1
        assert result[0]["id"] == 101
        assert "description" in result[0]
        sql = _normalize_sql(mock_db.query.call_args[0][0])
        assert "tag_id in" in sql
        assert "description_embedding" in sql
        assert mock_db.query.call_args[0][1] == ["10", "11"]

    def test_and_uses_exists_per_group(self):
        mock_db = MagicMock()
        mock_db.query.return_value = []

        with patch.object(pfa, "db", mock_db):
            pfa.get_candidate_photos([[10, 11], [20]], logic="AND")

        sql = _normalize_sql(mock_db.query.call_args[0][0])
        assert sql.count("exists") == 2
        assert mock_db.query.call_args[0][1] == ["10", "11", "20"]

    def test_empty_tag_ids_returns_all(self):
        mock_db = MagicMock()
        mock_db.query.return_value = [
            {"id": 1, "description": "x", "description_embedding": _vec(0, 1)},
        ]

        with patch.object(pfa, "db", mock_db):
            result = pfa.get_candidate_photos([], logic="OR")

        assert len(result) == 1
        sql = _normalize_sql(mock_db.query.call_args[0][0])
        assert "order by i.created_at desc" in sql
        assert "tag_id" not in sql

    def test_invalid_logic_raises(self):
        with patch.object(pfa, "db", MagicMock()):
            with pytest.raises(ValueError, match="Invalid Tag Selection Logic Type"):
                pfa.get_candidate_photos([1], logic="XOR")  # type: ignore[arg-type]


class TestRankPhotos:
    def test_orders_by_similarity_and_adds_preview_url(self):
        # target embedding ≈ [1, 0] → photo A closer than B
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = np.array([1.0, 0.0], dtype=np.float32)

        photos = [
            {
                "id": 2,
                "description": "A red car",
                "description_embedding": _vec(0.0, 1.0),
            },
            {
                "id": 1,
                "description": "An orange cat on a sofa",
                "description_embedding": _vec(1.0, 0.0),
            },
        ]

        with patch.object(pfa, "embedding_model", mock_embed):
            result = pfa.rank_photos("a cat on the couch", photos, limit=5)

        assert [r["id"] for r in result] == [1, 2]
        assert result[0]["description"] == "An orange cat on a sofa"
        assert result[0]["preview_url"] == "/api/pictures/1/preview"
        assert result[1]["preview_url"] == "/api/pictures/2/preview"
        assert result[0]["similarity"] > result[1]["similarity"]
        mock_embed.embed_text.assert_called_once_with("a cat on the couch")

    def test_respects_limit(self):
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = np.array([1.0, 0.0], dtype=np.float32)
        photos = [
            {"id": i, "description": f"d{i}", "description_embedding": _vec(1.0, 0.0)}
            for i in range(10)
        ]

        with patch.object(pfa, "embedding_model", mock_embed):
            result = pfa.rank_photos("x", photos, limit=3)

        assert len(result) == 3

    def test_skips_missing_embedding(self):
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = np.array([1.0, 0.0], dtype=np.float32)
        photos = [
            {"id": 1, "description": "no vec", "description_embedding": None},
            {
                "id": 2,
                "description": "has vec",
                "description_embedding": _vec(1.0, 0.0),
            },
        ]

        with patch.object(pfa, "embedding_model", mock_embed):
            result = pfa.rank_photos("x", photos)

        assert [r["id"] for r in result] == [2]
