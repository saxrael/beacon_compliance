from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.repository import ComplianceRepository
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_deliverables_env(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_deliv.db")
    db = D1DatabaseClient(db_path=db_path)
    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('user_deliv_1', 'chair@pottershouse.org.uk', 'hash', 'Chair Name', 'Chair', 1)"
    )

    repo = ComplianceRepository(db_client=db)
    repo.save_financial_state(
        run_id="run_deliv_2026",
        fund="unrestricted_general",
        receipts={"total_receipts_decimal": "150000.00", "gross_receipts_decimal": "150000.00"},
        payments={"total_payments_decimal": "80000.00", "gross_payments_decimal": "80000.00"},
        opening_balance_pence=1000000,
        closing_balance_pence=8000000,
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    token = create_jwt_token(
        user_id="user_deliv_1", role="Chair", email="chair@pottershouse.org.uk"
    )
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def test_get_deliverables_success(tmp_path, monkeypatch):
    headers = setup_deliverables_env(tmp_path, monkeypatch)

    res = client.get("/api/deliverables/run_deliv_2026", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] == "run_deliv_2026"
    assert data["deliverables_ready"] is True
    assert len(data["deliverables"]) > 0


def test_get_deliverables_not_found(tmp_path, monkeypatch):
    headers = setup_deliverables_env(tmp_path, monkeypatch)

    res = client.get("/api/deliverables/nonexistent_run_999", headers=headers)
    assert res.status_code == 404
    assert "Financial state for run_id 'nonexistent_run_999' not found" in res.json()["detail"]
