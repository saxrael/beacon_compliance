"""Unit tests for background cognitive memory worker (test_cognitive_worker.py)."""

from unittest.mock import MagicMock

from backend.src.agents.cognitive_worker import CognitiveWorker
from backend.src.core.memory import MemoryFact


def test_cognitive_worker_tier2_summary_update():
    mock_llm = MagicMock()
    mock_llm.call_cognitive_summary.return_value = (
        "Trustee reviewed Section 66 duties and requested assistance with TAR structure."
    )

    worker = CognitiveWorker(llm_client=mock_llm)
    evicted_msgs = [
        {"role": "user", "content": "What are Section 66 duties?"},
        {"role": "assistant", "content": "Under Section 66 of 2005 Act..."},
    ]

    summary, _ = worker.process_cognitive_turn(
        user_id="trustee_01",
        run_id="run_001",
        evicted_messages=evicted_msgs,
        existing_summary="Trustee previously asked about OSCR deadlines.",
        existing_facts=[],
    )

    assert summary is not None
    assert "Section 66 duties" in summary.summary_text
    assert mock_llm.call_cognitive_summary.called


def test_cognitive_worker_tier3_fact_extraction_create_and_update():
    mock_llm = MagicMock()
    mock_llm.call_cognitive_summary.return_value = "Summary text."
    mock_llm.call_cognitive_fact_extractor.return_value = [
        {
            "think": "Trustee stated they serve as Chair.",
            "plan": "Create new permanent fact about trustee role.",
            "action": "CREATE",
            "target_existing_fact_id": None,
            "final_fact_text": "Trustee John serves as Board Chair.",
        },
        {
            "think": "Trustee updated preferred AGM date.",
            "plan": "Update existing fact f_agm.",
            "action": "UPDATE",
            "target_existing_fact_id": "f_agm",
            "final_fact_text": "Annual General Meeting is scheduled for November each year.",
        },
    ]

    existing_facts = [
        MemoryFact(
            fact_id="f_agm",
            user_id="trustee_01",
            fact_text="Annual General Meeting is in October.",
            created_at="2026-08-01T00:00:00Z",
        )
    ]

    worker = CognitiveWorker(llm_client=mock_llm)
    _, fact_mutations = worker.process_cognitive_turn(
        user_id="trustee_01",
        run_id="run_001",
        evicted_messages=[{"role": "user", "content": "Update AGM to November."}],
        existing_summary=None,
        existing_facts=existing_facts,
    )

    assert len(fact_mutations) == 2
    actions = [m["action"] for m in fact_mutations]
    assert "CREATE" in actions
    assert "UPDATE" in actions


def test_cognitive_worker_fact_fallback_on_invalid_uuid():
    mock_llm = MagicMock()
    mock_llm.call_cognitive_summary.return_value = "Summary."
    mock_llm.call_cognitive_fact_extractor.return_value = [
        {
            "think": "LLM hallucinated a non-existent UUID for update.",
            "plan": "Update fact that does not exist.",
            "action": "UPDATE",
            "target_existing_fact_id": "non_existent_uuid_123",
            "final_fact_text": "Independent examination completed by Henderson & Co.",
        }
    ]

    worker = CognitiveWorker(llm_client=mock_llm)
    _, fact_mutations = worker.process_cognitive_turn(
        user_id="trustee_01",
        run_id="run_001",
        evicted_messages=[{"role": "user", "content": "Henderson & Co did the exam."}],
        existing_summary=None,
        existing_facts=[],  # Empty facts list -> target UUID does not exist
    )

    assert len(fact_mutations) == 1
    # Fallback from UPDATE to CREATE
    assert fact_mutations[0]["action"] == "CREATE"
    assert "Henderson & Co" in fact_mutations[0]["fact_text"]


def test_cognitive_worker_financial_facts_strictly_rejected():
    mock_llm = MagicMock()
    mock_llm.call_cognitive_summary.return_value = "Summary."
    mock_llm.call_cognitive_fact_extractor.return_value = [
        {
            "think": "Attempting to extract monetary amount.",
            "plan": "Create fact with financial number.",
            "action": "CREATE",
            "target_existing_fact_id": None,
            "final_fact_text": "Total mission offering was £12,000.",
        }
    ]

    worker = CognitiveWorker(llm_client=mock_llm)
    _, fact_mutations = worker.process_cognitive_turn(
        user_id="trustee_01",
        run_id="run_001",
        evicted_messages=[{"role": "user", "content": "We had £12,000."}],
        existing_summary=None,
        existing_facts=[],
    )

    assert len(fact_mutations) == 0
