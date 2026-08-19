"""Unit tests for embedding generation and vector operations (test_embeddings.py)."""

from unittest.mock import MagicMock, patch

import pytest

from backend.src.core.embeddings import (
    EmbeddingEngine,
    compute_cosine_distance,
    compute_cosine_similarity,
    deserialize_vector,
    serialize_vector,
)


def test_cosine_similarity_and_distance():
    vec_a = [1.0, 0.0, 0.0]
    vec_b = [1.0, 0.0, 0.0]
    vec_c = [0.0, 1.0, 0.0]
    vec_d = [0.7071, 0.7071, 0.0]

    assert pytest.approx(compute_cosine_similarity(vec_a, vec_b), rel=1e-3) == 1.0
    assert pytest.approx(compute_cosine_distance(vec_a, vec_b), rel=1e-3) == 0.0

    assert pytest.approx(compute_cosine_similarity(vec_a, vec_c), rel=1e-3) == 0.0
    assert pytest.approx(compute_cosine_distance(vec_a, vec_c), rel=1e-3) == 1.0

    dist_ad = compute_cosine_distance(vec_a, vec_d)
    assert dist_ad < 0.75


def test_deterministic_fallback_embeddings():
    engine = EmbeddingEngine(openrouter_api_key=None)
    emb1 = engine.embed_query("Scottish charity OSCR compliance regulations")
    emb2 = engine.embed_query("Scottish charity OSCR compliance regulations")
    emb3 = engine.embed_query("Completely unrelated culinary recipe for cooking pasta")

    assert len(emb1) == 2048
    assert emb1 == emb2

    dist_same = compute_cosine_distance(emb1, emb2)
    dist_diff = compute_cosine_distance(emb1, emb3)

    assert pytest.approx(dist_same, abs=1e-4) == 0.0
    assert dist_diff > dist_same


def test_openrouter_nemotron_embedding_call():
    mock_resp = {
        "data": [
            {"embedding": [0.1, 0.2, 0.3], "index": 0},
            {"embedding": [0.4, 0.5, 0.6], "index": 1},
        ],
        "model": "nvidia/llama-nemotron-embed-vl-1b-v2",
        "usage": {"prompt_tokens": 15, "total_tokens": 15},
    }

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = mock_resp
        mock_post_resp.raise_for_status.return_value = None
        mock_client.__enter__.return_value.post.return_value = mock_post_resp
        mock_client_cls.return_value = mock_client

        engine = EmbeddingEngine(openrouter_api_key="sk-or-test-key")
        embeddings = engine.embed_texts(["First text to embed", "Second text to embed"])

        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2, 0.3]
        assert embeddings[1] == [0.4, 0.5, 0.6]


def test_vector_blob_serialization():
    vec = [0.12345, -0.6789, 1.0, 0.0]
    blob = serialize_vector(vec)
    recovered = deserialize_vector(blob)

    assert len(recovered) == len(vec)
    for orig, rec in zip(vec, recovered, strict=False):
        assert pytest.approx(orig, rel=1e-4) == rec
