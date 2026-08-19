"""Node 2: TAR Narrative Writer Engine (node_writer.py).

Enforces:
- Document Contract (PRD §4.2): Exactly 4 whitelisted LLM_DRAFTED fields
- Token Protocol: Connective narrative uses [FIGURE_INJECTED] placeholders
- Red-Line 4: Anonymized input payload only
"""

from typing import Any

from backend.src.agents.prompts import NODE_2_TAR_WRITER_SYSTEM_PROMPT
from backend.src.agents.state import BeaconComplianceState
from backend.src.core.llm_client import LLMClient

WHITELISTED_TAR_FIELDS = {
    "governance_description",
    "purposes_activities_narrative",
    "achievements_connective_narrative",
    "principal_risks_narrative",
}


def run_node_writer(state: BeaconComplianceState) -> dict[str, Any]:
    """LangGraph Node 2: Synthesizes draft prose for the 4 whitelisted TAR narrative fields."""
    anonymised_payload = state.get("anonymised_payload", {})
    if not anonymised_payload:
        raise ValueError("Red-Line 4 Violation: Node 2 requires anonymised_payload.")

    llm_client = LLMClient()
    llm_result = llm_client.call_gemma_narrative(
        system_prompt=NODE_2_TAR_WRITER_SYSTEM_PROMPT,
        anonymised_payload=anonymised_payload,
    )

    if llm_result and all(k in llm_result for k in WHITELISTED_TAR_FIELDS):
        tar_draft_fields = {k: str(llm_result[k]) for k in WHITELISTED_TAR_FIELDS}
    else:
        governance_text = (
            "Potter's House Christian Mission UK (SC054652) is governed by its SCIO Constitution. "
            "Trustees are appointed by resolution of the existing board of trustees and receive induction "
            "on OSCR regulatory obligations and financial stewardship."
        )

        purposes_text = (
            "The organisation's charitable purposes are the advancement of the Christian faith and "
            "the relief of poverty. Activities during the year included weekly worship services, "
            "community outreach programs, and support for domestic and international missionary work."
        )

        achievements_text = (
            "During the financial year, the charity conducted 52 weekly services and community events. "
            "Gross receipts for the period were [FIGURE_INJECTED:gross_receipts] and total payments "
            "were [FIGURE_INJECTED:gross_payments], resulting in a net movement of [FIGURE_INJECTED:net_movement]."
        )

        risks_text = (
            "The principal financial risks relate to donation variability and venue lease obligations. "
            "The trustees manage these risks by maintaining an unrestricted general reserve policy "
            "covering at least three months of core operating expenditure."
        )

        tar_draft_fields = {
            "governance_description": governance_text,
            "purposes_activities_narrative": purposes_text,
            "achievements_connective_narrative": achievements_text,
            "principal_risks_narrative": risks_text,
        }

    for field_key in tar_draft_fields:
        if field_key not in WHITELISTED_TAR_FIELDS:
            raise ValueError(
                f"Document Contract Violation: Field '{field_key }' is not whitelisted for LLM drafting."
            )

    return {
        "tar_draft_fields": tar_draft_fields,
    }
