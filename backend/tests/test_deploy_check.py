"""Unit tests for Pre-Flight Deployment Audit Script (scripts/deploy_check.py)."""

from scripts.deploy_check import (
    check_crypto_secret_strength,
    check_document_templates,
    check_env_template_coverage,
    run_full_preflight_check,
)


def test_env_template_coverage():
    passed, msg = check_env_template_coverage()
    assert passed is True
    assert "covers all required" in msg


def test_crypto_secret_strength(monkeypatch):
    monkeypatch.setenv("AES_256_GCM_SECRET", "test_secret_32_bytes_long_high_entropy_beacon_2026")
    passed, msg = check_crypto_secret_strength()
    assert passed is True
    assert "verified" in msg


def test_document_templates_exist():
    passed, msg = check_document_templates()
    assert passed is True


def test_run_full_preflight_check(monkeypatch):
    monkeypatch.setenv("AES_256_GCM_SECRET", "test_secret_32_bytes_long_high_entropy_beacon_2026")
    success = run_full_preflight_check()
    assert success is True
