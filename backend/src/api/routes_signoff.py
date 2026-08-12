"""Trustee Sign-off API Route (routes_signoff.py).

Strictly enforces Red-Line 3 (Role-restricted Trustee Sign-off via HMAC-SHA256).
"""

from backend.src.core.crypto import generate_trustee_hmac, verify_trustee_hmac
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/signoff", tags=["Sign-off"])


class TrusteeSignoffRequest(BaseModel):
    trustee_role: str  # 'Chair', 'Secretary', 'Treasurer'
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
async def approve_deliverable(req: TrusteeSignoffRequest) -> TrusteeSignoffResponse:
    role = req.trustee_role.title()
    if role not in ("Chair", "Secretary", "Treasurer"):
        raise HTTPException(
            status_code=403,
            detail=f"Role '{req.trustee_role}' is not authorized for trustee sign-off. Must be Chair, Secretary, or Treasurer.",
        )

    try:
        secret_bytes = req.trustee_secret.encode("utf-8")
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
            raise HTTPException(status_code=401, detail="HMAC Signature verification failed.")

        return TrusteeSignoffResponse(
            status="approved",
            trustee_role=role,
            hmac_signature=signature,
            verified=True,
        )
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
