import json
from unittest.mock import MagicMock, patch

import httpx

from backend.src.core.llm_client import LLMClient


def test_llm_client_no_keys_returns_none(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    client = LLMClient()
    assert client.call_gemma_narrative("system", {"key": "val"}) is None
    assert client.call_tier25_classifier("description", "receipt") is None
    assert client.call_gemma_chat("system", "user") is None


def test_call_gemma_narrative_openrouter_success(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_openrouter_key")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    client = LLMClient()
    mock_resp_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "governance_description": "SCIO governance model.",
                            "purposes_activities_narrative": "Relief of poverty.",
                            "achievements_connective_narrative": "52 services held.",
                            "principal_risks_narrative": "Operating reserve maintained.",
                        }
                    )
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_resp_data

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_gemma_narrative("system prompt", {"test": "data"})

    assert res is not None
    assert res["governance_description"] == "SCIO governance model."


def test_call_gemma_narrative_groq_success(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "mock_groq_key")

    client = LLMClient()
    mock_resp_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "governance_description": "Groq governance model.",
                            "purposes_activities_narrative": "Activities.",
                        }
                    )
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_resp_data

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_gemma_narrative("system prompt", {"test": "data"})

    assert res is not None
    assert res["governance_description"] == "Groq governance model."


def test_call_gemma_narrative_http_500_fallback(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_openrouter_key")
    client = LLMClient()

    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_gemma_narrative("system prompt", {"test": "data"})

    assert res is None


def test_call_tier25_classifier_groq_success_and_rule3_scrubbing(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "mock_groq_key")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    client = LLMClient()
    llm_output_json = json.dumps(
        {
            "category": "Donations & Offerings",
            "confidence": 0.95,
            "reasoning": "Sunday tithes match pattern",
            "amount": 500.0,
            "currency": "GBP",
        }
    )
    mock_resp_data = {"choices": [{"message": {"content": llm_output_json}}]}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_resp_data

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_tier25_classifier("Sunday tithes offering", "receipt")

    assert res is not None
    assert set(res.keys()) == {"category", "confidence", "reasoning"}
    assert "amount" not in res
    assert "currency" not in res
    assert res["category"] == "Donations & Offerings"
    assert res["confidence"] == 0.95


def test_call_tier25_classifier_openrouter_fallback(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_or_key")

    client = LLMClient()
    llm_output_json = json.dumps(
        {
            "category": "Premises Rent & Utility",
            "confidence": 0.88,
            "reasoning": "Hall rent keyword match",
        }
    )
    mock_resp_data = {"choices": [{"message": {"content": llm_output_json}}]}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_resp_data

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_tier25_classifier("St Mary Hall Rent", "payment")

    assert res is not None
    assert set(res.keys()) == {"category", "confidence", "reasoning"}
    assert res["category"] == "Premises Rent & Utility"


def test_call_tier25_classifier_http_error_returns_none(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "mock_groq_key")
    client = LLMClient()

    with patch("httpx.Client.post", side_effect=httpx.HTTPError("Network failure")):
        res = client.call_tier25_classifier("Sunday tithes", "receipt")

    assert res is None


def test_call_gemma_chat_with_tool_context(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_or_key")
    client = LLMClient()

    mock_resp_data = {"choices": [{"message": {"content": "OSCR regulatory response text"}}]}
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_resp_data

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_gemma_chat(
            "System instruction",
            "What is SCIO requirement?",
            tool_context="Tool output: Section 44",
        )

    assert res == "OSCR regulatory response text"


def test_call_gemma_chat_without_tool_context(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "mock_groq_key")
    client = LLMClient()

    mock_resp_data = {"choices": [{"message": {"content": "Direct chat response"}}]}
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_resp_data

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_gemma_chat("System instruction", "User question")

    assert res == "Direct chat response"


def test_call_gemma_chat_http_500_fallback(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock_or_key")
    client = LLMClient()

    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("httpx.Client.post", return_value=mock_resp):
        res = client.call_gemma_chat("System", "User")

    assert res is None
