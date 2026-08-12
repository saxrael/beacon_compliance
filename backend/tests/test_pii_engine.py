"""Unit tests for PII Redaction Engine (backend/src/core/pii_engine.py).

Verifies Red-Line 4 PII scrubbing requirements.
"""

from backend.src.core.pii_engine import PIIRedactor, anonymise_transaction_description


def test_email_and_phone_redaction():
    redactor = PIIRedactor()
    raw = "Donation from john.doe@example.com call 07123456789"
    redacted, audit = redactor.redact_text(raw)

    assert "john.doe@example.com" not in redacted
    assert "07123456789" not in redacted
    assert "[EMAIL_REDACTED]" in redacted or "EMAIL" in audit.entities_detected
    assert "[UK_PHONE_REDACTED]" in redacted or "UK_PHONE" in audit.entities_detected


def test_sort_code_and_account_number_redaction():
    raw = "Transfer to sort code 12-34-56 account 87654321"
    redacted = anonymise_transaction_description(raw)

    assert "12-34-56" not in redacted
    assert "87654321" not in redacted
    assert "REDACTED" in redacted


def test_postcode_redaction():
    raw = "Rent payment Beachmont Court Dunbar EH42 1AB"
    redacted = anonymise_transaction_description(raw)

    assert "EH42 1AB" not in redacted
    assert "REDACTED" in redacted
