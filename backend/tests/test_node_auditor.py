"""Unit tests for Node 4 Hallucination Auditor (backend/src/agents/node_auditor.py)."""

from backend.src.agents.node_auditor import run_node_auditor
from backend.src.agents.state import BeaconComplianceState


def test_node_auditor_pass():
    state: BeaconComplianceState = {
        "tar_draft_fields": {
            "governance_description": "Governance description text without numbers.",
            "purposes_activities_narrative": "Charitable purposes text.",
            "achievements_connective_narrative": "Achievements narrative with [FIGURE_INJECTED:gross_receipts].",
            "principal_risks_narrative": "Risk management text.",
        }
    }

    res = run_node_auditor(state)
    assert res["hallucination_audit_results"]["passed"] is True


def test_node_auditor_detects_hallucination():
    state: BeaconComplianceState = {
        "tar_draft_fields": {
            "governance_description": "Governance text mentioning £50,000 hallucinated amount.",
            "purposes_activities_narrative": "Charitable purposes text.",
            "achievements_connective_narrative": "Token text.",
            "principal_risks_narrative": "Risk text.",
        }
    }

    res = run_node_auditor(state)
    assert res["hallucination_audit_results"]["passed"] is False
    assert "hallucinations_detected" in res["hallucination_audit_results"]
