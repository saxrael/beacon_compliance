import pytest
from backend.src.core.crypto import (
    AESGCMCipher,
    generate_trustee_hmac,
    verify_trustee_hmac,
)
from cryptography.exceptions import InvalidTag


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
    assert len(signature) == 64
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
    with pytest.raises(ValueError, match="Invalid trustee role"):
        generate_trustee_hmac(
            trustee_secret=b"secret",
            trustee_id="u1",
            role="Auditor",
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


def test_aes_gcm_invalid_key_length_value_error():
    with pytest.raises(ValueError, match="AES-256-GCM key must be exactly 32 bytes"):
        AESGCMCipher(key=b"invalid_short_key")


def test_aes_gcm_decryption_invalid_tag_error():
    cipher = AESGCMCipher()
    payload = b"Confidential financial statement"
    nonce, ciphertext = cipher.encrypt(payload)

    corrupted_ciphertext = (
        ciphertext[:-1] + b"\x00"
        if ciphertext[-1:] != b"\x00"
        else ciphertext[:-1] + b"\xff"
    )
    with pytest.raises(InvalidTag):
        cipher.decrypt(nonce, corrupted_ciphertext)
