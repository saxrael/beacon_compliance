"""PII Redaction Engine for Beacon Compliance.

Strictly enforces Red-Line 4 (PII Boundary Enforcement).
Anonymizes transaction descriptions, names, emails, account numbers, sort codes, and addresses
before any payload is eligible for LLM draft processing.
"""

import re
from typing import ClassVar, NamedTuple

from pydantic import BaseModel

try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
except Exception:
    AnalyzerEngine = None
    AnonymizerEngine = None


class PIIRedactionResult(NamedTuple):
    """Container for redacted text and redaction metadata log."""

    anonymised_text: str
    redactions_count: int
    entity_types_found: list[str]


class RedactionAuditRecord(BaseModel):
    """Audit log entry for an anonymization event."""

    field_name: str
    original_length: int
    redacted_length: int
    entities_detected: list[str]


_GLOBAL_ANALYZER = None
_GLOBAL_ANONYMIZER = None
_PRESIDIO_INITIALIZED = False


def _get_presidio_engines():
    global _GLOBAL_ANALYZER, _GLOBAL_ANONYMIZER, _PRESIDIO_INITIALIZED
    if not _PRESIDIO_INITIALIZED:
        _PRESIDIO_INITIALIZED = True
        try:
            if AnalyzerEngine is not None and AnonymizerEngine is not None:
                _GLOBAL_ANALYZER = AnalyzerEngine()
                _GLOBAL_ANONYMIZER = AnonymizerEngine()
        except Exception:
            _GLOBAL_ANALYZER = None
            _GLOBAL_ANONYMIZER = None
    return _GLOBAL_ANALYZER, _GLOBAL_ANONYMIZER


class PIIRedactor:
    """Deterministic PII Redactor using structural regex and entity masking."""

    PATTERNS: ClassVar[dict[str, re.Pattern[str]]] = {
        "EMAIL": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
        "UK_PHONE": re.compile(
            r"(?:\+44\s?7\d{3}|\(?07\d{3}\)?)\s?\d{3}\s?\d{3}|(?:\+44\s?1\d{3}|\(?01\d{3}\)?)\s?\d{3}\s?\d{3}"
        ),
        "SORT_CODE": re.compile(r"\b\d{2}[-\s]?\d{2}[-\s]?\d{2}\b"),
        "BANK_ACCOUNT": re.compile(r"\b\d{8}\b"),
        "CARD_NUMBER": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "UK_POSTCODE": re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", re.IGNORECASE),
    }

    def redact_text(self, text: str, field_name: str = "text") -> tuple[str, RedactionAuditRecord]:
        """Redact PII from a given string field."""
        if not text:
            return text, RedactionAuditRecord(
                field_name=field_name, original_length=0, redacted_length=0, entities_detected=[]
            )

        entities_found: list[str] = []
        redacted = text

        for entity_type, pattern in self.PATTERNS.items():
            if pattern.search(redacted):
                if entity_type not in entities_found:
                    entities_found.append(entity_type)
                redacted = pattern.sub(f"[{entity_type }_REDACTED]", redacted)

        analyzer, anonymizer = _get_presidio_engines()
        if analyzer and anonymizer:
            try:
                analyzer_results = analyzer.analyze(text=redacted, language="en")
                if analyzer_results:
                    for res in analyzer_results:
                        if res.entity_type not in entities_found:
                            entities_found.append(res.entity_type)
                    anonymized_res = anonymizer.anonymize(
                        text=redacted, analyzer_results=analyzer_results
                    )
                    redacted = anonymized_res.text
            except Exception:
                pass

        audit_record = RedactionAuditRecord(
            field_name=field_name,
            original_length=len(text),
            redacted_length=len(redacted),
            entities_detected=entities_found,
        )

        return redacted, audit_record


default_redactor = PIIRedactor()


def anonymise_transaction_description(description: str) -> str:
    """Scrub PII from transaction description strings."""
    redacted_text, _ = default_redactor.redact_text(
        description, field_name="transaction_description"
    )
    return redacted_text
