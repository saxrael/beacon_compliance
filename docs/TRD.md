# Beacon Compliance
## Technical Requirements Document
### Document 3 of 5 — Project Summary → PRD → **TRD** → Security Document → Prompt Document
### Version 1.0

---

## 0. Purpose

This TRD resolves every item PRD §10 explicitly deferred: D1 schemas, the LangGraph state machine, API contracts, embedding/chunking parameters, and rate-limit sizing. It assumes the PRD's functional requirements as fixed and does not re-derive them — it specifies how they're built.

---

## 1. Repository Structure

```
beacon-compliance/
├── frontend/                          # Next.js app — Vercel deployment target
│   ├── app/                           # App Router pages
│   ├── components/                    # ui-ux-pro-max + 21st.dev Magic generated components
│   ├── lib/                           # API client, SSE handling
│   └── design-system/                 # ui-ux-pro-max persisted MASTER.md + page overrides
├── backend/                           # FastAPI + LangGraph — Render deployment target
│   ├── src/
│   │   ├── api/                       # FastAPI routes
│   │   ├── agents/
│   │   │   ├── graph.py               # LangGraph state machine
│   │   │   ├── state.py               # BeaconComplianceState TypedDict
│   │   │   ├── node_ingest.py         # Node 1
│   │   │   ├── node_classify.py       # Tier 1/2/2.5 classification pipeline
│   │   │   ├── node_calculator.py     # Node 3
│   │   │   ├── node_writer.py         # Node 2
│   │   │   ├── node_auditor.py        # Node 4
│   │   │   ├── node_assembler.py      # Node 5
│   │   │   └── chat_agent.py          # Chat agent + tool definitions
│   │   ├── core/
│   │   │   ├── pii_engine.py          # Presidio wrapper
│   │   │   ├── ocr_engine.py          # pytesseract + Pillow + PyMuPDF pipeline
│   │   │   ├── financial.py           # Decimal-safe arithmetic
│   │   │   ├── memory.py              # 3-tier memory architecture
│   │   │   ├── retrieval.py           # Hybrid dense+sparse RRF
│   │   │   └── crypto.py              # AES-256-GCM
│   │   └── db/
│   │       ├── d1_client.py           # Cloudflare D1 HTTP API client
│   │       └── r2_client.py           # Cloudflare R2 S3-compatible client
│   └── tests/
├── config/
│   ├── charity_profile.yaml           # SC054652 identity, trustees, IE contact
│   └── fund_classifier.yaml           # Tier 1 classification ruleset (self-updating)
└── .agents/skills/
    └── beacon-financial-boundary/     # Workspace-scoped skill (Document 5)
```

---

## 2. Cloudflare D1 — Schema

| Table | Key Columns | Purpose |
|---|---|---|
| `users` | `user_id`, `email`, `password_hash`, `name`, `role` (Chair/Secretary/Treasurer), `first_login_complete` (bool) | Trustee accounts, admin-provisioned |
| `runs` | `run_id`, `charity_scn`, `year_end`, `status`, `created_at` | One row per annual compliance cycle |
| `documents` | `doc_id`, `run_id`, `category`, `description`, `r2_object_key`, `hash`, `anonymised_at`, `ocr_confidence_avg` | Uploaded source documents |
| `transactions` | `txn_id`, `run_id`, `date`, `description`, `amount`, `fund`, `category`, `classification_tier` (1/2/2.5), `classification_confidence` | Every bank transaction, post-classification |
| `classification_rules` | `rule_id`, `pattern`, `fund`, `category`, `created_from_txn_id`, `confirmed_by_tier` | The self-updating Tier 1 ruleset |
| `financial_state` | `run_id`, `fund`, `receipts_json`, `payments_json`, `opening_balance`, `closing_balance` | Node 3 output — immutable once written |
| `deliverables` | `deliverable_id`, `run_id`, `type` (OAR/TAR/RP/IE), `status`, `r2_object_key` | The four deliverables per run |
| `approvals` | `approval_id`, `run_id`, `deliverable_id`, `trustee_id`, `approval_hash` (SHA-256), `approved_at` | Cryptographic sign-off trail |
| `audit_log` | `log_id`, `run_id`, `node_name`, `input_hash`, `output_hash`, `status`, `error_msg`, `timestamp` | Full node execution trail |
| `ie_deliveries` | `delivery_id`, `run_id`, `signed_url_generated_at`, `expires_at`, `sent_to`, `resend_count` | IE pack delivery tracking (§4.4, PRD) |
| `notifications` | `notification_id`, `user_id`, `severity`, `type`, `sent_at` | Resend send log |
| `memory_summaries` | `user_id`, `run_id`, `summary_text`, `updated_at` | Tier 2 rolling narrative |
| `memory_facts` | `fact_id`, `user_id`, `fact_text`, `source_type` (non-financial only per PRD §7.9), `created_at` | Tier 3 semantic facts |
| `embeddings` | `chunk_id`, `source_type` (document/kb/conversation), `source_id`, `text`, `embedding_blob`, `fts_indexed` | Tier 4 archive + KB, hybrid RRF source |

All monetary columns stored as integer pence (never float/decimal-as-string ambiguity across the D1/HTTP API boundary) and converted to Python `Decimal` immediately on read.

---

## 3. LangGraph State Machine

```python
class BeaconComplianceState(TypedDict):
    # Node 1 outputs
    raw_documents: list[RawDocument]              # Pre-scrub only — never LLM-eligible
    anonymised_payload: AnonymisedPayload          # Post-scrub
    pii_audit_log: list[PIIRedaction]
    ocr_flags: list[OCRLowConfidenceFlag]          # Below 90% confidence, pending trustee review

    # Classification pipeline outputs
    classified_transactions: list[ClassifiedTransaction]
    pending_tier2_review: list[UnclassifiedTransaction]
    pending_tier25_suggestions: list[ClassificationSuggestion]  # category/confidence/reasoning only, never amount

    # Node 3 outputs (IMMUTABLE once set — structural enforcement per PRD §7.3)
    receipts_payments: RnPStatement
    statement_of_balances: BalanceStatement
    income_threshold_breach: bool                  # Red-Line 5

    # Node 2 outputs
    tar_draft_fields: dict[str, str]                # Exactly 4 keys — the LLM_DRAFTED fields (PRD §4.2)
    tar_revision_count: int                         # Max 3

    # Node 4 outputs
    validation_report: ValidationReport
    confidence_score: float

    # Node 6 / Human Gate
    trustee_approvals: list[TrusteeApproval]
    submission_package_path: str | None
    ie_delivery_status: IEDeliveryStatus | None
```

Conditional edges of note beyond the PRD's node sequence:
- `income_threshold_breach == True` → hard-route to `HALT_INCOME_THRESHOLD`, bypassing every downstream node regardless of other state (Red-Line 5, independently re-checked at both Node 1 and Node 4 per PRD §7.5).
- `pending_tier2_review` or `pending_tier25_suggestions` non-empty → route to `HUMAN_CLASSIFICATION_GATE` before Node 3 is permitted to execute.
- Attempted write to `receipts_payments` or `statement_of_balances` outside Node 3 → raises `StateImmutabilityViolation`, not a silent overwrite.

Checkpointing: state persisted to D1 (not local SQLite — Render's ephemeral disk ruled this out per Project Summary §10) after every node execution, keyed by `run_id`.

---

## 4. API Contracts (Frontend ↔ Backend)

| Endpoint | Method | Purpose |
|---|---|---|
| `/auth/login` | POST | Trustee login; returns session token |
| `/auth/first-login-reset` | POST | Forced password change flow |
| `/ingest` | POST | Document upload (category + description + file) |
| `/status/{run_id}` | GET | Pipeline progress |
| `/chat/stream` | SSE | Live agent step streaming (tool calls, reasoning) — Project Summary §10 |
| `/classification/pending` | GET | Tier 2/2.5 items awaiting trustee decision |
| `/classification/{txn_id}/confirm` | POST | Trustee confirms/overrides a classification |
| `/approve/{deliverable_id}` | POST | Role-gated approval, SHA-256 commitment |
| `/export/{run_id}/{deliverable}` | GET | Download a finalized deliverable |
| `/ie-package/{run_id}/resend` | POST | Trustee-initiated IE link regeneration (never autonomous, per Red-Line 1) |
| `/admin/provision-trustee` | POST | Admin-only, Israel-authenticated separately from trustee auth |

All endpoints authenticated except `/auth/login`. `/admin/*` requires a distinct admin credential, never a trustee session token — this is the CLI-adjacent provisioning path from PRD §7.12, exposed as an endpoint the admin script calls rather than a raw script only.

---

## 5. Hybrid RAG — Chunking & Retrieval Parameters

- **Chunking**: 800–1000 character target chunks (mirrors the RAG Document Engineer's 500–1500 char section rule — see Document 5), with 150-character overlap.
- **Embedding model**: Given the two-model constraint (Gemma 4 26B A4B + `openai/gpt-oss-20b` only, per Project Summary §10), embeddings are generated via Gemini API's dedicated embedding endpoint (not a chat model) — this is a separate, free-tier embedding call, not a third chat model, so it doesn't violate the confirmed model-exclusivity boundary.
- **Sparse index**: SQLite FTS5 virtual table over the same `embeddings.text` column, D1-native.
- **Fusion**: Reciprocal Rank Fusion, k=60, computed in the Render backend after both dense (cosine similarity, Python-side over D1-stored vectors) and sparse (FTS5) queries return.
- **Retrieval depth**: top-k=5 per query, consistent with the reference architecture's calibration.

---

## 6. Rate-Limit Sizing

At confirmed scale (2 trustees, small charity transaction/document volume):
- **Gemma 4 26B A4B** (AI Studio free tier): governs Node 2, chat agent, Tier 2/3 memory. Estimated peak load — a handful of chat turns per trustee per day plus periodic background memory summarization — sits comfortably within AI Studio's free-tier RPM/TPM/RPD limits; no contention risk identified at this scale (Project Summary §10's accepted shared-quota tradeoff).
- **`openai/gpt-oss-20b`** (Groq free tier: 30,000 TPM / 14,400 RPD): Tier 2.5 classification only fires on transactions Tier 1 can't match — realistically tens per month for a charity this size, orders of magnitude under any Groq free-tier ceiling.

No paid-tier upgrade is anticipated at current scale for either model.

---

## 7. Deployment Configuration

- **Vercel**: Next.js frontend, standard git-integrated deployment, environment variables for backend API URL and public config only — no secrets in frontend env.
- **Render**: FastAPI backend, free web service tier; **cold-start behavior (15-min inactivity spin-down, ~60s wake) is an accepted tradeoff** per Project Summary §10, not a defect to engineer around at this stage.
- **Cloudflare D1 + R2**: Provisioned via Cloudflare dashboard/Wrangler CLI; backend authenticates to both via API token stored in Render's environment secrets, never committed.
- **Resend**: API key in Render environment secrets; sender domain verification required before production notification sends.
- **Secrets management**: `.env.example` committed with variable names only; actual `.env` never committed; Render's built-in environment variable store is the source of truth for deployed secrets.

---

## 8. Items Deferred to the Security Document

Per PRD §10, backup/disaster-recovery mechanics for D1/R2 remain Security Document territory specifically — this TRD establishes the schema and infrastructure those mechanics will operate over, but does not itself specify retention/recovery policy.

---

## 9. Document Status

Every item PRD §10 flagged as deferred is now resolved. No open ambiguities remain. Proceeding to the Security Document (Document 4) on your authorization.
