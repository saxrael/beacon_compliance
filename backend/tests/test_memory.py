"""Unit tests for 4-tier cognitive memory architecture (test_memory.py)."""

from backend.src.core.embeddings import EmbeddingEngine
from backend.src.core.memory import (
    CognitiveMemoryManager,
    MemoryFact,
    Tier1WorkingMemoryBuffer,
)


def test_memory_non_financial_fact_allowed():
    mgr = CognitiveMemoryManager()
    fact = mgr.filter_non_financial_fact(
        fact_id="fact_001",
        user_id="trustee_01",
        fact_text="Trustee prefers communication via email for statutory OSCR notices.",
        created_at="2026-08-12T10:00:00Z",
    )
    assert fact is not None
    assert fact.fact_id == "fact_001"
    assert fact.user_id == "trustee_01"


def test_memory_financial_fact_rejected():
    mgr = CognitiveMemoryManager()
    financial_facts = [
        "Trustee confirmed £15000 donation was received.",
        "Total receipts for 2025 were 12500 pounds.",
        "The closing balance on the general fund is £4,500.",
        "We spent 300 pence on stationery.",
    ]
    for text in financial_facts:
        fact = mgr.filter_non_financial_fact(
            fact_id="fact_bad",
            user_id="trustee_01",
            fact_text=text,
            created_at="2026-08-12T10:00:00Z",
        )
        assert fact is None, f"Financial fact was not rejected: {text}"


def test_memory_financial_summary_rejected():
    mgr = CognitiveMemoryManager()
    bad_summary = "Trustee discussed our receipts of £20,000 and payments of £5,000."
    summary = mgr.filter_non_financial_summary(
        user_id="trustee_01",
        run_id="run_001",
        summary_text=bad_summary,
        updated_at="2026-08-12T10:00:00Z",
    )
    assert summary is None


def test_tier1_sliding_window_buffer():
    buf = Tier1WorkingMemoryBuffer(window_size=3)
    messages = [{"role": "user", "content": f"Turn {i}"} for i in range(5)]
    active, evicted = buf.process_turns(messages)

    assert len(active) == 3
    assert active[0]["content"] == "Turn 2"
    assert active[1]["content"] == "Turn 3"
    assert active[2]["content"] == "Turn 4"

    assert len(evicted) == 2
    assert evicted[0]["content"] == "Turn 0"
    assert evicted[1]["content"] == "Turn 1"


def test_vector_matched_facts_cosine_filtering():
    engine = EmbeddingEngine(openrouter_api_key=None)
    mgr = CognitiveMemoryManager(embedding_engine=engine)

    query_vec = engine.embed_query("charity governance board meetings")

    fact1 = MemoryFact(
        fact_id="f1",
        user_id="u1",
        fact_text="Board meetings are held quarterly at Beachmont Court.",
        created_at="2026-08-12T10:00:00Z",
        embedding_vec=engine.embed_query("Board meetings are held quarterly at Beachmont Court."),
    )
    fact2 = MemoryFact(
        fact_id="f2",
        user_id="u1",
        fact_text="Pasta recipe requires boiled salted water and fresh basil.",
        created_at="2026-08-12T10:00:00Z",
        embedding_vec=engine.embed_query(
            "Pasta recipe requires boiled salted water and fresh basil."
        ),
    )

    matched = mgr.filter_vector_matched_facts([fact1, fact2], query_vec, max_distance=0.75)
    matched_ids = [f.fact_id for f in matched]

    assert "f1" in matched_ids
    assert "f2" not in matched_ids
