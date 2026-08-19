"""Master Agent System Prompts Package (backend/src/agents/prompts).

Provides production-grade, hardened master system prompts for all Beacon Compliance AI agents and state machine nodes:
- CHAT_AGENT_SYSTEM_PROMPT: Beacon OSCR Statutory Advisor / Interactive Chat Assistant
- NODE_2_TAR_WRITER_SYSTEM_PROMPT: Node 2 TAR Narrative Synthesis Agent
- TIER_25_CLASSIFICATION_SYSTEM_PROMPT: Node 1 / Tier 2.5 Probabilistic Transaction Classifier
- NODE_4_AUDITOR_SYSTEM_PROMPT: Node 4 Hallucination & Consistency Auditor
"""

from backend.src.agents.prompts.auditor_prompts import NODE_4_AUDITOR_SYSTEM_PROMPT
from backend.src.agents.prompts.chat_prompts import CHAT_AGENT_SYSTEM_PROMPT
from backend.src.agents.prompts.classifier_prompts import (
    TIER_25_CLASSIFICATION_SYSTEM_PROMPT,
)
from backend.src.agents.prompts.writer_prompts import NODE_2_TAR_WRITER_SYSTEM_PROMPT

__all__ = [
    "CHAT_AGENT_SYSTEM_PROMPT",
    "NODE_2_TAR_WRITER_SYSTEM_PROMPT",
    "NODE_4_AUDITOR_SYSTEM_PROMPT",
    "TIER_25_CLASSIFICATION_SYSTEM_PROMPT",
]
