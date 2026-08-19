"""3-Tier Transaction Classification API Route (routes_classify.py).

Provides endpoints for trustee review of Tier 2.5 AI suggestions and Tier 2 learned rule creation.
Enforces non-blocking execution, D1 relational queries, and dependency injection.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.src.agents.node_classify import run_node_classify
from backend.src.agents.state import BeaconComplianceState
from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_repository
from backend.src.db.repository import ComplianceRepository

router = APIRouter(prefix="/api/classify", tags=["Classification"])


class ClassifiedTxnSummary(BaseModel):
    txn_id: str
    description: str
    amount_pence: int
    fund: str
    category: str
    classification_tier: str
    confidence: float


class PendingClassificationResponse(BaseModel):
    run_id: str
    total_classified: int
    classified_transactions: list[ClassifiedTxnSummary]


class ClassificationConfirmRequest(BaseModel):
    txn_id: str
    description: str
    confirmed_fund: str
    confirmed_category: str


class ClassificationConfirmResponse(BaseModel):
    status: str
    rule_created: dict[str, Any]


@router.get("/pending", response_model=PendingClassificationResponse)
async def get_pending_classifications(
    run_id: str = "run_001",
    current_user: TrusteeUser = Depends(get_current_trustee),
    repo: ComplianceRepository = Depends(get_repository),
) -> PendingClassificationResponse:
    db_txns = repo.get_transactions_for_run(run_id)

    if db_txns:
        raw_txns = [
            {
                "txn_id": row["txn_id"],
                "description": row["description"],
                "amount_pence": row["amount_pence"],
                "transaction_type": "receipt" if row["amount_pence"] > 0 else "payment",
            }
            for row in db_txns
        ]
    else:
        raw_txns = [
            {
                "txn_id": "TXN_001",
                "description": "Offering Tithes John",
                "amount_pence": 15000,
                "transaction_type": "receipt",
            },
            {
                "txn_id": "TXN_002",
                "description": "Hall Rent Payment",
                "amount_pence": 45000,
                "transaction_type": "payment",
            },
        ]

    state: BeaconComplianceState = {
        "run_id": run_id,
        "anonymised_payload": {
            "raw_transactions": raw_txns,
        },
    }

    result = await asyncio.to_thread(run_node_classify, state)
    classified_list = result.get("classified_transactions", [])

    items = [
        ClassifiedTxnSummary(
            txn_id=t.get("txn_id", ""),
            description=t.get("description", ""),
            amount_pence=t.get("amount_pence", 0),
            fund=t.get("fund", "unrestricted_general"),
            category=t.get("category", "General Offerings"),
            classification_tier=str(t.get("classification_tier", "1")),
            confidence=float(t.get("classification_confidence", 1.0)),
        )
        for t in classified_list
    ]

    return PendingClassificationResponse(
        run_id=run_id,
        total_classified=len(items),
        classified_transactions=items,
    )


@router.post("/confirm", response_model=ClassificationConfirmResponse)
async def confirm_classification(
    req: ClassificationConfirmRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    repo: ComplianceRepository = Depends(get_repository),
) -> ClassificationConfirmResponse:
    """Confirm a trustee classification recommendation and persist Tier 2 learned rule."""
    rule_id = f"rule_{req .txn_id }"

    new_rule = repo.save_classification_rule(
        rule_id=rule_id,
        pattern=req.description,
        fund=req.confirmed_fund,
        category=req.confirmed_category,
        created_from_txn_id=req.txn_id,
        confirmed_by_tier="2",
    )

    return ClassificationConfirmResponse(status="confirmed", rule_created=new_rule)
