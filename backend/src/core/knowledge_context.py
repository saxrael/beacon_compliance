"""Unified RAG Retrieval & Upfront Context Engineering Facade (knowledge_context.py).

Provides:
1. Upfront Context Engineering Assembler (eliminates single-turn context starvation)
2. Hybrid Sparse+Dense RAG retrieval facade
3. 4-Tier cognitive memory management & Red-Line 2 financial boundary exclusions.
"""

from typing import Any

from pydantic import BaseModel, Field

from backend.src.core.memory import CognitiveMemoryManager, MemoryFact
from backend.src.core.retrieval import HybridRRFRetriever, SearchResultChunk


class TrusteeContext(BaseModel):
    """Trustee authenticated identity metadata."""

    user_id: str = "trustee_01"
    name: str = "Trustee Officer"
    email: str = "trustee@pottershouse.org.uk"
    role: str = "Trustee"
    is_chair: bool = False
    is_treasurer: bool = False


class CharityContext(BaseModel):
    """SC054652 statutory charity profile."""

    charity_number: str = "SC054652"
    name: str = "Potter's House Christian Mission UK"
    constitution: str = "Scottish Charitable Incorporated Organisation (SCIO)"
    principal_office: str = "5B Beachmont Court, Dunbar, East Lothian, Scotland, EH42 1YF"
    financial_year_end: str = "31 December"
    statutory_deadline: str = "30 September"
    funds: list[str] = Field(
        default_factory=lambda: ["unrestricted_general", "restricted_mission", "designated_events"]
    )


class FinancialStateContext(BaseModel):
    """Deterministic Node 3 financial snapshot (Red-Line 2 compliant)."""

    gross_receipts: str = "0.00"
    gross_payments: str = "0.00"
    net_movement: str = "0.00"
    reconciled: bool = True
    is_threshold_breached: bool = False


class ComplianceContextEnvelope(BaseModel):
    """Complete, pre-engineered context envelope injected upfront before chat generation."""

    trustee: TrusteeContext
    charity: CharityContext = Field(default_factory=CharityContext)
    financial_state: FinancialStateContext = Field(default_factory=FinancialStateContext)
    tier1_history: list[dict[str, Any]] = Field(default_factory=list)
    tier2_summary: str | None = None
    tier3_facts: list[str] = Field(default_factory=list)
    active_run_id: str = "run_001"


class ComplianceContextAssembler:
    """Builder assembling complete context envelope to prevent LLM context starvation."""

    def build_context_envelope(
        self,
        user_id: str,
        run_id: str,
        user_profile: dict[str, Any] | None = None,
        financial_state: dict[str, Any] | None = None,
        query: str | None = None,
        history_turns: list[dict[str, Any]] | None = None,
        tier2_summary: str | None = None,
        tier3_facts: list[str] | None = None,
    ) -> ComplianceContextEnvelope:
        """Assemble full upfront context envelope."""
        prof = user_profile or {}
        role = prof.get("role", "Trustee")
        trustee = TrusteeContext(
            user_id=user_id,
            name=prof.get("name", "Trustee Officer"),
            email=prof.get("email", "trustee@pottershouse.org.uk"),
            role=role,
            is_chair=(role.lower() == "chair"),
            is_treasurer=(role.lower() == "treasurer"),
        )

        fin = financial_state or {}
        rnp = fin.get("receipts_payments", {})
        sob = fin.get("statement_of_balances", {})
        fin_context = FinancialStateContext(
            gross_receipts=str(rnp.get("gross_receipts_decimal", "0.00")),
            gross_payments=str(rnp.get("gross_payments_decimal", "0.00")),
            net_movement=str(rnp.get("net_movement_decimal", "0.00")),
            reconciled=bool(sob.get("reconciled", True)),
            is_threshold_breached=bool(rnp.get("is_threshold_breached", False)),
        )

        return ComplianceContextEnvelope(
            trustee=trustee,
            charity=CharityContext(),
            financial_state=fin_context,
            tier1_history=history_turns or [],
            tier2_summary=tier2_summary,
            tier3_facts=tier3_facts or [],
            active_run_id=run_id,
        )

    def format_system_context(self, envelope: ComplianceContextEnvelope) -> str:
        """Render context envelope as structured XML block for system prompt."""
        t = envelope.trustee
        c = envelope.charity
        f = envelope.financial_state

        facts_xml = ""
        if envelope.tier3_facts:
            facts_xml = "\n".join(f"        <fact>{fact}</fact>" for fact in envelope.tier3_facts)

        summary_xml = (
            f"      <tier2_rolling_summary>{envelope.tier2_summary}</tier2_rolling_summary>\n"
            if envelope.tier2_summary
            else ""
        )

        return f"""<active_session_context>
  <authenticated_trustee>
    <user_id>{t.user_id}</user_id>
    <trustee_name>{t.name}</trustee_name>
    <trustee_role>{t.role}</trustee_role>
    <email>{t.email}</email>
    <is_chair>{str(t.is_chair).lower()}</is_chair>
    <is_treasurer>{str(t.is_treasurer).lower()}</is_treasurer>
  </authenticated_trustee>
  <charity_profile>
    <charity_number>{c.charity_number}</charity_number>
    <charity_name>{c.name}</charity_name>
    <constitution>{c.constitution}</constitution>
    <principal_office>{c.principal_office}</principal_office>
    <financial_year_end>{c.financial_year_end}</financial_year_end>
    <statutory_filing_deadline>{c.statutory_deadline}</statutory_filing_deadline>
  </charity_profile>
  <verified_financial_ledger>
    <gross_receipts>£{f.gross_receipts}</gross_receipts>
    <gross_payments>£{f.gross_payments}</gross_payments>
    <net_movement>£{f.net_movement}</net_movement>
    <bank_reconciled>{str(f.reconciled).lower()}</bank_reconciled>
    <income_threshold_breached>{str(f.is_threshold_breached).lower()}</income_threshold_breached>
  </verified_financial_ledger>
  <cognitive_memory>
{summary_xml}    <tier3_permanent_facts>
{facts_xml}
    </tier3_permanent_facts>
  </cognitive_memory>
</active_session_context>"""


class ComplianceKnowledgeContext:
    """Deep facade for knowledge retrieval, cognitive memory, and financial safety."""

    def __init__(
        self,
        retriever: HybridRRFRetriever | None = None,
        memory_manager: CognitiveMemoryManager | None = None,
        repository: Any | None = None,
    ) -> None:
        self.retriever = retriever or HybridRRFRetriever()
        self.memory = memory_manager or CognitiveMemoryManager()
        self.repository = repository
        self.assembler = ComplianceContextAssembler()
        self.stored_facts: list[MemoryFact] = []

    def add_non_financial_fact(
        self, fact_id: str, user_id: str, fact_text: str, created_at: str
    ) -> bool:
        """Add semantic fact after enforcing Red-Line 2 non-financial memory exclusion."""
        fact = self.memory.filter_non_financial_fact(
            fact_id=fact_id, user_id=user_id, fact_text=fact_text, created_at=created_at
        )
        if fact:
            self.stored_facts.append(fact)
            if self.repository is not None and hasattr(self.repository, "save_memory_fact"):
                try:
                    self.repository.save_memory_fact(
                        fact_id=fact_id,
                        user_id=user_id,
                        fact_text=fact_text,
                        source_type="non_financial_convo",
                        created_at=created_at,
                    )
                except Exception:
                    pass
            return True
        return False

    def query_context(
        self,
        user_id: str,
        query: str,
        corpus: list[dict[str, Any]] | None = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Query knowledge base and cognitive memory in a single unified seam."""
        kb_matches: list[SearchResultChunk] = []
        if corpus:
            kb_matches = self.retriever.hybrid_rrf_search(
                query=query, query_vec=None, corpus=corpus, top_n=top_k
            )

        user_facts = [f.fact_text for f in self.stored_facts if f.user_id == user_id]
        if self.repository is not None and hasattr(self.repository, "get_memory_facts"):
            try:
                db_facts = self.repository.get_memory_facts(user_id)
                for df in db_facts:
                    text = df.get("fact_text")
                    if (
                        text
                        and text not in user_facts
                        and not self.memory.is_financial_content(text)
                    ):
                        user_facts.append(text)
            except Exception:
                pass

        kb_texts = [m.text for m in kb_matches]
        sources = [m.chunk_id for m in kb_matches]

        combined_context = ""
        if user_facts:
            combined_context += (
                "User Preferences & Facts:\n" + "\n".join(f"- {f }" for f in user_facts) + "\n\n"
            )
        if kb_texts:
            combined_context += "OSCR Regulatory Guidance Matches:\n" + "\n".join(
                f"- {t }" for t in kb_texts
            )

        return {
            "query": query,
            "user_id": user_id,
            "kb_matches": kb_matches,
            "sources": sources,
            "user_facts": user_facts,
            "formatted_context": combined_context,
        }
