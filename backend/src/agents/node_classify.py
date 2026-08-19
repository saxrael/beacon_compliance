"""3-Tier Transaction Classification Engine (node_classify.py).

Classification Tiers:
- Tier 1: Deterministic keyword/pattern matching (config/fund_classifier.yaml)
- Tier 2: Learned rule matching from persistent trustee confirmations
- Tier 2.5: Probabilistic suggestions using LLM (openai/gpt-oss-20b), strictly isolated schema (Rule 3)
"""

import os
from pathlib import Path
from typing import Any

import yaml

from backend.src.agents.state import BeaconComplianceState, ClassificationSuggestion
from backend.src.core.llm_client import LLMClient
from backend.src.core.pii_engine import anonymise_transaction_description


def load_tier1_rules(config_path: str = "config/fund_classifier.yaml") -> list[dict[str, Any]]:
    """Load Tier 1 deterministic rules from configuration YAML."""
    target_path = config_path
    if not os.path.exists(target_path):
        project_root = Path(__file__).resolve().parents[3]
        target_path = str(project_root / config_path)

    if not os.path.exists(target_path):
        return []
    try:
        with open(target_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("rules", [])
    except Exception:
        return []


def classify_transaction_tier1(
    description: str, rules: list[dict[str, Any]]
) -> tuple[str, str, float] | None:
    """Classify transaction using Tier 1 deterministic rules."""
    desc_upper = description.upper()
    for rule in rules:
        pattern = rule.get("pattern", "").upper()
        pattern_type = rule.get("pattern_type", "contains")

        matched = False
        if pattern_type == "contains" and pattern in desc_upper:
            matched = True

        if matched:
            return (
                rule.get("fund", "unrestricted_general"),
                rule.get("category", "Uncategorized"),
                1.0,
            )

    return None


def generate_tier25_suggestion(
    txn_id: str,
    scrubbed_description: str,
    transaction_type: str,
) -> ClassificationSuggestion:
    """Generate Tier 2.5 probabilistic classification suggestion using Gemma 4 / gpt-oss-20b model.

    STRICT RULE 3 MANDATE: Output schema contains ONLY category, confidence, and reasoning.
    Zero monetary fields (amount, total, etc.) permitted.
    """
    desc_lower = scrubbed_description.lower()
    llm_client = LLMClient()
    llm_res = llm_client.call_tier25_classifier(
        description=scrubbed_description, transaction_type=transaction_type
    )

    if llm_res and isinstance(llm_res, dict) and "category" in llm_res:
        suggested_category = str(llm_res.get("category", "General Donations"))
        confidence = float(llm_res.get("confidence", 0.85))
        reasoning = str(llm_res.get("reasoning", "openai/gpt-oss-20b Tier 2.5 LLM classification"))
    elif "rent" in desc_lower or "premises" in desc_lower:
        suggested_category = "Premises & Rent"
        confidence = 0.92
        reasoning = "High similarity to premises occupancy patterns."
    elif "mission" in desc_lower or "overseas" in desc_lower:
        suggested_category = "Mission Support"
        confidence = 0.90
        reasoning = "Contains mission-related terminology."
    elif "utility" in desc_lower or "power" in desc_lower or "gas" in desc_lower:
        suggested_category = "Utilities & Insurance"
        confidence = 0.88
        reasoning = "Identified utility vendor pattern."
    else:
        suggested_category = (
            "General Expenses" if transaction_type == "payment" else "General Donations"
        )
        confidence = 0.85
        reasoning = "Suggested based on description text features."

    suggestion = ClassificationSuggestion(
        txn_id=txn_id, category=suggested_category, confidence=confidence, reasoning=reasoning
    )

    dict_repr = suggestion.model_dump()
    for forbidden_key in ("amount", "total", "monetary_value", "pence", "amount_pence"):
        if forbidden_key in dict_repr:
            raise ValueError(
                f"Rule 3 Violation: Tier 2.5 suggestion contains forbidden monetary field '{forbidden_key }'"
            )

    return suggestion


def run_node_classify(
    state: BeaconComplianceState,
    tier1_rules_path: str = "config/fund_classifier.yaml",
    learned_tier2_rules: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """LangGraph Classification Node executing Tier 1, Tier 2, and Tier 2.5 classification pipeline."""
    raw_txns = state.get("anonymised_payload", {}).get("raw_transactions", [])
    if not raw_txns:
        raw_txns = state.get("pending_tier2_review", [])

    tier1_rules = load_tier1_rules(tier1_rules_path)
    tier2_rules = learned_tier2_rules or []

    classified_transactions: list[dict[str, Any]] = []
    pending_tier2_review: list[dict[str, Any]] = []
    pending_tier25_suggestions: list[ClassificationSuggestion] = []

    for item in raw_txns:
        txn_id = item.get("txn_id", "txn_unknown")
        raw_desc = item.get("description", "")
        scrubbed_desc = anonymise_transaction_description(raw_desc)
        amount_pence = item.get("amount_pence", 0)
        txn_type = item.get("transaction_type", "receipt")

        t1_match = classify_transaction_tier1(scrubbed_desc, tier1_rules)
        if t1_match:
            fund, category, conf = t1_match
            classified_transactions.append(
                {
                    "txn_id": txn_id,
                    "run_id": state.get("run_id", "run_001"),
                    "date": item.get("date", "2026-01-01"),
                    "description": scrubbed_desc,
                    "amount_pence": amount_pence,
                    "fund": fund,
                    "category": category,
                    "transaction_type": txn_type,
                    "classification_tier": "1",
                    "classification_confidence": conf,
                }
            )
            continue

        t2_match = classify_transaction_tier1(scrubbed_desc, tier2_rules)
        if t2_match:
            fund, category, conf = t2_match
            classified_transactions.append(
                {
                    "txn_id": txn_id,
                    "run_id": state.get("run_id", "run_001"),
                    "date": item.get("date", "2026-01-01"),
                    "description": scrubbed_desc,
                    "amount_pence": amount_pence,
                    "fund": fund,
                    "category": category,
                    "transaction_type": txn_type,
                    "classification_tier": "2",
                    "classification_confidence": conf,
                }
            )
            continue

        suggestion = generate_tier25_suggestion(
            txn_id=txn_id, scrubbed_description=scrubbed_desc, transaction_type=txn_type
        )
        pending_tier25_suggestions.append(suggestion)

        pending_tier2_review.append(
            {
                "txn_id": txn_id,
                "description": scrubbed_desc,
                "amount_pence": amount_pence,
                "transaction_type": txn_type,
                "suggested_category": suggestion.category,
                "suggestion_confidence": suggestion.confidence,
                "suggestion_reasoning": suggestion.reasoning,
            }
        )

    return {
        "classified_transactions": classified_transactions,
        "pending_tier2_review": pending_tier2_review,
        "pending_tier25_suggestions": pending_tier25_suggestions,
    }
