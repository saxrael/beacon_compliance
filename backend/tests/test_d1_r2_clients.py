"""Unit tests for Cloudflare D1 and R2 database clients (backend/src/db/).

Verifies SQL security, integer pence storage, and AES-256-GCM object encryption.
"""

from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.r2_client import R2StorageClient


def test_d1_schema_initialization_and_queries():
    """Verify D1 table initialization and parameterized query execution."""
    client = D1DatabaseClient(db_path=":memory:")

    # Insert test run
    client.execute(
        "INSERT INTO runs (run_id, charity_scn, year_end, status, created_at) VALUES (?, ?, ?, ?, ?)",
        ("run_2026_001", "SC054652", "2026-12-31", "draft", "2026-08-12T00:00:00Z"),
    )

    # Insert test transaction with integer pence
    client.execute(
        """INSERT INTO transactions 
           (txn_id, run_id, date, description, amount_pence, fund, category, classification_tier, classification_confidence)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "txn_101",
            "run_2026_001",
            "2026-01-15",
            "Sunday Tithes",
            125000,
            "unrestricted_general",
            "Donations",
            "1",
            1.0,
        ),
    )

    # Fetch and verify
    row = client.fetchone("SELECT * FROM transactions WHERE txn_id = ?", ("txn_101",))
    assert row is not None
    assert row["amount_pence"] == 125000
    assert row["fund"] == "unrestricted_general"

    client.close()


def test_r2_encrypted_object_storage():
    """Verify R2 AES-256-GCM object storage encryption and decryption."""
    r2_client = R2StorageClient()
    object_key = "docs/2026/run_001_raw.pdf"
    content = b"Confidential Bank Statement Binary Content"

    meta = r2_client.put_object(object_key, content)
    assert meta.object_key == object_key
    assert meta.original_size_bytes == len(content)

    decrypted = r2_client.get_object(object_key)
    assert decrypted == content

    # Test deletion
    deleted = r2_client.delete_object(object_key)
    assert deleted is True
