"""FastAPI Main Application Entrypoint for Beacon Compliance (main.py).

Provides CORS middleware, API route registration, and health status endpoint.
"""

import os

from backend.src.api.rate_limiter import (
    RateLimitExceeded,
    RateLimitMiddleware,
    _rate_limit_exceeded_handler,
    limiter,
)
from backend.src.api.routes_admin import router as admin_router
from backend.src.api.routes_auth import router as auth_router
from backend.src.api.routes_chat import router as chat_router
from backend.src.api.routes_classify import router as classify_router
from backend.src.api.routes_deliverables import router as deliverables_router
from backend.src.api.routes_ingest import router as ingest_router
from backend.src.api.routes_pipeline import router as pipeline_router
from backend.src.api.routes_settings import router as settings_router
from backend.src.api.routes_signoff import router as signoff_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Beacon Compliance OS API",
    description="Agentic OSCR compliance web application backend for Potter's House Christian Mission UK (SC054652)",
    version="1.0.0",
)

if limiter:
    app.state.limiter = limiter
    if _rate_limit_exceeded_handler:
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins_env = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
origins = [
    origin.strip().strip("\"'").rstrip("/")
    for origin in allowed_origins_env.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(admin_router)
app.include_router(ingest_router)
app.include_router(classify_router)
app.include_router(pipeline_router)
app.include_router(signoff_router)
app.include_router(deliverables_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "charity": "SC054652", "version": "1.0.0"}
