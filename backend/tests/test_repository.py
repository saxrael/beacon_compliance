"""Unit tests for ComplianceRepository facade (test_repository.py)."""

from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.r2_client import R2StorageClient
from backend.src.db.repository import ComplianceRepository


def test_compliance_repository_financial_state_roundtrip():
    d1 = D1DatabaseClient(db_path=":memory:")
    r2 = R2StorageClient()
    repo = ComplianceRepository(db_client=d1, r2_client=r2)

    repo.save_financial_state(
        run_id="run_repo_001",
        fund="unrestricted_general",
        receipts={"total_receipts_decimal": "25000.00"},
        payments={"total_payments_decimal": "12000.00"},
        opening_balance_pence=1000000,
        closing_balance_pence=2300000,
    )

    state = repo.get_financial_state("run_repo_001")
    assert state is not None
    assert state["run_id"] == "run_repo_001"
    assert state["fund"] == "unrestricted_general"
    assert state["receipts"]["total_receipts_decimal"] == "25000.00"
    assert state["payments"]["total_payments_decimal"] == "12000.00"
    assert state["opening_balance_pence"] == 1000000
    assert state["closing_balance_pence"] == 2300000


def test_compliance_repository_classification_rule():
    d1 = D1DatabaseClient(db_path=":memory:")
    repo = ComplianceRepository(db_client=d1)

    rule = repo.save_classification_rule(
        rule_id="rule_test_01",
        pattern="St Mary Hall Rent",
        fund="unrestricted_general",
        category="Premises & Rent",
        created_from_txn_id="txn_01",
    )
    assert rule["rule_id"] == "rule_test_01"
    assert rule["category"] == "Premises & Rent"


def test_compliance_repository_blob_storage():
    d1 = D1DatabaseClient(db_path=":memory:")
    r2 = R2StorageClient()
    repo = ComplianceRepository(db_client=d1, r2_client=r2)

    content = b"Sample bank statement document"
    key = repo.store_document_blob(
        run_id="run_001",
        doc_id="doc_01",
        filename="statement.txt",
        content_bytes=content,
    )
    assert key == "documents/run_001/doc_01/statement.txt"

    fetched = repo.fetch_document_blob(key)
    assert fetched == content
