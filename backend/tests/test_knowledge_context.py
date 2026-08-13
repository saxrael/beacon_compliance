"""Unit tests for ComplianceKnowledgeContext facade (test_knowledge_context.py)."""

from backend .src .core .knowledge_context import ComplianceKnowledgeContext 


def test_compliance_knowledge_context_non_financial_memory ():
    ctx =ComplianceKnowledgeContext ()

    accepted =ctx .add_non_financial_fact (
    fact_id ="fact_01",
    user_id ="trustee_chair",
    fact_text ="Trustees prefer concise summary reports.",
    created_at ="2026-08-12",
    )
    assert accepted is True 

    rejected =ctx .add_non_financial_fact (
    fact_id ="fact_02",
    user_id ="trustee_chair",
    fact_text ="Gross income was £15,000.",
    created_at ="2026-08-12",
    )
    assert rejected is False 


def test_compliance_knowledge_context_query ():
    ctx =ComplianceKnowledgeContext ()
    ctx .add_non_financial_fact (
    fact_id ="fact_01",
    user_id ="trustee_chair",
    fact_text ="Trustees prefer monthly R&P reviews.",
    created_at ="2026-08-12",
    )

    corpus =[
    {
    "chunk_id":"oscr_01",
    "text":"OSCR requires SCIOs under £250,000 gross income to prepare Receipts and Payments accounts.",
    }
    ]

    res =ctx .query_context (
    user_id ="trustee_chair",query ="OSCR receipts and payments rules",corpus =corpus 
    )
    assert res ["user_id"]=="trustee_chair"
    assert len (res ["user_facts"])==1 
    assert "Trustees prefer monthly R&P reviews."in res ["user_facts"][0 ]
    assert len (res ["kb_matches"])==1 
    assert res ["sources"]==["oscr_01"]
