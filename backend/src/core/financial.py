"""Deterministic Financial Arithmetic Engine for Beacon Compliance.

Strictly enforces Red-Line 2 (Zero LLM Financial Arithmetic) and
Rule 2 of beacon-financial-boundary (Universal Decimal Monetary Representation).
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import NamedTuple

from pydantic import BaseModel, Field, field_validator


class MonetaryValue(NamedTuple):
    """Immutable monetary container carrying exact Decimal value and integer pence representation."""

    decimal_amount: Decimal
    pence_amount: int


def pence_to_decimal(pence: int) -> Decimal:
    """Convert integer pence to exact Decimal pounds with 2 decimal places.

    Example: 1250 pence -> Decimal('12.50')
    """
    if not isinstance(pence, int):
        raise TypeError(f"Pence amount must be an integer, got {type(pence).__name__}")
    return (Decimal(pence) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_to_pence(amount: Decimal | str | int) -> int:
    """Convert a Decimal/string/int monetary value to integer pence.

    Raises TypeError if float is passed to prevent binary rounding errors.
    """
    if isinstance(amount, float):
        raise TypeError(
            "Floating point monetary inputs are strictly prohibited by Red-Line 2. "
            "Use Decimal, str, or int pence instead."
        )

    try:
        dec = Decimal(str(amount)) if not isinstance(amount, Decimal) else amount
        pence_dec = (dec * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(pence_dec)
    except InvalidOperation as err:
        raise ValueError(f"Invalid monetary format: {amount}") from err


class TransactionRecord(BaseModel):
    """Pydantic model representing a monetary bank transaction with strict Decimal conversion."""

    txn_id: str
    run_id: str
    date: str
    description: str
    amount_pence: int = Field(..., description="Monetary value stored strictly as integer pence.")
    fund: str
    category: str
    transaction_type: str = Field(..., description="'receipt' or 'payment'")
    classification_tier: str = Field(
        "1", description="'1' (deterministic rule), '2' (human rule), '2.5' (suggested)"
    )
    classification_confidence: float = 1.0

    @field_validator("amount_pence")
    @classmethod
    def validate_amount_pence(cls, v: int) -> int:
        if not isinstance(v, int):
            raise TypeError("amount_pence must be an integer.")
        return v

    @property
    def amount_decimal(self) -> Decimal:
        """Returns exact Decimal value of the transaction."""
        return pence_to_decimal(self.amount_pence)


class FundSummary(BaseModel):
    """Fund-segregated receipts and payments summary."""

    fund_id: str
    fund_name: str
    total_receipts_pence: int = 0
    total_payments_pence: int = 0
    net_movement_pence: int = 0

    @property
    def total_receipts_decimal(self) -> Decimal:
        return pence_to_decimal(self.total_receipts_pence)

    @property
    def total_payments_decimal(self) -> Decimal:
        return pence_to_decimal(self.total_payments_pence)

    @property
    def net_movement_decimal(self) -> Decimal:
        return pence_to_decimal(self.net_movement_pence)


class RnPAccount(BaseModel):
    """Receipts & Payments Account for all charity funds."""

    run_id: str
    charity_number: str = "SC054652"
    fund_summaries: dict[str, FundSummary]
    gross_receipts_pence: int = 0
    gross_payments_pence: int = 0
    net_receipts_payments_pence: int = 0
    is_threshold_breached: bool = False


class StatementOfBalances(BaseModel):
    """Statement of Balances reconciling bank accounts."""

    run_id: str
    opening_balance_pence: int
    closing_balance_pence: int
    total_net_movement_pence: int
    reconciled: bool

    @property
    def opening_balance_decimal(self) -> Decimal:
        return pence_to_decimal(self.opening_balance_pence)

    @property
    def closing_balance_decimal(self) -> Decimal:
        return pence_to_decimal(self.closing_balance_pence)


def calculate_fund_totals(transactions: list[TransactionRecord]) -> dict[str, FundSummary]:
    """Deterministically aggregate receipts and payments by fund using integer pence arithmetic."""
    summaries: dict[str, FundSummary] = {}

    for txn in transactions:
        fund_id = txn.fund
        if fund_id not in summaries:
            summaries[fund_id] = FundSummary(
                fund_id=fund_id, fund_name=fund_id.replace("_", " ").title()
            )

        summary = summaries[fund_id]
        if txn.transaction_type == "receipt":
            summary.total_receipts_pence += txn.amount_pence
        elif txn.transaction_type == "payment":
            summary.total_payments_pence += txn.amount_pence
        else:
            raise ValueError(
                f"Unknown transaction_type '{txn.transaction_type}' in transaction {txn.txn_id}"
            )

        summary.net_movement_pence = summary.total_receipts_pence - summary.total_payments_pence

    return summaries


def check_income_threshold(gross_receipts_pence: int, threshold_pounds: int = 250000) -> bool:
    """Check if gross receipts reach or exceed the R&P threshold (£250,000).

    This deterministic check is enforced independently at ingest and validation (Red-Line 5).
    """
    threshold_pence = threshold_pounds * 100
    return gross_receipts_pence >= threshold_pence
