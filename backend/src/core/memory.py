"""3-Tier Memory Architecture Engine for Beacon Compliance (memory.py).

Enforces:
- Non-Financial Cognitive Memory Exclusion (PRD §7.9 / Red-Line 2):
  Financial facts, figures, balances, and transaction amounts are strictly barred from autonomous memory extractions.
  Financial state is managed 100% deterministically by Node 3 in financial_state.
"""

import re

from pydantic import BaseModel, Field


class MemoryFact(BaseModel):
    """Tier 3 Semantic Fact model."""

    fact_id: str
    user_id: str
    fact_text: str
    source_type: str = Field("non_financial_convo", description="Must be non-financial.")
    created_at: str


class MemorySummary(BaseModel):
    """Tier 2 Rolling Narrative Summary model."""

    user_id: str
    run_id: str
    summary_text: str
    updated_at: str


class CognitiveMemoryManager:
    """Manager for Tier 2 rolling summaries and Tier 3 semantic facts."""

    FINANCIAL_KEYWORD_REGEX = re.compile(
        r"[\$£€]|(?:\b(?:pence|amount|receipts|payments|balance|revenue|income|expenditure|legacy|offering|tithe|donation|£\d+)\b)",
        re.IGNORECASE,
    )

    def is_financial_content(self, text: str) -> bool:
        """Check if text contains monetary figures or financial keywords."""
        return bool(self.FINANCIAL_KEYWORD_REGEX.search(text))

    def filter_non_financial_fact(
        self, fact_id: str, user_id: str, fact_text: str, created_at: str
    ) -> MemoryFact | None:
        """Filter and extract non-financial semantic facts. Returns None if financial content detected."""
        if self.is_financial_content(fact_text):
            return None

        return MemoryFact(
            fact_id=fact_id,
            user_id=user_id,
            fact_text=fact_text,
            source_type="non_financial_convo",
            created_at=created_at,
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
            summary_text=summary_text,
            updated_at=updated_at,
        )
