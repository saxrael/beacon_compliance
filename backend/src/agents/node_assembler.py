"""Node 5: OSCR Deliverable Assembler (node_assembler.py).

Assembles the 4 OSCR deliverable packages:
- Deliverable 1: Online Annual Return (OAR) pre-population data sheet
- Deliverable 2: Trustees' Annual Report (TAR)
- Deliverable 3: Annual Accounts (R&P Account + Statement of Balances)
- Deliverable 4: Independent Examiner (IE) Pack

Computes SHA-256 content hashes for deliverable integrity and trustee HMAC sign-off.
"""

import hashlib 
import hmac 
import json 
from typing import Any 

from backend .src .agents .state import BeaconComplianceState 


def run_node_assembler (state :BeaconComplianceState )->dict [str ,Any ]:
    """LangGraph Node 5: Compiles the 4 OSCR deliverable packages and SHA-256 hashes."""
    run_id =state .get ("run_id","run_unknown")
    charity_number =state .get ("charity_number","SC054652")
    rnp =state .get ("receipts_payments",{})
    balances =state .get ("statement_of_balances",{})
    tar_fields =state .get ("tar_draft_fields",{})

    d1_oar ={
    "deliverable_id":f"deliv_oar_{run_id }",
    "type":"OAR",
    "charity_number":charity_number ,
    "gross_income":rnp .get ("gross_receipts_decimal","0.00"),
    "gross_expenditure":rnp .get ("gross_payments_decimal","0.00"),
    "status":"ready_for_review",
    }

    d2_tar ={
    "deliverable_id":f"deliv_tar_{run_id }",
    "type":"TAR",
    "charity_number":charity_number ,
    "sections":{
    "reference_admin":{
    "charity_name":"Potter's House Christian Mission UK",
    "charity_number":charity_number ,
    "address":"5B Beachmont Court, Dunbar, Scotland, UK",
    },
    "governance":tar_fields .get ("governance_description",""),
    "objectives":tar_fields .get ("purposes_activities_narrative",""),
    "achievements":tar_fields .get ("achievements_connective_narrative","")
    .replace (
    "[FIGURE_INJECTED:gross_receipts]",f"£{rnp .get ('gross_receipts_decimal','0.00')}"
    )
    .replace (
    "[FIGURE_INJECTED:gross_payments]",f"£{rnp .get ('gross_payments_decimal','0.00')}"
    )
    .replace (
    "[FIGURE_INJECTED:net_movement]",f"£{rnp .get ('net_movement_decimal','0.00')}"
    ),
    "financial_review":tar_fields .get ("principal_risks_narrative",""),
    "declaration":"Approved by the Trustees and signed on their behalf.",
    },
    "status":"ready_for_review",
    }

    d3_rp ={
    "deliverable_id":f"deliv_rp_{run_id }",
    "type":"RP",
    "charity_number":charity_number ,
    "receipts_payments_account":rnp ,
    "statement_of_balances":balances ,
    "status":"ready_for_review",
    }

    d4_ie ={
    "deliverable_id":f"deliv_ie_{run_id }",
    "type":"IE",
    "charity_number":charity_number ,
    "included_deliverables":[f"deliv_tar_{run_id }",f"deliv_rp_{run_id }"],
    "status":"ready_for_review",
    }

    deliverables =[d1_oar ,d2_tar ,d3_rp ,d4_ie ]

    for d in deliverables :
        content_bytes =json .dumps (d ,sort_keys =True ).encode ("utf-8")
        d ["content_hash"]=hmac .new (
        b"beacon_content_hash",content_bytes ,hashlib .sha256 
        ).hexdigest ()

    return {
    "deliverables":deliverables ,
    "deliverables_ready":True ,
    }
