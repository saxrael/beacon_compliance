"""Compliance Repository Facade for Beacon Compliance (repository.py).

Provides a deep, unified domain repository hiding D1 relational database operations,
encrypted R2 blob storage, JSON serialization/deserialization, and schema details
behind clean domain methods.
"""

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

from backend.src.core.embeddings import deserialize_vector, serialize_vector
from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.r2_client import R2StorageClient


class ComplianceRepository:
    """Deep domain repository facade for Beacon Compliance state and object persistence."""

    def __init__(
        self,
        db_client: D1DatabaseClient | None = None,
        r2_client: R2StorageClient | None = None,
    ) -> None:
        self.db = db_client or D1DatabaseClient(db_path=":memory:")
        self.r2 = r2_client or R2StorageClient()

    def save_financial_state(
        self,
        run_id: str,
        *,
        fund: str,
        receipts: dict[str, Any],
        payments: dict[str, Any],
        opening_balance_pence: int,
        closing_balance_pence: int,
    ) -> None:
        """Persist compiled receipts & payments financial state to D1 database."""
        self.db.execute(
            "INSERT OR REPLACE INTO financial_state "
            "(run_id, fund, receipts_json, payments_json, opening_balance_pence, closing_balance_pence) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                run_id,
                fund,
                json.dumps(receipts),
                json.dumps(payments),
                opening_balance_pence,
                closing_balance_pence,
            ),
        )

    def get_financial_state(self, run_id: str) -> dict[str, Any] | None:
        """Fetch financial state for run_id from D1 database."""
        row = self.db.fetchone(
            "SELECT run_id, fund, receipts_json, payments_json, opening_balance_pence, closing_balance_pence "
            "FROM financial_state WHERE run_id = ?",
            (run_id,),
        )
        if not row:
            return None

        return {
            "run_id": row["run_id"],
            "fund": row["fund"],
            "receipts": json.loads(row["receipts_json"]),
            "payments": json.loads(row["payments_json"]),
            "opening_balance_pence": row["opening_balance_pence"],
            "closing_balance_pence": row["closing_balance_pence"],
        }

    def get_transactions_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Query transactions belonging to run_id from D1 database."""
        rows = self.db.fetchall(
            "SELECT txn_id, run_id, date, description, amount_pence, fund, category, "
            "classification_tier, classification_confidence FROM transactions WHERE run_id = ?",
            (run_id,),
        )
        return [
            {
                "txn_id": r["txn_id"],
                "run_id": r["run_id"],
                "date": r["date"],
                "description": r["description"],
                "amount_pence": r["amount_pence"],
                "fund": r["fund"],
                "category": r["category"],
                "classification_tier": r["classification_tier"],
                "classification_confidence": r["classification_confidence"],
            }
            for r in rows
        ]

    def save_classification_rule(
        self,
        rule_id: str,
        *,
        pattern: str,
        fund: str,
        category: str,
        created_from_txn_id: str | None = None,
        confirmed_by_tier: str = "2",
    ) -> dict[str, Any]:
        """Persist trustee confirmed Tier 2 classification rule."""
        self.db.execute(
            "INSERT OR REPLACE INTO classification_rules "
            "(rule_id, pattern, fund, category, created_from_txn_id, confirmed_by_tier) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (rule_id, pattern, fund, category, created_from_txn_id, confirmed_by_tier),
        )
        return {
            "rule_id": rule_id,
            "pattern": pattern,
            "fund": fund,
            "category": category,
            "created_from_txn_id": created_from_txn_id,
            "confirmed_by_tier": confirmed_by_tier,
        }

    def store_document_blob(
        self,
        run_id: str,
        doc_id: str,
        filename: str,
        content_bytes: bytes,
        category: str = "bank_statement",
    ) -> str:
        """Encrypt content and store in R2 object storage, saving metadata to D1."""
        object_key = f"documents/{run_id }/{doc_id }/{filename }"
        self.r2.put_object(object_key, content_bytes)

        doc_hash = hmac.new(b"beacon_doc_hash", content_bytes, hashlib.sha256).hexdigest()

        self.db.execute(
            "INSERT OR REPLACE INTO documents "
            "(doc_id, run_id, category, description, r2_object_key, hash) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, run_id, category, filename, object_key, doc_hash),
        )
        return object_key

    def fetch_document_blob(self, object_key: str) -> bytes:
        """Fetch and decrypt document blob from R2 object storage."""
        return self.r2.get_object(object_key)

    def save_approval(
        self,
        approval_id: str,
        *,
        run_id: str,
        deliverable_id: str,
        trustee_id: str,
        role: str,
        approval_hash: str,
        approved_at: str,
    ) -> dict[str, Any]:
        """Persist trustee HMAC sign-off approval record to D1 database."""
        self.db.execute(
            "INSERT OR REPLACE INTO approvals "
            "(approval_id, run_id, deliverable_id, trustee_id, role, approval_hash, approved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (approval_id, run_id, deliverable_id, trustee_id, role, approval_hash, approved_at),
        )
        return {
            "approval_id": approval_id,
            "run_id": run_id,
            "deliverable_id": deliverable_id,
            "trustee_id": trustee_id,
            "role": role,
            "approval_hash": approval_hash,
            "approved_at": approved_at,
        }

    def get_approvals_for_run(self, run_id: str) -> list[dict[str, Any]]:
        """Fetch all trustee approvals recorded for run_id."""
        rows = self.db.fetchall(
            "SELECT approval_id, run_id, deliverable_id, trustee_id, role, approval_hash, approved_at "
            "FROM approvals WHERE run_id = ?",
            (run_id,),
        )
        return [dict(r) for r in rows]

    def get_chair_user(self) -> dict[str, Any] | None:
        """Fetch designated Chair user profile from D1 users table."""
        row = self.db.fetchone(
            "SELECT user_id, name, email, role FROM users WHERE role = 'Chair' LIMIT 1"
        )
        return dict(row) if row else None

    def get_signing_chair_name(self, run_id: str | None = None) -> str:
        """Resolve real name of the Chair with guaranteed safe institutional fallback.

        Resolution order:
        1. Approved Chair from approvals JOIN users for run_id (if signed)
        2. Designated Chair from users table (role = 'Chair')
        3. Fallback safely to 'Chair of the Board of Trustees'
        """
        if run_id:
            row = self.db.fetchone(
                "SELECT u.name FROM approvals a "
                "JOIN users u ON a.trustee_id = u.user_id "
                "WHERE a.run_id = ? AND a.role = 'Chair' "
                "ORDER BY a.approved_at DESC LIMIT 1",
                (run_id,),
            )
            if row and row.get("name"):
                sanitized = _sanitize_chair_name(row["name"])
                if sanitized != "Chair of the Board of Trustees":
                    return sanitized

        chair = self.get_chair_user()
        if chair and chair.get("name"):
            sanitized = _sanitize_chair_name(chair["name"])
            if sanitized != "Chair of the Board of Trustees":
                return sanitized

        return "Chair of the Board of Trustees"

    def save_chat_message(
        self,
        message_id: str,
        *,
        user_id: str,
        run_id: str | None = None,
        role: str,
        content: str,
        thinking: str | None = None,
        tool_calls: list[dict[str, Any]] | None = None,
        sources: list[str] | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        """Persist a conversation turn to D1 chat_messages table."""
        ts = created_at or datetime.now(UTC).isoformat()
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        sources_json = json.dumps(sources) if sources else None

        self.db.execute(
            "INSERT INTO chat_messages (message_id, user_id, run_id, role, content, thinking, tool_calls_json, sources_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                message_id,
                user_id,
                run_id,
                role,
                content,
                thinking,
                tool_calls_json,
                sources_json,
                ts,
            ),
        )
        return {
            "message_id": message_id,
            "user_id": user_id,
            "run_id": run_id,
            "role": role,
            "content": content,
            "thinking": thinking,
            "tool_calls": tool_calls or [],
            "sources": sources or [],
            "created_at": ts,
        }

    def get_chat_history(
        self,
        *,
        user_id: str | None = None,
        run_id: str | None = None,
        limit: int = 50,
        before_timestamp: str | None = None,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Fetch chat history with 50-turn pagination and scroll-up older history support."""
        conditions = []
        params: list[Any] = []

        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        if run_id:
            conditions.append("run_id = ?")
            params.append(run_id)
        if before_timestamp:
            conditions.append("created_at < ?")
            params.append(before_timestamp)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        count_row = self.db.fetchone(
            f"SELECT COUNT(*) as total FROM chat_messages {where_clause}", tuple(params)
        )
        total_count = count_row["total"] if count_row else 0

        query = f"SELECT message_id, user_id, run_id, role, content, thinking, tool_calls_json, sources_json, created_at FROM chat_messages {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
        query_params = [*params, limit, offset]

        rows = self.db.fetchall(query, tuple(query_params))

        messages = []
        for r in rows:
            messages.append(
                {
                    "message_id": r["message_id"],
                    "user_id": r["user_id"],
                    "run_id": r["run_id"],
                    "role": r["role"],
                    "content": r["content"],
                    "thinking": r.get("thinking"),
                    "tool_calls": json.loads(r["tool_calls_json"])
                    if r.get("tool_calls_json")
                    else [],
                    "sources": json.loads(r["sources_json"]) if r.get("sources_json") else [],
                    "created_at": r["created_at"],
                }
            )

        messages.reverse()
        has_more = (offset + len(rows)) < total_count

        return {
            "messages": messages,
            "total_count": total_count,
            "has_more": has_more,
            "next_cursor": messages[0]["created_at"] if messages and has_more else None,
        }

    def save_memory_summary(
        self, user_id: str, run_id: str, summary_text: str, updated_at: str
    ) -> None:
        """Persist Tier 2 cognitive rolling summary to D1."""
        self.db.execute(
            "INSERT OR REPLACE INTO memory_summaries (user_id, run_id, summary_text, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, run_id, summary_text, updated_at),
        )

    def get_memory_summary(self, user_id: str, run_id: str) -> str | None:
        """Fetch Tier 2 cognitive rolling summary from D1."""
        row = self.db.fetchone(
            "SELECT summary_text FROM memory_summaries WHERE user_id = ? AND run_id = ?",
            (user_id, run_id),
        )
        return row["summary_text"] if row else None

    def save_memory_fact(
        self,
        fact_id: str,
        user_id: str,
        fact_text: str,
        source_type: str,
        created_at: str,
        embedding_vec: list[float] | None = None,
    ) -> None:
        """Persist Tier 3 semantic fact and its vector embedding to D1."""
        blob = serialize_vector(embedding_vec) if embedding_vec else None
        try:
            self.db.execute(
                "INSERT OR REPLACE INTO memory_facts (fact_id, user_id, fact_text, source_type, created_at, embedding_blob) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (fact_id, user_id, fact_text, source_type, created_at, blob),
            )
        except Exception:
            self.db.execute(
                "INSERT OR REPLACE INTO memory_facts (fact_id, user_id, fact_text, source_type, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (fact_id, user_id, fact_text, source_type, created_at),
            )

    def get_memory_facts(self, user_id: str) -> list[dict[str, Any]]:
        """Fetch Tier 3 semantic facts and deserialize vector embeddings for a user from D1."""
        try:
            rows = self.db.fetchall(
                "SELECT fact_id, user_id, fact_text, source_type, created_at, embedding_blob FROM memory_facts WHERE user_id = ?",
                (user_id,),
            )
        except Exception:
            rows = self.db.fetchall(
                "SELECT fact_id, user_id, fact_text, source_type, created_at FROM memory_facts WHERE user_id = ?",
                (user_id,),
            )

        facts = []
        for r in rows:
            fact_dict = dict(r)
            if fact_dict.get("embedding_blob"):
                fact_dict["embedding_vec"] = deserialize_vector(fact_dict["embedding_blob"])
            facts.append(fact_dict)
        return facts

    def save_embedding(
        self,
        chunk_id: str,
        source_type: str,
        source_id: str,
        text: str,
        embedding_vec: list[float] | None = None,
        fts_indexed: int = 0,
    ) -> None:
        """Persist document/knowledge chunk and its vector embedding to D1 embeddings table."""
        blob = serialize_vector(embedding_vec) if embedding_vec else None
        self.db.execute(
            "INSERT OR REPLACE INTO embeddings (chunk_id, source_type, source_id, text, embedding_blob, fts_indexed) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (chunk_id, source_type, source_id, text, blob, fts_indexed),
        )

    def get_embeddings(
        self, source_type: str | None = None, source_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve embeddings from D1 with deserialized float vector arrays."""
        conditions = []
        params = []
        if source_type:
            conditions.append("source_type = ?")
            params.append(source_type)
        if source_id:
            conditions.append("source_id = ?")
            params.append(source_id)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT chunk_id, source_type, source_id, text, embedding_blob, fts_indexed FROM embeddings {where_clause}"
        rows = self.db.fetchall(query, tuple(params))

        results = []
        for r in rows:
            item = dict(r)
            blob = item.get("embedding_blob")
            item["embedding_vec"] = deserialize_vector(blob) if blob else []
            results.append(item)
        return results

    def delete_embeddings(self, source_type: str, source_id: str) -> None:
        """Delete embeddings for a specific source from D1."""
        self.db.execute(
            "DELETE FROM embeddings WHERE source_type = ? AND source_id = ?",
            (source_type, source_id),
        )

    def update_user_profile(
        self,
        user_id: str,
        *,
        name: str | None = None,
        email: str | None = None,
        avatar: str | None = None,
    ) -> dict[str, Any]:
        """Update trustee profile fields in D1."""
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name.strip())
        if email is not None:
            updates.append("email = ?")
            params.append(email.strip())
        if avatar is not None:
            updates.append("avatar = ?")
            params.append(avatar.strip())

        if updates:
            params.append(user_id)
            try:
                self.db.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", tuple(params)
                )
            except Exception:
                if hasattr(self.db, "_migrate_existing_tables"):
                    self.db._migrate_existing_tables()
                self.db.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", tuple(params)
                )

        try:
            user = self.db.fetchone(
                "SELECT user_id, email, name, role, avatar FROM users WHERE user_id = ?", (user_id,)
            )
        except Exception:
            if hasattr(self.db, "_migrate_existing_tables"):
                self.db._migrate_existing_tables()
            user = self.db.fetchone(
                "SELECT user_id, email, name, role, avatar FROM users WHERE user_id = ?", (user_id,)
            )
        return dict(user) if user else {}

    def get_user_profile(self, user_id: str) -> dict[str, Any] | None:
        """Fetch trustee user profile from D1."""
        try:
            row = self.db.fetchone(
                "SELECT user_id, email, name, role, avatar FROM users WHERE user_id = ?", (user_id,)
            )
        except Exception:
            if hasattr(self.db, "_migrate_existing_tables"):
                self.db._migrate_existing_tables()
            row = self.db.fetchone(
                "SELECT user_id, email, name, role, avatar FROM users WHERE user_id = ?", (user_id,)
            )
        return dict(row) if row else None


def _sanitize_chair_name(name_candidate: Any) -> str:
    """Safely sanitize a Chair name candidate, preventing None, null, undefined, or empty strings."""
    if name_candidate is None:
        return "Chair of the Board of Trustees"
    candidate_str = str(name_candidate).strip()
    if not candidate_str or candidate_str.lower() in ("none", "null", "undefined"):
        return "Chair of the Board of Trustees"
    return candidate_str
