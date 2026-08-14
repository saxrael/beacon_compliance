import pytest
from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.r2_client import R2StorageClient


def test_d1_schema_initialization_and_queries():
    client = D1DatabaseClient(db_path=":memory:")

    client.execute(
        "INSERT INTO runs (run_id, charity_scn, year_end, status, created_at) VALUES (?, ?, ?, ?, ?)",
        ("run_2026_001", "SC054652", "2026-12-31", "draft", "2026-08-12T00:00:00Z"),
    )

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

    row = client.fetchone("SELECT * FROM transactions WHERE txn_id = ?", ("txn_101",))
    assert row is not None
    assert row["amount_pence"] == 125000
    assert row["fund"] == "unrestricted_general"
    client.close()


def test_r2_encrypted_object_storage():
    r2_client = R2StorageClient()
    object_key = "docs/2026/run_001_raw.pdf"
    content = b"Confidential Bank Statement Binary Content"

    meta = r2_client.put_object(object_key, content)
    assert meta.object_key == object_key
    assert meta.original_size_bytes == len(content)

    decrypted = r2_client.get_object(object_key)
    assert decrypted == content

    deleted = r2_client.delete_object(object_key)
    assert deleted is True


def test_r2_missing_key_key_error():
    r2_client = R2StorageClient()
    with pytest.raises(KeyError, match="not found in R2 storage"):
        r2_client.get_object("non_existent_key.pdf")


def test_r2_empty_key_value_error():
    r2_client = R2StorageClient()
    with pytest.raises(ValueError, match="object_key cannot be empty"):
        r2_client.put_object("", b"some content")


def test_r2_delete_non_existent_object():
    r2_client = R2StorageClient()
    assert r2_client.delete_object("non_existent_key_for_delete.pdf") is False


def test_d1_client_nested_directory_auto_creation(tmp_path):
    nested_db_path = tmp_path / "deeply" / "nested" / "data" / "beacon_compliance.db"
    assert not nested_db_path.parent.exists()

    client = D1DatabaseClient(db_path=str(nested_db_path))
    assert nested_db_path.parent.exists()
    assert nested_db_path.exists()

    client.execute(
        "INSERT INTO runs (run_id, charity_scn, year_end, status, created_at) VALUES (?, ?, ?, ?, ?)",
        ("run_nested_001", "SC054652", "2026-12-31", "draft", "2026-08-12T00:00:00Z"),
    )
    row = client.fetchone("SELECT run_id FROM runs WHERE run_id = ?", ("run_nested_001",))
    assert row is not None
    assert row["run_id"] == "run_nested_001"
    client.close()


def test_d1_client_file_persistence(tmp_path):
    db_file = str(tmp_path / "persistent" / "beacon.db")
    client1 = D1DatabaseClient(db_path=db_file)
    client1.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role) VALUES (?, ?, ?, ?, ?)",
        ("usr_persisted", "trustee@pottershouse.org.uk", "hash123", "Trustee", "Chair"),
    )
    client1.close()

    client2 = D1DatabaseClient(db_path=db_file)
    user_row = client2.fetchone(
        "SELECT email, role FROM users WHERE user_id = ?", ("usr_persisted",)
    )
    assert user_row is not None
    assert user_row["email"] == "trustee@pottershouse.org.uk"
    assert user_row["role"] == "Chair"
    client2.close()
