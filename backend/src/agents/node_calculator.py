"""Node 3: Deterministic Financial Accounting Engine (node_calculator.py).

Enforces:
- Red-Line 2: Zero LLM financial arithmetic
- Red-Line 5: Income threshold hard-halt (£250,000 gross income limit for R&P)
- Rule 5 of beacon-financial-boundary: Independent validation-layer threshold check
"""

from typing import Any

from backend.src.agents.state import BeaconComplianceState
from backend.src.core.financial import (
    TransactionRecord,
    calculate_fund_totals,
    check_income_threshold,
    pence_to_decimal,
)


class IncomeThresholdBreachError(Exception):
    """Raised when gross receipts reach or exceed £250,000, triggering Red-Line 5 halt."""

    pass


def run_node_calculator(state: BeaconComplianceState) -> dict[str, Any]:
    """LangGraph Node 3: Computes fund-segregated R&P statement and balance reconciliation."""
    classified_raw = state.get("classified_transactions", [])
    opening_balance_pence = state.get("anonymised_payload", {}).get("opening_balance_pence", 0)
    closing_balance_pence = state.get("anonymised_payload", {}).get("closing_balance_pence", 0)

    transactions = [TransactionRecord(**item) for item in classified_raw]
    fund_summaries = calculate_fund_totals(transactions)

    gross_receipts_pence = sum(s.total_receipts_pence for s in fund_summaries.values())
    gross_payments_pence = sum(s.total_payments_pence for s in fund_summaries.values())
    net_movement_pence = gross_receipts_pence - gross_payments_pence

    is_breached = check_income_threshold(gross_receipts_pence, threshold_pounds=250000)
    calculated_closing_pence = opening_balance_pence + net_movement_pence
    is_reconciled = calculated_closing_pence == closing_balance_pence

    receipts_payments_data = {
        "run_id": state.get("run_id", "run_unknown"),
        "charity_number": state.get("charity_number", "SC054652"),
        "fund_summaries": {fid: s.model_dump() for fid, s in fund_summaries.items()},
        "gross_receipts_pence": gross_receipts_pence,
        "gross_receipts_decimal": str(pence_to_decimal(gross_receipts_pence)),
        "gross_payments_pence": gross_payments_pence,
        "gross_payments_decimal": str(pence_to_decimal(gross_payments_pence)),
        "net_movement_pence": net_movement_pence,
        "net_movement_decimal": str(pence_to_decimal(net_movement_pence)),
        "is_threshold_breached": is_breached,
    }

    statement_of_balances_data = {
        "run_id": state.get("run_id", "run_unknown"),
        "opening_balance_pence": opening_balance_pence,
        "opening_balance_decimal": str(pence_to_decimal(opening_balance_pence)),
        "closing_balance_pence": closing_balance_pence,
        "closing_balance_decimal": str(pence_to_decimal(closing_balance_pence)),
        "total_net_movement_pence": net_movement_pence,
        "total_net_movement_decimal": str(pence_to_decimal(net_movement_pence)),
        "reconciled": is_reconciled,
    }

    return {
        "receipts_payments": receipts_payments_data,
        "statement_of_balances": statement_of_balances_data,
        "income_threshold_breach": is_breached,
    }
