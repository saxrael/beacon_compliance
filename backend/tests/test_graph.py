"""End-to-End Integration tests for LangGraph State Machine Graph (backend/src/agents/graph.py)."""

from backend.src.agents.graph import BeaconComplianceGraph
from backend.src.agents.state import BeaconComplianceState


def test_graph_end_to_end_success():
    graph = BeaconComplianceGraph()
    initial_state: BeaconComplianceState = {
        "run_id": "run_graph_01",
        "charity_number": "SC054652",
        "raw_documents": [
            {
                "doc_id": "doc_g1",
                "filename": "offering_list.txt",
                "content_bytes": b"Sunday Offering Tithes john@example.com",
                "declared_receipts_pence": 1500000,
            }
        ],
        "anonymised_payload": {
            "opening_balance_pence": 500000,
            "closing_balance_pence": 2000000,
            "raw_transactions": [
                {
                    "txn_id": "TXN_G1",
                    "description": "Weekly Offering",
                    "amount_pence": 1500000,
                    "transaction_type": "receipt",
                }
            ],
        },
    }

    final_state = graph.run(initial_state)

    assert final_state.get("income_threshold_breach") is False
    assert final_state.get("deliverables_ready") is True
    assert len(final_state.get("deliverables", [])) == 4


def test_graph_end_to_end_threshold_halt():
    """Red-Line 5 Test: State machine halts DAG execution if gross income reaches £250,000."""
    graph = BeaconComplianceGraph()
    initial_state: BeaconComplianceState = {
        "run_id": "run_graph_halt",
        "charity_number": "SC054652",
        "raw_documents": [
            {
                "doc_id": "doc_large",
                "filename": "large_legacy.txt",
                "content_bytes": b"Large legacy donation",
                "declared_receipts_pence": 25000000,  # £250,000.00
            }
        ],
    }

    final_state = graph.run(initial_state)

    assert final_state.get("income_threshold_breach") is True
    assert final_state.get("deliverables_ready") is not True
