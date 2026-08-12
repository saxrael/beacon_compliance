"""Unit tests for Cryptographic Sign-Off & Encryption Engine (backend/src/core/crypto.py).

Verifies Red-Line 3 & Rule 4 of beacon-financial-boundary.
"""

import pytest
from backend.src.core.crypto import (
    AESGCMCipher,
    generate_trustee_hmac,
    verify_trustee_hmac,
)


def test_trustee_hmac_signoff_verification():
    secret = b"trustee_secret_key_123456789012"
    trustee_id = "trustee_001"
    role = "Treasurer"
    deliverable_id = "deliv_tar_2026"
    run_id = "run_2026_001"
    content_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    signature = generate_trustee_hmac(
        trustee_secret=secret,
        trustee_id=trustee_id,
        role=role,
        deliverable_id=deliverable_id,
        run_id=run_id,
        deliverable_content_hash=content_hash,
    )

    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA-256 hex digest length

    # Verify signature passes with exact credentials
    is_valid = verify_trustee_hmac(
        trustee_secret=secret,
        trustee_id=trustee_id,
        role=role,
        deliverable_id=deliverable_id,
        run_id=run_id,
        deliverable_content_hash=content_hash,
        provided_signature=signature,
    )
    assert is_valid is True

    # Verify signature fails with tampered content hash
    tampered_valid = verify_trustee_hmac(
        trustee_secret=secret,
        trustee_id=trustee_id,
        role=role,
        deliverable_id=deliverable_id,
        run_id=run_id,
        deliverable_content_hash="tampered_hash",
        provided_signature=signature,
    )
    assert tampered_valid is False


def test_invalid_trustee_role_rejection():
    """Verify non-trustee roles are rejected."""
    with pytest.raises(ValueError, match="Invalid trustee role"):
        generate_trustee_hmac(
            trustee_secret=b"secret",
            trustee_id="u1",
            role="Auditor",  # Only Chair, Secretary, Treasurer allowed
            deliverable_id="d1",
            run_id="r1",
            deliverable_content_hash="hash",
        )


def test_aes_gcm_encryption_roundtrip():
    cipher = AESGCMCipher()
    payload = b"Sensitive Trustee Document Content"

    nonce, ciphertext = cipher.encrypt(payload)
    assert ciphertext != payload

    decrypted = cipher.decrypt(nonce, ciphertext)
    assert decrypted == payload
