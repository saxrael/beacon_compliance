"""Unit tests for Compliance Chat Assistant Agent (backend/src/agents/chat_agent.py)."""

from unittest.mock import MagicMock

from backend.src.agents.chat_agent import ComplianceChatAgent
from backend.src.core.llm_client import LLMClient


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


def test_chat_agent_upfront_context_engineering_zero_starvation():
    mock_llm = MagicMock()
    mock_llm.call_gemma_chat.return_value = (
        "Greetings Pastor David Robertson. As the Chair of Potter's House Christian Mission UK (SCIO, SC054652), "
        "our verified gross receipts stand at £18,450.00 and the accounts are fully reconciled."
    )

    agent = ComplianceChatAgent(llm_client=mock_llm)
    user_profile = {
        "name": "Pastor David Robertson",
        "role": "Chair",
        "email": "chair@pottershouse.org.uk",
    }
    fin_state = {
        "receipts_payments": {
            "gross_receipts_decimal": "18450.00",
            "gross_payments_decimal": "12000.00",
            "net_movement_decimal": "6450.00",
            "is_threshold_breached": False,
        },
        "statement_of_balances": {"reconciled": True},
    }

    res = agent.process_message(
        "Who am I and what is our active financial position?",
        state=fin_state,
        user_id="user_chair_01",
        run_id="run_001",
        user_profile=user_profile,
        tier2_summary="Trustee previously reviewed OSCR Section 66 requirements.",
        tier3_facts=["Annual General Meeting is held annually in November."],
    )

    assert "Pastor David Robertson" in res.message
    assert "Chair" in res.message
    # Verified call received injected system prompt with metadata
    call_args = mock_llm.call_gemma_chat.call_args
    system_prompt_arg = call_args[1].get("system_prompt") or call_args[0][0]
    assert "Pastor David Robertson" in system_prompt_arg
    assert "SC054652" in system_prompt_arg
    assert "£18450.00" in system_prompt_arg


def test_chat_agent_multi_turn_history_retention():
    mock_llm = MagicMock()
    mock_llm.call_gemma_chat.return_value = "Sarah is the appointed Charity Treasurer."

    agent = ComplianceChatAgent(llm_client=mock_llm)
    history_turns = [
        {"role": "user", "content": "Our newly elected treasurer is Sarah Jenkins."},
        {
            "role": "assistant",
            "content": "Acknowledged. Sarah Jenkins has been noted as Treasurer.",
        },
    ]

    res = agent.process_message(
        "Who is our treasurer?",
        state={},
        user_id="trustee_01",
        history_turns=history_turns,
    )

    assert "Sarah" in res.message
    call_args = mock_llm.call_gemma_chat.call_args
    messages_history_arg = call_args[1].get("messages_history")
    assert messages_history_arg is not None
    assert len(messages_history_arg) == 2
    assert "Sarah Jenkins" in messages_history_arg[0]["content"]


def test_chat_agent_cyclical_reviewer_and_circuit_breaker():
    agent = ComplianceChatAgent()

    # Reviewer detects error in tool output
    is_valid, critique = agent._review_agent_output(
        response_text="Error occurred during processing.",
        tool_context="Note: Live Receipts & Payments query failed: database locked",
        tool_calls=[{"tool": "get_financial_summary", "output": {"error": "database locked"}}],
    )
    assert is_valid is False
    assert "error" in critique.lower()

    # Reviewer approves valid output
    is_valid_ok, critique_ok = agent._review_agent_output(
        response_text="According to our verified accounts, gross receipts are £15,000.00.",
        tool_context="Verified gross receipts: £15,000.00",
        tool_calls=[{"tool": "get_financial_summary", "output": {"gross_receipts": "15000.00"}}],
    )
    assert is_valid_ok is True
    assert critique_ok is None


def test_llm_client_stream_parses_dynamic_think_tags():
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


def test_chat_agent_with_langfuse_telemetry_enabled(monkeypatch):
    """Verify chat agent executes and traces turns when Langfuse is enabled."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    agent = ComplianceChatAgent()
    state = {
        "receipts_payments": {
            "gross_receipts_decimal": "10000.00",
            "gross_payments_decimal": "5000.00",
            "net_movement_decimal": "5000.00",
            "is_threshold_breached": False,
        },
        "statement_of_balances": {"reconciled": True},
        "run_id": "run_test_01",
    }

    # Synchronous turn
    res = agent.process_message(
        "What are our gross receipts?",
        state=state,
        user_id="trustee_test",
        run_id="run_test_01",
    )
    assert "£10000.00" in res.message
    assert len(res.tool_calls) == 1

    # Streaming turn
    events = list(
        agent.stream_message(
            "What are our total financial receipts?",
            state=state,
            user_id="trustee_test",
            run_id="run_test_01",
        )
    )
    done_event = next(e for e in events if e["type"] == "done")
    assert "10000.00" in done_event["full_message"]
