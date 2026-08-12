"""Cryptographic Engine for Beacon Compliance.

Strictly enforces Red-Line 3 & Rule 4 of beacon-financial-boundary:
Mandatory HMAC-based sign-off for trustee approvals (Chair, Secretary, Treasurer)
and AES-256-GCM encryption for stored R2 objects.
"""

import hashlib
import hmac
import os
from typing import NamedTuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class TrusteeApprovalSignature(NamedTuple):
    """Container for trustee sign-off data and HMAC digest."""

    trustee_id: str
    role: str
    deliverable_id: str
    run_id: str
    approval_hash: str
    timestamp_iso: str


def generate_trustee_hmac(
    trustee_secret: bytes,
    trustee_id: str,
    role: str,
    deliverable_id: str,
    run_id: str,
    deliverable_content_hash: str,
) -> str:
    """Generate per-trustee HMAC signature for deliverable sign-off."""
    if role not in {"Chair", "Secretary", "Treasurer"}:
        raise ValueError(f"Invalid trustee role '{role}'. Must be Chair, Secretary, or Treasurer.")

    message = f"{trustee_id}:{role}:{deliverable_id}:{run_id}:{deliverable_content_hash}".encode()
    signature = hmac.new(trustee_secret, message, hashlib.sha256).hexdigest()
    return signature


def verify_trustee_hmac(
    trustee_secret: bytes,
    trustee_id: str,
    role: str,
    deliverable_id: str,
    run_id: str,
    deliverable_content_hash: str,
    provided_signature: str,
) -> bool:
    """Verify trustee HMAC signature using constant-time digest comparison."""
    expected_signature = generate_trustee_hmac(
        trustee_secret=trustee_secret,
        trustee_id=trustee_id,
        role=role,
        deliverable_id=deliverable_id,
        run_id=run_id,
        deliverable_content_hash=deliverable_content_hash,
    )
    return hmac.compare_digest(expected_signature, provided_signature)


class AESGCMCipher:
    """AES-256-GCM encryption manager for Cloudflare R2 binary objects."""

    def __init__(self, key: bytes | None = None) -> None:
        self.key = key or os.urandom(32)
        if len(self.key) != 32:
            raise ValueError("AES-256-GCM key must be exactly 32 bytes.")
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, data: bytes) -> tuple[bytes, bytes]:
        """Encrypt payload data using AES-256-GCM. Returns (nonce, ciphertext)."""
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        return nonce, ciphertext

    def decrypt(self, nonce: bytes, ciphertext: bytes) -> bytes:
        """Decrypt ciphertext using AES-256-GCM and provided nonce."""
        return self.aesgcm.decrypt(nonce, ciphertext, None)
