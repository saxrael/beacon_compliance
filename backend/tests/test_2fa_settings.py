"""Tests for 2FA settings and password changes (test_2fa_settings.py)."""

import pyotp 
from backend .src .api .auth import create_jwt_token 
from backend .src .api .main import app 
from backend .src .db .d1_client import D1DatabaseClient 
from fastapi .testclient import TestClient 

client =TestClient (app )


def setup_test_env (tmp_path ,monkeypatch ,role ="Trustee",email ="test@pottershouse.org.uk"):
    db_path =str (tmp_path /"test_2fa.db")
    db =D1DatabaseClient (db_path =db_path )
    db .execute (
    "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete, totp_enabled, totp_secret) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
    ("user_123",email ,"mockhash","Test User",role ,1 ,0 ,None ),
    )
    db .close ()

    monkeypatch .setenv ("D1_DB_PATH",db_path )

    token =create_jwt_token ("user_123",role =role ,email =email )
    client .cookies .set ("session_token",token )

    return D1DatabaseClient (db_path =db_path )


def test_generate_2fa_success (tmp_path ,monkeypatch ):
    db =setup_test_env (tmp_path ,monkeypatch )

    response =client .post ("/api/settings/2fa/generate")
    assert response .status_code ==200 
    data =response .json ()
    assert "secret"in data 
    assert "provisioning_uri"in data 
    assert "otpauth://"in data ["provisioning_uri"]

    user =db .fetchone ("SELECT * FROM users WHERE user_id = 'user_123'")
    assert user ["totp_secret"]==data ["secret"]
    assert user ["totp_enabled"]==0 
    db .close ()


def test_enable_2fa_success (tmp_path ,monkeypatch ):
    db =setup_test_env (tmp_path ,monkeypatch )

    gen_res =client .post ("/api/settings/2fa/generate")
    secret =gen_res .json ()["secret"]

    totp =pyotp .TOTP (secret )
    code =totp .now ()

    response =client .post ("/api/settings/2fa/enable",json ={"totp_code":code })
    assert response .status_code ==200 

    user =db .fetchone ("SELECT * FROM users WHERE user_id = 'user_123'")
    assert user ["totp_enabled"]==1 
    db .close ()


def test_enable_2fa_invalid_code (tmp_path ,monkeypatch ):
    db =setup_test_env (tmp_path ,monkeypatch )
    client .post ("/api/settings/2fa/generate")

    response =client .post ("/api/settings/2fa/enable",json ={"totp_code":"000000"})
    assert response .status_code ==401 
    assert "Invalid 2FA code"in response .json ()["detail"]
    db .close ()
