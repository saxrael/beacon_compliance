-- Cloudflare D1 Migration for Chat Messages Duration and Actions (0005_chat_messages_duration_and_actions.sql)

ALTER TABLE chat_messages ADD COLUMN duration_seconds REAL;
ALTER TABLE chat_messages ADD COLUMN actions_json TEXT;
