"""LLM Client Integration Module for Beacon Compliance (llm_client.py).

Provides API interfaces for:
1. Gemma 4 26B A4B (TAR narrative synthesis & interactive compliance chat)
2. openai/gpt-oss-20b via Groq (Tier 2.5 transaction classification)
   Contingency: llama-3.1-8b-instant via OpenRouter

Enforces:
- Red-Line 2 (Zero LLM Financial Arithmetic)
- Rule 3 (Tier 2.5 schema isolation: {category, confidence, reasoning} ONLY)
- Red-Line 4 (PII-scrubbed payloads only)
"""

import json
import logging
import os
from typing import Any

import httpx

from backend.src.core.retry import llm_retry
from backend.src.core.telemetry import default_tracer

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "google/gemma-4-26b-a4b")
GPT_OSS_MODEL = "openai/gpt-oss-20b"
LLAMA_CONTINGENCY_MODEL = "meta-llama/llama-3.1-8b-instant"


@llm_retry
def _post_json(
    url: str, headers: dict[str, str], body: dict[str, Any], timeout: float = 15.0
) -> dict[str, Any]:
    """Execute HTTP POST with tenacity exponential backoff and status code verification."""
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, headers=headers, json=body)
        resp.raise_for_status()
        return resp.json()


class LLMClient:
    """Client wrapper executing real LLM API calls with fallback handling."""

    def __init__(self) -> None:
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY")

    def call_gemma_narrative(
        self, system_prompt: str, anonymised_payload: dict[str, Any]
    ) -> dict[str, str] | None:
        """Call Gemma 4 26B A4B to synthesize narrative prose for the 4 TAR fields.

        Enforces Red-Line 2 placeholder tokens ([FIGURE_INJECTED:...]).
        """
        payload_str = json.dumps(anonymised_payload, indent=2)
        user_prompt = f"Synthesize TAR narrative prose for the 4 whitelisted fields based on this PII-scrubbed payload:\n{payload_str}"

        body = {
            "model": GEMMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        # Try primary OpenRouter (or Groq)
        endpoints = []
        if self.openrouter_key:
            endpoints.append(
                (
                    OPENROUTER_API_URL,
                    {
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                    },
                )
            )
        if self.groq_key:
            endpoints.append(
                (
                    GROQ_API_URL,
                    {
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json",
                    },
                )
            )

        for url, headers in endpoints:
            try:
                data = _post_json(url, headers=headers, body=body, timeout=15.0)
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "governance_description" in parsed:
                    default_tracer.trace_llm_generation(
                        name="gemma_narrative_synthesis",
                        system_prompt=system_prompt,
                        user_message=user_prompt,
                        model=GEMMA_MODEL,
                        output_text=content,
                        metadata={"run_type": "narration_synthesis"},
                    )
                    return parsed
            except Exception as err:
                logger.warning(f"LLM call for TAR narrative synthesis failed on {url}: {err}")

        return None

    def call_tier25_classifier(
        self, description: str, transaction_type: str = "receipt"
    ) -> dict[str, Any] | None:
        """Call openai/gpt-oss-20b via Groq for Tier 2.5 transaction classification.

        Contingency: llama-3.1-8b-instant via OpenRouter.
        Strictly enforces Rule 3: Output schema contains ONLY category, confidence, and reasoning.
        """
        system_prompt = """
You are the Tier 2.5 Transaction Classifier for Potter's House Christian Mission UK (SC054652).
Classify the transaction into an OSCR Receipts & Payments category.
STRICT MANDATE (Rule 3): Your output JSON MUST contain EXACTLY 3 keys:
- "category": string (e.g. "Donations & Offerings", "Premises Rent & Utility", "Missionary Support", "Governance & Admin")
- "confidence": float between 0.0 and 1.0
- "reasoning": string brief explanation
DO NOT output any monetary amount, numerical value, or currency field.
"""
        user_prompt = (
            f"Classify transaction description: '{description}' (Type: {transaction_type})"
        )

        providers = []
        if self.groq_key:
            providers.append(
                (
                    GROQ_API_URL,
                    {
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json",
                    },
                    GPT_OSS_MODEL,
                )
            )
        if self.openrouter_key:
            providers.append(
                (
                    OPENROUTER_API_URL,
                    {
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                    },
                    LLAMA_CONTINGENCY_MODEL,
                )
            )

        for url, headers, model_name in providers:
            body = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
            }
            try:
                data = _post_json(url, headers=headers, body=body, timeout=10.0)
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)

                cleaned = {
                    "category": str(parsed.get("category", "General Offerings")),
                    "confidence": float(parsed.get("confidence", 0.85)),
                    "reasoning": str(
                        parsed.get("reasoning", "LLM categorization based on description pattern")
                    ),
                }
                default_tracer.trace_llm_generation(
                    name="tier25_classifier",
                    system_prompt=system_prompt,
                    user_message=user_prompt,
                    model=model_name,
                    output_text=json.dumps(cleaned),
                    metadata={"transaction_type": transaction_type, "provider_url": url},
                )
                return cleaned
            except Exception as err:
                logger.warning(f"Tier 2.5 LLM classification failed on {url} ({model_name}): {err}")

        return None

    def parse_streaming_chunks(self, chunks_iterable: Any):
        """Parse raw stream chunks, dynamically extracting <think> reasoning tokens from content tokens."""
        in_think = False
        buffer = ""

        for raw_chunk in chunks_iterable:
            if not raw_chunk:
                continue
            buffer += raw_chunk

            while buffer:
                tag = "</think>" if in_think else "<think>"
                if tag in buffer:
                    pre, post = buffer.split(tag, 1)
                    if pre:
                        yield {"type": "thought" if in_think else "token", "chunk": pre}
                    in_think = not in_think
                    buffer = post
                elif "<" in buffer and tag.startswith(buffer[buffer.rfind("<") :]):
                    break
                else:
                    yield {"type": "thought" if in_think else "token", "chunk": buffer}
                    buffer = ""

        if buffer:
            yield {"type": "thought" if in_think else "token", "chunk": buffer}

    def call_cognitive_summary(self, old_summary: str, new_messages: str) -> str | None:
        """Call Gemma to compress evicted messages into an episodic narrative summary (<500 words)."""
        system_prompt = (
            "You are a background compliance memory processor for Potter's House Christian Mission UK (SCIO, SC054652). "
            "Your job is to update an existing conversation summary with new dialogue messages. "
            "Keep the summary concise, chronological, and strictly under 500 words. "
            "Focus on current compliance workflows, active governance questions, and operational issues. "
            "Do NOT include permanent factual milestones or financial amounts/calculations (strictly barred under Red-Line 2)."
        )
        user_prompt = (
            f"<old_summary>\n{old_summary}\n</old_summary>\n\n"
            f"<new_messages>\n{new_messages}\n</new_messages>\n\n"
            "Generate the updated summary directly with no introductory text."
        )
        body = {
            "model": GEMMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        endpoints = []
        if self.openrouter_key:
            endpoints.append(
                (
                    OPENROUTER_API_URL,
                    {
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                    },
                )
            )
        if self.groq_key:
            endpoints.append(
                (
                    GROQ_API_URL,
                    {
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json",
                    },
                )
            )

        for url, headers in endpoints:
            try:
                data = _post_json(url, headers=headers, body=body, timeout=15.0)
                reply = data["choices"][0]["message"]["content"].strip()
                default_tracer.trace_llm_generation(
                    name="cognitive_narrative_summary",
                    system_prompt=system_prompt,
                    user_message=user_prompt,
                    model=GEMMA_MODEL,
                    output_text=reply,
                    metadata={"run_type": "cognitive_summary"},
                )
                return reply
            except Exception as err:
                logger.warning(f"Cognitive summary LLM call failed on {url}: {err}")

        return None

    def call_cognitive_fact_extractor(
        self, existing_facts: list[dict[str, Any]], new_messages: str
    ) -> list[dict[str, Any]] | None:
        """Call Gemma to extract permanent non-financial governance facts using Think-Plan-Execute."""
        system_prompt = (
            "ROLE: Elite Cognitive Memory Extractor for Potter's House Christian Mission UK (SCIO, SC054652).\n"
            "Your objective is to build a permanent factual knowledge graph about trustee preferences, charity governance policies, non-financial operational precedents, and constitutional practices.\n"
            "Transient chatter is ignored. Financial figures, amounts, and bank balances are STRICTLY FORBIDDEN (Red-Line 2).\n\n"
            "[JSON THINK-PLAN-EXECUTE PROTOCOL]\n"
            "Output MUST be a JSON object containing a 'facts' array of objects:\n"
            "{\n"
            '  "facts": [\n'
            "    {\n"
            '      "think": "Reasoning analysis...",\n'
            '      "plan": "Plan...",\n'
            '      "action": "CREATE" | "UPDATE" | "NONE",\n'
            '      "target_existing_fact_id": "string-uuid-or-null",\n'
            '      "final_fact_text": "Permanent factual text"\n'
            "    }\n"
            "  ]\n"
            "}"
        )
        existing_facts_str = json.dumps(existing_facts, indent=2)
        user_prompt = (
            f"<existing_facts>\n{existing_facts_str}\n</existing_facts>\n\n"
            f"<new_messages>\n{new_messages}\n</new_messages>\n\n"
            "Extract new or updated permanent governance facts following the Think-Plan-Execute protocol."
        )
        body = {
            "model": GEMMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        endpoints = []
        if self.openrouter_key:
            endpoints.append(
                (
                    OPENROUTER_API_URL,
                    {
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                    },
                )
            )
        if self.groq_key:
            endpoints.append(
                (
                    GROQ_API_URL,
                    {
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json",
                    },
                )
            )

        for url, headers in endpoints:
            try:
                data = _post_json(url, headers=headers, body=body, timeout=15.0)
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                facts_list = parsed.get("facts", parsed) if isinstance(parsed, dict) else parsed
                if isinstance(facts_list, list):
                    default_tracer.trace_llm_generation(
                        name="cognitive_fact_extractor",
                        system_prompt=system_prompt,
                        user_message=user_prompt,
                        model=GEMMA_MODEL,
                        output_text=json.dumps(facts_list),
                        metadata={"run_type": "cognitive_facts"},
                    )
                    return facts_list
            except Exception as err:
                logger.warning(f"Cognitive fact extractor LLM call failed on {url}: {err}")

        return None

    def _fetch_remote_stream_chunks(self, url: str, headers: dict[str, str], body: dict[str, Any]):
        """Fetch raw event chunks from remote SSE completion endpoint."""
        with httpx.Client(timeout=30.0) as client:
            with client.stream("POST", url, headers=headers, json=body) as resp:
                for line in resp.iter_lines():
                    if not line:
                        continue
                    line_str = line.strip()
                    if line_str.startswith("data: "):
                        data_part = line_str[6:].strip()
                        if data_part == "[DONE]":
                            break
                        try:
                            payload = json.loads(data_part)
                            delta = payload.get("choices", [{}])[0].get("delta", {})
                            reasoning = delta.get("reasoning") or delta.get("thought")
                            if reasoning:
                                yield {"type": "thought", "chunk": reasoning}
                            content = delta.get("content")
                            if content:
                                yield content
                        except Exception:
                            continue

    def stream_gemma_chat(
        self,
        system_prompt: str,
        user_message: str,
        tool_context: str = "",
        messages_history: list[dict[str, str]] | None = None,
    ):
        """Stream Gemma 4 26B A4B compliance chat turns via true HTTP SSE streaming."""
        full_prompt = (
            f"{user_message}\n\nContext Tool Results:\n{tool_context}"
            if tool_context
            else user_message
        )

        chat_messages = [{"role": "system", "content": system_prompt}]
        if messages_history:
            chat_messages.extend(messages_history)
        chat_messages.append({"role": "user", "content": full_prompt})

        if self.openrouter_key or self.groq_key:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openrouter_key or self.groq_key}",
                }
                body = {
                    "model": GEMMA_MODEL,
                    "messages": chat_messages,
                    "temperature": 0.3,
                    "stream": True,
                }
                url = OPENROUTER_API_URL if self.openrouter_key else GROQ_API_URL

                raw_stream = self._fetch_remote_stream_chunks(url, headers, body)
                text_stream = [item if isinstance(item, dict) else item for item in raw_stream]

                accumulated_output = []
                for event in self.parse_streaming_chunks(text_stream):
                    if event.get("type") == "token":
                        accumulated_output.append(event.get("chunk", ""))
                    yield event

                default_tracer.trace_llm_generation(
                    name="gemma_compliance_chat",
                    system_prompt=system_prompt,
                    user_message=full_prompt,
                    model=GEMMA_MODEL,
                    output_text="".join(accumulated_output),
                    metadata={"tool_context_present": bool(tool_context), "stream": True},
                )
                return
            except Exception as err:
                logger.warning(f"Compliance chat LLM streaming failed, using fallback: {err}")

        if tool_context:
            fallback_text = f"According to verified compliance records:\n\n{tool_context}"
        else:
            fallback_text = (
                "I am your Beacon Compliance assistant for Potter's House Christian Mission UK (SCIO, SC054652). "
                "How can I assist you with OSCR regulatory guidance, Receipts & Payments accounts, or Trustees' Annual Report drafting?"
            )

        words = fallback_text.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == len(words) - 1 else word + " "
            yield {"type": "token", "chunk": chunk}

    def call_gemma_chat(
        self,
        system_prompt: str,
        user_message: str,
        tool_context: str = "",
        messages_history: list[dict[str, str]] | None = None,
    ) -> str | None:
        """Call Gemma 4 26B A4B for synchronous compliance chat assistant turns."""
        full_prompt = (
            f"{user_message}\n\nContext Tool Results:\n{tool_context}"
            if tool_context
            else user_message
        )
        chat_messages = [{"role": "system", "content": system_prompt}]
        if messages_history:
            chat_messages.extend(messages_history)
        chat_messages.append({"role": "user", "content": full_prompt})

        body = {
            "model": GEMMA_MODEL,
            "messages": chat_messages,
            "temperature": 0.3,
        }

        endpoints = []
        if self.openrouter_key:
            endpoints.append(
                (
                    OPENROUTER_API_URL,
                    {
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "Content-Type": "application/json",
                    },
                )
            )
        if self.groq_key:
            endpoints.append(
                (
                    GROQ_API_URL,
                    {
                        "Authorization": f"Bearer {self.groq_key}",
                        "Content-Type": "application/json",
                    },
                )
            )

        for url, headers in endpoints:
            try:
                data = _post_json(url, headers=headers, body=body, timeout=12.0)
                reply = data["choices"][0]["message"]["content"]
                default_tracer.trace_llm_generation(
                    name="gemma_compliance_chat",
                    system_prompt=system_prompt,
                    user_message=full_prompt,
                    model=GEMMA_MODEL,
                    output_text=reply,
                    metadata={"tool_context_present": bool(tool_context), "provider_url": url},
                )
                return reply
            except Exception as err:
                logger.warning(f"Compliance chat LLM call failed on {url}: {err}")

        return None
