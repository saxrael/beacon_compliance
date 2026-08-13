"""Beacon Compliance LangGraph State Definition.

Enforces Red-Line 4 (PII Boundary Enforcement) and Red-Line 2 (Zero LLM Financial Arithmetic)
via structural type separation across workflow nodes.
"""

from typing import Any ,TypedDict 

from pydantic import BaseModel 


class ClassificationSuggestion (BaseModel ):
    """Tier 2.5 classification output schema per Rule 3 of beacon-financial-boundary.

    STRICT MANDATE: Must contain ONLY category, confidence, and reasoning.
    No monetary fields (amount, total, etc.) permitted.
    """

    txn_id :str 
    category :str 
    confidence :float 
    reasoning :str 


class BeaconComplianceState (TypedDict ,total =False ):
    run_id :str 
    charity_number :str 
    financial_year_end :str 
    raw_documents :list [dict [str ,Any ]]
    anonymised_payload :dict [str ,Any ]
    pii_audit_log :list [dict [str ,Any ]]
    ocr_flags :list [dict [str ,Any ]]
    classified_transactions :list [dict [str ,Any ]]
    pending_tier2_review :list [dict [str ,Any ]]
    pending_tier25_suggestions :list [ClassificationSuggestion ]
    receipts_payments :dict [str ,Any ]
    statement_of_balances :dict [str ,Any ]
    income_threshold_breach :bool 
    tar_draft_fields :dict [str ,str ]
    hallucination_audit_results :dict [str ,Any ]
    approvals :list [dict [str ,Any ]]
    deliverables_ready :bool 
    deliverables :list [dict [str ,Any ]]
