"""Unit tests for Node 2 TAR Narrative Writer (backend/src/agents/node_writer.py).

Verifies Document Contract 4 whitelisted fields and token protocol.
"""

from backend.src.agents.node_writer import (
    WHITELISTED_TAR_FIELDS,
    run_node_writer,
)
from backend.src.agents.state import BeaconComplianceState


def test_node_writer_whitelisted_fields():
    state: BeaconComplianceState = {
        "run_id": "run_w_01",
        "anonymised_payload": {"documents": [{"doc_id": "d1", "anonymised_text": "Scrubbed text"}]},
    }

    res = run_node_writer(state)
    fields = res["tar_draft_fields"]

    assert set(fields.keys()) == WHITELISTED_TAR_FIELDS
    assert "[FIGURE_INJECTED:gross_receipts]" in fields["achievements_connective_narrative"]
