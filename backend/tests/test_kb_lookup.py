"""Tests for kb_lookup.py — RAG manual search."""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# Sample test chunks with embeddings
def _make_chunk(text: str, section: str, page: int, embedding: list[float]) -> dict:
    return {
        "text": text,
        "source": "Test Manual",
        "section": section,
        "page": page,
        "embedding": embedding,
    }


# Create orthogonal-ish embeddings for deterministic testing
CHUNK_A_EMB = [1.0, 0.0, 0.0, 0.0]
CHUNK_B_EMB = [0.0, 1.0, 0.0, 0.0]
CHUNK_C_EMB = [0.0, 0.0, 1.0, 0.0]
CHUNK_LOW_EMB = [0.0, 0.0, 0.0, 1.0]  # Orthogonal to query

SAMPLE_CHUNKS = [
    _make_chunk(
        "DC overvoltage protection activates when string voltage exceeds 600V.",
        "6.2 Overvoltage Protection",
        44,
        CHUNK_A_EMB,
    ),
    _make_chunk(
        "AC grid impedance monitoring ensures safe grid connection.",
        "7.1 Grid Impedance",
        58,
        CHUNK_B_EMB,
    ),
    _make_chunk(
        "LED indicator shows red blinking for critical faults.",
        "3.4 LED Indicators",
        22,
        CHUNK_C_EMB,
    ),
    _make_chunk(
        "General safety instructions for installation.",
        "1.1 Safety",
        2,
        CHUNK_LOW_EMB,
    ),
]


@pytest.fixture
def mock_gcs():
    """Mock Cloud Storage to return sample chunks."""
    with patch("tools.kb_lookup.storage.Client") as mock_cls:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_cls.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_as_text.return_value = json.dumps(SAMPLE_CHUNKS)

        yield mock_blob


@pytest.fixture
def mock_embed():
    """Mock the embedding function to return a known vector."""
    with patch("tools.kb_lookup._embed") as mock_fn:
        # Default: return vector aligned with CHUNK_A
        mock_fn.return_value = [0.9, 0.1, 0.0, 0.0]
        yield mock_fn


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the LRU cache between tests."""
    from tools.kb_lookup import _load_chunks
    _load_chunks.cache_clear()
    yield
    _load_chunks.cache_clear()


class TestSearchManual:
    """Tests for the search_manual tool."""

    def test_returns_top_3_by_score(self, mock_gcs, mock_embed):
        """Verify results are ranked by cosine similarity."""
        from tools.kb_lookup import search_manual

        result = search_manual.__wrapped__(
            query="DC overvoltage fault",
            industry="solar",
            equipment_model="SMA-Sunny5000",
            top_k=3,
        )

        assert result["found"] is True
        assert len(result["results"]) > 0
        # First result should be the one most aligned with the query embedding
        assert "Overvoltage" in result["results"][0]["section"]

        # Verify scores are in descending order
        scores = [r["relevance_score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_relevance_threshold_filters_low_scores(self, mock_gcs, mock_embed):
        """Verify results below 0.3 threshold are filtered out."""
        from tools.kb_lookup import search_manual

        # Set embedding to be orthogonal to all chunks except CHUNK_LOW
        mock_embed.return_value = [0.0, 0.0, 0.0, 1.0]

        result = search_manual.__wrapped__(
            query="safety instructions",
            industry="solar",
            equipment_model="SMA-Sunny5000",
            top_k=3,
        )

        # Only the matching chunk (CHUNK_LOW) should be returned
        # Others are orthogonal and score 0.0 (below threshold)
        assert result["found"] is True
        for r in result["results"]:
            assert r["relevance_score"] >= 0.3

    def test_no_manual_returns_not_found(self, mock_embed):
        """Verify graceful handling when no manual is loaded."""
        from tools.kb_lookup import search_manual

        with patch("tools.kb_lookup.storage.Client") as mock_cls:
            mock_client = MagicMock()
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            mock_blob.exists.return_value = False

            result = search_manual.__wrapped__(
                query="anything",
                industry="solar",
                equipment_model="NonExistent-Model",
                top_k=3,
            )

        assert result["found"] is False
        assert "No manual loaded" in result["message"]
        assert len(result["results"]) == 0

    def test_citation_format(self, mock_gcs, mock_embed):
        """Verify citations are formatted correctly."""
        from tools.kb_lookup import search_manual

        result = search_manual.__wrapped__(
            query="DC overvoltage",
            industry="solar",
            equipment_model="SMA-Sunny5000",
            top_k=1,
        )

        if result["results"]:
            citation = result["results"][0]["citation"]
            assert "Test Manual" in citation
            assert "§" in citation
            assert "p." in citation

    def test_chunks_without_embeddings_are_skipped(self, mock_embed):
        """Verify chunks missing embedding field are gracefully skipped."""
        from tools.kb_lookup import search_manual

        chunks_no_emb = [{"text": "test", "source": "X", "section": "1", "page": 1}]

        with patch("tools.kb_lookup.storage.Client") as mock_cls:
            mock_client = MagicMock()
            mock_bucket = MagicMock()
            mock_blob = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            mock_blob.exists.return_value = True
            mock_blob.download_as_text.return_value = json.dumps(chunks_no_emb)

            result = search_manual.__wrapped__(
                query="test",
                industry="solar",
                equipment_model="Test",
                top_k=3,
            )

        assert result["found"] is False
