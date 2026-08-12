-- Cloudflare D1 Initial Migration Schema for Beacon Compliance (0001_initial_schema.sql)
-- Enforces D1 relational schema per TRD §2

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT CHECK(role IN ('Chair', 'Secretary', 'Treasurer', 'Trustee', 'Admin')) NOT NULL,
    first_login_complete INTEGER NOT NULL DEFAULT 0
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

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    text TEXT NOT NULL,
    embedding_blob BLOB,
    fts_indexed INTEGER NOT NULL DEFAULT 0
);
