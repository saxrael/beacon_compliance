"""Account Settings & Security API Routes (routes_settings.py).

Provides endpoints for 2FA (TOTP) generation, enabling, and password changing.
"""

import hashlib
import hmac
import os

import pyotp
from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_d1_db
from backend.src.db.d1_client import D1DatabaseClient
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class Generate2FAResponse(BaseModel):
    secret: str
    provisioning_uri: str


class Enable2FARequest(BaseModel):
    totp_code: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    totp_code: str | None = None


@router.post("/2fa/generate", response_model=Generate2FAResponse)
async def generate_2fa(
    current_user: TrusteeUser = Depends(get_current_trustee),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> Generate2FAResponse:
    """Generate a new TOTP secret for the authenticated user."""
    user = db.fetchone("SELECT * FROM users WHERE user_id = ?", (current_user.user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="2FA is already enabled.")

    secret = pyotp.random_base32()

    db.execute("UPDATE users SET totp_secret = ? WHERE user_id = ?", (secret, current_user.user_id))

    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email, issuer_name="Beacon Compliance"
    )

    return Generate2FAResponse(secret=secret, provisioning_uri=provisioning_uri)


@router.post("/2fa/enable")
async def enable_2fa(
    req: Enable2FARequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> dict[str, str]:
    """Verify the first TOTP code and enable 2FA."""
    user = db.fetchone("SELECT * FROM users WHERE user_id = ?", (current_user.user_id,))

    if not user or not user.get("totp_secret"):
        raise HTTPException(status_code=400, detail="No 2FA secret generated.")

    if user.get("totp_enabled"):
        raise HTTPException(status_code=400, detail="2FA is already enabled.")

    totp = pyotp.TOTP(user["totp_secret"])
    if not totp.verify(req.totp_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code.")

    db.execute("UPDATE users SET totp_enabled = 1 WHERE user_id = ?", (current_user.user_id,))

    return {"status": "success", "message": "2FA successfully enabled."}


@router.post("/password/change")
async def change_password(
    req: PasswordChangeRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> dict[str, str]:
    """Change user password, enforcing 2FA if enabled."""
    user = db.fetchone("SELECT * FROM users WHERE user_id = ?", (current_user.user_id,))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    curr_pwd_hash = hmac.new(
        salt.encode(), f"{req .current_password }:{salt }".encode(), hashlib.sha256
    ).hexdigest()

    if curr_pwd_hash != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Current password incorrect.")

    if user.get("totp_enabled"):
        if not req.totp_code:
            raise HTTPException(status_code=401, detail="2FA code required to change password.")
        totp = pyotp.TOTP(user["totp_secret"])
        if not totp.verify(req.totp_code):
            raise HTTPException(status_code=401, detail="Invalid 2FA code.")

    if len(req.new_password) < 8:
        raise HTTPException(
            status_code=400, detail="New password must be at least 8 characters long."
        )

    new_pwd_hash = hmac.new(
        salt.encode(), f"{req .new_password }:{salt }".encode(), hashlib.sha256
    ).hexdigest()

    db.execute(
        "UPDATE users SET password_hash = ? WHERE user_id = ?",
        (new_pwd_hash, current_user.user_id),
    )

    return {"status": "success", "message": "Password updated successfully."}
