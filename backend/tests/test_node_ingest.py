"""Unit tests for Node 1 Document Ingestion (backend/src/agents/node_ingest.py).

Verifies Red-Line 4 PII scrubbing and Rule 5 Ingest-Layer Income Threshold Check.
"""

from backend.src.agents.node_ingest import run_node_ingest
from backend.src.agents.state import BeaconComplianceState


def test_node_ingest_normal():
    state: BeaconComplianceState = {
        "run_id": "run_ingest_001",
        "charity_number": "SC054652",
        "raw_documents": [
            {
                "doc_id": "doc_1",
                "filename": "bank_statement.txt",
                "content_bytes": b"Bank statement for john.doe@example.com account 12345678",
                "declared_receipts_pence": 5000000,
            }
        ],
        "anonymised_payload": {
            "opening_balance_pence": 100000,
            "closing_balance_pence": 5100000,
        },
    }

    res = run_node_ingest(state)

    assert res["income_threshold_breach"] is False
    assert len(res["anonymised_payload"]["documents"]) == 1
    clean_text = res["anonymised_payload"]["documents"][0]["anonymised_text"]
    assert "john.doe@example.com" not in clean_text
    assert "12345678" not in clean_text
    assert len(res["pii_audit_log"]) == 1


def test_node_ingest_income_threshold_breach():
    """Rule 5 Test: Independent Ingest-Layer Income Threshold Check (£250,000 limit)."""
    state: BeaconComplianceState = {
        "run_id": "run_ingest_breach",
        "charity_number": "SC054652",
        "raw_documents": [
            {
                "doc_id": "doc_large",
                "filename": "large_legacy_statement.txt",
                "content_bytes": b"Legacy donation receipt",
                "declared_receipts_pence": 25000000,
            }
        ],
    }

    res = run_node_ingest(state)
    assert res["income_threshold_breach"] is True
