"""Unit tests for Google OAuth 2.0 and Session Authentication Flow (test_auth_google.py).

Verifies OAuth login initiation, code exchange callback, pre-approved trustee enforcement,
email/password login, first-login password resets, and session profile endpoints.
"""

import os

from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient
from fastapi.testclient import TestClient

client = TestClient(app)


def test_google_login_url_generation():
    """Test /api/auth/google/login generates valid state and authorization URL."""
    res = client.get("/api/auth/google/login")
    assert res.status_code == 200
    data = res.json()
    assert "auth_url" in data
    assert "state" in data
    assert "accounts.google.com" in data["auth_url"]


def test_google_oauth_callback_preapproved_trustee_success(tmp_path, monkeypatch):
    """Test Google OAuth callback succeeds for pre-approved trustee email."""
    db_path = str(tmp_path / "test_auth.db")
    db = D1DatabaseClient(db_path=db_path)

    # Provision pre-approved trustee
    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('usr_chair_1', 'chair@pottershouse.org.uk', 'pwd_hash', 'Chairperson Name', 'Chair', 1)"
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)
    monkeypatch.setenv("MOCK_GOOGLE_OAUTH", "true")
    monkeypatch.setenv("MOCK_GOOGLE_EMAIL", "chair@pottershouse.org.uk")
    monkeypatch.setenv("MOCK_GOOGLE_NAME", "Chairperson Name")

    res = client.get("/api/auth/google/callback?code=mock_code&state=mock_state")
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "chair@pottershouse.org.uk"
    assert data["user"]["role"] == "Chair"
    assert data["user"]["google_linked"] is True


def test_google_oauth_callback_unapproved_email_rejected(tmp_path, monkeypatch):
    """Test Google OAuth callback returns HTTP 403 Forbidden for non-provisioned emails."""
    db_path = str(tmp_path / "test_auth_reject.db")
    db = D1DatabaseClient(db_path=db_path)
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)
    monkeypatch.setenv("MOCK_GOOGLE_OAUTH", "true")
    monkeypatch.setenv("MOCK_GOOGLE_EMAIL", "unauthorized_hacker@gmail.com")

    res = client.get("/api/auth/google/callback?code=mock_code&state=mock_state")
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


def test_login_with_password_and_first_login_reset(tmp_path, monkeypatch):
    """Test email/password authentication and forced password reset on first login."""
    db_path = str(tmp_path / "test_login.db")
    db = D1DatabaseClient(db_path=db_path)

    import hashlib
    import hmac

    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    temp_pwd_hash = hmac.new(
        salt.encode("utf-8"),
        f"Temp_Password123!:{salt}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('usr_sec_1', 'secretary@pottershouse.org.uk', ?, 'Secretary Name', 'Secretary', 0)",
        (temp_pwd_hash,),
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    # 1. Login with temporary credentials
    login_res = client.post(
        "/api/auth/login",
        json={"email": "secretary@pottershouse.org.uk", "password": "Temp_Password123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["first_login_complete"] is False

    # 2. Reset password
    reset_res = client.post(
        "/api/auth/first-login-reset",
        json={
            "email": "secretary@pottershouse.org.uk",
            "current_password": "Temp_Password123!",
            "new_password": "NewPermanentPassword2026!",
        },
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["first_login_complete"] is True


def test_get_current_user_profile_me(tmp_path, monkeypatch):
    """Test /api/auth/me returns authenticated user profile."""
    db_path = str(tmp_path / "test_me.db")
    db = D1DatabaseClient(db_path=db_path)
    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('usr_dev_1', 'developer@pottershouse.org.uk', 'hash', 'Dev Engineer', 'Developer', 1)"
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    from backend.src.api.auth import create_jwt_token

    jwt_token = create_jwt_token(
        user_id="usr_dev_1", role="Developer", email="developer@pottershouse.org.uk"
    )

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {jwt_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == "usr_dev_1"
    assert data["role"] == "Developer"
