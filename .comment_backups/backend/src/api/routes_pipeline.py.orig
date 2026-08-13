"""State Machine Pipeline Orchestrator API Route (routes_pipeline.py).

Executes the LangGraph compliance state machine DAG non-blockingly.
Persists execution results to Cloudflare D1 database.
"""

import asyncio
import os
from typing import Any

from backend.src.agents.graph import BeaconComplianceGraph
from backend.src.agents.state import BeaconComplianceState
from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_repository
from backend.src.core.email_service import send_email
from backend.src.db.repository import ComplianceRepository
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


class PipelineRunRequest(BaseModel):
    run_id: str = "run_001"
    opening_balance_pence: int = 500000
    closing_balance_pence: int = 2000000
    raw_transactions: list[dict[str, Any]] = Field(default_factory=list)


class PipelineRunResponse(BaseModel):
    run_id: str
    income_threshold_breach: bool
    receipts_payments: dict[str, Any]
    statement_of_balances: dict[str, Any]
    tar_draft_fields: dict[str, Any]
    deliverables_ready: bool
    deliverables: list[dict[str, Any]]


@router.post("/run", response_model=PipelineRunResponse)
async def run_pipeline(
    req: PipelineRunRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    repo: ComplianceRepository = Depends(get_repository),
) -> PipelineRunResponse:
    graph = BeaconComplianceGraph()
    txns = req.raw_transactions or [
        {
            "txn_id": "TXN_P1",
            "description": "Weekly Tithes and Offerings",
            "amount_pence": 1500000,
            "transaction_type": "receipt",
        }
    ]

    initial_state: BeaconComplianceState = {
        "run_id": req.run_id,
        "charity_number": "SC054652",
        "raw_documents": [
            {
                "doc_id": "doc_p1",
                "filename": "offering_record.txt",
                "content_bytes": b"Weekly offerings",
                "declared_receipts_pence": 1500000,
            }
        ],
        "anonymised_payload": {
            "opening_balance_pence": req.opening_balance_pence,
            "closing_balance_pence": req.closing_balance_pence,
            "raw_transactions": txns,
        },
    }

    final_state = await asyncio.to_thread(graph.run, initial_state)

    rnp = final_state.get("receipts_payments", {})
    balances = final_state.get("statement_of_balances", {})

    repo.save_financial_state(
        run_id=req.run_id,
        fund="unrestricted_general",
        receipts=rnp,
        payments={},
        opening_balance_pence=req.opening_balance_pence,
        closing_balance_pence=req.closing_balance_pence,
    )

    breached = final_state.get("income_threshold_breach", False)
    if breached:
        target_email = os.environ.get("NOTIFICATION_FROM_EMAIL", "compliance@pottershouse.org.uk")
        send_email(
            to_email=target_email,
            subject="[CRITICAL ALERT] OSCR Income Threshold Breach (£250,000)",
            body_html="<p>Red-Line 5 Hard-Halt Triggered: Annual receipts reached or exceeded £250,000. R&P pipeline execution halted per Scottish charity regulations.</p>",
        )

    return PipelineRunResponse(
        run_id=req.run_id,
        income_threshold_breach=breached,
        receipts_payments=rnp,
        statement_of_balances=balances,
        tar_draft_fields=final_state.get("tar_draft_fields", {}),
        deliverables_ready=final_state.get("deliverables_ready", False),
        deliverables=final_state.get("deliverables", []),
    )
