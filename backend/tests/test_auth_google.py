import hashlib
import hmac
import os

import pyotp
from fastapi.testclient import TestClient

from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient

client = TestClient(app)


def test_google_login_url_generation():
    res = client.get("/api/auth/google/login")
    assert res.status_code == 200
    data = res.json()
    assert "auth_url" in data
    assert "state" in data
    assert "accounts.google.com" in data["auth_url"]


def test_google_oauth_callback_preapproved_trustee_success(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_auth.db")
    db = D1DatabaseClient(db_path=db_path)

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
    db_path = str(tmp_path / "test_login.db")
    db = D1DatabaseClient(db_path=db_path)

    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    temp_pwd_hash = hmac.new(
        salt.encode(), f"Temp_Password123!:{salt }".encode(), hashlib.sha256
    ).hexdigest()

    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('usr_sec_1', 'secretary@pottershouse.org.uk', ?, 'Secretary Name', 'Secretary', 0)",
        (temp_pwd_hash,),
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    login_res = client.post(
        "/api/auth/login",
        json={"email": "secretary@pottershouse.org.uk", "password": "Temp_Password123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["first_login_complete"] is False

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
    db_path = str(tmp_path / "test_me.db")
    db = D1DatabaseClient(db_path=db_path)
    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('usr_dev_1', 'developer@pottershouse.org.uk', 'hash', 'Dev Engineer', 'Developer', 1)"
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    jwt_token = create_jwt_token(
        user_id="usr_dev_1", role="Developer", email="developer@pottershouse.org.uk"
    )

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {jwt_token }"})
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == "usr_dev_1"
    assert data["role"] == "Developer"


def test_login_with_2fa_flow(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_login_2fa.db")
    db = D1DatabaseClient(db_path=db_path)

    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)
    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    pwd_hash = hmac.new(
        salt.encode(), f"ValidPassword123!:{salt }".encode(), hashlib.sha256
    ).hexdigest()

    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete, totp_enabled, totp_secret) "
        "VALUES ('usr_2fa_1', '2fa_trustee@pottershouse.org.uk', ?, 'Trustee 2FA', 'Trustee', 1, 1, ?)",
        (pwd_hash, totp_secret),
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    login_res = client.post(
        "/api/auth/login",
        json={"email": "2fa_trustee@pottershouse.org.uk", "password": "ValidPassword123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["requires_2fa"] is True
    temp_token = login_data["access_token"]

    bad_token_res = client.post(
        "/api/auth/login/2fa",
        json={"temp_token": "invalid_jwt_token", "totp_code": totp.now()},
    )
    assert bad_token_res.status_code == 401

    bad_code_res = client.post(
        "/api/auth/login/2fa",
        json={"temp_token": temp_token, "totp_code": "000000"},
    )
    assert bad_code_res.status_code == 401

    success_res = client.post(
        "/api/auth/login/2fa",
        json={"temp_token": temp_token, "totp_code": totp.now()},
    )
    assert success_res.status_code == 200
    success_data = success_res.json()
    assert success_data["user"]["email"] == "2fa_trustee@pottershouse.org.uk"
    assert success_data["user"]["role"] == "Trustee"


def test_google_oauth_callback_with_2fa_enforcement(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test_auth_google_2fa.db")
    db = D1DatabaseClient(db_path=db_path)

    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)

    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete, totp_secret, totp_enabled) "
        "VALUES ('usr_chair_2fa', 'chair_2fa@pottershouse.org.uk', 'pwd_hash', 'Chairperson 2FA', 'Chair', 1, ?, 1)",
        (totp_secret,),
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)
    monkeypatch.setenv("MOCK_GOOGLE_OAUTH", "true")
    monkeypatch.setenv("MOCK_GOOGLE_EMAIL", "chair_2fa@pottershouse.org.uk")
    monkeypatch.setenv("MOCK_GOOGLE_NAME", "Chairperson 2FA")

    # Step 1: Google OAuth callback should require 2FA when totp_enabled is 1
    oauth_res = client.get("/api/auth/google/callback?code=mock_code&state=mock_state")
    assert oauth_res.status_code == 200
    oauth_data = oauth_res.json()
    assert oauth_data["requires_2fa"] is True
    assert "access_token" in oauth_data
    temp_token = oauth_data["access_token"]

    # Step 2: Complete 2FA verification with the TOTP code
    totp_res = client.post(
        "/api/auth/login/2fa",
        json={"temp_token": temp_token, "totp_code": totp.now()},
    )
    assert totp_res.status_code == 200
    totp_data = totp_res.json()
    assert totp_data["user"]["email"] == "chair_2fa@pottershouse.org.uk"
    assert totp_data["user"]["role"] == "Chair"


def test_logout_endpoint():
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    assert res.json()["status"] == "logged_out"
