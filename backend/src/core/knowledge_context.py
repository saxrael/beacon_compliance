"""Unified RAG Retrieval & Cognitive Memory Context Facade (knowledge_context.py).

Provides a single deep interface combining hybrid sparse+dense RAG retrieval,
3-tier cognitive memory management, and Red-Line 2 financial boundary exclusions.
"""

from typing import Any

from backend.src.core.memory import CognitiveMemoryManager, MemoryFact
from backend.src.core.retrieval import HybridRRFRetriever, SearchResultChunk


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
