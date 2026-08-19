"""Unit test suite for Tenacity Retry Engine & Agent Tool Resilience (backend/tests/test_retry_resilience.py)."""

import json
import sqlite3
from unittest.mock import MagicMock, patch

import httpx

from backend.src.agents.chat_agent import ComplianceChatAgent
from backend.src.core.llm_client import LLMClient
from backend.src.core.retry import (
    db_retry,
    is_retryable_http_error,
    llm_retry,
)


def test_is_retryable_http_error_predicates():
    """Verify HTTP status codes correctly identify retryable transient errors."""
    req = httpx.Request("POST", "https://api.groq.com")

    # 429 Rate Limit, 500, 502, 503, 504 are retryable
    for status_code in (429, 500, 502, 503, 504):
        err = httpx.HTTPStatusError(
            f"Error {status_code}", request=req, response=httpx.Response(status_code, request=req)
        )
        assert is_retryable_http_error(err) is True

    # 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found are NOT retryable
    for status_code in (400, 401, 403, 404):
        err = httpx.HTTPStatusError(
            f"Error {status_code}", request=req, response=httpx.Response(status_code, request=req)
        )
        assert is_retryable_http_error(err) is False

    # Network timeouts / connection errors are retryable
    assert is_retryable_http_error(httpx.TimeoutException("Timeout")) is True
    assert is_retryable_http_error(httpx.ConnectError("Connection refused")) is True

    # Standard exceptions are not
    assert is_retryable_http_error(ValueError("Invalid argument")) is False


def test_llm_retry_decorator_succeeds_after_transient_failure():
    """Verify tenacity llm_retry retries on transient errors and succeeds."""
    call_count = 0

    @llm_retry
    def mock_flaky_llm_call():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            req = httpx.Request("POST", "https://api.groq.com")
            raise httpx.HTTPStatusError(
                "Rate limited", request=req, response=httpx.Response(429, request=req)
            )
        return "success"

    result = mock_flaky_llm_call()
    assert result == "success"
    assert call_count == 2


def test_db_retry_decorator_retries_on_sqlite_lock():
    """Verify tenacity db_retry retries on sqlite3.OperationalError and succeeds."""
    call_count = 0

    @db_retry
    def mock_flaky_db_query():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise sqlite3.OperationalError("database is locked")
        return {"rows": [1, 2, 3]}

    result = mock_flaky_db_query()
    assert result == {"rows": [1, 2, 3]}
    assert call_count == 3


def test_tier25_classifier_tenacity_failover_to_openrouter(monkeypatch):
    """Verify Tier 2.5 classifier retries primary Groq and seamlessly falls back to OpenRouter."""
    monkeypatch.setenv("GROQ_API_KEY", "mock_groq_key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_openrouter_key")

    client = LLMClient()
    req = httpx.Request("POST", "https://api.groq.com")

    # Groq returns 503 error, OpenRouter succeeds with contingency model
    def mock_post(url, *args, **kwargs):
        if "groq.com" in url:
            resp = httpx.Response(503, request=req)
            raise httpx.HTTPStatusError("Service Unavailable", request=req, response=resp)
        elif "openrouter.ai" in url:
            mock_success = MagicMock()
            mock_success.status_code = 200
            mock_success.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "category": "Premises Rent & Utility",
                                    "confidence": 0.91,
                                    "reasoning": "Contingency Llama classification",
                                }
                            )
                        }
                    }
                ]
            }
            return mock_success
        raise ValueError(f"Unexpected url: {url}")

    with patch("httpx.Client.post", side_effect=mock_post):
        result = client.call_tier25_classifier("Hall hire electricity bill", "payment")

    assert result is not None
    assert result["category"] == "Premises Rent & Utility"
    assert result["confidence"] == 0.91


def test_chat_stream_handles_tool_failure_gracefully():
    """Verify chat stream captures tool failure, emits status='failed', and continues streaming."""
    agent = ComplianceChatAgent()

    # Mock tool to fail with unrecoverable error
    with patch.object(
        agent, "get_financial_summary_tool", side_effect=RuntimeError("D1 connection timed out")
    ):
        events = list(agent.stream_message("What are our total financial receipts?", state={}))

    event_types = [e["type"] for e in events]
    assert "action" in event_types

    # Find the failed action event
    action_events = [e for e in events if e["type"] == "action"]
    failed_actions = [a for a in action_events if a.get("status") == "failed"]
    assert len(failed_actions) == 1
    assert "Receipts & Payments" in failed_actions[0].get("label", "")

    # Ensure stream finished cleanly with done event
    done_event = next(e for e in events if e["type"] == "done")
    assert done_event is not None
    assert (
        "unable to retrieve" in done_event["full_message"].lower()
        or "records" in done_event["full_message"].lower()
    )
