"""Unit tests for deterministic financial arithmetic engine (backend/src/core/financial.py).

Verifies Red-Line 2 and Rule 2 of beacon-financial-boundary.
"""

from decimal import Decimal

import pytest
from backend.src.core.financial import (
    TransactionRecord,
    calculate_fund_totals,
    check_income_threshold,
    decimal_to_pence,
    pence_to_decimal,
)


def test_pence_to_decimal_conversion():
    """Verify exact integer pence to Decimal pounds conversion."""
    assert pence_to_decimal(100) == Decimal("1.00")
    assert pence_to_decimal(1250) == Decimal("12.50")
    assert pence_to_decimal(0) == Decimal("0.00")
    assert pence_to_decimal(99) == Decimal("0.99")


def test_decimal_to_pence_conversion():
    """Verify Decimal to integer pence conversion."""
    assert decimal_to_pence(Decimal("1.00")) == 100
    assert decimal_to_pence(Decimal("12.50")) == 1250
    assert decimal_to_pence("12.50") == 1250
    assert decimal_to_pence(100) == 10000


def test_float_input_prohibition():
    """Red-Line 2 test: floats MUST be rejected to prevent binary floating-point rounding errors."""
    with pytest.raises(TypeError, match="Floating point monetary inputs are strictly prohibited"):
        decimal_to_pence(12.50)


def test_calculate_fund_totals():
    """Verify fund-segregated receipts and payments calculation."""
    txns = [
        TransactionRecord(
            txn_id="TXN1",
            run_id="RUN1",
            date="2026-01-10",
            description="Sunday Offering",
            amount_pence=50000,
            fund="unrestricted_general",
            category="Donations",
            transaction_type="receipt",
        ),
        TransactionRecord(
            txn_id="TXN2",
            run_id="RUN1",
            date="2026-01-12",
            description="Rent Payment",
            amount_pence=20000,
            fund="unrestricted_general",
            category="Premises",
            transaction_type="payment",
        ),
        TransactionRecord(
            txn_id="TXN3",
            run_id="RUN1",
            date="2026-01-15",
            description="Mission Support",
            amount_pence=30000,
            fund="restricted_mission",
            category="Missions",
            transaction_type="receipt",
        ),
    ]

    totals = calculate_fund_totals(txns)

    assert "unrestricted_general" in totals
    assert totals["unrestricted_general"].total_receipts_pence == 50000
    assert totals["unrestricted_general"].total_payments_pence == 20000
    assert totals["unrestricted_general"].net_movement_pence == 30000
    assert totals["unrestricted_general"].net_movement_decimal == Decimal("300.00")

    assert "restricted_mission" in totals
    assert totals["restricted_mission"].total_receipts_pence == 30000
    assert totals["restricted_mission"].total_payments_pence == 0
    assert totals["restricted_mission"].net_movement_pence == 30000


def test_income_threshold_check():
    """Verify gross income threshold boundary checks (£250,000 limit)."""
    assert not check_income_threshold(24999999, threshold_pounds=250000)
    assert check_income_threshold(25000000, threshold_pounds=250000)
    assert check_income_threshold(25000001, threshold_pounds=250000)
