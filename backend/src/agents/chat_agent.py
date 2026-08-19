"""Interactive Compliance Chat Assistant Sentinel Agent (chat_agent.py).

Powered by Gemma 4 26B A4B.
Enforces:
- 4-Tier Cognitive Memory & Upfront Context Engineering (Zero Context Starvation)
- Cyclical Reviewer Self-Correction Loop (Internal Reviewer, max 3 retries)
- Red-Line 1: Zero autonomous submission or external transmission
- Red-Line 2: Zero LLM financial arithmetic (uses deterministic financial tools / state)
- Red-Line 4: Anonymized state and PII-scrubbed context only
"""

import logging
from typing import Any

from pydantic import BaseModel, Field

from backend.src.agents.prompts.chat_prompts import CHAT_AGENT_SYSTEM_PROMPT
from backend.src.core.knowledge_context import ComplianceKnowledgeContext
from backend.src.core.llm_client import LLMClient
from backend.src.core.retry import db_retry
from backend.src.core.telemetry import default_tracer

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message schema."""

    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str


class ChatAgentResponse(BaseModel):
    """Chat agent output schema."""

    message: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    thinking: str | None = None


class ComplianceChatAgent:
    """Gemma 4 26B A4B Compliance Assistant Sentinel with cyclical review and upfront context."""

    def __init__(
        self,
        knowledge_context: ComplianceKnowledgeContext | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.knowledge = knowledge_context or ComplianceKnowledgeContext()
        self.llm = llm_client or LLMClient()

    @db_retry
    def get_financial_summary_tool(self, state: dict[str, Any]) -> dict[str, Any]:
        """Deterministic tool returning Node 3 receipts and payments financial summary."""
        rnp = state.get("receipts_payments", {})
        balances = state.get("statement_of_balances", {})
        return {
            "gross_receipts": str(rnp.get("gross_receipts_decimal", "0.00")),
            "gross_payments": str(rnp.get("gross_payments_decimal", "0.00")),
            "net_movement": str(rnp.get("net_movement_decimal", "0.00")),
            "reconciled": balances.get("reconciled", True),
            "threshold_breached": rnp.get("is_threshold_breached", False),
        }

    @db_retry
    def search_knowledge_base_tool(
        self, query: str, corpus: list[dict[str, Any]], user_id: str = "trustee_01"
    ) -> dict[str, Any]:
        """Unified context tool retrieving OSCR regulatory guidance and cognitive memory facts."""
        return self.knowledge.query_context(user_id=user_id, query=query, corpus=corpus, top_k=3)

    def is_out_of_scope(self, message: str) -> bool:
        """Check if query is entirely unrelated to charity compliance, governance, or finance."""
        lower = message.lower().strip()
        compliance_terms = (
            "oscr",
            "charity",
            "scio",
            "trustee",
            "receipt",
            "payment",
            "income",
            "fund",
            "balance",
            "account",
            "filing",
            "deadline",
            "audit",
            "examination",
            "independent",
            "tar",
            "oar",
            "statutory",
            "constitution",
            "governance",
            "sc054652",
            "potter",
            "mission",
            "donor",
            "hmac",
            "sign-off",
            "approval",
            "compliance",
            "voucher",
            "tier",
            "classification",
            "gift aid",
            "restricted",
            "unrestricted",
            "endowment",
            "2005 act",
            "2006 regs",
            "hello",
            "hi",
            "help",
            "who are you",
            "what can you do",
            "who am i",
            "my role",
            "our position",
        )
        if any(term in lower for term in compliance_terms):
            return False

        unrelated_terms = (
            "football",
            "soccer",
            "basketball",
            "recipe",
            "cook",
            "movie",
            "cinema",
            "song",
            "lyrics",
            "poem",
            "joke",
            "weather",
            "horoscope",
            "video game",
            "crypto trading",
            "write python code for a game",
            "tell me a story",
        )
        return any(term in lower for term in unrelated_terms)

    def _review_agent_output(
        self,
        response_text: str,
        tool_context: str,
        tool_calls: list[dict[str, Any]],
    ) -> tuple[bool, str | None]:
        """Internal Reviewer node inspecting tool outputs and generated response."""
        lower_resp = response_text.lower()
        lower_tool = tool_context.lower()

        if "error" in lower_tool or "failed" in lower_tool:
            for tc in tool_calls:
                out = tc.get("output", {})
                if isinstance(out, dict) and ("error" in out or "failed" in str(out)):
                    return False, f"Tool execution error: {out.get('error', 'Execution failure')}"
            if "failed" in lower_tool or "error" in lower_tool:
                return False, f"Tool output error: {tool_context[:100]}"

        if "i calculated" in lower_resp or "i multiplied" in lower_resp or "i added" in lower_resp:
            return False, "Red-Line 2 violation: LLM self-reported arithmetic calculation."

        return True, None

    def _build_system_prompt_with_context(
        self,
        user_id: str,
        run_id: str,
        state: dict[str, Any],
        user_profile: dict[str, Any] | None,
        history_turns: list[dict[str, Any]] | None,
        tier2_summary: str | None,
        tier3_facts: list[str] | None,
    ) -> str:
        """Assemble full upfront context and prepend to master system prompt."""
        envelope = self.knowledge.assembler.build_context_envelope(
            user_id=user_id,
            run_id=run_id,
            user_profile=user_profile,
            financial_state=state,
            history_turns=history_turns,
            tier2_summary=tier2_summary,
            tier3_facts=tier3_facts,
        )
        context_xml = self.knowledge.assembler.format_system_context(envelope)
        return f"{CHAT_AGENT_SYSTEM_PROMPT}\n\n{context_xml}"

    def _execute_sync_tools(
        self,
        lower_msg: str,
        user_message: str,
        session_id: str,
        state: dict[str, Any],
        kb_corpus: list[dict[str, Any]] | None,
        user_id: str,
    ) -> tuple[list[dict[str, Any]], list[str], str]:
        """Execute deterministic financial or RAG tools synchronously."""
        tool_calls: list[dict[str, Any]] = []
        sources: list[str] = []
        tool_context = ""

        fin_keywords = (
            "financial",
            "total",
            "income",
            "receipt",
            "payment",
            "balance",
            "money",
            "figures",
        )
        kb_keywords = (
            "oscr",
            "rule",
            "guidance",
            "reporting",
            "threshold",
            "constitution",
            "deadline",
            "scio",
            "act",
        )

        if any(kw in lower_msg for kw in fin_keywords):
            try:
                with default_tracer.trace_tool_execution(
                    name="get_financial_summary_tool",
                    as_type="tool",
                    input_data={"run_id": session_id},
                ) as tool_ctx:
                    fin_summary = self.get_financial_summary_tool(state)
                    tool_calls.append({"tool": "get_financial_summary", "output": fin_summary})
                    tool_context = (
                        f"Deterministic Node 3 Financial Statement:\n"
                        f"- Gross Receipts: £{fin_summary['gross_receipts']}\n"
                        f"- Gross Payments: £{fin_summary['gross_payments']}\n"
                        f"- Net Movement: £{fin_summary['net_movement']}\n"
                        f"- Reconciled: {fin_summary['reconciled']}"
                    )
                    tool_ctx.set_output(fin_summary)
            except Exception as err:
                tool_context = f"Note: Live Receipts & Payments query failed: {err}"
        elif any(kw in lower_msg for kw in kb_keywords):
            try:
                with default_tracer.trace_tool_execution(
                    name="search_knowledge_base_tool",
                    as_type="retriever",
                    input_data={"query": user_message},
                ) as ret_ctx:
                    search_results = self.search_knowledge_base_tool(
                        user_message, kb_corpus or [], user_id=user_id
                    )
                    tool_calls.append(
                        {
                            "tool": "search_knowledge_base",
                            "matches": len(search_results.get("kb_matches", [])),
                        }
                    )
                    sources = search_results.get("sources", [])
                    tool_context = search_results.get("formatted_context", "")
                    ret_ctx.set_output(
                        {
                            "sources": sources,
                            "matches_count": len(search_results.get("kb_matches", [])),
                        }
                    )
            except Exception as err:
                tool_context = f"Note: OSCR knowledge base query failed: {err}"

        return tool_calls, sources, tool_context

    def _run_cyclical_review_loop(
        self,
        system_prompt: str,
        user_message: str,
        tool_context: str,
        tool_calls: list[dict[str, Any]],
        formatted_history: list[dict[str, str]],
    ) -> str:
        """Run Cyclical Reviewer loop with critique feedback and circuit breaker."""
        retry_count = 0
        max_retries = 3
        current_critique = ""
        response_text = ""

        while retry_count <= max_retries:
            augmented_prompt = (
                f"{user_message}\n\n[Reviewer Critique from Previous Attempt]: {current_critique}"
                if current_critique
                else user_message
            )

            llm_response = self.llm.call_gemma_chat(
                system_prompt=system_prompt,
                user_message=augmented_prompt,
                tool_context=tool_context,
                messages_history=formatted_history,
            )

            if llm_response:
                response_text = llm_response
            elif tool_context:
                response_text = f"According to the verified compliance records:\n{tool_context}"
            else:
                response_text = (
                    "I am your Beacon Compliance assistant for Potter's House Christian Mission UK (SCIO, SC054652). "
                    "How can I assist you with OSCR regulatory guidance, Receipts & Payments reconciliation, or Trustees' Annual Report drafting?"
                )

            is_valid, critique = self._review_agent_output(response_text, tool_context, tool_calls)
            if is_valid or retry_count >= max_retries:
                break

            current_critique = critique or "Please ensure statutory accuracy."
            retry_count += 1

        return response_text

    def process_message(
        self,
        user_message: str,
        state: dict[str, Any],
        kb_corpus: list[dict[str, Any]] | None = None,
        user_id: str = "trustee_01",
        run_id: str = "run_001",
        user_profile: dict[str, Any] | None = None,
        history_turns: list[dict[str, Any]] | None = None,
        tier2_summary: str | None = None,
        tier3_facts: list[str] | None = None,
    ) -> ChatAgentResponse:
        """Process user compliance query with upfront context injection and Cyclical Reviewer loop."""
        if self.is_out_of_scope(user_message):
            refusal = (
                "I am specialized exclusively in OSCR regulatory compliance and financial reporting "
                "for Potter's House Christian Mission UK (SCIO, SC054652). I can only assist with statutory compliance, "
                "Receipts & Payments accounts, Trustees' Annual Report drafting, and OSCR deadlines."
            )
            return ChatAgentResponse(message=refusal, tool_calls=[], sources=[], thinking=None)

        session_id = run_id or state.get("run_id", "run_001")
        tags = ["compliance_chat", "oscr", "sc054652", f"run:{session_id}"]
        meta = {
            "charity_number": "SC054652",
            "run_id": session_id,
            "reconciled": state.get("statement_of_balances", {}).get("reconciled", True),
        }

        with default_tracer.trace_agent_turn(
            name="compliance_chat_agent",
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            metadata=meta,
        ) as agent_ctx:
            lower_msg = user_message.lower()
            tool_calls, sources, tool_context = self._execute_sync_tools(
                lower_msg, user_message, session_id, state, kb_corpus, user_id
            )

            system_prompt = self._build_system_prompt_with_context(
                user_id, session_id, state, user_profile, history_turns, tier2_summary, tier3_facts
            )

            formatted_history = [
                {"role": h["role"], "content": h["content"]}
                for h in (history_turns or [])
                if h.get("role") in ("user", "assistant") and h.get("content")
            ]

            response_text = self._run_cyclical_review_loop(
                system_prompt, user_message, tool_context, tool_calls, formatted_history
            )
            agent_ctx.set_output(response_text)

            return ChatAgentResponse(
                message=response_text, tool_calls=tool_calls, sources=sources, thinking=None
            )

    def _stream_financial_tool(
        self, state: dict[str, Any], session_id: str, tool_calls: list[dict[str, Any]]
    ):
        """Execute deterministic financial tool with streaming action events and error containment."""
        yield {
            "type": "action",
            "action_id": "act_fin_01",
            "label": "Checking verified Receipts & Payments schedule",
            "status": "running",
        }
        try:
            with default_tracer.trace_tool_execution(
                name="get_financial_summary_tool",
                as_type="tool",
                input_data={"run_id": session_id},
            ) as tool_ctx:
                fin_summary = self.get_financial_summary_tool(state)
                tool_calls.append({"tool": "get_financial_summary", "output": fin_summary})
                tool_context = (
                    f"Deterministic Node 3 Financial Statement:\n"
                    f"- Gross Receipts: £{fin_summary['gross_receipts']}\n"
                    f"- Gross Payments: £{fin_summary['gross_payments']}\n"
                    f"- Net Movement: £{fin_summary['net_movement']}\n"
                    f"- Reconciled: {fin_summary['reconciled']}"
                )
                tool_ctx.set_output(fin_summary)
            yield {
                "type": "action",
                "action_id": "act_fin_01",
                "label": "Reviewed Receipts & Payments schedule",
                "status": "completed",
            }
            return tool_context
        except Exception as err:
            yield {
                "type": "action",
                "action_id": "act_fin_01",
                "label": "Checking verified Receipts & Payments schedule",
                "status": "failed",
            }
            return f"Note: Unable to retrieve live Receipts & Payments records due to temporary error: {err}"

    def _stream_kb_tool(
        self,
        user_message: str,
        kb_corpus: list[dict[str, Any]] | None,
        user_id: str,
        tool_calls: list[dict[str, Any]],
        sources: list[str],
    ):
        """Execute OSCR RAG tool with streaming action events and error containment."""
        yield {
            "type": "action",
            "action_id": "act_kb_01",
            "label": "Searching OSCR guidance knowledge base",
            "status": "running",
        }
        try:
            with default_tracer.trace_tool_execution(
                name="search_knowledge_base_tool",
                as_type="retriever",
                input_data={"query": user_message},
            ) as ret_ctx:
                search_results = self.search_knowledge_base_tool(
                    user_message, kb_corpus or [], user_id=user_id
                )
                tool_calls.append(
                    {
                        "tool": "search_knowledge_base",
                        "matches": len(search_results.get("kb_matches", [])),
                    }
                )
                sources.extend(search_results.get("sources", []))
                tool_context = search_results.get("formatted_context", "")
                ret_ctx.set_output(
                    {
                        "sources": sources,
                        "matches_count": len(search_results.get("kb_matches", [])),
                    }
                )
            yield {
                "type": "action",
                "action_id": "act_kb_01",
                "label": "Reviewed OSCR Scottish charity guidance",
                "status": "completed",
            }
            return tool_context
        except Exception as err:
            yield {
                "type": "action",
                "action_id": "act_kb_01",
                "label": "Searching OSCR guidance knowledge base",
                "status": "failed",
            }
            return f"Note: Unable to retrieve OSCR knowledge base records due to temporary error: {err}"

    def stream_message(
        self,
        user_message: str,
        state: dict[str, Any],
        kb_corpus: list[dict[str, Any]] | None = None,
        user_id: str = "trustee_01",
        run_id: str = "run_001",
        user_profile: dict[str, Any] | None = None,
        history_turns: list[dict[str, Any]] | None = None,
        tier2_summary: str | None = None,
        tier3_facts: list[str] | None = None,
    ):
        """Yield structured SSE-ready dicts for real-time thought, action, and token streaming."""
        if self.is_out_of_scope(user_message):
            refusal = (
                "I am specialized exclusively in OSCR regulatory compliance and financial reporting "
                "for Potter's House Christian Mission UK (SCIO, SC054652). I can only assist with statutory compliance, "
                "Receipts & Payments accounts, Trustees' Annual Report drafting, and OSCR deadlines."
            )
            for token in refusal.split(" "):
                yield {"type": "token", "chunk": token + " "}
            yield {
                "type": "done",
                "full_message": refusal,
                "thinking": None,
                "tool_calls": [],
                "sources": [],
            }
            return

        session_id = run_id or state.get("run_id", "run_001")
        tags = ["compliance_chat", "oscr", "sc054652", "stream", f"run:{session_id}"]
        meta = {
            "charity_number": "SC054652",
            "run_id": session_id,
            "streaming": True,
            "reconciled": state.get("statement_of_balances", {}).get("reconciled", True),
        }

        with default_tracer.trace_agent_turn(
            name="compliance_chat_agent",
            user_message=user_message,
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            metadata=meta,
        ) as agent_ctx:
            lower_msg = user_message.lower()
            tool_calls: list[dict[str, Any]] = []
            sources: list[str] = []
            tool_context = ""

            fin_keywords = (
                "financial",
                "total",
                "income",
                "receipt",
                "payment",
                "balance",
                "money",
                "figures",
            )
            kb_keywords = (
                "oscr",
                "rule",
                "guidance",
                "reporting",
                "threshold",
                "constitution",
                "deadline",
                "scio",
                "act",
            )

            if any(kw in lower_msg for kw in fin_keywords):
                gen = self._stream_financial_tool(state, session_id, tool_calls)
                try:
                    while True:
                        yield next(gen)
                except StopIteration as stop:
                    tool_context = stop.value or ""
            elif any(kw in lower_msg for kw in kb_keywords):
                gen = self._stream_kb_tool(user_message, kb_corpus, user_id, tool_calls, sources)
                try:
                    while True:
                        yield next(gen)
                except StopIteration as stop:
                    tool_context = stop.value or ""

            system_prompt = self._build_system_prompt_with_context(
                user_id=user_id,
                run_id=session_id,
                state=state,
                user_profile=user_profile,
                history_turns=history_turns,
                tier2_summary=tier2_summary,
                tier3_facts=tier3_facts,
            )

            formatted_history = [
                {"role": h["role"], "content": h["content"]}
                for h in (history_turns or [])
                if h.get("role") in ("user", "assistant") and h.get("content")
            ]

            accumulated_tokens = []
            accumulated_thoughts = []

            for stream_event in self.llm.stream_gemma_chat(
                system_prompt=system_prompt,
                user_message=user_message,
                tool_context=tool_context,
                messages_history=formatted_history,
            ):
                ev_type = stream_event.get("type")
                chunk = stream_event.get("chunk", "")
                if ev_type == "thought":
                    accumulated_thoughts.append(chunk)
                    yield stream_event
                elif ev_type == "token":
                    accumulated_tokens.append(chunk)
                    yield stream_event

            full_message = "".join(accumulated_tokens).strip()
            full_thinking = "".join(accumulated_thoughts).strip() if accumulated_thoughts else None

            agent_ctx.set_output(full_message)

            yield {
                "type": "done",
                "full_message": full_message,
                "thinking": full_thinking,
                "tool_calls": tool_calls,
                "sources": sources,
            }
