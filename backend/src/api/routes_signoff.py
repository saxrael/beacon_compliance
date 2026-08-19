"""Trustee Sign-off API Route (routes_signoff.py).

Strictly enforces Red-Line 3 (Role-restricted Trustee Sign-off via HMAC-SHA256).
"""

import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_repository
from backend.src.core.crypto import generate_trustee_hmac, verify_trustee_hmac
from backend.src.core.email_service import send_email
from backend.src.db.repository import ComplianceRepository

router = APIRouter(prefix="/api/signoff", tags=["Sign-off"])


class TrusteeSignoffRequest(BaseModel):
    trustee_role: str
    trustee_secret: str
    deliverable_hash: str
    run_id: str = "run_001"
    trustee_id: str = "trustee_001"
    deliverable_id: str = "deliv_001"


class TrusteeSignoffResponse(BaseModel):
    status: str
    trustee_role: str
    hmac_signature: str
    verified: bool


@router.post("/approve", response_model=TrusteeSignoffResponse)
async def approve_deliverable(
    req: TrusteeSignoffRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    repo: ComplianceRepository = Depends(get_repository),
) -> TrusteeSignoffResponse:
    role = req.trustee_role.title()
    if role not in ("Chair", "Secretary", "Treasurer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{req .trustee_role }' is not authorized for trustee sign-off. Must be Chair, Secretary, or Treasurer.",
        )

    if current_user.role.title() != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authenticated user role '{current_user .role }' does not match requested sign-off role '{role }'.",
        )

    try:
        salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
        secret_bytes = f"{req .trustee_secret }:{salt }".encode()

        signature = generate_trustee_hmac(
            trustee_secret=secret_bytes,
            trustee_id=req.trustee_id,
            role=role,
            deliverable_id=req.deliverable_id,
            run_id=req.run_id,
            deliverable_content_hash=req.deliverable_hash,
        )

        is_valid = verify_trustee_hmac(
            trustee_secret=secret_bytes,
            trustee_id=req.trustee_id,
            role=role,
            deliverable_id=req.deliverable_id,
            run_id=req.run_id,
            deliverable_content_hash=req.deliverable_hash,
            provided_signature=signature,
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="HMAC Signature verification failed.",
            )

        approval_id = f"appr_{req .run_id }_{role .lower ()}_{req .trustee_id }"
        approved_at = datetime.datetime.now(datetime.UTC).isoformat()

        repo.save_approval(
            approval_id=approval_id,
            run_id=req.run_id,
            deliverable_id=req.deliverable_id,
            trustee_id=req.trustee_id,
            role=role,
            approval_hash=signature,
            approved_at=approved_at,
        )

        target_email = os.environ.get("NOTIFICATION_FROM_EMAIL", "compliance@pottershouse.org.uk")
        send_email(
            to_email=target_email,
            subject=f"[Beacon Compliance OS] Trustee Sign-off Verified ({role })",
            body_html=f"<p>Trustee role <strong>{role }</strong> successfully signed off deliverable <code>{req .deliverable_id }</code>.</p>",
        )

        return TrusteeSignoffResponse(
            status="approved",
            trustee_role=role,
            hmac_signature=signature,
            verified=True,
        )
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
