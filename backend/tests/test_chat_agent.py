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


def test_chat_agent_stream_simple_greeting_has_no_fake_thinking_or_actions():
    agent = ComplianceChatAgent()
    events = list(agent.stream_message("Hello, good morning", state={}))
    event_types = [e["type"] for e in events]

    assert "thought" not in event_types
    assert "action" not in event_types
    assert "token" in event_types
    assert "done" in event_types

    done_event = next(e for e in events if e["type"] == "done")
    assert not done_event.get("thinking")
    assert not done_event.get("tool_calls")


def test_chat_agent_stream_financial_query_emits_clean_action_lifecycle():
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

    assert "thought" not in event_types

    action_events = [e for e in events if e["type"] == "action"]
    assert len(action_events) >= 1
    assert any("Receipts & Payments" in a.get("label", a.get("detail", "")) for a in action_events)

    done_event = next(e for e in events if e["type"] == "done")
    assert "15000.00" in done_event["full_message"]
    assert len(done_event.get("tool_calls", [])) == 1


def test_chat_agent_stream_regulatory_query_emits_clean_action_lifecycle():
    agent = ComplianceChatAgent()
    kb_corpus = [{"chunk_id": "kb_01", "text": "OSCR requires annual filings within 9 months."}]

    events = list(
        agent.stream_message("What is the OSCR filing deadline?", state={}, kb_corpus=kb_corpus)
    )
    event_types = [e["type"] for e in events]

    assert "thought" not in event_types

    action_events = [e for e in events if e["type"] == "action"]
    assert len(action_events) >= 1
    assert any("OSCR" in a.get("label", a.get("detail", "")) for a in action_events)

    done_event = next(e for e in events if e["type"] == "done")
    assert len(done_event.get("sources", [])) > 0


def test_llm_client_stream_parses_dynamic_think_tags():
    from backend.src.core.llm_client import LLMClient

    client = LLMClient()
    mock_raw_stream = [
        "<think>\n",
        "Assessing compliance ",
        "with SCIO provisions.\n",
        "</think>\n",
        "Under Scottish charity ",
        "regulations, filings ",
        "are due in 9 months.",
    ]

    parsed_events = list(client.parse_streaming_chunks(mock_raw_stream))
    thought_chunks = [e["chunk"] for e in parsed_events if e["type"] == "thought"]
    token_chunks = [e["chunk"] for e in parsed_events if e["type"] == "token"]

    full_thought = "".join(thought_chunks)
    full_tokens = "".join(token_chunks)

    assert "Assessing compliance with SCIO provisions." in full_thought
    assert "Under Scottish charity regulations" in full_tokens
    assert "<think>" not in full_tokens
    assert "</think>" not in full_tokens
