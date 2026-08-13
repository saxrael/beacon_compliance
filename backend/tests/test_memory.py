"""Unit tests for 3-Tier Memory Architecture Engine (backend/src/core/memory.py).

Verifies strict Non-Financial Cognitive Memory Exclusion (PRD §7.9 / Red-Line 2).
"""

from backend.src.core.memory import CognitiveMemoryManager


def test_memory_non_financial_fact_allowed():
    mgr = CognitiveMemoryManager()
    fact = mgr.filter_non_financial_fact(
        fact_id="f1",
        user_id="user_1",
        fact_text="Trustee board meetings occur on the first Monday of each month.",
        created_at="2026-08-12T10:00:00Z",
    )
    assert fact is not None
    assert fact.fact_id == "f1"


def test_memory_financial_fact_rejected():
    mgr = CognitiveMemoryManager()
    fact = mgr.filter_non_financial_fact(
        fact_id="f2",
        user_id="user_1",
        fact_text="Total receipts for the mission fund were £15,000.",
        created_at="2026-08-12T10:00:00Z",
    )
    assert fact is None


def test_memory_financial_summary_rejected():
    mgr = CognitiveMemoryManager()
    summary = mgr.filter_non_financial_summary(
        user_id="user_1",
        run_id="run_1",
        summary_text="Charity had total payments of £5000 and balance of £2000.",
        updated_at="2026-08-12T10:00:00Z",
    )
    assert summary is None
