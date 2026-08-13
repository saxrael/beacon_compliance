"""Unit tests for 3-Tier Classification Engine (backend/src/agents/node_classify.py).

Verifies Tier 1 matching, Tier 2 learned rules, and Tier 2.5 schema isolation (Rule 3).
"""

from backend .src .agents .node_classify import (
generate_tier25_suggestion ,
run_node_classify ,
)
from backend .src .agents .state import BeaconComplianceState ,ClassificationSuggestion 


def test_tier1_deterministic_classification ():
    state :BeaconComplianceState ={
    "run_id":"run_class_01",
    "anonymised_payload":{
    "raw_transactions":[
    {
    "txn_id":"TXN_T1",
    "description":"Weekly Tithe Offering",
    "amount_pence":25000 ,
    "transaction_type":"receipt",
    },
    {
    "txn_id":"TXN_T1_RENT",
    "description":"Beachmont Court Rent Payment",
    "amount_pence":80000 ,
    "transaction_type":"payment",
    },
    ]
    },
    }

    res =run_node_classify (state )

    classified =res ["classified_transactions"]
    assert len (classified )==2 
    assert classified [0 ]["classification_tier"]=="1"
    assert classified [0 ]["category"]=="Donations & Offerings"
    assert classified [1 ]["classification_tier"]=="1"
    assert classified [1 ]["category"]=="Premises & Rent"


def test_tier25_schema_isolation_rule_3 ():
    """Rule 3 Test: Tier 2.5 suggestion schema strictly restricted to category, confidence, reasoning.

    Zero monetary fields allowed.
    """
    suggestion =generate_tier25_suggestion (
    txn_id ="TXN_UNCLASSIFIED",
    scrubbed_description ="Payment to unusual vendor for sound equipment",
    transaction_type ="payment",
    )

    assert isinstance (suggestion ,ClassificationSuggestion )
    assert suggestion .txn_id =="TXN_UNCLASSIFIED"
    assert isinstance (suggestion .category ,str )
    assert isinstance (suggestion .confidence ,float )
    assert isinstance (suggestion .reasoning ,str )

    dump =suggestion .model_dump ()
    assert set (dump .keys ())=={"txn_id","category","confidence","reasoning"}
    for monetary_key in ("amount","amount_pence","total","value"):
        assert monetary_key not in dump 
