# Stage 1: Build & Dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend package metadata
COPY pyproject.toml /app/pyproject.toml
COPY backend /app/backend
COPY config /app/config
COPY templates /app/templates
COPY knowledge-base /app/knowledge-base

# Install backend dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "/app/backend"

# SpaCy model download (optional — OCR enhancement, not critical)
RUN python -m spacy download en_core_web_sm || true

# Verify critical dependencies installed
RUN python -c "from langfuse import Langfuse; from langfuse.langchain import CallbackHandler; print('Langfuse & CallbackHandler OK')"

# Stage 2: Final Production Runtime Image
FROM python:3.11-slim AS production

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged app user for security
RUN addgroup --gid 1001 appgroup && \
    adduser --uid 1001 --gid 1001 --disabled-password --gecos "" appuser

# Copy installed Python packages and source files from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder --chown=appuser:appgroup /app /app

RUN mkdir -p /app/data && chown -R appuser:appgroup /app/data

# Verify langfuse and langchain CallbackHandler are importable in production stage
RUN python -c "from langfuse import Langfuse; from langfuse.langchain import CallbackHandler; print('Langfuse & CallbackHandler production OK')"

USER appuser

ENV PORT=8000 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

