import asyncio
import json
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any

from backend.src.agents.chat_agent import ComplianceChatAgent
from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_chat_agent, get_d1_db
from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.repository import ComplianceRepository
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/chat", tags=["Chat Assistant"])


class ChatMessageRequest(BaseModel):
    message: str
    run_id: str = "run_001"
    context_state: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    message_id: str | None = None
    message: str
    thinking: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


def _build_state_from_db(
    db: D1DatabaseClient, run_id: str, context_state: dict[str, Any]
) -> dict[str, Any]:
    if context_state:
        return context_state
    fin_row = db.fetchone(
        "SELECT receipts_json, payments_json FROM financial_state WHERE run_id = ?",
        (run_id,),
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
        return {
            "receipts_payments": {
                "gross_receipts_decimal": str(gross_rec_dec),
                "gross_payments_decimal": str(gross_pay_dec),
                "net_movement_decimal": str(net_mov_dec),
                "is_threshold_breached": False,
            },
            "statement_of_balances": {"reconciled": True},
        }
    return {
        "receipts_payments": {
            "gross_receipts_decimal": "0.00",
            "gross_payments_decimal": "0.00",
            "net_movement_decimal": "0.00",
            "is_threshold_breached": False,
        },
        "statement_of_balances": {"reconciled": True},
    }


@router.get("/history")
async def get_chat_history(
    run_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    before_timestamp: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    current_user: TrusteeUser = Depends(get_current_trustee),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> dict[str, Any]:
    """Retrieve 50-turn paginated chat history for current user and run."""
    repo = ComplianceRepository(db_client=db)
    return repo.get_chat_history(
        user_id=current_user.user_id,
        run_id=run_id,
        limit=limit,
        before_timestamp=before_timestamp,
        offset=offset,
    )


@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    req: ChatMessageRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    agent: ComplianceChatAgent = Depends(get_chat_agent),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> ChatMessageResponse:
    """Process a single turn and persist both user query and assistant response in D1."""
    repo = ComplianceRepository(db_client=db)
    state = _build_state_from_db(db, req.run_id, req.context_state)

    user_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    repo.save_chat_message(
        message_id=user_msg_id,
        user_id=current_user.user_id,
        run_id=req.run_id,
        role="user",
        content=req.message,
    )

    res = await asyncio.to_thread(
        agent.process_message, req.message, state, None, current_user.user_id
    )

    asst_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    repo.save_chat_message(
        message_id=asst_msg_id,
        user_id=current_user.user_id,
        run_id=req.run_id,
        role="assistant",
        content=res.message,
        thinking=res.thinking,
        tool_calls=res.tool_calls,
        sources=res.sources,
    )

    return ChatMessageResponse(
        message_id=asst_msg_id,
        message=res.message,
        thinking=res.thinking,
        tool_calls=res.tool_calls,
        sources=res.sources,
    )


@router.post("/stream")
async def chat_stream(
    req: ChatMessageRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    agent: ComplianceChatAgent = Depends(get_chat_agent),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> StreamingResponse:
    """Server-Sent Events (SSE) streaming endpoint emitting real-time thinking, actions, and tokens."""
    repo = ComplianceRepository(db_client=db)
    state = _build_state_from_db(db, req.run_id, req.context_state)

    user_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    repo.save_chat_message(
        message_id=user_msg_id,
        user_id=current_user.user_id,
        run_id=req.run_id,
        role="user",
        content=req.message,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        accumulated_thoughts = []
        accumulated_text = []
        final_tool_calls = []
        final_sources = []

        for event in agent.stream_message(req.message, state, None, current_user.user_id):
            ev_type = event.get("type")
            if ev_type == "thought":
                chunk = event.get("chunk", "")
                accumulated_thoughts.append(chunk)
                payload = json.dumps({"chunk": chunk})
                yield f"event: thought\ndata: {payload}\n\n"
            elif ev_type == "action":
                detail = event.get("detail", "")
                payload = json.dumps({"detail": detail})
                yield f"event: action\ndata: {payload}\n\n"
            elif ev_type == "token":
                chunk = event.get("chunk", "")
                accumulated_text.append(chunk)
                payload = json.dumps({"chunk": chunk})
                yield f"event: token\ndata: {payload}\n\n"
            elif ev_type == "done":
                final_tool_calls = event.get("tool_calls", [])
                final_sources = event.get("sources", [])
                asst_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
                full_content = "".join(accumulated_text) or event.get("full_message", "")
                full_thinking = "".join(accumulated_thoughts)

                repo.save_chat_message(
                    message_id=asst_msg_id,
                    user_id=current_user.user_id,
                    run_id=req.run_id,
                    role="assistant",
                    content=full_content,
                    thinking=full_thinking,
                    tool_calls=final_tool_calls,
                    sources=final_sources,
                )

                payload = json.dumps(
                    {
                        "message_id": asst_msg_id,
                        "full_message": full_content,
                        "thinking": full_thinking,
                        "tool_calls": final_tool_calls,
                        "sources": final_sources,
                    }
                )
                yield f"event: done\ndata: {payload}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
