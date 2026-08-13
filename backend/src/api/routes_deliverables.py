"""Deliverables Download API Route (routes_deliverables.py).

Provides compiled OSCR deliverable packages and SHA-256 integrity hashes.
Enforces non-blocking execution, D1 query integration, and Pydantic response models.
"""

import asyncio
from decimal import Decimal
from typing import Any

from backend.src.agents.node_assembler import run_node_assembler
from backend.src.agents.state import BeaconComplianceState
from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_repository
from backend.src.db.repository import ComplianceRepository
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/deliverables", tags=["Deliverables"])


class DeliverableItemModel(BaseModel):
    deliverable_id: str
    type: str
    charity_number: str
    status: str
    content_hash: str
    sections: dict[str, Any] | None = None
    receipts_payments_account: dict[str, Any] | None = None
    statement_of_balances: dict[str, Any] | None = None


class DeliverablesResponse(BaseModel):
    run_id: str
    deliverables_ready: bool
    deliverables: list[dict[str, Any]]


@router.get("/{run_id}", response_model=DeliverablesResponse)
async def get_deliverables(
    run_id: str,
    current_user: TrusteeUser = Depends(get_current_trustee),
    repo: ComplianceRepository = Depends(get_repository),
) -> DeliverablesResponse:
    fin_state = repo.get_financial_state(run_id)

    if not fin_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Financial state for run_id '{run_id }' not found.",
        )

    receipts = fin_state.get("receipts", {})
    payments = fin_state.get("payments", {})
    gross_rec_dec = Decimal(
        str(receipts.get("gross_receipts_decimal", receipts.get("total_receipts_decimal", "0.00")))
    )
    gross_pay_dec = Decimal(
        str(payments.get("gross_payments_decimal", payments.get("total_payments_decimal", "0.00")))
    )
    net_mov_dec = gross_rec_dec - gross_pay_dec

    rnp_data = {
        "gross_receipts_decimal": str(gross_rec_dec),
        "gross_payments_decimal": str(gross_pay_dec),
        "net_movement_decimal": str(net_mov_dec),
    }

    sample_state: BeaconComplianceState = {
        "run_id": run_id,
        "charity_number": "SC054652",
        "receipts_payments": rnp_data,
        "statement_of_balances": {"reconciled": True},
        "tar_draft_fields": {
            "governance_description": "SCIO governance per Constitution.",
            "purposes_activities_narrative": "Advancement of Christian faith and relief of poverty.",
            "achievements_connective_narrative": "52 services conducted. Receipts: [FIGURE_INJECTED:gross_receipts].",
            "principal_risks_narrative": "3-month operating reserve policy.",
        },
    }

    result = await asyncio.to_thread(run_node_assembler, sample_state)
    return DeliverablesResponse(
        run_id=run_id,
        deliverables_ready=result.get("deliverables_ready", True),
        deliverables=result.get("deliverables", []),
    )
