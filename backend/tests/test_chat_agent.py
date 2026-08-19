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


def test_chat_agent_out_of_scope_guardrail_refusal():
    agent = ComplianceChatAgent()
    off_topic_queries = [
        "Tell me who won the football game yesterday",
        "Can you write python code for a video game?",
        "What is the best recipe to cook pasta?",
    ]
    for query in off_topic_queries:
        res = agent.process_message(query, state={})
        assert "specialized exclusively in OSCR regulatory compliance" in res.message
        assert "SC054652" in res.message
        assert len(res.tool_calls) == 0


def test_chat_agent_stream_message():
    agent = ComplianceChatAgent()
    state = {
        "receipts_payments": {
            "gross_receipts_decimal": "15000.00",
            "gross_payments_decimal": "9000.00",
            "net_movement_decimal": "6000.00",
            "is_threshold_breached": False,
        },
        "statement_of_balances": {"reconciled": True},
    }

    events = list(agent.stream_message("What were our total financial receipts?", state=state))
    event_types = [e["type"] for e in events]
    assert "thought" in event_types
    assert "action" in event_types
    assert "token" in event_types
    assert "done" in event_types

    done_event = next(e for e in events if e["type"] == "done")
    assert "15000.00" in done_event["full_message"]
