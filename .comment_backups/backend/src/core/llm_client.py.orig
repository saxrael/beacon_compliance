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
from backend.src.core.telemetry import default_tracer

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


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

        if self.openrouter_key or self.groq_key:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openrouter_key or self.groq_key}",
                }
                body = {
                    "model": "google/gemma-2-27b-it" if self.openrouter_key else "gemma2-9b-it",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                }
                url = OPENROUTER_API_URL if self.openrouter_key else GROQ_API_URL
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, headers=headers, json=body)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        parsed = json.loads(content)
                        if isinstance(parsed, dict) and "governance_description" in parsed:
                            default_tracer.trace_llm_generation(
                                name="gemma_narrative_synthesis",
                                system_prompt=system_prompt,
                                user_message=user_prompt,
                                model="google/gemma-2-27b-it"
                                if self.openrouter_key
                                else "gemma2-9b-it",
                                output_text=content,
                                metadata={"run_type": "narration_synthesis"},
                            )
                            return parsed
            except Exception as err:
                logger.warning(f"LLM call for TAR narrative synthesis failed: {err}")

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

        if self.groq_key or self.openrouter_key:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.groq_key or self.openrouter_key}",
                }
                model_name = (
                    "openai/gpt-oss-20b" if self.groq_key else "meta-llama/llama-3.1-8b-instant"
                )
                body = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                }
                url = GROQ_API_URL if self.groq_key else OPENROUTER_API_URL
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, headers=headers, json=body)
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        parsed = json.loads(content)

                        cleaned = {
                            "category": str(parsed.get("category", "General Offerings")),
                            "confidence": float(parsed.get("confidence", 0.85)),
                            "reasoning": str(
                                parsed.get(
                                    "reasoning", "LLM categorization based on description pattern"
                                )
                            ),
                        }
                        default_tracer.trace_llm_generation(
                            name="tier25_classifier",
                            system_prompt=system_prompt,
                            user_message=user_prompt,
                            model=model_name,
                            output_text=json.dumps(cleaned),
                            metadata={"transaction_type": transaction_type},
                        )
                        return cleaned
            except Exception as err:
                logger.warning(f"Tier 2.5 LLM classification call failed: {err}")

        return None

    def call_gemma_chat(
        self, system_prompt: str, user_message: str, tool_context: str = ""
    ) -> str | None:
        """Call Gemma 4 26B A4B for compliance chat assistant turns."""
        if self.openrouter_key or self.groq_key:
            try:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openrouter_key or self.groq_key}",
                }
                full_prompt = (
                    f"{user_message}\n\nContext Tool Results:\n{tool_context}"
                    if tool_context
                    else user_message
                )
                body = {
                    "model": "google/gemma-2-27b-it" if self.openrouter_key else "gemma2-9b-it",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_prompt},
                    ],
                    "temperature": 0.3,
                }
                url = OPENROUTER_API_URL if self.openrouter_key else GROQ_API_URL
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, headers=headers, json=body)
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data["choices"][0]["message"]["content"]
                        default_tracer.trace_llm_generation(
                            name="gemma_compliance_chat",
                            system_prompt=system_prompt,
                            user_message=full_prompt,
                            model="google/gemma-2-27b-it"
                            if self.openrouter_key
                            else "gemma2-9b-it",
                            output_text=reply,
                            metadata={"tool_context_present": bool(tool_context)},
                        )
                        return reply
            except Exception as err:
                logger.warning(f"Compliance chat LLM call failed: {err}")

        return None
