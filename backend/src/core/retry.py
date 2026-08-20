"""Tenacity Retry Engine and Error Handling Policies (backend/src/core/retry.py).

Provides production-grade exponential backoff, jitter, and error classification for:
1. LLM API Gateways (Groq, OpenRouter, Google AI Studio)
2. Deterministic Database and Hybrid RAG Tool Execution (Cloudflare D1 SQLite)
"""

import logging
import sqlite3

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
)

logger = logging.getLogger(__name__)

RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


def is_retryable_http_error(exc: BaseException) -> bool:
    """Predicate to determine if an HTTP exception is transient and eligible for tenacity retry."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_HTTP_STATUS_CODES
    if isinstance(exc, httpx.TimeoutException | httpx.ConnectError | httpx.NetworkError):
        return True
    return False


def is_retryable_db_error(exc: BaseException) -> bool:
    """Predicate to determine if a database exception is transient (e.g. SQLite database locked/busy)."""
    if isinstance(exc, sqlite3.OperationalError):
        msg = str(exc).lower()
        if "locked" in msg or "busy" in msg:
            return True
    return False


llm_retry = retry(
    retry=retry_if_exception(is_retryable_http_error),
    wait=wait_random_exponential(multiplier=0.3, max=4.0),
    stop=stop_after_attempt(3),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

db_retry = retry(
    retry=retry_if_exception(is_retryable_db_error),
    wait=wait_exponential(multiplier=0.1, max=1.0),
    stop=stop_after_attempt(3),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
