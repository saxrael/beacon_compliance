from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_auth_env(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_classify.db")
    db = D1DatabaseClient(db_path=db_path)
    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('user_classify_1', 'treasurer@pottershouse.org.uk', 'hash', 'Treasurer Name', 'Treasurer', 1)"
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    token = create_jwt_token(
        user_id="user_classify_1",
        role="Treasurer",
        email="treasurer@pottershouse.org.uk",
    )
    headers = {"Authorization": f"Bearer {token}"}
    return headers, db_path


def test_get_pending_classifications_endpoint(tmp_path, monkeypatch):
    headers, _db_path = setup_auth_env(tmp_path, monkeypatch)

    res = client.get("/api/classify/pending?run_id=run_test_01", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] == "run_test_01"
    assert data["total_classified"] > 0
    assert len(data["classified_transactions"]) > 0


def test_confirm_classification_endpoint(tmp_path, monkeypatch):
    headers, _db_path = setup_auth_env(tmp_path, monkeypatch)

    res = client.post(
        "/api/classify/confirm",
        headers=headers,
        json={
            "txn_id": "txn_101",
            "description": "Hall Rent Payment",
            "confirmed_fund": "unrestricted_general",
            "confirmed_category": "Premises Rent & Utility",
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert data["rule_created"]["rule_id"] == "rule_txn_101"
    assert data["rule_created"]["category"] == "Premises Rent & Utility"
