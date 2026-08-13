from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient
from fastapi.testclient import TestClient

client = TestClient(app)


def test_provision_trustee_success(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_admin.db")
    db = D1DatabaseClient(db_path=db_path)
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)
    monkeypatch.setenv("ADMIN_PROVISION_SECRET", "test_admin_secret")

    res = client.post(
        "/api/admin/provision-trustee",
        headers={"X-Admin-Secret": "test_admin_secret"},
        json={
            "email": "treasurer@pottershouse.org.uk",
            "name": "New Treasurer",
            "role": "Treasurer",
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "treasurer@pottershouse.org.uk"
    assert data["role"] == "Treasurer"
    assert "user_id" in data
    assert "temp_password" in data

    db_check = D1DatabaseClient(db_path=db_path)
    user = db_check.fetchone("SELECT * FROM users WHERE email = 'treasurer@pottershouse.org.uk'")
    assert user is not None
    assert user["role"] == "Treasurer"
    db_check.close()


def test_provision_trustee_unauthorized_secret(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_admin_unauth.db")
    db = D1DatabaseClient(db_path=db_path)
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)
    monkeypatch.setenv("ADMIN_PROVISION_SECRET", "correct_secret")

    res = client.post(
        "/api/admin/provision-trustee",
        headers={"X-Admin-Secret": "wrong_secret"},
        json={
            "email": "hacker@pottershouse.org.uk",
            "name": "Hacker",
            "role": "Chair",
        },
    )

    assert res.status_code == 401
    assert "Invalid admin provisioning secret" in res.json()["detail"]


def test_provision_trustee_invalid_role(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_admin_role.db")
    db = D1DatabaseClient(db_path=db_path)
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)
    monkeypatch.setenv("ADMIN_PROVISION_SECRET", "correct_secret")

    res = client.post(
        "/api/admin/provision-trustee",
        headers={"X-Admin-Secret": "correct_secret"},
        json={
            "email": "invalid_role@pottershouse.org.uk",
            "name": "Invalid Role User",
            "role": "SuperUser",
        },
    )

    assert res.status_code == 400
    assert "Invalid role 'SuperUser'" in res.json()["detail"]
