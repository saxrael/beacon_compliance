"""Unit tests for Hybrid Dense+Sparse RRF Retrieval Engine (backend/src/core/retrieval.py)."""

import pytest

from backend.src.core.embeddings import EmbeddingEngine
from backend.src.core.retrieval import HybridRRFRetriever


def test_hybrid_rrf_retriever_sparse_search():
    retriever = HybridRRFRetriever(rrf_k=60)
    corpus = [
        {
            "chunk_id": "c1",
            "text": "OSCR requires charities under £250,000 to submit Receipts and Payments accounts.",
        },
        {
            "chunk_id": "c2",
            "text": "Trustees must prepare a Trustees Annual Report outlining governance and achievements.",
        },
    ]

    results = retriever.hybrid_rrf_search(
        query="Receipts and Payments", query_vec=None, corpus=corpus, top_n=2
    )
    assert len(results) > 0
    assert results[0].chunk_id == "c1"


def test_hybrid_rrf_retriever_dense_and_sparse():
    retriever = HybridRRFRetriever(rrf_k=60)
    corpus = [
        {"chunk_id": "c1", "text": "OSCR guidance on R&P.", "embedding_vec": [1.0, 0.0]},
        {"chunk_id": "c2", "text": "Trustee governance guide.", "embedding_vec": [0.0, 1.0]},
    ]

    results = retriever.hybrid_rrf_search(query="R&P", query_vec=[1.0, 0.0], corpus=corpus, top_n=2)
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert pytest.approx(results[0].rrf_score, rel=1e-3) == (1 / 61 + 1 / 61)


def test_multi_query_concurrent_hybrid_search_and_deduplication():
    retriever = HybridRRFRetriever(rrf_k=60)
    engine = EmbeddingEngine(openrouter_api_key=None)

    corpus = [
        {
            "chunk_id": "doc_oar_01",
            "source_type": "document",
            "source_id": "oar_template",
            "text": "OSCR Online Annual Return statutory filing guidance.",
            "embedding_vec": engine.embed_query(
                "OSCR Online Annual Return statutory filing guidance."
            ),
        },
        {
            "chunk_id": "kb_gov_01",
            "source_type": "kb",
            "source_id": "scio_governance",
            "text": "Scottish SCIO constitution and trustee duties under Section 66.",
            "embedding_vec": engine.embed_query(
                "Scottish SCIO constitution and trustee duties under Section 66."
            ),
        },
        {
            "chunk_id": "chat_hist_01",
            "source_type": "conversation",
            "source_id": "run_001",
            "text": "Trustee asked about submitting annual accounts by 30 September.",
            "embedding_vec": engine.embed_query(
                "Trustee asked about submitting annual accounts by 30 September."
            ),
        },
    ]

    queries = [
        "OSCR annual return filing deadline",
        "Statutory filing date 30 September",
    ]

    results = retriever.search_multi_query_hybrid(
        queries=queries,
        corpus=corpus,
        embedding_engine=engine,
        top_n=5,
        min_rrf_threshold=0.015,
    )

    assert len(results) > 0
    chunk_ids = [r.chunk_id for r in results]
    assert len(chunk_ids) == len(set(chunk_ids))

    for r in results:
        assert r.rrf_score >= 0.015
