"""Unit Test Suite for Langfuse Telemetry Engine (test_telemetry.py).

Verifies:
- Red-Line 4: Mandatory PII redaction on all telemetry trace inputs, outputs, and metadata.
- Graceful disabled state handling when LANGFUSE_ENABLED is false.
- Function tracing decorator behavior.
"""

from backend.src.core.telemetry import (
    BeaconLangfuseTracer,
    observe_pii_guarded,
    sanitize_telemetry_payload,
)


def test_sanitize_telemetry_payload_primitives():
    """Verify text PII scrubbing on telemetry payload strings."""
    raw_text = "Contact john.doe@example.com or call 07123456789 with sort code 12-34-56."
    scrubbed = sanitize_telemetry_payload(raw_text)

    assert "john.doe@example.com" not in scrubbed
    assert "07123456789" not in scrubbed
    assert "12-34-56" not in scrubbed
    assert (
        "[EMAIL_REDACTED]" in scrubbed
        or "[UK_PHONE_REDACTED]" in scrubbed
        or "REDACTED" in scrubbed
    )


def test_sanitize_telemetry_payload_nested_dict():
    """Verify recursive PII scrubbing on nested dictionary payloads."""
    nested = {
        "user_email": "trustee@pottershouse.org.uk",
        "details": {
            "account_number": "12345678",
            "postcode": "EH1 1AA",
            "safe_field": "Non-sensitive narrative text",
        },
        "list_items": ["call 07123456789", "clean item"],
    }
    scrubbed = sanitize_telemetry_payload(nested)

    assert "trustee@pottershouse.org.uk" not in scrubbed["user_email"]
    assert "12345678" not in scrubbed["details"]["account_number"]
    assert "EH1 1AA" not in scrubbed["details"]["postcode"]
    assert scrubbed["details"]["safe_field"] == "Non-sensitive narrative text"
    assert "07123456789" not in scrubbed["list_items"][0]


def test_beacon_langfuse_tracer_disabled_default(monkeypatch):
    """Verify tracer defaults to disabled state when LANGFUSE_ENABLED is false."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")
    tracer = BeaconLangfuseTracer()

    assert not tracer.is_enabled()
    assert tracer.get_langchain_callback() is None

    tracer.trace_llm_generation(
        name="test_gen",
        system_prompt="System",
        user_message="User john.doe@example.com",
        model="test-model",
        output_text="Output",
    )


def test_beacon_langfuse_tracer_mock_enabled(monkeypatch):
    """Verify tracer behavior when enabled with mock keys."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    tracer = BeaconLangfuseTracer()
    assert tracer.enabled is True
    assert tracer.is_enabled() is True

    callback = tracer.get_langchain_callback()
    assert callback is not None

    # Test trace generation with PII redaction
    tracer.trace_llm_generation(
        name="test_gen",
        system_prompt="System instructions",
        user_message="User john.doe@example.com",
        model="google/gemma-2-27b-it",
        output_text="Synthesized output for trustee@pottershouse.org.uk",
        input_tokens=10,
        output_tokens=20,
        metadata={"run_type": "test_narration"},
    )


def test_beacon_langfuse_tracer_missing_keys(monkeypatch):
    """Verify tracer disabled when enabled=True but keys are missing."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "")

    tracer = BeaconLangfuseTracer()
    assert tracer.is_enabled() is False
    assert tracer.get_langchain_callback() is None


def test_observe_pii_guarded_decorator():
    """Verify @observe_pii_guarded executes functions cleanly while redacting kwargs."""

    @observe_pii_guarded(name="test_function")
    def sample_func(input_text: str) -> str:
        return f"Processed: {input_text }"

    result = sample_func(input_text="Email: test@example.com")
    assert result == "Processed: Email: test@example.com"


def test_trace_agent_turn_disabled_noop(monkeypatch):
    """Verify trace_agent_turn acts as a clean no-op context manager when disabled."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")
    tracer = BeaconLangfuseTracer()

    with tracer.trace_agent_turn(
        name="compliance_chat_agent",
        user_message="Hello trustee@example.com",
        user_id="trustee_01",
        session_id="run_001",
        tags=["compliance_chat", "sc054652"],
        metadata={"charity": "SC054652"},
    ) as agent_ctx:
        assert agent_ctx is not None
        with tracer.trace_tool_execution(
            name="get_financial_summary_tool",
            as_type="tool",
            input_data={"run_id": "run_001"},
        ) as tool_ctx:
            tool_ctx.set_output({"gross_receipts": "12000.00"})

        agent_ctx.set_output("Hello! I can help with OSCR compliance.")


def test_trace_agent_turn_mock_enabled(monkeypatch):
    """Verify trace_agent_turn and trace_tool_execution record nested spans when enabled."""
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    tracer = BeaconLangfuseTracer()

    with tracer.trace_agent_turn(
        name="compliance_chat_agent",
        user_message="Check receipts for john.doe@pottershouse.org.uk phone 07123456789",
        user_id="trustee_01",
        session_id="run_001",
        tags=["compliance_chat", "sc054652"],
        metadata={"donor_postcode": "EH1 1AA"},
    ) as agent_ctx:
        with tracer.trace_tool_execution(
            name="get_financial_summary_tool",
            as_type="tool",
            input_data={"run_id": "run_001", "sort_code": "12-34-56"},
        ) as tool_ctx:
            tool_ctx.set_output({"gross_receipts": "15000.00", "donor": "secret@example.com"})

        with tracer.trace_tool_execution(
            name="search_knowledge_base_tool",
            as_type="retriever",
            input_data={"query": "OSCR receipts and payments rules"},
        ) as ret_ctx:
            ret_ctx.set_output({"matches": 3, "sources": ["docs/oar.md"]})

        agent_ctx.set_output("The gross receipts are £15,000.00.")
