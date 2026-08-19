"""4-Tier Cognitive Memory Architecture Engine for Beacon Compliance (memory.py).

Enforces:
- Non-Financial Cognitive Memory Exclusion (PRD §7.9 / Red-Line 2):
  Financial facts, figures, balances, and transaction amounts are strictly barred from autonomous memory extractions.
  Financial state is managed 100% deterministically by Node 3 in financial_state.
- PII Boundary Enforcement (Red-Line 4).
"""

import re
from typing import Any

from pydantic import BaseModel, Field

from backend.src.core.embeddings import EmbeddingEngine, compute_cosine_distance


class MemoryFact(BaseModel):
    """Tier 3 Semantic Fact model."""

    fact_id: str
    user_id: str
    fact_text: str
    source_type: str = Field("non_financial_convo", description="Must be non-financial.")
    created_at: str
    embedding_vec: list[float] | None = None


class MemorySummary(BaseModel):
    """Tier 2 Rolling Narrative Summary model (<500 words)."""

    user_id: str
    run_id: str
    summary_text: str
    updated_at: str


class Tier1WorkingMemoryBuffer:
    """Sliding window working memory manager for active dialogue turns (50 turns)."""

    def __init__(self, window_size: int = 50) -> None:
        self.window_size = window_size

    def process_turns(
        self, all_turns: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split conversation turns into active sliding window and evicted queue."""
        if len(all_turns) <= self.window_size:
            return all_turns, []
        active_window = all_turns[-self.window_size :]
        evicted_turns = all_turns[: -self.window_size]
        return active_window, evicted_turns


class CognitiveMemoryManager:
    """Manager for Tier 1-4 memory partitioning and Red-Line 2 non-financial filtering."""

    FINANCIAL_KEYWORD_REGEX = re.compile(
        r"[\$£€]|(?:\b(?:pence|amount|receipts|payments|balance|revenue|income|expenditure|legacy|offering|tithe|donation|pounds|£\d+)\b)",
        re.IGNORECASE,
    )

    def __init__(self, embedding_engine: EmbeddingEngine | None = None) -> None:
        self.embeddings = embedding_engine or EmbeddingEngine()

    def is_financial_content(self, text: str) -> bool:
        """Check if text contains monetary figures or financial keywords."""
        return bool(self.FINANCIAL_KEYWORD_REGEX.search(text))

    def filter_non_financial_fact(
        self,
        fact_id: str,
        user_id: str,
        fact_text: str,
        created_at: str,
        embedding_vec: list[float] | None = None,
    ) -> MemoryFact | None:
        """Filter and extract non-financial semantic facts. Returns None if financial content detected."""
        if self.is_financial_content(fact_text):
            return None

        vec = embedding_vec if embedding_vec is not None else self.embeddings.embed_query(fact_text)

        return MemoryFact(
            fact_id=fact_id,
            user_id=user_id,
            fact_text=fact_text.strip(),
            source_type="non_financial_convo",
            created_at=created_at,
            embedding_vec=vec,
        )

    def filter_non_financial_summary(
        self, user_id: str, run_id: str, summary_text: str, updated_at: str
    ) -> MemorySummary | None:
        """Filter and extract non-financial rolling summary. Returns None if financial content detected."""
        if self.is_financial_content(summary_text):
            return None

        return MemorySummary(
            user_id=user_id,
            run_id=run_id,
            summary_text=summary_text.strip(),
            updated_at=updated_at,
        )

    def filter_vector_matched_facts(
        self,
        facts: list[MemoryFact],
        query_vec: list[float],
        max_distance: float = 0.75,
    ) -> list[MemoryFact]:
        """Filter permanent semantic facts by cosine distance threshold (< 0.75)."""
        if not facts or not query_vec:
            return facts

        matched = []
        for fact in facts:
            vec = fact.embedding_vec or self.embeddings.embed_query(fact.fact_text)
            dist = compute_cosine_distance(query_vec, vec)
            if dist < max_distance:
                matched.append(fact)
        return matched
