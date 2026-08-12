"""Node 1: Document Ingestion & PII Anonymization Engine (node_ingest.py).

Enforces:
- Red-Line 4: PII Boundary Enforcement (raw documents stay pre-scrub only, never LLM-eligible)
- Rule 5 of beacon-financial-boundary: Independent Ingest-Layer Income Threshold Check
"""

from typing import Any

from backend.src.agents.state import BeaconComplianceState
from backend.src.core.financial import check_income_threshold
from backend.src.core.ocr_engine import MultiFormatDocumentExtractor
from backend.src.core.pii_engine import default_redactor


def run_node_ingest(state: BeaconComplianceState) -> dict[str, Any]:
    """LangGraph Node 1: Ingests raw documents, performs PII scrubbing, and checks ingest income limit."""
    raw_docs = state.get("raw_documents", [])
    extractor = MultiFormatDocumentExtractor(confidence_threshold=0.90)

    anonymised_docs: list[dict[str, Any]] = []
    pii_audit_log: list[dict[str, Any]] = []
    ocr_flags: list[dict[str, Any]] = []
    raw_receipts_total_pence = 0

    for doc_item in raw_docs:
        doc_id = doc_item.get("doc_id", "doc_unknown")
        filename = doc_item.get("filename", "document.txt")
        content_bytes = doc_item.get("content_bytes", b"")

        extraction_res, ocr_flag = extractor.extract_document(
            doc_id=doc_id, filename=filename, content_bytes=content_bytes
        )

        if ocr_flag:
            ocr_flags.append(ocr_flag.model_dump())

        clean_text, audit_rec = default_redactor.redact_text(
            text=extraction_res.extracted_text, field_name=f"doc_{doc_id}"
        )
        pii_audit_log.append(audit_rec.model_dump())

        anonymised_docs.append(
            {
                "doc_id": doc_id,
                "filename": filename,
                "anonymised_text": clean_text,
                "ocr_confidence": extraction_res.ocr_confidence_avg,
            }
        )

        doc_declared_pence = doc_item.get("declared_receipts_pence", 0)
        raw_receipts_total_pence += doc_declared_pence

    ingest_threshold_breach = check_income_threshold(
        raw_receipts_total_pence, threshold_pounds=250000
    )

    opening_pence = state.get("anonymised_payload", {}).get("opening_balance_pence", 0)
    closing_pence = state.get("anonymised_payload", {}).get("closing_balance_pence", 0)

    anonymised_payload = {
        "documents": anonymised_docs,
        "opening_balance_pence": opening_pence,
        "closing_balance_pence": closing_pence,
        "raw_receipts_total_pence": raw_receipts_total_pence,
    }

    return {
        "anonymised_payload": anonymised_payload,
        "pii_audit_log": pii_audit_log,
        "ocr_flags": ocr_flags,
        "income_threshold_breach": ingest_threshold_breach,
    }
