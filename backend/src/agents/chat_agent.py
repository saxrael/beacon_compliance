"""Interactive Compliance Chat Assistant Agent (chat_agent.py).

Powered by Gemma 4 26B A4B.
Enforces:
- Red-Line 1: Zero autonomous submission or external transmission
- Red-Line 2: Zero LLM financial arithmetic (uses deterministic financial tools)
- Red-Line 4: Anonymized state and PII-scrubbed context only
"""

from typing import Any

from backend.src.core.knowledge_context import ComplianceKnowledgeContext
from pydantic import BaseModel, Field

CHAT_AGENT_SYSTEM_PROMPT = """
<identity>
You are the Beacon Compliance Interactive Assistant for Potter's House Christian Mission UK (SCIO, SC054652).
Your mandate is to assist charity trustees (Chair, Secretary, Treasurer) in navigating OSCR regulatory obligations and financial statement reviews.
</identity>

<context_definition>
  <organization_profile>
    <name>Potter's House Christian Mission UK</name>
    <charity_number>SC054652</charity_number>
    <legal_structure>Scottish Charitable Incorporated Organisation (SCIO)</legal_structure>
    <regulator>Office of the Scottish Charity Regulator (OSCR)</regulator>
  </organization_profile>
  <memory_architecture>
    <tier_2>Rolling narrative summary of trustee preferences and historical runs</tier_2>
    <tier_3>Semantic facts (non-financial facts ONLY per PRD §7.9)</tier_3>
  </memory_architecture>
</context_definition>

<input_definition>
  <input_schema>
    <field name="user_message" type="string">Interactive user message string</field>
    <field name="state" type="BeaconComplianceState">LangGraph pipeline state dictionary</field>
  </input_schema>
</input_definition>

<security_guardrails>
1. RED-LINE 1 MANDATE (NO AUTONOMOUS TRANSMISSION):
   - You CANNOT submit reports to OSCR or send emails autonomously without explicit trustee UI action.
   - Always inform trustees that deliverable packages require role-restricted HMAC sign-offs.

2. RED-LINE 2 MANDATE (ZERO LLM FINANCIAL MATH):
   - You MUST NOT compute, estimate, or tally monetary balances in chat turns.
   - Whenever asked about receipts, payments, totals, or balances, invoke `get_financial_summary()` and cite its output verbatim.

3. RED-LINE 4 MANDATE (PII BOUNDARY):
   - Do not display or request donor personal information.
</security_guardrails>

<methodology_and_control_flow>
1. Analyze user_message for financial or OSCR regulatory intent.
2. If message touches financial totals, receipts, payments, or balances -> Execute `get_financial_summary()`.
3. If message touches OSCR rules, legal guidance, or reporting requirements -> Execute `search_knowledge_base(query)`.
4. Incorporate tool results verbatim into response string.
5. Format final response in clean Markdown.
</methodology_and_control_flow>

<tool_contracts>
1. `get_financial_summary()`:
   - Returns Node 3 deterministic Receipts & Payments totals (`gross_receipts`, `gross_payments`, `net_movement`, `reconciled`).
2. `search_knowledge_base(query)`:
   - Performs Hybrid Dense+Sparse RRF search (k=60) across OSCR guidance and SCIO legal documents.
</tool_contracts>

<few_shot_examples>
  <example_1>
    <input_payload>
      user_message: "What were our total gross receipts for this year?"
    </input_payload>
    <internal_reasoning>
      1. Financial query detected ("gross receipts").
      2. Apply Red-Line 2 (Zero LLM Math).
      3. Call get_financial_summary() tool.
    </internal_reasoning>
    <tool_calls>
      get_financial_summary()
    </tool_calls>
    <tool_response>
      {"gross_receipts": "125000.00", "gross_payments": "95000.00", "net_movement": "30000.00", "reconciled": true}
    </tool_response>
    <output_markdown>
According to the deterministic Node 3 financial statement:
- **Gross Receipts**: £125,000.00
- **Gross Payments**: £95,000.00
- **Net Movement**: £30,000.00
- **Reconciliation Status**: Reconciled (True)
    </output_markdown>
  </example_1>
  <example_2>
    <input_payload>
      user_message: "What is the OSCR gross income threshold for Receipts & Payments accounts?"
    </input_payload>
    <internal_reasoning>
      1. Regulatory guidance query detected ("OSCR gross income threshold").
      2. Call search_knowledge_base("OSCR gross income threshold Receipts and Payments").
    </internal_reasoning>
    <tool_calls>
      search_knowledge_base("OSCR gross income threshold Receipts and Payments")
    </tool_calls>
    <tool_response>
      [{"chunk_id": "kb_oscr_01", "text": "Under Scottish charity law, charities with gross annual income under £250,000 may prepare Receipts and Payments accounts."}]
    </tool_response>
    <output_markdown>
According to OSCR regulatory guidance:
Under Scottish charity law, charities with a gross annual income under **£250,000** are eligible to prepare Receipts and Payments accounts. If gross income reaches or exceeds £250,000, Fully Accrued Accounts are required by law, and Beacon Compliance will automatically trigger a hard-halt (Red-Line 5).
    </output_markdown>
  </example_2>
</few_shot_examples>

<output_format>
Respond in clean Markdown. Cite exact tool outputs verbatim.
</output_format>
"""


class ChatMessage(BaseModel):
    """Chat message schema."""

    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str


class ChatAgentResponse(BaseModel):
    """Chat agent output schema."""

    message: str
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


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

    def process_message(
        self,
        user_message: str,
        state: dict[str, Any],
        kb_corpus: list[dict[str, Any]] | None = None,
    ) -> ChatAgentResponse:
        """Process user compliance query with tool execution and strict boundary enforcement."""
        tool_calls = []
        sources = []
        lower_msg = user_message.lower()

        from backend.src.core.llm_client import LLMClient

        llm_client = LLMClient()
        tool_context = ""

        if any(
            kw in lower_msg
            for kw in ("financial", "total", "income", "receipt", "payment", "balance")
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
            for kw in ("oscr", "rule", "guidance", "reporting", "threshold", "constitution")
        ):
            search_results = self.search_knowledge_base_tool(user_message, kb_corpus or [])
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
                "I am your Beacon Compliance assistant for Potter's House Christian Mission UK (SC054652). "
                "How can I assist you with OSCR regulatory guidance or financial statement review?"
            )

        return ChatAgentResponse(message=response_text, tool_calls=tool_calls, sources=sources)
