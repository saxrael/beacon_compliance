"""Unit tests for FastAPI REST API Endpoints (backend/tests/test_api_endpoints.py)."""

from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["charity"] == "SC054652"


def test_signoff_endpoint_valid_role():
    token = create_jwt_token(
        {
            "user_id": "trustee_001",
            "name": "Treasurer User",
            "email": "treasurer@pottershouse.org.uk",
            "role": "Treasurer",
        }
    )
    res = client.post(
        "/api/signoff/approve",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "trustee_role": "Treasurer",
            "trustee_secret": "secret_treasurer_key_123",
            "deliverable_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "run_id": "run_001",
            "trustee_id": "trustee_001",
            "deliverable_id": "deliv_001",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "approved"
    assert data["trustee_role"] == "Treasurer"
    assert data["verified"] is True


def test_signoff_endpoint_unauthorized_role_rejected():
    res = client.post(
        "/api/signoff/approve",
        json={
            "trustee_role": "unauthorized_role",
            "trustee_secret": "secret_key",
            "deliverable_hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
            "run_id": "run_001",
            "trustee_id": "trustee_001",
            "deliverable_id": "deliv_001",
        },
    )
    assert res.status_code == 403


def test_pipeline_run_endpoint():
    res = client.post(
        "/api/pipeline/run",
        json={
            "run_id": "run_test_api",
            "opening_balance_pence": 500000,
            "closing_balance_pence": 2000000,
            "raw_transactions": [
                {
                    "txn_id": "TXN_API_1",
                    "description": "Sunday Tithes",
                    "amount_pence": 1500000,
                    "transaction_type": "receipt",
                }
            ],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["deliverables_ready"] is True
    assert len(data["deliverables"]) == 4
