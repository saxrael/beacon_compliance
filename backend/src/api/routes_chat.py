"""Interactive Compliance Chat API Endpoints (routes_chat.py).

Enforces:
- 4-Tier Memory Pipeline & Upfront Context Engineering (Zero Context Starvation)
- Multi-Turn Conversation Continuity via Sliding Window
- Background Cognitive Memory Processing (Tier 2 Summaries & Tier 3 Facts)
- Real-time Server-Sent Events (SSE) Streaming with Thought & Action Lifecycle
"""

import asyncio
import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.src.agents.chat_agent import ComplianceChatAgent
from backend.src.agents.cognitive_worker import CognitiveWorker
from backend.src.api.auth import TrusteeUser, get_current_trustee
from backend.src.api.dependencies import get_chat_agent, get_d1_db
from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.repository import ComplianceRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat Assistant"])
_background_tasks: set[asyncio.Task[Any]] = set()


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
    duration_seconds: float | None = None
    actions: list[dict[str, Any]] = Field(default_factory=list)


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


def _trigger_background_cognitive_processing(
    repo: ComplianceRepository, user_id: str, run_id: str
) -> None:
    """Synchronous worker invoking Tier 2 summary and Tier 3 fact cognitive workers in background."""
    try:
        worker = CognitiveWorker(repo=repo)
        worker.process_turn_memory(user_id=user_id, run_id=run_id)
    except Exception as exc:
        logger.warning(
            "Background cognitive worker execution failed for user %s: %s",
            user_id,
            exc,
        )


@router.get("/history")
def get_chat_history(
    run_id: str = Query("run_001"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    before_timestamp: str | None = Query(None),
    current_user: TrusteeUser = Depends(get_current_trustee),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> dict[str, Any]:
    """Retrieve persistent conversation turns from Tier 1 D1 storage."""
    repo = ComplianceRepository(db_client=db)
    return repo.get_chat_history(
        user_id=current_user.user_id,
        run_id=run_id,
        limit=limit,
        offset=offset,
        before_timestamp=before_timestamp,
    )


@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(
    req: ChatMessageRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    agent: ComplianceChatAgent = Depends(get_chat_agent),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> ChatMessageResponse:
    """Non-streaming compliance advisory chat turn."""
    repo = ComplianceRepository(db_client=db)
    state = _build_state_from_db(db, req.run_id, req.context_state)

    user_prof = repo.get_user_profile(current_user.user_id) or {
        "name": current_user.name,
        "role": current_user.role,
        "email": current_user.email,
    }
    history_resp = repo.get_chat_history(user_id=current_user.user_id, run_id=req.run_id, limit=50)
    history_turns = history_resp.get("messages", [])

    tier2_summary = repo.get_memory_summary(current_user.user_id, req.run_id)
    raw_facts = repo.get_memory_facts(current_user.user_id)
    tier3_facts = [rf["fact_text"] for rf in raw_facts if rf.get("fact_text")]

    user_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    repo.save_chat_message(
        message_id=user_msg_id,
        user_id=current_user.user_id,
        run_id=req.run_id,
        role="user",
        content=req.message,
    )

    start_time = time.time()
    res = await asyncio.to_thread(
        agent.process_message,
        req.message,
        state,
        None,
        current_user.user_id,
        req.run_id,
        user_prof,
        history_turns,
        tier2_summary,
        tier3_facts,
    )
    duration_sec = round(time.time() - start_time, 2)

    asst_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    action_items = [
        {
            "id": f"act_{idx}",
            "label": (
                tc.get("function", {}).get("name")
                if isinstance(tc, dict) and "function" in tc
                else tc.get("name") or tc.get("label") or "Statutory Action"
            ),
            "status": "completed",
        }
        for idx, tc in enumerate(res.tool_calls)
    ]

    repo.save_chat_message(
        message_id=asst_msg_id,
        user_id=current_user.user_id,
        run_id=req.run_id,
        role="assistant",
        content=res.message,
        thinking=res.thinking,
        tool_calls=res.tool_calls,
        sources=res.sources,
        duration_seconds=duration_sec,
        actions=action_items,
    )

    bg_task = asyncio.create_task(
        asyncio.to_thread(
            _trigger_background_cognitive_processing, repo, current_user.user_id, req.run_id
        )
    )
    _background_tasks.add(bg_task)
    bg_task.add_done_callback(_background_tasks.discard)

    return ChatMessageResponse(
        message_id=asst_msg_id,
        message=res.message,
        thinking=res.thinking,
        tool_calls=res.tool_calls,
        sources=res.sources,
        duration_seconds=duration_sec,
        actions=action_items,
    )


@router.post("/stream")
async def chat_stream(  # noqa: PLR0915
    req: ChatMessageRequest,
    current_user: TrusteeUser = Depends(get_current_trustee),
    agent: ComplianceChatAgent = Depends(get_chat_agent),
    db: D1DatabaseClient = Depends(get_d1_db),
) -> StreamingResponse:
    """Server-Sent Events (SSE) streaming endpoint emitting real-time thinking, actions, and tokens."""
    repo = ComplianceRepository(db_client=db)
    state = _build_state_from_db(db, req.run_id, req.context_state)

    user_prof = repo.get_user_profile(current_user.user_id) or {
        "name": current_user.name,
        "role": current_user.role,
        "email": current_user.email,
    }
    history_resp = repo.get_chat_history(user_id=current_user.user_id, run_id=req.run_id, limit=50)
    history_turns = history_resp.get("messages", [])

    tier2_summary = repo.get_memory_summary(current_user.user_id, req.run_id)
    raw_facts = repo.get_memory_facts(current_user.user_id)
    tier3_facts = [rf["fact_text"] for rf in raw_facts if rf.get("fact_text")]

    user_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
    repo.save_chat_message(
        message_id=user_msg_id,
        user_id=current_user.user_id,
        run_id=req.run_id,
        role="user",
        content=req.message,
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        start_time = time.time()
        accumulated_thoughts = []
        accumulated_text = []
        stream_actions: list[dict[str, Any]] = []
        final_tool_calls = []
        final_sources = []
        thinking_duration_sec: float | None = None

        for event in agent.stream_message(
            req.message,
            state,
            None,
            current_user.user_id,
            req.run_id,
            user_prof,
            history_turns,
            tier2_summary,
            tier3_facts,
        ):
            ev_type = event.get("type")
            if ev_type == "thought":
                chunk = event.get("chunk", "")
                accumulated_thoughts.append(chunk)
                payload = json.dumps({"chunk": chunk})
                yield f"event: thought\ndata: {payload}\n\n"
            elif ev_type == "action":
                label = event.get("label") or event.get("detail", "")
                status = event.get("status", "running")
                action_id = event.get("action_id", f"act_{len(stream_actions)}")
                act_item = {
                    "id": action_id,
                    "action_id": action_id,
                    "label": label,
                    "status": status,
                    "detail": label,
                }
                existing_idx = next(
                    (i for i, a in enumerate(stream_actions) if a.get("id") == action_id),
                    None,
                )
                if existing_idx is not None:
                    stream_actions[existing_idx] = act_item
                else:
                    stream_actions.append(act_item)
                payload = json.dumps(act_item)
                yield f"event: action\ndata: {payload}\n\n"
            elif ev_type == "token":
                chunk = event.get("chunk", "")
                accumulated_text.append(chunk)
                if thinking_duration_sec is None:
                    thinking_duration_sec = round(time.time() - start_time, 2)
                payload = json.dumps({"chunk": chunk})
                yield f"event: token\ndata: {payload}\n\n"
            elif ev_type == "done":
                final_tool_calls = event.get("tool_calls", [])
                final_sources = event.get("sources", [])
                asst_msg_id = f"msg_{uuid.uuid4().hex[:12]}"
                full_content = "".join(accumulated_text) or event.get("full_message", "")
                full_thinking = "".join(accumulated_thoughts)
                final_duration = (
                    thinking_duration_sec
                    if thinking_duration_sec is not None
                    else round(time.time() - start_time, 2)
                )

                repo.save_chat_message(
                    message_id=asst_msg_id,
                    user_id=current_user.user_id,
                    run_id=req.run_id,
                    role="assistant",
                    content=full_content,
                    thinking=full_thinking,
                    tool_calls=final_tool_calls,
                    sources=final_sources,
                    duration_seconds=final_duration,
                    actions=stream_actions,
                )

                payload = json.dumps(
                    {
                        "message_id": asst_msg_id,
                        "full_message": full_content,
                        "thinking": full_thinking,
                        "tool_calls": final_tool_calls,
                        "sources": final_sources,
                        "duration_seconds": final_duration,
                        "actions": stream_actions,
                    }
                )
                yield f"event: done\ndata: {payload}\n\n"

                bg_stream_task = asyncio.create_task(
                    asyncio.to_thread(
                        _trigger_background_cognitive_processing,
                        repo,
                        current_user.user_id,
                        req.run_id,
                    )
                )
                _background_tasks.add(bg_stream_task)
                bg_stream_task.add_done_callback(_background_tasks.discard)
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
