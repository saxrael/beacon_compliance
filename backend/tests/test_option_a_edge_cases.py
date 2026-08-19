"""Empirical stress tests and edge case verification for Option A deliverables,
Dynamic Chair Name Resolution, and Template Rendering Hygiene (test_option_a_edge_cases.py).
"""

import re
from pathlib import Path
from typing import Any

import pytest

from backend.src.agents.node_assembler import _sanitize_chair_name, run_node_assembler
from backend.src.agents.state import BeaconComplianceState
from backend.src.db.d1_client import D1DatabaseClient
from backend.src.db.repository import ComplianceRepository

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = PROJECT_ROOT / "templates"

TEMPLATE_FILES = [
    "oar_template.html",
    "tar_template.html",
    "rnp_account_template.html",
    "ie_pack_template.html",
]


class TestChairNameSanitizationEdgeCases:
    """Stress-test _sanitize_chair_name with comprehensive edge cases."""

    @pytest.mark.parametrize(
        ("input_val", "expected_output"),
        [
            ("Dr. John Doe, O.B.E.", "Dr. John Doe, O.B.E."),
            (
                "Rev. Dr. Mary Smith-Jones (Ph.D., M.B.E.)",
                "Rev. Dr. Mary Smith-Jones (Ph.D., M.B.E.)",
            ),
            ("Pastor Israel & Deacon Jane", "Pastor Israel & Deacon Jane"),
            ("O'Connor, Patrick Esq.", "O'Connor, Patrick Esq."),
            ("Prof. Alistair MacLeod-Stewart III", "Prof. Alistair MacLeod-Stewart III"),
            ("  Dr. Jane Doe  ", "Dr. Jane Doe"),
            ("\t\n  Elder Thomas  \r\n", "Elder Thomas"),
        ],
    )
    def test_special_characters_and_titles_preserved(self, input_val: str, expected_output: str):
        assert _sanitize_chair_name(input_val) == expected_output

    @pytest.mark.parametrize(
        "falsy_or_invalid_val",
        [
            None,
            "",
            "   ",
            "\t\t\n\r  ",
            "None",
            "none",
            "NONE",
            "null",
            "Null",
            "NULL",
            "undefined",
            "Undefined",
            "UNDEFINED",
        ],
    )
    def test_null_empty_undefined_fallbacks(self, falsy_or_invalid_val: Any):
        assert _sanitize_chair_name(falsy_or_invalid_val) == "Chair of the Board of Trustees"


class TestRepositoryChairResolutionEdgeCases:
    """Stress-test ComplianceRepository dynamic Chair resolution across database states."""

    def test_zero_users_in_d1_database(self):
        """When D1 database has 0 users, resolver must return institutional default."""
        db = D1DatabaseClient(db_path=":memory:")
        repo = ComplianceRepository(db_client=db)

        assert repo.get_chair_user() is None
        assert repo.get_signing_chair_name() == "Chair of the Board of Trustees"
        assert repo.get_signing_chair_name("non_existent_run") == "Chair of the Board of Trustees"
        db.close()

    def test_multiple_users_with_different_roles_no_chair(self):
        """When users exist with roles like Treasurer/Secretary/Trustee but no Chair, returns fallback."""
        db = D1DatabaseClient(db_path=":memory:")
        db.execute(
            "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) VALUES "
            "('u_sec', 'sec@example.org', 'h1', 'Alice Secretary', 'Secretary', 1), "
            "('u_tres', 'tres@example.org', 'h2', 'Bob Treasurer', 'Treasurer', 1), "
            "('u_tru', 'tru@example.org', 'h3', 'Charlie Trustee', 'Trustee', 1)"
        )
        repo = ComplianceRepository(db_client=db)

        assert repo.get_chair_user() is None
        assert repo.get_signing_chair_name() == "Chair of the Board of Trustees"
        db.close()

    def test_chair_user_with_special_characters_and_titles(self):
        """When designated Chair in users table has special characters/titles, it is cleanly resolved."""
        db = D1DatabaseClient(db_path=":memory:")
        db.execute(
            "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
            "VALUES ('u_c1', 'chair@pottershouse.org.uk', 'h', 'Dr. John Doe, O.B.E.', 'Chair', 1)"
        )
        repo = ComplianceRepository(db_client=db)

        chair = repo.get_chair_user()
        assert chair is not None
        assert chair["name"] == "Dr. John Doe, O.B.E."
        assert repo.get_signing_chair_name() == "Dr. John Doe, O.B.E."
        db.close()

    def test_chair_user_with_whitespace_or_null_name_falls_back(self):
        """When designated Chair in users table has whitespace/null/empty name, safely falls back."""
        db = D1DatabaseClient(db_path=":memory:")
        db.execute(
            "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) "
            "VALUES ('u_c2', 'chair@pottershouse.org.uk', 'h', '   ', 'Chair', 1)"
        )
        repo = ComplianceRepository(db_client=db)

        assert repo.get_signing_chair_name() == "Chair of the Board of Trustees"
        db.close()

    def test_acting_chair_approval_overrides_default_for_specific_run(self):
        """When a specific run was approved by an acting Chair, get_signing_chair_name(run_id) returns acting Chair."""
        db = D1DatabaseClient(db_path=":memory:")
        db.execute(
            "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) VALUES "
            "('u_perm', 'perm@pottershouse.org.uk', 'h', 'Pastor Israel', 'Chair', 1), "
            "('u_acting', 'acting@pottershouse.org.uk', 'h', 'Dr. John Doe, O.B.E.', 'Chair', 1), "
            "('u_treas', 'treas@pottershouse.org.uk', 'h', 'Treasurer Tom', 'Treasurer', 1)"
        )
        db.execute(
            "INSERT INTO runs (run_id, charity_scn, year_end, status, created_at) "
            "VALUES ('run_2026_01', 'SC054652', '2026-12-31', 'approved', '2026-08-19T00:00:00Z')"
        )
        db.execute(
            "INSERT INTO deliverables (deliverable_id, run_id, type, status) "
            "VALUES ('deliv_tar_2026', 'run_2026_01', 'TAR', 'approved')"
        )
        repo = ComplianceRepository(db_client=db)
        repo.save_approval(
            approval_id="appr_acting",
            run_id="run_2026_01",
            deliverable_id="deliv_tar_2026",
            trustee_id="u_acting",
            role="Chair",
            approval_hash="sig_hash_001",
            approved_at="2026-08-19T02:00:00Z",
        )

        assert repo.get_signing_chair_name("run_2026_01") == "Dr. John Doe, O.B.E."
        assert repo.get_signing_chair_name("run_other") == "Pastor Israel"
        assert repo.get_signing_chair_name() == "Pastor Israel"
        db.close()

    def test_non_chair_approval_does_not_override_chair_name(self):
        """When an approval exists from a Treasurer or Secretary, Chair resolution ignores it and falls back to Chair."""
        db = D1DatabaseClient(db_path=":memory:")
        db.execute(
            "INSERT INTO users (user_id, email, password_hash, name, role, first_login_complete) VALUES "
            "('u_perm', 'perm@pottershouse.org.uk', 'h', 'Pastor Israel', 'Chair', 1), "
            "('u_treas', 'treas@pottershouse.org.uk', 'h', 'Treasurer Tom', 'Treasurer', 1)"
        )
        db.execute(
            "INSERT INTO runs (run_id, charity_scn, year_end, status, created_at) "
            "VALUES ('run_2026_02', 'SC054652', '2026-12-31', 'approved', '2026-08-19T00:00:00Z')"
        )
        repo = ComplianceRepository(db_client=db)
        repo.save_approval(
            approval_id="appr_treas",
            run_id="run_2026_02",
            deliverable_id="deliv_tar_2026",
            trustee_id="u_treas",
            role="Treasurer",
            approval_hash="sig_hash_002",
            approved_at="2026-08-19T02:00:00Z",
        )

        assert repo.get_signing_chair_name("run_2026_02") == "Pastor Israel"
        db.close()


class TestNodeAssemblerStressCases:
    """Stress-test node_assembler with special characters, titles, and boundary values."""

    def test_assembler_with_special_characters_in_chair_name(self):
        state: BeaconComplianceState = {
            "run_id": "run_stress_01",
            "charity_number": "SC054652",
            "financial_year": "2026",
            "chair_name": "Dr. John Doe, O.B.E.",
            "receipts_payments": {
                "gross_receipts_decimal": "150000.00",
                "gross_payments_decimal": "90000.00",
                "net_movement_decimal": "60000.00",
            },
            "statement_of_balances": {"reconciled": True},
            "tar_draft_fields": {},
        }

        result = run_node_assembler(state)
        assert result["deliverables_ready"] is True
        delivs = {d["type"]: d for d in result["deliverables"]}

        assert delivs["OAR"]["signing_trustee_name"] == "Dr. John Doe, O.B.E."
        assert delivs["TAR"]["signing_trustee_name"] == "Dr. John Doe, O.B.E."
        assert delivs["TAR"]["chair_name"] == "Dr. John Doe, O.B.E."
        assert delivs["TAR"]["sections"]["reference_admin"]["chair_name"] == "Dr. John Doe, O.B.E."
        assert (
            "Dr. John Doe, O.B.E. (Chair), Secretary, Treasurer"
            in delivs["TAR"]["sections"]["reference_admin"]["current_trustees"]
        )
        assert (
            "Approved by the Board of Trustees and signed on their behalf by: Dr. John Doe, O.B.E., Chair."
            in delivs["TAR"]["sections"]["declaration"]
        )
        assert delivs["RP"]["signing_trustee_name"] == "Dr. John Doe, O.B.E."
        assert delivs["IE"]["signing_trustee_name"] == "Dr. John Doe, O.B.E."

        assert delivs["OAR"]["doc_ref"] == "SC054652-2026-OAR"
        assert delivs["TAR"]["doc_ref"] == "SC054652-2026-TAR"
        assert delivs["RP"]["doc_ref"] == "SC054652-2026-RPA"
        assert delivs["IE"]["doc_ref"] == "SC054652-2026-IEP"

        for d in result["deliverables"]:
            assert "content_hash" in d
            assert len(d["content_hash"]) == 64
            assert re.match(r"^[a-f0-9]{64}$", d["content_hash"])


class TestTemplateRenderingAssertions:
    """Stress-test template rendering across all 4 templates with regex assertions."""

    @pytest.fixture
    def full_context(self) -> dict[str, Any]:
        return {
            "charity_name": "Potter's House Christian Mission UK",
            "charity_number": "SC054652",
            "financial_year": "2026",
            "signing_trustee_name": "Dr. John Doe, O.B.E.",
            "signing_trustee_role": "Chair of the Board of Trustees",
            "approval_date": "31 December 2026",
            "doc_ref": "SC054652-2026-TAR",
            "signoff_status": "Approved & Certified by Trustees",
            "current_trustees": "Dr. John Doe, O.B.E. (Chair), Secretary, Treasurer",
            "gross_receipts_decimal": "145000.50",
            "gross_payments_decimal": "95000.25",
            "net_movement_decimal": "50000.25",
            "closing_balance_decimal": "125000.00",
            "governance_description": "SCIO governed in accordance with its Model Constitution adopted 2024.",
            "purposes_activities_narrative": "Advancement of the Christian religion and relief of hardship in Dunbar and East Lothian.",
            "achievements_connective_narrative": "Delivered 52 Sunday worship services, weekly youth ministries, and community food bank support.",
            "principal_risks_narrative": "The charity maintains 3 months of core operational reserves to mitigate income fluctuation.",
        }

    def _render(self, template_text: str, context: dict[str, Any]) -> str:
        rendered = template_text
        for k, v in context.items():
            rendered = rendered.replace(f"{{{{ {k} }}}}", str(v))
            rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
        return rendered

    def test_no_64_char_hex_strings_in_any_template(self, full_context):
        """Empirically assert NO 64-character hexadecimal strings appear anywhere in rendered templates."""
        hex_64_regex = re.compile(r"[a-f0-9]{64}", re.IGNORECASE)

        for filename in TEMPLATE_FILES:
            raw_html = (TEMPLATES_DIR / filename).read_text(encoding="utf-8")
            rendered = self._render(raw_html, full_context)

            matches = hex_64_regex.findall(rendered)
            assert not matches, f"Found 64-char hex strings in {filename}: {matches}"

    def test_no_beacon_compliance_vendor_strings_in_any_template(self, full_context):
        """Empirically assert NO 'Beacon Compliance' vendor strings appear anywhere in rendered templates."""
        vendor_regex = re.compile(r"Beacon\s*Compliance", re.IGNORECASE)

        for filename in TEMPLATE_FILES:
            raw_html = (TEMPLATES_DIR / filename).read_text(encoding="utf-8")
            rendered = self._render(raw_html, full_context)

            matches = vendor_regex.findall(rendered)
            assert not matches, f"Found vendor string '{matches}' in {filename}"

    def test_all_expected_fields_rendered_without_unrendered_tags(self, full_context):
        """Empirically verify all required fields render and zero unrendered double-curly brackets exist."""
        unrendered_tag_regex = re.compile(r"\{\{.*?\}\}")

        for filename in TEMPLATE_FILES:
            raw_html = (TEMPLATES_DIR / filename).read_text(encoding="utf-8")
            ctx = dict(full_context)
            if "oar" in filename:
                ctx["doc_ref"] = "SC054652-2026-OAR"
            elif "tar" in filename:
                ctx["doc_ref"] = "SC054652-2026-TAR"
            elif "rnp" in filename:
                ctx["doc_ref"] = "SC054652-2026-RPA"
            elif "ie_pack" in filename:
                ctx["doc_ref"] = "SC054652-2026-IEP"

            rendered = self._render(raw_html, ctx)

            unrendered = unrendered_tag_regex.findall(rendered)
            assert not unrendered, f"Unrendered tags found in {filename}: {unrendered}"

            assert "Dr. John Doe, O.B.E." in rendered
            assert "Chair of the Board of Trustees" in rendered
            assert "31 December 2026" in rendered
            assert ctx["doc_ref"] in rendered
            assert "SC054652" in rendered
            assert "Potter's House Christian Mission UK" in rendered
