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


def test_chat_message_persistence_and_pagination():
    d1 = D1DatabaseClient(db_path=":memory:")
    repo = ComplianceRepository(db_client=d1)

    d1.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role) VALUES (?, ?, ?, ?, ?)",
        ("usr_001", "trustee@pottershouse.org.uk", "hash", "Pastor John", "Trustee"),
    )

    for i in range(60):
        repo.save_chat_message(
            message_id=f"msg_{i:03d}",
            user_id="usr_001",
            run_id="run_chat_test",
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message turn number {i}",
            created_at=f"2026-08-19T01:{i:02d}:00Z",
        )

    res = repo.get_chat_history(user_id="usr_001", run_id="run_chat_test", limit=50, offset=0)
    assert res["total_count"] == 60
    assert len(res["messages"]) == 50
    assert res["has_more"] is True
    assert res["messages"][0]["message_id"] == "msg_010"
    assert res["messages"][-1]["message_id"] == "msg_059"

    older_res = repo.get_chat_history(
        user_id="usr_001", run_id="run_chat_test", limit=50, offset=50
    )
    assert len(older_res["messages"]) == 10
    assert older_res["has_more"] is False
    assert older_res["messages"][0]["message_id"] == "msg_000"
    assert older_res["messages"][-1]["message_id"] == "msg_009"


def test_cognitive_memory_facts_and_summaries():
    d1 = D1DatabaseClient(db_path=":memory:")
    repo = ComplianceRepository(db_client=d1)

    repo.save_memory_summary(
        user_id="usr_001",
        run_id="run_001",
        summary_text="Trustee prefers detailed breakdown of mission fund grants.",
        updated_at="2026-08-19T02:00:00Z",
    )
    summary = repo.get_memory_summary("usr_001", "run_001")
    assert summary == "Trustee prefers detailed breakdown of mission fund grants."

    repo.save_memory_fact(
        fact_id="fact_001",
        user_id="usr_001",
        fact_text="Potter's House UK operates a community outreach program in Dunbar.",
        source_type="conversation",
        created_at="2026-08-19T02:00:00Z",
    )
    facts = repo.get_memory_facts("usr_001")
    assert len(facts) == 1
    assert facts[0]["fact_id"] == "fact_001"
    assert "Dunbar" in facts[0]["fact_text"]


def test_user_profile_crud():
    d1 = D1DatabaseClient(db_path=":memory:")
    repo = ComplianceRepository(db_client=d1)

    d1.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role) VALUES (?, ?, ?, ?, ?)",
        ("usr_002", "chair@pottershouse.org.uk", "hash", "Original Name", "Chair"),
    )

    profile = repo.get_user_profile("usr_002")
    assert profile is not None
    assert profile["name"] == "Original Name"

    updated = repo.update_user_profile(
        "usr_002",
        name="Updated Chair Name",
        email="new_chair@pottershouse.org.uk",
        avatar="data:image/jpeg;base64,/9j/4AAQSkZJRg==",
    )
    assert updated["name"] == "Updated Chair Name"
    assert updated["email"] == "new_chair@pottershouse.org.uk"
    assert updated["avatar"] == "data:image/jpeg;base64,/9j/4AAQSkZJRg=="

    cleared = repo.update_user_profile(
        "usr_002",
        avatar="",
    )
    assert cleared["avatar"] == ""
    assert cleared["name"] == "Updated Chair Name"


def test_user_profile_migration_on_preexisting_table():
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE users ("
        "user_id TEXT PRIMARY KEY, "
        "email TEXT UNIQUE NOT NULL, "
        "password_hash TEXT NOT NULL, "
        "name TEXT NOT NULL, "
        "role TEXT NOT NULL"
        ")"
    )
    conn.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role) VALUES (?, ?, ?, ?, ?)",
        ("usr_legacy", "legacy@pottershouse.org.uk", "hash123", "Legacy Trustee", "Trustee"),
    )

    d1 = D1DatabaseClient(db_path=":memory:")
    d1._conn = conn
    d1.init_schema()

    repo = ComplianceRepository(db_client=d1)
    updated = repo.update_user_profile(
        "usr_legacy",
        name="Migrated Trustee",
        avatar="data:image/jpeg;base64,mockavatarlegacy",
    )
    assert updated["name"] == "Migrated Trustee"
    assert updated["avatar"] == "data:image/jpeg;base64,mockavatarlegacy"

    fetched = repo.get_user_profile("usr_legacy")
    assert fetched is not None
    assert fetched["avatar"] == "data:image/jpeg;base64,mockavatarlegacy"

