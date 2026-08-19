-- Cloudflare D1 Migration for Vector Embeddings and Memory Fact Vectors (0004_embeddings_and_vector_facts.sql)

ALTER TABLE memory_facts ADD COLUMN embedding_blob BLOB;

CREATE INDEX IF NOT EXISTS idx_embeddings_source ON embeddings(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_memory_facts_user ON memory_facts(user_id, created_at);
