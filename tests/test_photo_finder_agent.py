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
        mock_db.query.return_value = [{"id": 101}]

        with patch.object(pfa, "db", mock_db):
            result = pfa.get_candidate_photos_ids([10, 11], logic="OR")

        assert result == [{"id": 101}]
        sql = _normalize_sql(mock_db.query.call_args[0][0])
        assert "tag_id in" in sql
        assert mock_db.query.call_args[0][1] == ["10", "11"]

    def test_and_uses_exists_per_group(self):
        mock_db = MagicMock()
        mock_db.query.return_value = []

        with patch.object(pfa, "db", mock_db):
            pfa.get_candidate_photos_ids([[10, 11], [20]], logic="AND")

        sql = _normalize_sql(mock_db.query.call_args[0][0])
        assert sql.count("exists") == 2
        assert mock_db.query.call_args[0][1] == ["10", "11", "20"]

    def test_empty_tag_ids_returns_all(self):
        mock_db = MagicMock()
        mock_db.query.return_value = [{"id": 1}]

        with patch.object(pfa, "db", mock_db):
            result = pfa.get_candidate_photos_ids([], logic="OR")

        assert result == [{"id": 1}]
        sql = _normalize_sql(mock_db.query.call_args[0][0])
        assert "order by i.created_at desc" in sql
        assert "tag_id" not in sql

    def test_invalid_logic_raises(self):
        with patch.object(pfa, "db", MagicMock()):
            with pytest.raises(ValueError, match="Invalid Tag Selection Logic Type"):
                pfa.get_candidate_photos_ids([1], logic="XOR")  # type: ignore[arg-type]


class TestRankPhotos:
    def test_orders_by_similarity_and_adds_preview_url(self):
        # target embedding ≈ [1, 0] → photo A closer than B
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = np.array([1.0, 0.0], dtype=np.float32)
        mock_db = MagicMock()
        mock_db.select.side_effect = [
            [
                {
                    "id": 2,
                    "description": "A red car",
                    "description_embedding": _vec(0.0, 1.0),
                }
            ],
            [
                {
                    "id": 1,
                    "description": "An orange cat on a sofa",
                    "description_embedding": _vec(1.0, 0.0),
                }
            ],
        ]

        with (
            patch.object(pfa, "embedding_model", mock_embed),
            patch.object(pfa, "db", mock_db),
        ):
            result = pfa.rank_photos("a cat on the couch", [2, 1], limit=5)

        assert result["type"] == pfa.SEARCH_RESULTS_TYPE
        assert result["query"] == "a cat on the couch"
        items = result["items"]
        assert [r["id"] for r in items] == [1, 2]
        assert items[0]["description"] == "An orange cat on a sofa"
        assert items[0]["preview_url"] == "/api/pictures/1/preview"
        assert items[1]["preview_url"] == "/api/pictures/2/preview"
        assert items[0]["similarity"] > items[1]["similarity"]
        mock_embed.embed_text.assert_called_once_with("a cat on the couch")

    def test_respects_limit(self):
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = np.array([1.0, 0.0], dtype=np.float32)
        mock_db = MagicMock()
        mock_db.select.side_effect = [
            [
                {
                    "id": i,
                    "description": f"d{i}",
                    "description_embedding": _vec(1.0, 0.0),
                }
            ]
            for i in range(10)
        ]

        with (
            patch.object(pfa, "embedding_model", mock_embed),
            patch.object(pfa, "db", mock_db),
        ):
            result = pfa.rank_photos("x", list(range(10)), limit=3)

        assert result["type"] == pfa.SEARCH_RESULTS_TYPE
        assert len(result["items"]) == 3

    def test_skips_missing_embedding(self):
        mock_embed = MagicMock()
        mock_embed.embed_text.return_value = np.array([1.0, 0.0], dtype=np.float32)
        mock_db = MagicMock()
        mock_db.select.side_effect = [
            [{"id": 1, "description": "no vec", "description_embedding": None}],
            [
                {
                    "id": 2,
                    "description": "has vec",
                    "description_embedding": _vec(1.0, 0.0),
                }
            ],
        ]

        with (
            patch.object(pfa, "embedding_model", mock_embed),
            patch.object(pfa, "db", mock_db),
        ):
            result = pfa.rank_photos("x", [1, 2])

        assert [r["id"] for r in result["items"]] == [2]


class TestExtractPhotoFinderTurn:
    def test_search_results_kind_from_rank_tool(self):
        payload = {
            "type": pfa.SEARCH_RESULTS_TYPE,
            "query": "cat on sofa",
            "items": [
                {
                    "id": 1,
                    "description": "cat",
                    "preview_url": "/api/pictures/1/preview",
                    "similarity": 0.9,
                }
            ],
        }
        fr = MagicMock()
        fr.name = pfa.RANK_TOOL_NAME
        fr.response = payload
        tool_event = MagicMock()
        tool_event.get_function_responses.return_value = [fr]
        tool_event.is_final_response.return_value = False

        final = MagicMock()
        final.get_function_responses.return_value = []
        final.is_final_response.return_value = True
        final.content.parts = [MagicMock(text="Here are the closest matches.")]

        turn = pfa.extract_photo_finder_turn([tool_event, final])
        assert turn["kind"] == pfa.SEARCH_RESULTS_TYPE
        assert turn["results"] == payload
        assert turn["message"] == "Here are the closest matches."

    def test_chat_kind_without_rank_tool(self):
        final = MagicMock()
        final.get_function_responses.return_value = []
        final.is_final_response.return_value = True
        final.content.parts = [MagicMock(text="What color is the sofa?")]

        turn = pfa.extract_photo_finder_turn([final])
        assert turn == {
            "kind": "chat",
            "message": "What color is the sofa?",
            "results": None,
        }
