"""Unit tests for Compliance Chat Assistant Agent (backend/src/agents/chat_agent.py)."""

from backend.src.agents.chat_agent import ComplianceChatAgent


def test_chat_agent_financial_query_uses_tool():
    agent = ComplianceChatAgent()
    state = {
        "receipts_payments": {
            "gross_receipts_decimal": "12500.00",
            "gross_payments_decimal": "8000.00",
            "net_movement_decimal": "4500.00",
            "is_threshold_breached": False,
        },
        "statement_of_balances": {"reconciled": True},
    }

    res = agent.process_message("What are our total receipts and payments?", state=state)
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0]["tool"] == "get_financial_summary"
    assert "£12500.00" in res.message


def test_chat_agent_oscr_guidance_query():
    agent = ComplianceChatAgent()
    kb_corpus = [
        {"chunk_id": "kb_01", "text": "OSCR SCIO regulations require a minimum of 3 trustees."}
    ]

    res = agent.process_message(
        "What does OSCR guidance say about trustees?", state={}, kb_corpus=kb_corpus
    )
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0]["tool"] == "search_knowledge_base"
    assert "kb_01" in res.sources
