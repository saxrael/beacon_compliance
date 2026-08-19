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
                thinking="Evaluated query domain. Query is outside OSCR statutory compliance scope.",
            )

        tool_calls = []
        sources = []
        lower_msg = user_message.lower()

        llm_client = LLMClient()
        tool_context = ""
        thinking_notes = []

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
            thinking_notes.append(
                "Detected financial inquiry. Invoking deterministic Node 3 financial state tool (Red-Line 2)."
            )
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
            thinking_notes.append(
                "Detected regulatory guidance inquiry. Querying OSCR hybrid knowledge base and cognitive facts."
            )
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

        thinking_text = (
            " ".join(thinking_notes)
            if thinking_notes
            else "Synthesizing OSCR statutory compliance guidance for SC054652."
        )
        return ChatAgentResponse(
            message=response_text, tool_calls=tool_calls, sources=sources, thinking=thinking_text
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
            yield {
                "type": "thought",
                "chunk": "Evaluating inquiry scope against Scottish charity regulatory mandate...",
            }
            yield {
                "type": "thought",
                "chunk": " Query falls outside statutory charity governance. Generating polite boundary notice.",
            }
            refusal = (
                "I am specialized exclusively in OSCR regulatory compliance and financial reporting "
                "for Potter's House Christian Mission UK (SCIO, SC054652). I can only assist with statutory compliance, "
                "Receipts & Payments accounts, Trustees' Annual Report drafting, and OSCR deadlines."
            )
            for token in refusal.split(" "):
                yield {"type": "token", "chunk": token + " "}
            yield {"type": "done", "full_message": refusal, "tool_calls": [], "sources": []}
            return

        lower_msg = user_message.lower()
        tool_calls = []
        sources = []
        tool_context = ""

        yield {
            "type": "thought",
            "chunk": "Analyzing inquiry under Charities and Trustee Investment (Scotland) Act 2005 and SCIO SC054652 profile...",
        }

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
                "type": "thought",
                "chunk": " Financial metric requested. Applying Red-Line 2 (Zero LLM Financial Arithmetic).",
            }
            yield {
                "type": "action",
                "detail": "Consulting verified 2026 Receipts & Payments schedule in Cloudflare D1...",
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
                "type": "thought",
                "chunk": " Statutory/regulatory question identified. Searching OSCR guidance knowledge base and trustee facts.",
            }
            yield {
                "type": "action",
                "detail": "Performing Reciprocal Rank Fusion search across OSCR Guidance & Scottish Charity Regulations...",
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
            "type": "thought",
            "chunk": " Formatting statutory answer with verifiable compliance citations.",
        }

        llm_client = LLMClient()
        llm_response = llm_client.call_gemma_chat(
            system_prompt=CHAT_AGENT_SYSTEM_PROMPT,
            user_message=user_message,
            tool_context=tool_context,
        )

        if llm_response:
            full_text = llm_response
        elif tool_context:
            full_text = f"According to verified compliance records:\n\n{tool_context}"
        else:
            full_text = (
                "I am your Beacon Compliance assistant for Potter's House Christian Mission UK (SCIO, SC054652). "
                "How can I assist you with OSCR regulatory guidance or financial statement review?"
            )

        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == len(words) - 1 else word + " "
            yield {"type": "token", "chunk": chunk}

        yield {
            "type": "done",
            "full_message": full_text,
            "tool_calls": tool_calls,
            "sources": sources,
        }
