import hashlib
import hmac
import os

import pyotp
from fastapi.testclient import TestClient

from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient

client = TestClient(app)


def setup_test_env(tmp_path, monkeypatch, role="Trustee", email="test@pottershouse.org.uk"):
    db_path = str(tmp_path / "test_2fa.db")
    db = D1DatabaseClient(db_path=db_path)

    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    pwd_hash = hmac.new(
        salt.encode(), f"CurrentPassword123!:{salt }".encode(), hashlib.sha256
    ).hexdigest()

    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete, totp_enabled, totp_secret) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("user_123", email, pwd_hash, "Test User", role, 1, 0, None),
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    token = create_jwt_token("user_123", role=role, email=email)
    client.cookies.set("session_token", token)

    return D1DatabaseClient(db_path=db_path)


def test_generate_2fa_success(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)

    response = client.post("/api/settings/2fa/generate")
    assert response.status_code == 200
    data = response.json()
    assert "secret" in data
    assert "provisioning_uri" in data
    assert "otpauth://" in data["provisioning_uri"]

    user = db.fetchone("SELECT * FROM users WHERE user_id = 'user_123'")
    assert user["totp_secret"] == data["secret"]
    assert user["totp_enabled"] == 0
    db.close()


def test_enable_2fa_success(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)

    gen_res = client.post("/api/settings/2fa/generate")
    secret = gen_res.json()["secret"]

    totp = pyotp.TOTP(secret)
    code = totp.now()

    response = client.post("/api/settings/2fa/enable", json={"totp_code": code})
    assert response.status_code == 200

    user = db.fetchone("SELECT * FROM users WHERE user_id = 'user_123'")
    assert user["totp_enabled"] == 1
    db.close()


def test_enable_2fa_invalid_code(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)
    client.post("/api/settings/2fa/generate")

    response = client.post("/api/settings/2fa/enable", json={"totp_code": "000000"})
    assert response.status_code == 401
    assert "Invalid 2FA code" in response.json()["detail"]
    db.close()


def test_change_password_success_without_2fa(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)

    res = client.post(
        "/api/settings/password/change",
        json={
            "current_password": "CurrentPassword123!",
            "new_password": "BrandNewPassword2026!",
        },
    )

    assert res.status_code == 200
    assert res.json()["status"] == "success"
    db.close()


def test_change_password_incorrect_current_password(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)

    res = client.post(
        "/api/settings/password/change",
        json={
            "current_password": "WrongPassword123!",
            "new_password": "BrandNewPassword2026!",
        },
    )

    assert res.status_code == 401
    assert "Current password incorrect" in res.json()["detail"]
    db.close()


def test_change_password_short_new_password(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)

    res = client.post(
        "/api/settings/password/change",
        json={
            "current_password": "CurrentPassword123!",
            "new_password": "short",
        },
    )

    assert res.status_code == 400
    assert "at least 8 characters" in res.json()["detail"]
    db.close()


def test_change_password_with_2fa_flow(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)

    gen_res = client.post("/api/settings/2fa/generate")
    secret = gen_res.json()["secret"]
    totp = pyotp.TOTP(secret)

    client.post("/api/settings/2fa/enable", json={"totp_code": totp.now()})

    res_missing_2fa = client.post(
        "/api/settings/password/change",
        json={
            "current_password": "CurrentPassword123!",
            "new_password": "BrandNewPassword2026!",
        },
    )
    assert res_missing_2fa.status_code == 401
    assert "2FA code required" in res_missing_2fa.json()["detail"]

    res_bad_2fa = client.post(
        "/api/settings/password/change",
        json={
            "current_password": "CurrentPassword123!",
            "new_password": "BrandNewPassword2026!",
            "totp_code": "000000",
        },
    )
    assert res_bad_2fa.status_code == 401
    assert "Invalid 2FA code" in res_bad_2fa.json()["detail"]

    res_success = client.post(
        "/api/settings/password/change",
        json={
            "current_password": "CurrentPassword123!",
            "new_password": "BrandNewPassword2026!",
            "totp_code": totp.now(),
        },
    )
    assert res_success.status_code == 200
    assert res_success.json()["status"] == "success"
    db.close()


def test_get_and_update_profile_success(tmp_path, monkeypatch):
    db = setup_test_env(tmp_path, monkeypatch)

    get_res = client.get("/api/settings/profile")
    assert get_res.status_code == 200
    profile_data = get_res.json()
    assert profile_data["user_id"] == "user_123"
    assert profile_data["name"] == "Test User"
    assert profile_data["email"] == "test@pottershouse.org.uk"

    update_res = client.post(
        "/api/settings/profile/update",
        json={
            "name": "Updated Trustee Name",
            "email": "updated.trustee@pottershouse.org.uk",
            "avatar": "data:image/png;base64,mockavatarstring123",
        },
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["name"] == "Updated Trustee Name"
    assert updated_data["email"] == "updated.trustee@pottershouse.org.uk"
    assert updated_data["avatar"] == "data:image/png;base64,mockavatarstring123"

    user_in_db = db.fetchone("SELECT * FROM users WHERE user_id = 'user_123'")
    assert user_in_db["name"] == "Updated Trustee Name"
    assert user_in_db["email"] == "updated.trustee@pottershouse.org.uk"
    assert user_in_db["avatar"] == "data:image/png;base64,mockavatarstring123"

    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["avatar"] == "data:image/png;base64,mockavatarstring123"

    login_res = client.post(
        "/api/auth/login",
        json={"email": "updated.trustee@pottershouse.org.uk", "password": "CurrentPassword123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["avatar"] == "data:image/png;base64,mockavatarstring123"

    db.close()
