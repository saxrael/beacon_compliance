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

    missing_state = repo.get_financial_state("non_existent_run")
    assert missing_state is None


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


def test_save_approval_and_get_approvals_for_run():
    d1 = D1DatabaseClient(db_path=":memory:")
    repo = ComplianceRepository(db_client=d1)

    approval_res = repo.save_approval(
        approval_id="appr_001",
        run_id="run_2026_signoff",
        deliverable_id="deliv_tar",
        trustee_id="usr_treasurer_1",
        role="Treasurer",
        approval_hash="hash_signature_64_bytes_hmac_digest_mock_value",
        approved_at="2026-08-13T12:00:00Z",
    )

    assert approval_res["approval_id"] == "appr_001"
    assert approval_res["role"] == "Treasurer"

    approvals = repo.get_approvals_for_run("run_2026_signoff")
    assert len(approvals) == 1
    assert approvals[0]["approval_id"] == "appr_001"
    assert approvals[0]["trustee_id"] == "usr_treasurer_1"
    assert approvals[0]["role"] == "Treasurer"

    empty_approvals = repo.get_approvals_for_run("non_existent_run")
    assert len(empty_approvals) == 0


def test_get_transactions_for_run():
    d1 = D1DatabaseClient(db_path=":memory:")
    repo = ComplianceRepository(db_client=d1)

    d1.execute(
        """INSERT INTO transactions 
           (txn_id, run_id, date, description, amount_pence, fund, category, classification_tier, classification_confidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "txn_999",
            "run_txns_01",
            "2026-01-10",
            "Sunday Collection",
            50000,
            "unrestricted_general",
            "Donations & Offerings",
            "1",
            1.0,
        ),
    )

    txns = repo.get_transactions_for_run("run_txns_01")
    assert len(txns) == 1
    assert txns[0]["txn_id"] == "txn_999"
    assert txns[0]["description"] == "Sunday Collection"
    assert txns[0]["amount_pence"] == 50000
