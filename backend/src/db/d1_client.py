"""Cloudflare D1 Relational Database Client for Beacon Compliance.

Strictly enforces:
- Parameterized SQL queries for security (OWASP Top 10 SQLi prevention)
- Integer pence storage for monetary amounts (Red-Line 2 / Rule 2)
- Schema definitions per TRD §2
"""

import io
import sqlite3
from pathlib import Path
from typing import Any

D1_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT CHECK(role IN ('Chair', 'Secretary', 'Treasurer', 'Trustee', 'Admin', 'Developer')) NOT NULL,
    first_login_complete INTEGER NOT NULL DEFAULT 0,
    google_id TEXT UNIQUE,
    totp_secret TEXT,
    totp_enabled INTEGER NOT NULL DEFAULT 0,
    avatar TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    charity_scn TEXT NOT NULL DEFAULT 'SC054652',
    year_end TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    r2_object_key TEXT NOT NULL,
    hash TEXT NOT NULL,
    anonymised_at TEXT,
    ocr_confidence_avg REAL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    txn_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_pence INTEGER NOT NULL,
    fund TEXT NOT NULL,
    category TEXT NOT NULL,
    classification_tier TEXT NOT NULL CHECK(classification_tier IN ('1', '2', '2.5')),
    classification_confidence REAL NOT NULL DEFAULT 1.0,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS classification_rules (
    rule_id TEXT PRIMARY KEY,
    pattern TEXT NOT NULL,
    fund TEXT NOT NULL,
    category TEXT NOT NULL,
    created_from_txn_id TEXT,
    confirmed_by_tier TEXT NOT NULL DEFAULT '2'
);

CREATE TABLE IF NOT EXISTS financial_state (
    run_id TEXT PRIMARY KEY,
    fund TEXT NOT NULL,
    receipts_json TEXT NOT NULL,
    payments_json TEXT NOT NULL,
    opening_balance_pence INTEGER NOT NULL,
    closing_balance_pence INTEGER NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS deliverables (
    deliverable_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('OAR', 'TAR', 'RP', 'IE')),
    status TEXT NOT NULL DEFAULT 'draft',
    r2_object_key TEXT,
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    deliverable_id TEXT NOT NULL,
    trustee_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Chair', 'Secretary', 'Treasurer')),
    approval_hash TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(run_id),
    FOREIGN KEY (deliverable_id) REFERENCES deliverables(deliverable_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    node_name TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    error_msg TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ie_deliveries (
    delivery_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    signed_url_generated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    sent_to TEXT NOT NULL,
    resend_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    type TEXT NOT NULL,
    sent_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_summaries (
    user_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (user_id, run_id)
);

CREATE TABLE IF NOT EXISTS memory_facts (
    fact_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    fact_text TEXT NOT NULL,
    source_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    message_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    run_id TEXT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    thinking TEXT,
    tool_calls_json TEXT,
    sources_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_run ON chat_messages(run_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id, created_at);

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding_blob BLOB,
    fts_indexed INTEGER NOT NULL DEFAULT 0
);
"""


class D1DatabaseClient:
    """Cloudflare D1 Client interface (with in-memory SQLite fallback for local execution/testing)."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        if self.db_path != ":memory:":
            try:
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
                self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            except (sqlite3.OperationalError, OSError):
                fallback_path = "/tmp/beacon_compliance.db"
                try:
                    Path(fallback_path).parent.mkdir(parents=True, exist_ok=True)
                    self._conn = sqlite3.connect(fallback_path, check_same_thread=False)
                    self.db_path = fallback_path
                except Exception:
                    self._conn = sqlite3.connect(":memory:", check_same_thread=False)
                    self.db_path = ":memory:"
        else:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self) -> None:
        """Initialize all D1 relational tables defined in TRD §2."""
        with self._conn:
            self._conn.executescript(D1_SCHEMA_SQL)

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Execute a parameterized SQL query safely."""
        with self._conn:
            return self._conn.execute(sql, params)

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Fetch all results for a parameterized query as dictionaries."""
        cursor = self._conn.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        """Fetch a single result row for a parameterized query."""
        cursor = self._conn.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self) -> None:
        """Close database connection."""
        self._conn.close()

    def backup_to_bytes(self) -> bytes:
        """Create an in-memory SQLite binary snapshot suitable for R2 disaster recovery upload."""
        dest = sqlite3.connect(":memory:")
        self._conn.backup(dest)
        raw_bytes = dest.serialize() if hasattr(dest, "serialize") else b""
        if not raw_bytes:
            buf = io.BytesIO()
            for line in dest.iterdump():
                buf.write(f"{line}\n".encode())
            raw_bytes = buf.getvalue()
        dest.close()
        return raw_bytes
