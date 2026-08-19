"""Autonomous Background Cognitive Memory Processor (cognitive_worker.py).

Implements Tier 2 Rolling Narrative Summarization and Tier 3 Semantic Fact Extraction
with Think-Plan-Execute protocol, UUID fallback safety, and Red-Line 2 Non-Financial Boundary.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from backend.src.core.llm_client import LLMClient
from backend.src.core.memory import CognitiveMemoryManager, MemoryFact, MemorySummary

logger = logging.getLogger(__name__)


class CognitiveWorker:
    """Background cognitive processor managing episodic summaries and semantic facts."""

    def __init__(
        self,
        llm_client: Any | None = None,
        memory_manager: CognitiveMemoryManager | None = None,
        repository: Any | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        self.memory = memory_manager or CognitiveMemoryManager()
        self.repository = repository

    def _format_messages_block(self, messages: list[dict[str, Any]]) -> str:
        """Format evicted dialogue turns into a clean text block."""
        lines = []
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "").strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _process_tier2_summary(
        self,
        user_id: str,
        run_id: str,
        dialogue_block: str,
        existing_summary: str | None,
        now_ts: str,
    ) -> MemorySummary | None:
        """Compress evicted dialogue into rolling narrative summary (<500 words)."""
        try:
            summary_raw = self.llm.call_cognitive_summary(
                old_summary=existing_summary or "",
                new_messages=dialogue_block,
            )
            if not summary_raw:
                return None
            filtered_sum = self.memory.filter_non_financial_summary(
                user_id=user_id,
                run_id=run_id,
                summary_text=summary_raw,
                updated_at=now_ts,
            )
            if filtered_sum and self.repository and hasattr(self.repository, "save_memory_summary"):
                self.repository.save_memory_summary(
                    user_id=user_id,
                    run_id=run_id,
                    summary_text=filtered_sum.summary_text,
                    updated_at=now_ts,
                )
            return filtered_sum
        except Exception as err:
            logger.warning(f"Tier 2 cognitive summary extraction failed: {err}")
            return None

    def _process_single_fact(
        self,
        item: dict[str, Any],
        user_id: str,
        existing_ids: set[str],
        now_ts: str,
    ) -> dict[str, Any] | None:
        """Process and validate a single extracted fact item."""
        action = str(item.get("action", "NONE")).upper().strip()
        fact_text = str(item.get("final_fact_text", "")).strip()

        if action == "NONE" or not fact_text or self.memory.is_financial_content(fact_text):
            return None

        target_id = item.get("target_existing_fact_id")
        if action == "UPDATE":
            if not target_id or target_id not in existing_ids:
                action = "CREATE"
                fact_id = f"fact_{uuid.uuid4().hex[:12]}"
            else:
                fact_id = str(target_id)
        else:
            action = "CREATE"
            fact_id = f"fact_{uuid.uuid4().hex[:12]}"

        embedding_vec = self.memory.embeddings.embed_query(fact_text)
        mutation = {
            "action": action,
            "fact_id": fact_id,
            "user_id": user_id,
            "fact_text": fact_text,
            "embedding_vec": embedding_vec,
            "created_at": now_ts,
        }

        if self.repository and hasattr(self.repository, "save_memory_fact"):
            self.repository.save_memory_fact(
                fact_id=fact_id,
                user_id=user_id,
                fact_text=fact_text,
                source_type="non_financial_convo",
                created_at=now_ts,
            )
        return mutation

    def _process_tier3_facts(
        self,
        user_id: str,
        dialogue_block: str,
        existing_facts: list[MemoryFact],
        now_ts: str,
    ) -> list[dict[str, Any]]:
        """Extract permanent non-financial facts using Think-Plan-Execute."""
        fact_mutations: list[dict[str, Any]] = []
        try:
            existing_payload = [
                {"fact_id": f.fact_id, "fact_text": f.fact_text} for f in existing_facts
            ]
            raw_facts = self.llm.call_cognitive_fact_extractor(
                existing_facts=existing_payload,
                new_messages=dialogue_block,
            )
            if isinstance(raw_facts, list):
                existing_ids = {f.fact_id for f in existing_facts}
                for item in raw_facts:
                    if isinstance(item, dict):
                        mutation = self._process_single_fact(item, user_id, existing_ids, now_ts)
                        if mutation:
                            fact_mutations.append(mutation)
        except Exception as err:
            logger.warning(f"Tier 3 semantic fact extraction failed: {err}")

        return fact_mutations

    def process_cognitive_turn(
        self,
        user_id: str,
        run_id: str,
        evicted_messages: list[dict[str, Any]],
        existing_summary: str | None,
        existing_facts: list[MemoryFact],
    ) -> tuple[MemorySummary | None, list[dict[str, Any]]]:
        """Process evicted dialogue turns to update Tier 2 summary and Tier 3 knowledge facts."""
        if not evicted_messages:
            return None, []

        dialogue_block = self._format_messages_block(evicted_messages)
        now_ts = datetime.now(UTC).isoformat()

        updated_summary = self._process_tier2_summary(
            user_id, run_id, dialogue_block, existing_summary, now_ts
        )
        fact_mutations = self._process_tier3_facts(user_id, dialogue_block, existing_facts, now_ts)

        return updated_summary, fact_mutations
