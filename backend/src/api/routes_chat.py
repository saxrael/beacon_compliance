"""Compliance Chat API Route (routes_chat.py).

Powered by Gemma 4 26B A4B compliance agent.
Enforces non-blocking execution, dynamic D1 state lookup, dependency injection, and Pydantic models.
"""

import asyncio
import json
from decimal import Decimal
from typing import Any

from backend.src.agents.chat_agent import ComplianceChatAgent
from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_chat_agent, get_d1_db
from backend.src.db.d1_client import D1DatabaseClient
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/chat", tags=["Chat Assistant"])


class ChatMessageRequest(BaseModel):
    message: str
    run_id: str = "run_001"
    context_state: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    message: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    req: ChatMessageRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    agent: ComplianceChatAgent = Depends(get_chat_agent),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> ChatMessageResponse:
    state = req.context_state
    if not state:
        fin_row = db.fetchone(
            "SELECT receipts_json, payments_json FROM financial_state WHERE run_id = ?",
            (req.run_id,),
        )
        if fin_row:
            receipts = json.loads(fin_row.get("receipts_json", "{}"))
            payments = json.loads(fin_row.get("payments_json", "{}"))
            gross_rec_dec = Decimal(
                str(
                    receipts.get(
                        "gross_receipts_decimal", receipts.get("total_receipts_decimal", "0.00")
                    )
                )
            )
            gross_pay_dec = Decimal(
                str(
                    payments.get(
                        "gross_payments_decimal", payments.get("total_payments_decimal", "0.00")
                    )
                )
            )
            net_mov_dec = gross_rec_dec - gross_pay_dec
            state = {
                "receipts_payments": {
                    "gross_receipts_decimal": str(gross_rec_dec),
                    "gross_payments_decimal": str(gross_pay_dec),
                    "net_movement_decimal": str(net_mov_dec),
                    "is_threshold_breached": False,
                },
                "statement_of_balances": {"reconciled": True},
            }
        else:
            state = {
                "receipts_payments": {
                    "gross_receipts_decimal": "0.00",
                    "gross_payments_decimal": "0.00",
                    "net_movement_decimal": "0.00",
                    "is_threshold_breached": False,
                },
                "statement_of_balances": {"reconciled": True},
            }

    res = await asyncio.to_thread(agent.process_message, req.message, state)
    return ChatMessageResponse(
        message=res.message,
        tool_calls=res.tool_calls,
        sources=res.sources,
    )
