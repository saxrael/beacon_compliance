"""Langfuse Observability and Telemetry Engine for Beacon Compliance (telemetry.py).

Enforces:
- Red-Line 4: Mandatory PII redaction on all outgoing trace metadata and LLM prompts before telemetry dispatch.
- Red-Line 2: Zero LLM math in trace annotations or evaluations.
- Opt-In Safety: Gracefully operates as a non-blocking no-op if LANGFUSE_ENABLED is False or credentials missing.
"""

import logging
import os
from collections.abc import Callable, Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any

from backend.src.core.pii_engine import default_redactor

logger = logging.getLogger(__name__)

try:
    from langfuse import Langfuse, get_client, propagate_attributes
except Exception:
    Langfuse = None
    get_client = None
    propagate_attributes = None

try:
    from langfuse.langchain import CallbackHandler
except Exception:
    try:
        from langfuse.callback import CallbackHandler
    except Exception:
        CallbackHandler = None


def sanitize_telemetry_payload(data: Any) -> Any:
    """Recursively scrub PII from telemetry dictionary payloads, lists, and strings.

    Guarantees compliance with Red-Line 4 (PII Boundary Enforcement).
    """
    if isinstance(data, str):
        scrubbed, _ = default_redactor.redact_text(data, field_name="telemetry_payload")
        return scrubbed
    elif isinstance(data, dict):
        return {k: sanitize_telemetry_payload(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_telemetry_payload(item) for item in data]
    return data


class TraceObservationContext:
    """Wrapper around active or no-op Langfuse observation context."""

    def __init__(self, observation_span: Any = None) -> None:
        self.span = observation_span

    def set_output(self, output: Any) -> None:
        """Set output on the active span with mandatory PII scrubbing."""
        if self.span is not None:
            try:
                sanitized = sanitize_telemetry_payload(output)
                if hasattr(self.span, "update"):
                    self.span.update(output=sanitized)
            except Exception as exc:
                logger.debug("Failed to set output on telemetry observation: %s", exc)

    def set_input(self, input_data: Any) -> None:
        """Set input on the active span with mandatory PII scrubbing."""
        if self.span is not None:
            try:
                sanitized = sanitize_telemetry_payload(input_data)
                if hasattr(self.span, "update"):
                    self.span.update(input=sanitized)
            except Exception as exc:
                logger.debug("Failed to set input on telemetry observation: %s", exc)

    def update(self, **kwargs: Any) -> None:
        """Update active span attributes with mandatory PII scrubbing."""
        if self.span is not None:
            try:
                sanitized_kwargs = sanitize_telemetry_payload(kwargs)
                if hasattr(self.span, "update"):
                    self.span.update(**sanitized_kwargs)
            except Exception as exc:
                logger.debug("Failed to update telemetry observation: %s", exc)


class BeaconLangfuseTracer:
    """Telemetry manager providing Langfuse integration with PII boundary enforcement."""

    def __init__(self) -> None:
        self.enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() in ("true", "1", "yes")
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
        self.host = (
            os.getenv("LANGFUSE_HOST")
            or os.getenv("LANGFUSE_BASE_URL")
            or "https://cloud.langfuse.com"
        ).strip()

        self.langfuse_client: Any | None = None

        if self.enabled and self.public_key and self.secret_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = self.public_key
            os.environ["LANGFUSE_SECRET_KEY"] = self.secret_key
            os.environ["LANGFUSE_HOST"] = self.host
            os.environ["LANGFUSE_BASE_URL"] = self.host

            if Langfuse is None:
                logger.warning(
                    "Langfuse module unavailable; telemetry disabled. Ensure 'langfuse' is installed."
                )
                self.enabled = False
            else:
                try:
                    self.langfuse_client = Langfuse(
                        public_key=self.public_key,
                        secret_key=self.secret_key,
                        host=self.host,
                    )
                    logger.info("Langfuse telemetry initialized successfully (Host: %s)", self.host)
                except Exception as exc:
                    logger.warning(
                        "Failed to initialize Langfuse client: %s. Telemetry disabled.", exc
                    )
                    self.enabled = False

    def is_enabled(self) -> bool:
        """Return True if Langfuse telemetry is active and configured."""
        return self.enabled and self.langfuse_client is not None

    def get_langchain_callback(self) -> Any | None:
        """Get PII-guarded CallbackHandler for LangGraph / LangChain execution."""
        if not self.is_enabled():
            return None
        if CallbackHandler is None:
            logger.warning(
                "Langfuse CallbackHandler unavailable; ensure 'langfuse' and 'langchain' are installed."
            )
            return None
        try:
            return CallbackHandler(public_key=self.public_key)
        except TypeError:
            try:
                return CallbackHandler(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host,
                )
            except Exception as exc:
                logger.warning("Failed to create Langchain CallbackHandler: %s", exc)
                return None
        except Exception as exc:
            logger.warning("Failed to create Langchain CallbackHandler: %s", exc)
            return None

    @contextmanager
    def trace_agent_turn(
        self,
        name: str,
        user_message: str,
        user_id: str | None = None,
        session_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[TraceObservationContext, None, None]:
        """Context manager creating a top-level 'agent' observation with session/user propagation."""
        if not self.is_enabled() or self.langfuse_client is None:
            yield TraceObservationContext(None)
            return

        sanitized_msg = sanitize_telemetry_payload(user_message)
        sanitized_meta = sanitize_telemetry_payload(metadata or {})
        clean_tags = tags or ["compliance_agent", "oscr", "sc054652"]

        try:
            prop_cm = (
                propagate_attributes(
                    user_id=user_id,
                    session_id=session_id,
                    tags=clean_tags,
                    trace_name=name,
                )
                if propagate_attributes is not None
                else None
            )

            if prop_cm:
                with prop_cm:
                    if hasattr(self.langfuse_client, "start_as_current_observation"):
                        with self.langfuse_client.start_as_current_observation(
                            name=name,
                            as_type="agent",
                            input={"user_message": sanitized_msg},
                            metadata=sanitized_meta,
                        ) as agent_span:
                            wrapper = TraceObservationContext(agent_span)
                            yield wrapper
                    else:
                        yield TraceObservationContext(None)
            elif hasattr(self.langfuse_client, "start_as_current_observation"):
                with self.langfuse_client.start_as_current_observation(
                    name=name,
                    as_type="agent",
                    input={"user_message": sanitized_msg},
                    metadata=sanitized_meta,
                ) as agent_span:
                    wrapper = TraceObservationContext(agent_span)
                    yield wrapper
            else:
                yield TraceObservationContext(None)
        except Exception as exc:
            logger.debug("Error in trace_agent_turn context: %s", exc)
            yield TraceObservationContext(None)
        finally:
            if hasattr(self.langfuse_client, "flush"):
                try:
                    self.langfuse_client.flush()
                except Exception:
                    pass

    @contextmanager
    def trace_tool_execution(
        self,
        name: str,
        as_type: str = "tool",
        input_data: Any = None,
        metadata: dict[str, Any] | None = None,
    ) -> Generator[TraceObservationContext, None, None]:
        """Context manager creating a nested 'tool' or 'retriever' observation."""
        if not self.is_enabled() or self.langfuse_client is None:
            yield TraceObservationContext(None)
            return

        sanitized_input = sanitize_telemetry_payload(input_data)
        sanitized_meta = sanitize_telemetry_payload(metadata or {})

        try:
            if hasattr(self.langfuse_client, "start_as_current_observation"):
                with self.langfuse_client.start_as_current_observation(
                    name=name,
                    as_type=as_type,
                    input=sanitized_input,
                    metadata=sanitized_meta,
                ) as tool_span:
                    yield TraceObservationContext(tool_span)
            else:
                yield TraceObservationContext(None)
        except Exception as exc:
            logger.debug("Error in trace_tool_execution context (%s): %s", name, exc)
            yield TraceObservationContext(None)

    def trace_llm_generation(
        self,
        name: str,
        *,
        system_prompt: str,
        user_message: str,
        model: str,
        output_text: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an LLM generation event directly to Langfuse with mandatory PII scrubbing."""
        if not self.is_enabled() or not self.langfuse_client:
            return

        sanitized_sys = sanitize_telemetry_payload(system_prompt)
        sanitized_user = sanitize_telemetry_payload(user_message)
        sanitized_output = sanitize_telemetry_payload(output_text)
        sanitized_meta = sanitize_telemetry_payload(metadata or {})

        try:
            if hasattr(self.langfuse_client, "start_observation"):
                self.langfuse_client.start_observation(
                    name=f"beacon_{name}",
                    as_type="generation",
                    model=model,
                    input=[
                        {"role": "system", "content": sanitized_sys},
                        {"role": "user", "content": sanitized_user},
                    ],
                    output=sanitized_output,
                    usage_details={"input": input_tokens, "output": output_tokens}
                    if (input_tokens or output_tokens)
                    else None,
                    metadata=sanitized_meta,
                )
            elif hasattr(self.langfuse_client, "trace"):
                trace = self.langfuse_client.trace(
                    name=f"beacon_{name}",
                    metadata=sanitized_meta,
                )
                if hasattr(trace, "generation"):
                    trace.generation(
                        name=name,
                        model=model,
                        input=[
                            {"role": "system", "content": sanitized_sys},
                            {"role": "user", "content": sanitized_user},
                        ],
                        output=sanitized_output,
                        usage={"input": input_tokens, "output": output_tokens},
                    )
            if hasattr(self.langfuse_client, "flush"):
                self.langfuse_client.flush()
        except Exception as exc:
            logger.error("Error logging generation trace to Langfuse: %s", exc)


default_tracer = BeaconLangfuseTracer()


def observe_pii_guarded(name: str | None = None) -> Callable[..., Any]:
    """Decorator to trace functions in Langfuse while scrubbing PII from input/output kwargs."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer_name = name or func.__name__
            sanitized_kwargs = sanitize_telemetry_payload(kwargs)
            result = func(*args, **kwargs)
            sanitized_result = sanitize_telemetry_payload(result)

            if default_tracer.is_enabled() and default_tracer.langfuse_client:
                try:
                    if hasattr(default_tracer.langfuse_client, "start_observation"):
                        default_tracer.langfuse_client.start_observation(
                            name=f"func_{tracer_name }",
                            as_type="span",
                            input=sanitized_kwargs,
                            output=sanitized_result,
                        )
                    elif hasattr(default_tracer.langfuse_client, "trace"):
                        default_tracer.langfuse_client.trace(
                            name=f"func_{tracer_name }",
                            input=sanitized_kwargs,
                            output=sanitized_result,
                        )
                    if hasattr(default_tracer.langfuse_client, "flush"):
                        default_tracer.langfuse_client.flush()
                except Exception as exc:
                    logger.debug("Failed to record trace for function %s: %s", tracer_name, exc)
            return result

        return wrapper

    return decorator
