import io

from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_ingest_auth_env(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_ingest.db")
    db = D1DatabaseClient(db_path=db_path)
    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('user_ingest_1', 'secretary@pottershouse.org.uk', 'hash', 'Secretary Name', 'Secretary', 1)"
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    token = create_jwt_token(
        user_id="user_ingest_1",
        role="Secretary",
        email="secretary@pottershouse.org.uk",
    )
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def test_upload_documents_endpoint(tmp_path, monkeypatch):
    headers = setup_ingest_auth_env(tmp_path, monkeypatch)

    file1_content = b"Potter's House Sunday Tithes 2026. Contact john.doe@example.com."
    file2_content = b"Premises rent invoice for St Mary Hall."

    files = [
        ("files", ("tithes.txt", io.BytesIO(file1_content), "text/plain")),
        ("files", ("rent.txt", io.BytesIO(file2_content), "text/plain")),
    ]

    res = client.post(
        "/api/ingest/upload?run_id=run_ingest_001",
        headers=headers,
        files=files,
    )

    assert res.status_code == 200
    data = res.json()
    assert data["run_id"] == "run_ingest_001"
    assert data["documents_processed"] == 2
    assert "anonymised_payload" in data
    assert data["pii_audit_count"] >= 1
