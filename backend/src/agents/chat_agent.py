"""Interactive Compliance Chat Assistant Agent (chat_agent.py).

Powered by Gemma 4 26B A4B.
Enforces:
- Red-Line 1: Zero autonomous submission or external transmission
- Red-Line 2: Zero LLM financial arithmetic (uses deterministic financial tools)
- Red-Line 4: Anonymized state and PII-scrubbed context only
"""

from typing import Any

from backend.src.agents.prompts import CHAT_AGENT_SYSTEM_PROMPT
from backend.src.core.knowledge_context import ComplianceKnowledgeContext
from backend.src.core.llm_client import LLMClient
from pydantic import BaseModel, Field


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
    """Gemma 4 26B A4B Compliance Assistant with deterministic tool boundaries."""

    def __init__(self, knowledge_context: ComplianceKnowledgeContext | None = None) -> None:
        self.knowledge = knowledge_context or ComplianceKnowledgeContext()

    def get_financial_summary_tool(self, state: dict[str, Any]) -> dict[str, Any]:
        """Deterministic tool returning Node 3 receipts and payments financial summary."""
        rnp = state.get("receipts_payments", {})
        balances = state.get("statement_of_balances", {})
        return {
            "gross_receipts": rnp.get("gross_receipts_decimal", "0.00"),
            "gross_payments": rnp.get("gross_payments_decimal", "0.00"),
            "net_movement": rnp.get("net_movement_decimal", "0.00"),
            "reconciled": balances.get("reconciled", False),
            "threshold_breached": rnp.get("is_threshold_breached", False),
        }

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

    def process_message(
        self,
        user_message: str,
        state: dict[str, Any],
        kb_corpus: list[dict[str, Any]] | None = None,
        user_id: str = "trustee_01",
    ) -> ChatAgentResponse:
        """Process user compliance query with tool execution and strict boundary enforcement."""
        if self.is_out_of_scope(user_message):
            refusal = (
                "I am specialized exclusively in OSCR regulatory compliance and financial reporting "
                "for Potter's House Christian Mission UK (SCIO, SC054652). I can only assist with statutory compliance, "
                "Receipts & Payments accounts, Trustees' Annual Report drafting, and OSCR deadlines."
            )
            return ChatAgentResponse(
                message=refusal,
                tool_calls=[],
                sources=[],
                thinking=None,
            )

        tool_calls = []
        sources = []
        lower_msg = user_message.lower()

        llm_client = LLMClient()
        tool_context = ""

        if any(
            kw in lower_msg
            for kw in (
                "financial",
                "total",
                "income",
                "receipt",
                "payment",
                "balance",
                "money",
                "figures",
            )
        ):
            fin_summary = self.get_financial_summary_tool(state)
            tool_calls.append({"tool": "get_financial_summary", "output": fin_summary})
            tool_context = (
                f"Deterministic Node 3 Financial Statement:\n"
                f"- Gross Receipts: £{fin_summary['gross_receipts']}\n"
                f"- Gross Payments: £{fin_summary['gross_payments']}\n"
                f"- Net Movement: £{fin_summary['net_movement']}\n"
                f"- Reconciled: {fin_summary['reconciled']}"
            )
        elif any(
            kw in lower_msg
            for kw in (
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
        ):
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

        llm_response = llm_client.call_gemma_chat(
            system_prompt=CHAT_AGENT_SYSTEM_PROMPT,
            user_message=user_message,
            tool_context=tool_context,
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

        return ChatAgentResponse(
            message=response_text, tool_calls=tool_calls, sources=sources, thinking=None
        )

    def stream_message(
        self,
        user_message: str,
        state: dict[str, Any],
        kb_corpus: list[dict[str, Any]] | None = None,
        user_id: str = "trustee_01",
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

        lower_msg = user_message.lower()
        tool_calls = []
        sources = []
        tool_context = ""

        if any(
            kw in lower_msg
            for kw in (
                "financial",
                "total",
                "income",
                "receipt",
                "payment",
                "balance",
                "money",
                "figures",
            )
        ):
            yield {
                "type": "action",
                "action_id": "act_fin_01",
                "label": "Checking verified Receipts & Payments schedule",
                "status": "running",
            }
            fin_summary = self.get_financial_summary_tool(state)
            tool_calls.append({"tool": "get_financial_summary", "output": fin_summary})
            tool_context = (
                f"Deterministic Node 3 Financial Statement:\n"
                f"- Gross Receipts: £{fin_summary['gross_receipts']}\n"
                f"- Gross Payments: £{fin_summary['gross_payments']}\n"
                f"- Net Movement: £{fin_summary['net_movement']}\n"
                f"- Reconciled: {fin_summary['reconciled']}"
            )
            yield {
                "type": "action",
                "action_id": "act_fin_01",
                "label": "Reviewed Receipts & Payments schedule",
                "status": "completed",
            }
        elif any(
            kw in lower_msg
            for kw in (
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
        ):
            yield {
                "type": "action",
                "action_id": "act_kb_01",
                "label": "Searching OSCR guidance knowledge base",
                "status": "running",
            }
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
            yield {
                "type": "action",
                "action_id": "act_kb_01",
                "label": "Reviewed OSCR Scottish charity guidance",
                "status": "completed",
            }

        llm_client = LLMClient()
        accumulated_tokens = []
        accumulated_thoughts = []

        for stream_event in llm_client.stream_gemma_chat(
            system_prompt=CHAT_AGENT_SYSTEM_PROMPT,
            user_message=user_message,
            tool_context=tool_context,
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

        yield {
            "type": "done",
            "full_message": full_message,
            "thinking": full_thinking,
            "tool_calls": tool_calls,
            "sources": sources,
        }
