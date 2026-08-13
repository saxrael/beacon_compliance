"""Unit tests for Node 5 OSCR Deliverable Assembler (backend/src/agents/node_assembler.py)."""

from backend .src .agents .node_assembler import run_node_assembler 
from backend .src .agents .state import BeaconComplianceState 


def test_node_assembler_compiles_4_deliverables ():
    state :BeaconComplianceState ={
    "run_id":"run_a_01",
    "charity_number":"SC054652",
    "receipts_payments":{
    "gross_receipts_decimal":"10000.00",
    "gross_payments_decimal":"5000.00",
    "net_movement_decimal":"5000.00",
    },
    "statement_of_balances":{"reconciled":True },
    "tar_draft_fields":{
    "governance_description":"Gov text",
    "purposes_activities_narrative":"Purposes text",
    "achievements_connective_narrative":"Connective narrative with [FIGURE_INJECTED:gross_receipts]",
    "principal_risks_narrative":"Risk text",
    },
    }

    res =run_node_assembler (state )
    assert res ["deliverables_ready"]is True 
    deliverables =res ["deliverables"]
    assert len (deliverables )==4 

    types ={d ["type"]for d in deliverables }
    assert types =={"OAR","TAR","RP","IE"}

    for d in deliverables :
        assert "content_hash"in d 
        assert len (d ["content_hash"])==64 
