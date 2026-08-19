"""Document Ingestion API Route (routes_ingest.py).

Handles document upload, triggers Node 1 OCR extraction and PII scrubbing (Red-Line 4).
"""

from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel

from backend.src.agents.node_ingest import run_node_ingest
from backend.src.agents.state import BeaconComplianceState
from backend.src.api.auth import TrusteeUser, get_current_trustee

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


class IngestResponse(BaseModel):
    run_id: str
    documents_processed: int
    pii_audit_count: int
    ocr_flags_count: int
    income_threshold_breach: bool
    anonymised_payload: dict[str, Any]


@router.post("/upload", response_model=IngestResponse)
async def upload_documents(
    run_id: str = "run_001",
    files: list[UploadFile] = File(...),
    current_user: TrusteeUser = Depends(get_current_trustee),
) -> IngestResponse:
    raw_documents = []
    for idx, f in enumerate(files):
        content = await f.read()
        raw_documents.append(
            {
                "doc_id": f"doc_{idx +1 }",
                "filename": f.filename or f"doc_{idx +1 }.txt",
                "content_bytes": content,
                "declared_receipts_pence": 0,
            }
        )

    initial_state: BeaconComplianceState = {
        "run_id": run_id,
        "charity_number": "SC054652",
        "raw_documents": raw_documents,
    }

    ingest_result = run_node_ingest(initial_state)

    return IngestResponse(
        run_id=run_id,
        documents_processed=len(files),
        pii_audit_count=len(ingest_result.get("pii_audit_log", [])),
        ocr_flags_count=len(ingest_result.get("ocr_flags", [])),
        income_threshold_breach=ingest_result.get("income_threshold_breach", False),
        anonymised_payload=ingest_result.get("anonymised_payload", {}),
    )
