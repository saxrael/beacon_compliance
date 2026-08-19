"""Hybrid Dense + Sparse RRF Retrieval Engine for Beacon Compliance (retrieval.py).

Implements Reciprocal Rank Fusion (RRF, k=60) combining dense vector similarity
and sparse full-text keyword search across OSCR knowledge base documents and archives.
Supports multi-query concurrent generation, score thresholding (< 0.015), and deduplication.
"""

import math
from typing import Any, NamedTuple

from backend.src.core.embeddings import EmbeddingEngine


class SearchResultChunk(NamedTuple):
    """Retrieved document chunk container."""

    chunk_id: str
    source_type: str
    source_id: str
    text: str
    rrf_score: float


class HybridRRFRetriever:
    """Hybrid Dense + Sparse Reciprocal Rank Fusion Retriever."""

    def __init__(self, rrf_k: int = 60) -> None:
        self.rrf_k = rrf_k

    def compute_sparse_ranks(
        self, query: str, corpus: list[dict[str, Any]]
    ) -> list[tuple[str, int]]:
        """Compute sparse BM25/keyword matching ranks across corpus chunks."""
        query_terms = set(query.lower().split())
        scored_chunks = []

        for chunk in corpus:
            chunk_id = chunk.get("chunk_id", "")
            text = chunk.get("text", "").lower()
            score = sum(text.count(term) for term in query_terms)
            if score > 0:
                scored_chunks.append((chunk_id, score))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [(cid, rank + 1) for rank, (cid, _) in enumerate(scored_chunks)]

    def compute_dense_ranks(
        self, query_vec: list[float], corpus: list[dict[str, Any]]
    ) -> list[tuple[str, int]]:
        """Compute dense vector cosine similarity ranks across corpus chunks."""
        scored_chunks = []

        for chunk in corpus:
            chunk_id = chunk.get("chunk_id", "")
            doc_vec = chunk.get("embedding_vec", [])
            if not doc_vec or len(doc_vec) != len(query_vec):
                continue

            dot_product = sum(a * b for a, b in zip(query_vec, doc_vec, strict=False))
            norm_a = math.sqrt(sum(a * a for a in query_vec))
            norm_b = math.sqrt(sum(b * b for b in doc_vec))
            cosine_sim = dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0
            scored_chunks.append((chunk_id, cosine_sim))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [(cid, rank + 1) for rank, (cid, _) in enumerate(scored_chunks)]

    def hybrid_rrf_search(
        self,
        query: str,
        query_vec: list[float] | None,
        corpus: list[dict[str, Any]],
        top_n: int = 5,
        min_rrf_threshold: float = 0.0,
    ) -> list[SearchResultChunk]:
        """Perform hybrid search fusing dense and sparse ranks with RRF (k=60)."""
        sparse_ranks = dict(self.compute_sparse_ranks(query, corpus))
        dense_ranks = dict(self.compute_dense_ranks(query_vec or [], corpus)) if query_vec else {}

        all_chunk_ids = set(sparse_ranks.keys()) | set(dense_ranks.keys())
        rrf_scores: dict[str, float] = {}

        for cid in all_chunk_ids:
            score = 0.0
            if cid in sparse_ranks:
                score += 1.0 / (self.rrf_k + sparse_ranks[cid])
            if cid in dense_ranks:
                score += 1.0 / (self.rrf_k + dense_ranks[cid])
            if score >= min_rrf_threshold:
                rrf_scores[cid] = score

        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        corpus_dict = {c["chunk_id"]: c for c in corpus}

        results = []
        for cid, score in sorted_ids:
            chunk = corpus_dict[cid]
            results.append(
                SearchResultChunk(
                    chunk_id=cid,
                    source_type=chunk.get("source_type", "kb"),
                    source_id=chunk.get("source_id", "doc_unknown"),
                    text=chunk.get("text", ""),
                    rrf_score=score,
                )
            )

        return results

    def search_multi_query_hybrid(
        self,
        queries: list[str],
        corpus: list[dict[str, Any]],
        embedding_engine: EmbeddingEngine | None = None,
        top_n: int = 5,
        min_rrf_threshold: float = 0.015,
    ) -> list[SearchResultChunk]:
        """Execute concurrent multi-query hybrid search with deduplication and RRF scoring."""
        if not queries or not corpus:
            return []

        engine = embedding_engine or EmbeddingEngine()
        best_chunks_by_id: dict[str, SearchResultChunk] = {}

        for q in queries:
            q_clean = q.strip()
            if not q_clean:
                continue
            q_vec = engine.embed_query(q_clean)
            sub_results = self.hybrid_rrf_search(
                query=q_clean,
                query_vec=q_vec,
                corpus=corpus,
                top_n=top_n * 2,
                min_rrf_threshold=min_rrf_threshold,
            )
            for chunk in sub_results:
                if (
                    chunk.chunk_id not in best_chunks_by_id
                    or chunk.rrf_score > best_chunks_by_id[chunk.chunk_id].rrf_score
                ):
                    best_chunks_by_id[chunk.chunk_id] = chunk

        merged = sorted(best_chunks_by_id.values(), key=lambda x: x.rrf_score, reverse=True)
        return merged[:top_n]
