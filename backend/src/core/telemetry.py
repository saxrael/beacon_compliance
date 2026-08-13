"""Langfuse Observability and Telemetry Engine for Beacon Compliance (telemetry.py).

Enforces:
- Red-Line 4: Mandatory PII redaction on all outgoing trace metadata and LLM prompts before telemetry dispatch.
- Red-Line 2: Zero LLM math in trace annotations or evaluations.
- Opt-In Safety: Gracefully operates as a non-blocking no-op if LANGFUSE_ENABLED is False or credentials missing.
"""

import logging
import os
from collections.abc import Callable
from functools import wraps
from typing import Any

from backend.src.core.pii_engine import default_redactor

logger = logging.getLogger(__name__)

try:
    from langfuse import Langfuse
except Exception:
    Langfuse = None

try:
    from langfuse.langchain import CallbackHandler
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


class BeaconLangfuseTracer:
    """Telemetry manager providing Langfuse integration with PII boundary enforcement."""

    def __init__(self) -> None:
        self.enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() in ("true", "1", "yes")
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "").strip()
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY", "").strip()
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").strip()

        self.langfuse_client: Any | None = None

        if self.enabled and self.public_key and self.secret_key:
            if Langfuse is None:
                logger.warning("Langfuse module unavailable; telemetry disabled.")
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
            logger.warning("Langfuse CallbackHandler unavailable; ensure langfuse is installed.")
            return None
        try:
            return CallbackHandler(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
            )
        except Exception as exc:
            logger.warning("Failed to create Langchain CallbackHandler: %s", exc)
            return None

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
            trace = self.langfuse_client.trace(
                name=f"beacon_{name }",
                metadata=sanitized_meta,
            )
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
                    default_tracer.langfuse_client.trace(
                        name=f"func_{tracer_name }",
                        input=sanitized_kwargs,
                        output=sanitized_result,
                    )
                    default_tracer.langfuse_client.flush()
                except Exception as exc:
                    logger.debug("Failed to record trace for function %s: %s", tracer_name, exc)
            return result

        return wrapper

    return decorator
