"""Unit tests for Hybrid Dense+Sparse RRF Retrieval Engine (backend/src/core/retrieval.py)."""

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
