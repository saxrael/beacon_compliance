"""NVIDIA Nemotron & OpenRouter Embedding Engine (embeddings.py).

Provides vector embeddings via OpenRouter (nvidia/llama-nemotron-embed-vl-1b-v2)
with cosine similarity, distance metrics, and vector serialization.
"""

import json
import logging
import math
import os
import struct
import zlib
from typing import Any

import httpx

from backend.src.core.retry import llm_retry

logger = logging.getLogger(__name__)

OPENROUTER_EMBEDDINGS_URL = "https://openrouter.ai/api/v1/embeddings"
DEFAULT_EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2"
NVIDIA_NEMOTRON_DIMENSIONS = 2048


def compute_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))


def compute_cosine_distance(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine distance (1.0 - cosine_similarity)."""
    sim = compute_cosine_similarity(vec_a, vec_b)
    return max(0.0, 1.0 - sim)


def serialize_vector(vec: list[float]) -> bytes:
    """Serialize float vector to binary bytes."""
    return struct.pack(f"{len(vec)}f", *vec)


def deserialize_vector(blob: bytes | str | None) -> list[float]:
    """Deserialize binary bytes or JSON string back to list of floats."""
    if not blob:
        return []
    if isinstance(blob, str):
        try:
            parsed = json.loads(blob)
            if isinstance(parsed, list):
                return [float(x) for x in parsed]
        except Exception:
            return []
    if isinstance(blob, bytes | bytearray):
        n_floats = len(blob) // 4
        if n_floats > 0:
            try:
                return list(struct.unpack(f"{n_floats}f", blob[: n_floats * 4]))
            except Exception:
                pass
    return []


def _deterministic_local_vector(text: str, dim: int = NVIDIA_NEMOTRON_DIMENSIONS) -> list[float]:
    """Generate normalized, deterministic float vector for local offline testing using signed projection."""

    vec = [0.0] * dim
    clean_text = text.lower().strip()
    words = clean_text.split()

    for idx, word in enumerate(words):
        h = zlib.crc32(word.encode("utf-8"))
        slot = h % dim
        sign = 1.0 if (h >> 16) & 1 else -1.0
        weight = 1.0 / (1.0 + math.log1p(idx + 1))
        vec[slot] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0.0:
        vec = [v / norm for v in vec]
    else:
        vec[0] = 1.0
    return vec


class EmbeddingEngine:
    """NVIDIA Nemotron & OpenRouter Embedding Client."""

    def __init__(
        self,
        openrouter_api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model or os.environ.get("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    @llm_retry
    def _call_openrouter_embeddings(self, texts: list[str]) -> list[list[float]] | None:
        """Execute OpenRouter embeddings API call with retry."""
        if not self.api_key or not texts:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://beaconcompliance.pottershouse.org.uk",
            "X-Title": "Beacon Compliance OSCR Sentinel",
        }
        body: dict[str, Any] = {
            "model": self.model,
            "input": texts if len(texts) > 1 else texts[0],
        }

        with httpx.Client(timeout=20.0) as client:
            resp = client.post(OPENROUTER_EMBEDDINGS_URL, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", [])
            items_sorted = sorted(items, key=lambda x: x.get("index", 0))
            return [item["embedding"] for item in items_sorted if "embedding" in item]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of strings."""
        if not texts:
            return []
        try:
            res = self._call_openrouter_embeddings(texts)
            if res and len(res) == len(texts):
                return res
        except Exception as err:
            logger.warning(
                f"OpenRouter embedding call failed ({self.model}), using fallback: {err}"
            )

        return [_deterministic_local_vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        """Generate embedding vector for a single search query or fact string."""
        results = self.embed_texts([text])
        return results[0] if results else _deterministic_local_vector(text)
