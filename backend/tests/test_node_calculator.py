"""Unit tests for Node 3 R&P Calculator & Threshold Enforcement (backend/src/agents/node_calculator.py).

Verifies Red-Line 2 and Red-Line 5 (Income Threshold Hard-Halt at £250,000).
"""

from backend.src.agents.node_calculator import run_node_calculator
from backend.src.agents.state import BeaconComplianceState


def test_node_calculator_normal_run():
    """Verify Node 3 execution under standard charity income (£50k–£200k)."""
    state: BeaconComplianceState = {
        "run_id": "run_2026_test",
        "charity_number": "SC054652",
        "anonymised_payload": {
            "opening_balance_pence": 1000000,  # £10,000.00
            "closing_balance_pence": 1500000,  # £15,000.00
        },
        "classified_transactions": [
            {
                "txn_id": "T1",
                "run_id": "run_2026_test",
                "date": "2026-01-05",
                "description": "General Tithes",
                "amount_pence": 1000000,  # £10,000.00
                "fund": "unrestricted_general",
                "category": "Donations",
                "transaction_type": "receipt",
            },
            {
                "txn_id": "T2",
                "run_id": "run_2026_test",
                "date": "2026-01-10",
                "description": "Hall Rent",
                "amount_pence": 500000,  # £5,000.00
                "fund": "unrestricted_general",
                "category": "Premises",
                "transaction_type": "payment",
            },
        ],
    }

    result = run_node_calculator(state)

    assert result["income_threshold_breach"] is False
    assert result["receipts_payments"]["gross_receipts_pence"] == 1000000
    assert result["receipts_payments"]["gross_payments_pence"] == 500000
    assert result["receipts_payments"]["net_movement_pence"] == 500000
    assert result["statement_of_balances"]["reconciled"] is True


def test_node_calculator_red_line_5_income_threshold_breach():
    """Red-Line 5 Test: £250,000 gross income MUST set income_threshold_breach=True to halt R&P."""
    state: BeaconComplianceState = {
        "run_id": "run_2026_breach_test",
        "charity_number": "SC054652",
        "anonymised_payload": {
            "opening_balance_pence": 100000,
            "closing_balance_pence": 25100000,
        },
        "classified_transactions": [
            {
                "txn_id": "T_LARGE",
                "run_id": "run_2026_breach_test",
                "date": "2026-06-01",
                "description": "Large Capital Legacy",
                "amount_pence": 25000000,  # £250,000.00 exactly
                "fund": "unrestricted_general",
                "category": "Legacy",
                "transaction_type": "receipt",
            },
        ],
    }

    result = run_node_calculator(state)

    # Must flag threshold breach per Red-Line 5
    assert result["income_threshold_breach"] is True
    assert result["receipts_payments"]["gross_receipts_pence"] == 25000000
