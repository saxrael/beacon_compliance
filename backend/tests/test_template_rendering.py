"""Comprehensive unit and integration test suite for Option A Institutional Templates,
Dynamic Chair Name Resolution, and Cryptographic Decoupling (test_template_rendering.py).
"""

import re
from pathlib import Path
from typing import Any

from backend.src.agents.node_assembler import _sanitize_chair_name, run_node_assembler
from backend.src.agents.state import BeaconComplianceState
from backend.src.api.auth import create_jwt_token
from backend.src.api.main import app
from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.repository import ComplianceRepository
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "templates"

TEMPLATE_FILES = [
    "oar_template.html",
    "tar_template.html",
    "rnp_account_template.html",
    "ie_pack_template.html",
]


def test_option_a_templates_exist():
    """Verify all 4 statutory OSCR deliverable document HTML templates exist."""
    for filename in TEMPLATE_FILES:
        path = TEMPLATES_DIR / filename
        assert path.exists(), f"Missing template file: {filename}"


def test_templates_contain_no_raw_hashes_or_vendor_branding():
    """Verify all 4 templates have zero raw 64-character hashes, zero content_hash / hmac_signature

    tokens in HTML body/footers, zero vendor branding, and contain proper charity publication footers.
    """
    disallowed_terms = [
        "content_hash",
        "hmac_signature",
        "Beacon Compliance OS",
        "Verified via Beacon Compliance",
        "verified-badge",
    ]
    hash_regex = re.compile(r"[a-f0-9]{64}", re.IGNORECASE)

    for filename in TEMPLATE_FILES:
        path = TEMPLATES_DIR / filename
        content = path.read_text(encoding="utf-8")

        for term in disallowed_terms:
            assert term not in content, f"Disallowed term '{term}' found in {filename}"

        assert not hash_regex.search(content), f"Raw 64-character hash pattern found in {filename}"

        assert (
            "Potter's House Christian Mission UK (SCIO SC054652)" in content
        ), f"Missing official charity publication footer in {filename}"


def test_oar_template_structure_and_option_a_signature_block():
    """Verify oar_template.html has Section 3 Trustee Certification with doc_ref and trustee details."""
    content = (TEMPLATES_DIR / "oar_template.html").read_text(encoding="utf-8")

    assert "3. Trustee Certification & Statutory Document Reference" in content
    assert "Doc Ref: {{ doc_ref }}" in content
    assert "{{ signing_trustee_name }}" in content
    assert "{{ signing_trustee_role }}" in content
    assert "{{ approval_date }}" in content
    assert "{{ signoff_status }}" in content


def test_tar_template_structure_and_option_a_signature_block():
    """Verify tar_template.html has formal Section 6 Trustee Declaration with doc_ref and trustee details."""
    content = (TEMPLATES_DIR / "tar_template.html").read_text(encoding="utf-8")

    assert "6. Trustee Declaration & Formal Approval" in content
    assert (
        "The trustees declare that they have approved the trustees' annual report above" in content
    )
    assert "{{ signing_trustee_name }}" in content
    assert "{{ signing_trustee_role }}" in content
    assert "{{ approval_date }}" in content
    assert "Doc Ref: {{ doc_ref }}" in content
    assert "{{ current_trustees }}" in content


def test_rnp_template_structure_and_section_4_approval():
    """Verify rnp_account_template.html has Section 4 Statement of Balances Trustee Approval."""
    content = (TEMPLATES_DIR / "rnp_account_template.html").read_text(encoding="utf-8")

    assert "4. Statement of Balances Trustee Approval" in content
    assert "We confirm that the Receipts and Payments Accounts and Statement of Balances" in content
    assert "{{ signing_trustee_name }}" in content
    assert "{{ signing_trustee_role }}" in content
    assert "{{ approval_date }}" in content
    assert "Doc Ref: {{ doc_ref }}" in content


def test_ie_pack_template_structure_and_section_3_transmittal():
    """Verify ie_pack_template.html has Document Reference index and Section 3 Trustee Transmittal Declaration."""
    content = (TEMPLATES_DIR / "ie_pack_template.html").read_text(encoding="utf-8")

    assert "1. Included Deliverables & Document Reference Index" in content
    assert "Doc Ref: SC054652-{{ financial_year }}-OAR" in content
    assert "Doc Ref: SC054652-{{ financial_year }}-TAR" in content
    assert "Doc Ref: SC054652-{{ financial_year }}-RPA" in content
    assert "3. Trustee Transmittal Declaration" in content
    assert "Transmitted to the Independent Examiner on behalf of the Board of Trustees" in content
    assert "{{ signing_trustee_name }}" in content
    assert "{{ signing_trustee_role }}" in content
    assert "{{ approval_date }}" in content
    assert "Doc Ref: {{ doc_ref }}" in content


def test_sanitize_chair_name():
    """Verify _sanitize_chair_name catches null, undefined, empty, and whitespace strings."""
    assert _sanitize_chair_name(None) == "Chair of the Board of Trustees"
    assert _sanitize_chair_name("") == "Chair of the Board of Trustees"
    assert _sanitize_chair_name("   ") == "Chair of the Board of Trustees"
    assert _sanitize_chair_name("None") == "Chair of the Board of Trustees"
    assert _sanitize_chair_name("null") == "Chair of the Board of Trustees"
    assert _sanitize_chair_name("NULL") == "Chair of the Board of Trustees"
    assert _sanitize_chair_name("undefined") == "Chair of the Board of Trustees"
    assert _sanitize_chair_name("Pastor Israel") == "Pastor Israel"
    assert _sanitize_chair_name("  Pastor Israel  ") == "Pastor Israel"


def test_repository_get_chair_user_and_signing_chair_name_hierarchy():
    """Verify dynamic Chair resolution hierarchy in ComplianceRepository:

    1. Approvals table Chair JOIN
    2. Users table Chair
    3. Fallback to 'Chair of the Board of Trustees'
    """
    db = D1DatabaseClient(db_path=":memory:")
    repo = ComplianceRepository(db_client=db)

    assert repo.get_chair_user() is None
    assert repo.get_signing_chair_name() == "Chair of the Board of Trustees"
    assert repo.get_signing_chair_name("run_test_001") == "Chair of the Board of Trustees"

    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('u_chair_1', 'chair@pottershouse.org.uk', 'hash', 'Pastor Israel', 'Chair', 1)"
    )

    chair_profile = repo.get_chair_user()
    assert chair_profile is not None
    assert chair_profile["name"] == "Pastor Israel"
    assert chair_profile["role"] == "Chair"
    assert repo.get_signing_chair_name() == "Pastor Israel"
    assert repo.get_signing_chair_name("run_unsigned") == "Pastor Israel"

    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('u_chair_2', 'acting_chair@pottershouse.org.uk', 'hash', 'Elder Smith', 'Chair', 1)"
    )
    db.execute(
        "INSERT INTO runs (run_id, charity_scn, year_end, status, created_at) "
        "VALUES ('run_signed_001', 'SC054652', '2026-12-31', 'approved', '2026-08-19T00:00:00Z')"
    )
    db.execute(
        "INSERT INTO deliverables (deliverable_id, run_id, type, status) "
        "VALUES ('deliv_tar_001', 'run_signed_001', 'TAR', 'approved')"
    )
    repo.save_approval(
        approval_id="appr_001",
        run_id="run_signed_001",
        deliverable_id="deliv_tar_001",
        trustee_id="u_chair_2",
        role="Chair",
        approval_hash="fake_hash_123",
        approved_at="2026-08-19T01:00:00Z",
    )

    assert repo.get_signing_chair_name("run_signed_001") == "Elder Smith"
    assert repo.get_signing_chair_name("run_other") == "Pastor Israel"


def test_node_assembler_populates_option_a_fields_and_computes_hashes():
    """Verify node_assembler generates doc_ref, injects Chair name, and preserves 64-char SHA-256 hashes."""
    state: BeaconComplianceState = {
        "run_id": "run_test_option_a",
        "charity_number": "SC054652",
        "financial_year": "2026",
        "chair_name": "Pastor Israel",
        "receipts_payments": {
            "gross_receipts_decimal": "125000.00",
            "gross_payments_decimal": "75000.00",
            "net_movement_decimal": "50000.00",
        },
        "statement_of_balances": {"reconciled": True},
        "tar_draft_fields": {
            "governance_description": "Governance per Constitution.",
            "purposes_activities_narrative": "Advancement of Christian faith.",
            "achievements_connective_narrative": "52 services conducted. Total: [FIGURE_INJECTED:gross_receipts].",
            "principal_risks_narrative": "Reserves policy.",
        },
    }

    result = run_node_assembler(state)
    assert result["deliverables_ready"] is True
    deliverables = result["deliverables"]
    assert len(deliverables) == 4

    deliv_map = {d["type"]: d for d in deliverables}

    oar = deliv_map["OAR"]
    assert oar["doc_ref"] == "SC054652-2026-OAR"
    assert oar["signing_trustee_name"] == "Pastor Israel"
    assert "content_hash" in oar
    assert len(oar["content_hash"]) == 64

    tar = deliv_map["TAR"]
    assert tar["doc_ref"] == "SC054652-2026-TAR"
    assert tar["chair_name"] == "Pastor Israel"
    assert tar["signing_trustee_name"] == "Pastor Israel"
    assert tar["sections"]["reference_admin"]["chair_name"] == "Pastor Israel"
    assert (
        "Pastor Israel (Chair), Secretary, Treasurer"
        in tar["sections"]["reference_admin"]["current_trustees"]
    )
    assert (
        "Approved by the Board of Trustees and signed on their behalf by: Pastor Israel, Chair."
        in tar["sections"]["declaration"]
    )
    assert "content_hash" in tar
    assert len(tar["content_hash"]) == 64

    rp = deliv_map["RP"]
    assert rp["doc_ref"] == "SC054652-2026-RPA"
    assert rp["signing_trustee_name"] == "Pastor Israel"
    assert "content_hash" in rp
    assert len(rp["content_hash"]) == 64

    ie = deliv_map["IE"]
    assert ie["doc_ref"] == "SC054652-2026-IEP"
    assert ie["signing_trustee_name"] == "Pastor Israel"
    assert "content_hash" in ie
    assert len(ie["content_hash"]) == 64


def test_node_assembler_graceful_fallback_when_chair_name_empty():
    """Verify node_assembler falls back safely when chair_name is None, whitespace, or invalid."""
    state: BeaconComplianceState = {
        "run_id": "run_fallback_001",
        "charity_number": "SC054652",
        "chair_name": "  ",
        "receipts_payments": {
            "gross_receipts_decimal": "10000.00",
            "gross_payments_decimal": "5000.00",
            "net_movement_decimal": "5000.00",
        },
        "statement_of_balances": {"reconciled": True},
        "tar_draft_fields": {},
    }

    result = run_node_assembler(state)
    deliv_map = {d["type"]: d for d in result["deliverables"]}

    tar = deliv_map["TAR"]
    assert tar["signing_trustee_name"] == "Chair of the Board of Trustees"
    assert tar["sections"]["reference_admin"]["current_trustees"] == "Chair, Secretary, Treasurer"
    assert (
        "Approved by the Board of Trustees and signed on their behalf by: Chair of the Board of Trustees, Chair."
        in tar["sections"]["declaration"]
    )


def test_template_rendering_simulation():
    """Simulate template rendering across all 4 templates and assert clean output with zero template leaks."""

    def render_template(template_str: str, context: dict[str, Any]) -> str:
        rendered = template_str
        for key, val in context.items():
            rendered = rendered.replace(f"{{{{ {key} }}}}", str(val))
            rendered = rendered.replace(f"{{{{{key}}}}}", str(val))
        return rendered

    context = {
        "financial_year": "2026",
        "signing_trustee_name": "Pastor Israel",
        "signing_trustee_role": "Chair of the Board of Trustees",
        "approval_date": "31 December 2026",
        "doc_ref": "SC054652-2026-TAR",
        "signoff_status": "Approved & Certified",
        "current_trustees": "Pastor Israel (Chair), Secretary, Treasurer",
        "gross_receipts_decimal": "125000.00",
        "gross_payments_decimal": "75000.00",
        "net_movement_decimal": "50000.00",
        "closing_balance_decimal": "100000.00",
        "governance_description": "Constitutional governance under SCIO model constitution.",
        "purposes_activities_narrative": "Advancement of religion and relief of poverty in Dunbar.",
        "achievements_connective_narrative": "Conducted 52 weekly services and community outreach.",
        "principal_risks_narrative": "Maintaining 3-month operating reserve policy.",
    }

    for filename in TEMPLATE_FILES:
        template_raw = (TEMPLATES_DIR / filename).read_text(encoding="utf-8")
        rendered = render_template(template_raw, context)

        for var in ["signing_trustee_name", "signing_trustee_role", "approval_date", "doc_ref"]:
            assert f"{{{{ {var} }}}}" not in rendered
            assert f"{{{{{var}}}}}" not in rendered

        assert not re.search(r"[a-f0-9]{64}", rendered)

        assert "Beacon Compliance OS" not in rendered


def test_deliverables_api_route_with_dynamic_chair(tmp_path, monkeypatch):
    """Integration test verifying GET /api/deliverables/{run_id} returns doc_ref and dynamically resolved Chair."""
    db_path = str(tmp_path / "test_deliv_api.db")
    db = D1DatabaseClient(db_path=db_path)
    db.execute(
        "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES ('u_chair_test', 'chair@pottershouse.org.uk', 'hash', 'Pastor Israel', 'Chair', 1)"
    )

    repo = ComplianceRepository(db_client=db)
    repo.save_financial_state(
        run_id="run_api_test_001",
        fund="unrestricted_general",
        receipts={"total_receipts_decimal": "120000.00", "gross_receipts_decimal": "120000.00"},
        payments={"total_payments_decimal": "70000.00", "gross_payments_decimal": "70000.00"},
        opening_balance_pence=5000000,
        closing_balance_pence=10000000,
    )
    db.close()

    monkeypatch.setenv("D1_DB_PATH", db_path)

    token = create_jwt_token(
        user_id="u_chair_test",
        role="Chair",
        email="chair@pottershouse.org.uk",
        name="Pastor Israel",
    )
    headers = {"Authorization": f"Bearer {token}"}

    client = TestClient(app)
    res = client.get("/api/deliverables/run_api_test_001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["deliverables_ready"] is True
    delivs = data["deliverables"]
    assert len(delivs) == 4

    for d in delivs:
        assert "doc_ref" in d
        assert d["doc_ref"].startswith("SC054652-2026-")
        assert d["signing_trustee_name"] == "Pastor Israel"
        assert "content_hash" in d
        assert len(d["content_hash"]) == 64
