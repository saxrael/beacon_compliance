"""Unit tests for Chat API Endpoints (GET /api/chat/history, POST /api/chat/message, POST /api/chat/stream)."""

from fastapi.testclient import TestClient

from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app

client = TestClient(app)


def test_chat_message_and_history_persistence():
    token = create_jwt_token(
        {
            "user_id": "usr_chat_test_1",
            "name": "Trustee Tester",
            "email": "tester@pottershouse.org.uk",
            "role": "Trustee",
        }
    )
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/chat/message",
        headers=headers,
        json={
            "message": "What is the OSCR annual return deadline?",
            "run_id": "run_test_chat_01",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert len(data["message"]) > 0

    hist_res = client.get(
        "/api/chat/history?run_id=run_test_chat_01&limit=50",
        headers=headers,
    )
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert hist_data["total_count"] >= 2
    assert len(hist_data["messages"]) >= 2
    assert hist_data["messages"][-2]["role"] == "user"
    assert hist_data["messages"][-2]["content"] == "What is the OSCR annual return deadline?"
    assert hist_data["messages"][-1]["role"] == "assistant"


def test_chat_stream_sse_endpoint():
    token = create_jwt_token(
        {
            "user_id": "usr_stream_test_2",
            "name": "Pastor Stream",
            "email": "stream@pottershouse.org.uk",
            "role": "Chair",
        }
    )
    headers = {"Authorization": f"Bearer {token}"}

    with client.stream(
        "POST",
        "/api/chat/stream",
        headers=headers,
        json={
            "message": "What are the Receipts and Payments financial thresholds?",
            "run_id": "run_test_stream_01",
        },
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        events_text = "".join(response.iter_text())
        assert (
            "event: thought" in events_text
            or "event: action" in events_text
            or "event: token" in events_text
        )
        assert "event: done" in events_text
