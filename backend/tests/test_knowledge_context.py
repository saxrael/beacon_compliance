"""Unit tests for ComplianceKnowledgeContext and ContextAssembler (test_knowledge_context.py)."""

from backend.src.core.knowledge_context import (
    ComplianceContextAssembler,
    ComplianceContextEnvelope,
    ComplianceKnowledgeContext,
)


def test_compliance_knowledge_context_non_financial_memory():
    ctx = ComplianceKnowledgeContext()

    accepted = ctx.add_non_financial_fact(
        fact_id="fact_01",
        user_id="trustee_chair",
        fact_text="Trustees prefer concise summary reports.",
        created_at="2026-08-12",
    )
    assert accepted is True

    rejected = ctx.add_non_financial_fact(
        fact_id="fact_02",
        user_id="trustee_chair",
        fact_text="Gross income was £15,000.",
        created_at="2026-08-12",
    )
    assert rejected is False


def test_compliance_knowledge_context_query():
    ctx = ComplianceKnowledgeContext()
    ctx.add_non_financial_fact(
        fact_id="fact_01",
        user_id="trustee_chair",
        fact_text="Trustees prefer monthly R&P reviews.",
        created_at="2026-08-12",
    )

    corpus = [
        {
            "chunk_id": "oscr_01",
            "text": "OSCR requires SCIOs under £250,000 gross income to prepare Receipts and Payments accounts.",
        }
    ]

    res = ctx.query_context(
        user_id="trustee_chair", query="OSCR receipts and payments rules", corpus=corpus
    )
    assert res["user_id"] == "trustee_chair"
    assert len(res["user_facts"]) == 1
    assert "Trustees prefer monthly R&P reviews." in res["user_facts"][0]
    assert len(res["kb_matches"]) == 1
    assert res["sources"] == ["oscr_01"]


def test_context_assembler_builds_complete_envelope():
    assembler = ComplianceContextAssembler()

    user_profile = {
        "user_id": "user_chair_01",
        "name": "Pastor David Robertson",
        "email": "chair@pottershouse.org.uk",
        "role": "Chair",
    }
    fin_state = {
        "receipts_payments": {
            "gross_receipts_decimal": "18450.00",
            "gross_payments_decimal": "12300.00",
            "net_movement_decimal": "6150.00",
            "is_threshold_breached": False,
        },
        "statement_of_balances": {"reconciled": True},
    }
    history_turns = [
        {"role": "user", "content": "What is our filing deadline?"},
        {"role": "assistant", "content": "The deadline is 30 September 2026."},
    ]

    envelope = assembler.build_context_envelope(
        user_id="user_chair_01",
        run_id="run_2025_01",
        user_profile=user_profile,
        financial_state=fin_state,
        query="What is my role and current financial balance?",
        history_turns=history_turns,
        tier2_summary="Trustee previously inquired about statutory submission deadlines.",
        tier3_facts=["Board meetings take place at 5B Beachmont Court."],
    )

    assert isinstance(envelope, ComplianceContextEnvelope)
    assert envelope.trustee.name == "Pastor David Robertson"
    assert envelope.trustee.role == "Chair"
    assert envelope.trustee.is_chair is True
    assert envelope.charity.charity_number == "SC054652"
    assert envelope.financial_state.gross_receipts == "18450.00"
    assert envelope.financial_state.reconciled is True
    assert len(envelope.tier1_history) == 2

    formatted_xml = assembler.format_system_context(envelope)
    assert "<trustee_name>Pastor David Robertson</trustee_name>" in formatted_xml
    assert "<trustee_role>Chair</trustee_role>" in formatted_xml
    assert "<gross_receipts>£18450.00</gross_receipts>" in formatted_xml
    assert "<charity_number>SC054652</charity_number>" in formatted_xml
    assert "5B Beachmont Court" in formatted_xml
