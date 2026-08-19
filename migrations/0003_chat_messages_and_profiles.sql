-- Cloudflare D1 Migration for Chat Messages and Profiles (0003_chat_messages_and_profiles.sql)

ALTER TABLE users ADD COLUMN avatar TEXT;

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
