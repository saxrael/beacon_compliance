"""Compliance Repository Facade for Beacon Compliance (repository.py).

Provides a deep, unified domain repository hiding D1 relational database operations,
encrypted R2 blob storage, JSON serialization/deserialization, and schema details
behind clean domain methods.
"""

import hashlib
import hmac
import json
from typing import Any

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
        object_key = f"documents/{run_id}/{doc_id}/{filename}"
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
