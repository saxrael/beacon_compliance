"""Unit tests for Master Agent System Prompts (backend/tests/test_master_prompts.py).

Verifies:
- 7-Part XML Architecture across all prompts
- Zero template placeholders
- Red-Lines 1 through 5 enforcement clauses
- Scottish charity law statutory references (2005 Act, 2006 Regs, SC054652)
- Domain-split few-shot demonstrations for the Chat Sentinel
"""

from backend.src.agents.prompts import (
    CHAT_AGENT_SYSTEM_PROMPT,
    NODE_2_TAR_WRITER_SYSTEM_PROMPT,
    NODE_4_AUDITOR_SYSTEM_PROMPT,
    TIER_25_CLASSIFICATION_SYSTEM_PROMPT,
)


def test_master_prompts_7_part_xml_architecture():
    """Verify that all 4 master agent prompts strictly include the 7-Part XML structural tags."""
    prompts = {
        "CHAT_AGENT": CHAT_AGENT_SYSTEM_PROMPT,
        "NODE_2_WRITER": NODE_2_TAR_WRITER_SYSTEM_PROMPT,
        "TIER_25_CLASSIFIER": TIER_25_CLASSIFICATION_SYSTEM_PROMPT,
        "NODE_4_AUDITOR": NODE_4_AUDITOR_SYSTEM_PROMPT,
    }

    required_tags = [
        "<identity>",
        "</identity>",
        "<context_definition>",
        "</context_definition>",
        "<input_definition>",
        "</input_definition>",
        "<security_guardrails>",
        "</security_guardrails>",
        "<methodology_and_control_flow>",
        "</methodology_and_control_flow>",
        "<tool_contracts>",
        "</tool_contracts>",
        "<few_shot_examples>",
        "</few_shot_examples>",
        "<output_format>",
        "</output_format>",
    ]

    for name, prompt_text in prompts.items():
        for tag in required_tags:
            assert tag in prompt_text, f"Prompt '{name}' is missing required structural tag '{tag}'"


def test_master_prompts_zero_template_placeholders():
    """Verify that no prompt contains lazy placeholders like '[paste X here]' or '{topic}'."""
    prompts = [
        CHAT_AGENT_SYSTEM_PROMPT,
        NODE_2_TAR_WRITER_SYSTEM_PROMPT,
        TIER_25_CLASSIFICATION_SYSTEM_PROMPT,
        NODE_4_AUDITOR_SYSTEM_PROMPT,
    ]

    forbidden_placeholders = [
        "[paste X here]",
        "[insert your text]",
        "{topic}",
        "<your_input>",
        "TODO:",
        "FIXME:",
    ]

    for prompt_text in prompts:
        for placeholder in forbidden_placeholders:
            assert (
                placeholder not in prompt_text
            ), f"Found forbidden placeholder '{placeholder}' in prompt"


def test_master_prompts_scottish_statutory_grounding():
    """Verify statutory references to Scottish charity legislation and SC054652."""
    prompts = [
        CHAT_AGENT_SYSTEM_PROMPT,
        NODE_2_TAR_WRITER_SYSTEM_PROMPT,
        TIER_25_CLASSIFICATION_SYSTEM_PROMPT,
        NODE_4_AUDITOR_SYSTEM_PROMPT,
    ]

    for prompt_text in prompts:
        assert "Potter's House Christian Mission UK" in prompt_text
        assert "SC054652" in prompt_text
        assert "SCIO" in prompt_text
        assert "OSCR" in prompt_text or "Scottish Charity" in prompt_text


def test_chat_agent_master_prompt_domain_few_shots():
    """Verify domain-split few-shot demonstrations in the Chat Sentinel prompt."""
    prompt = CHAT_AGENT_SYSTEM_PROMPT

    assert "Domain A — Financial Ledger Status & Reconciliation" in prompt
    assert "Domain A — Income Threshold Breach Warning" in prompt
    assert "Domain A — Multi-Fund Segregation" in prompt
    assert "Domain B — OSCR Annual Filing Deadline" in prompt
    assert "Domain B — General Trustee Duties" in prompt
    assert "Domain B — Safety and Security Dispensations" in prompt
    assert "Domain C — TAR Structure & Whitelisted Field Protocol" in prompt
    assert "Domain C — Reserves Policy Drafting Guidance" in prompt
    assert "Domain D — Independent Examination Eligibility" in prompt
    assert "Domain D — HMAC-Based Trustee Sign-Off Protocol" in prompt
    assert "Domain E — Out-of-Scope Query Refusal" in prompt
    assert "Domain E — Anti-Prompt Injection" in prompt

    assert "get_financial_summary" in prompt
    assert "search_knowledge_base" in prompt

    prompt_lower = prompt.lower()
    assert "red_line_1" in prompt_lower or "red-line 1" in prompt_lower
    assert "red_line_2" in prompt_lower or "red-line 2" in prompt_lower
    assert "red_line_3" in prompt_lower or "red-line 3" in prompt_lower
    assert "red_line_4" in prompt_lower or "red-line 4" in prompt_lower
    assert "red_line_5" in prompt_lower or "red-line 5" in prompt_lower


def test_writer_prompt_document_contract_and_tokens():
    """Verify that Node 2 Writer prompt enforces exactly the 4 whitelisted fields and token syntax."""
    prompt = NODE_2_TAR_WRITER_SYSTEM_PROMPT

    whitelisted_fields = [
        "governance_description",
        "purposes_activities_narrative",
        "achievements_connective_narrative",
        "principal_risks_narrative",
    ]
    for field in whitelisted_fields:
        assert field in prompt

    assert "[FIGURE_INJECTED:gross_receipts]" in prompt
    assert "[FIGURE_INJECTED:gross_payments]" in prompt
    assert "[FIGURE_INJECTED:net_movement]" in prompt


def test_classifier_prompt_schema_isolation_rule_3():
    """Verify that Tier 2.5 Classifier prompt enforces schema isolation and bans monetary fields."""
    prompt = TIER_25_CLASSIFICATION_SYSTEM_PROMPT

    assert "txn_id" in prompt
    assert "category" in prompt
    assert "confidence" in prompt
    assert "reasoning" in prompt
    assert "ZERO MONETARY FIELDS" in prompt.upper() or "ZERO MONETARY FIELD" in prompt.upper()


def test_auditor_prompt_hallucination_rules():
    """Verify that Node 4 Auditor prompt defines strict regex scanning and token checks."""
    prompt = NODE_4_AUDITOR_SYSTEM_PROMPT

    assert "hallucinations_detected" in prompt
    assert "token_violations" in prompt
    assert "inconsistencies" in prompt
    assert "passed" in prompt
