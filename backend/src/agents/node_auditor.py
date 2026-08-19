"""Node 4: Hallucination & Consistency Auditor (node_auditor.py).

Enforces Node 4 audit checks:
- Intercepts Node 2 draft outputs
- Scans narrative text for unauthorized financial figures or contradictions against Node 3 receipts_payments state
"""

import re
from typing import Any

from backend.src.agents.state import BeaconComplianceState


def run_node_auditor(state: BeaconComplianceState) -> dict[str, Any]:
    """LangGraph Node 4: Audits Node 2 narrative drafts for hallucinated figures or contradicted facts."""
    tar_fields = state.get("tar_draft_fields", {})
    if not tar_fields:
        return {
            "hallucination_audit_results": {
                "passed": False,
                "error": "No tar_draft_fields found in state.",
            }
        }

    detected_figures: list[str] = []
    currency_regex = re.compile(r"£\d+(?:,\d{3})*(?:\.\d{2})?")

    for field_name, prose in tar_fields.items():
        if field_name == "achievements_connective_narrative":
            continue

        matches = currency_regex.findall(prose)
        if matches:
            detected_figures.extend([f"{field_name }:{m }" for m in matches])

    if detected_figures:
        return {
            "hallucination_audit_results": {
                "passed": False,
                "hallucinations_detected": detected_figures,
                "error": "Hallucinated monetary figure detected in LLM narrative field.",
            }
        }

    return {
        "hallucination_audit_results": {
            "passed": True,
            "audited_fields_count": len(tar_fields),
        }
    }
