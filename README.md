# Beacon Compliance OS

<p align="center">
  <img src="assets/scio_header_banner.png" alt="Beacon Compliance OS - Potter's House Christian Mission UK Header Banner" width="100%" />
</p>

> **Beacon Compliance is an agentic OSCR-compliance webapp for Potter's House Christian Mission UK (SCIO, SC054652). It deterministically computes statutory accounts, drafts narrative reports, tracks filing deadlines, and provides an interactive chat assistant—all under 5 strict compliance red-lines.**

![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)
![Tests](https://img.shields.io/badge/pytest-62%2F62%20passed-success?style=flat-square)
![Preflight Audit](https://img.shields.io/badge/audit-100%25%20passed-success?style=flat-square)
![Boundary AST Check](https://img.shields.io/badge/boundary--ast-0%20violations-success?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)
![Next.js](https://img.shields.io/badge/next.js-16%2B-black?style=flat-square)
![TypeScript](https://img.shields.io/badge/typescript-5.0%2B-blue?style=flat-square)
![License](https://img.shields.io/badge/license-SCIO%20Internal-amber?style=flat-square)

---

## 📋 Table of Contents

- [System Architecture & Core Principles](#-system-architecture--core-principles)
- [Key Features](#-key-features)
- [Technology Stack](#-technology-stack)
- [Repository Structure](#-repository-structure)
- [Database & Data Isolation](#-database--data-isolation)
- [Environment Configuration & Secrets](#-environment-configuration--secrets)
- [Local Quick Start & Verification](#-local-quick-start--verification)
- [Automated Testing & Pre-Flight Audits](#-automated-testing--pre-flight-audits)
- [CI/CD & Production Deployment](#-cicd--production-deployment)
- [Security & Compliance Red-Lines](#-security--compliance-red-lines)
- [License & Support](#-license--support)

---

## 🏗️ System Architecture & Core Principles

Beacon Compliance OS is a domain-specific compliance operating system built strictly to automate statutory reporting to the **Office of the Scottish Charity Regulator (OSCR)** for **Potter's House Christian Mission UK (SC054652)**.

The core compliance workflow is driven by an automated, idempotent **LangGraph state machine (`BeaconComplianceGraph`)** that governs data ingestion, transaction classification, narrative synthesis, deterministic arithmetic, hallucination auditing, and package assembly.

### LangGraph Pipeline Topology

```mermaid
graph TD
    A[Raw Document / Bank Statement Ingest] -->|Presidio + Regex Scrubbing| B[Node 1: Ingest & PII Redactor]
    B -->|Ingest Income Check < £250k| C[Node 1.5: 3-Tier Classifier]
    C -->|Tier 1: Rules / Tier 2: Trustee / Tier 2.5: Isolated LLM| D[Node 3: Deterministic Calculator]
    D -->|Python Decimal Arithmetic| E[Node 2: Gemma 4 26B Narrative Writer]
    E -->|Tokens & [FIGURE_INJECTED] Placeholders| F[Node 4: Hallucination Auditor]
    F -->|Zero Discrepancy Gate| G[Node 5: OSCR Package Assembler]
    G -->|HMAC-SHA256 Sign-off| H[4 OSCR Submission Packages]
```

### Deterministic vs. Probabilistic Boundary Matrix

To guarantee strict compliance with Scottish charity law and eliminate LLM math hallucinations:

- **Deterministic Primitives (Python `Decimal`)**: Monetary totals, gross receipts, gross payments, fund balances, income threshold checks, SHA-256 content hashes, and per-trustee HMAC sign-offs.
- **Probabilistic Assistance (Gemma 4 26B A4B & `openai/gpt-oss-20b`)**: Transaction categorization suggestions (strictly restricted to `{category, confidence, reasoning}`) and narrative synthesis for the 4 statutory Trustees' Annual Report (TAR) fields using `[FIGURE_INJECTED]` token placeholders.

---

## ⚡ Key Features

- **5 Mandatory Compliance Red-Lines**: Hard security and regulatory boundaries built directly into code.
- **4 OSCR Submission Packages (Publication-Grade Templates)**:
  1. **Deliverable 1 (OAR)**: OSCR Online Annual Return Pre-Population Data Sheet.
  2. **Deliverable 2 (TAR)**: Trustees' Annual Report with statutory narrative fields.
  3. **Deliverable 3 (R&P)**: Receipts & Payments Accounts matrix and Statement of Balances reconciliation.
  4. **Deliverable 4 (IE Pack)**: Independent Examiner Review Package with audit logs and SHA-256 verification hashes.
- **Publication-Grade CSS & Print Architecture**: Embedded Google Fonts (`Cinzel`, `Inter`, `JetBrains Mono`), `@media print` A4 pagination controls, watermark seal (`trustee_seal.png`), and authentic header banner (`scio_header_banner.png`).
- **Dynamic Dark/Light Theme System**: Seamless toggle between Light Mode and Dark Mode with adaptive brand tokens, CSS glassmorphism, and dynamic logo swapping (`logo.png` vs `logo_dark.png`).
- **Langfuse Cloud LLM Observability**: PII-guarded generation tracing, latency monitoring, and token cost tracking (`backend/src/core/telemetry.py`).
- **Per-Trustee HMAC Authentication**: Cryptographic sign-off using `hmac.new(trustee_secret, message, hashlib.sha256)` for Chair, Treasurer, and Secretary roles.
- **Automated PII Scrubbing**: Structural Presidio + regex scrubber redacts sort codes, bank account numbers, emails, phone numbers, and postcodes prior to any LLM eligibility.

---

## 🛠️ Technology Stack

| Layer | Technologies | Purpose & Details |
|---|---|---|
| **Backend Engine** | Python 3.11+, FastAPI, LangGraph, Pydantic v2 | REST API, state machine orchestration, deterministic Decimal accounting |
| **Frontend UI** | Next.js 16+ (App Router), TypeScript, Tailwind CSS, Lucide Icons | Responsive trustee compliance dashboard with dynamic dark/light mode toggle |
| **AI Models** | Gemma 4 26B A4B & `openai/gpt-oss-20b` (via Groq / OpenRouter) | Narrative synthesis and Tier 2.5 transaction categorization |
| **Relational Database** | Cloudflare D1 (Serverless SQLite) | 14 relational tables (transactions, funds, audit logs, deliverables) |
| **Object Storage** | Cloudflare R2 | Encrypted document and blob storage (AES-256-GCM) |
| **Telemetry & Observability** | Langfuse Cloud (`https://cloud.langfuse.com`) | PII-guarded LLM tracing, latency tracking, and prompt monitoring |
| **Production Server** | OCI Always-Free VM + Docker + Caddy Reverse Proxy | Dedicated backend compute with automated HTTPS via DuckDNS |

---

## 📁 Repository Structure

```
beacon_compliance/
├── assets/                          # Primary brand graphics (logo.png, scio_header_banner.png, trustee_seal.png)
├── backend/
│   ├── pyproject.toml               # Python dependencies (fastapi, langgraph, langfuse, cryptography, uv)
│   ├── src/
│   │   ├── agents/                  # LangGraph nodes (ingest, classify, calculator, writer, auditor, assembler, graph)
│   │   ├── api/                     # FastAPI endpoints (ingest, classify, pipeline, signoff, deliverables, chat)
│   │   ├── core/                    # Security, PII scrubber, crypto, financial arithmetic, telemetry, retrieval
│   │   └── db/                      # Cloudflare D1 and R2 client interfaces & repository facade
│   └── tests/                       # Complete pytest test suite (62 unit & integration tests)
├── config/
│   ├── charity_profile.yaml         # SC054652 profile & fund definitions
│   └── fund_classifier.yaml        # Tier 1 deterministic classification matrix
├── docs/                            # Comprehensive specifications (PRD.md, TRD.md, security_doc.md, DEPLOYMENT.md)
├── frontend/                        # Next.js 16+ Trustee Web Application
│   ├── design-system/MASTER.md      # Master design system specification
│   ├── public/assets/               # Mirrored web assets (logo.png, scio_header_banner.png, favicon.ico)
│   └── src/                         # Next.js app pages, components, context (ThemeContext), hooks
├── migrations/                      # Cloudflare D1 SQL schema migrations (0001_initial_schema.sql)
├── scripts/
│   └── deploy_check.py              # Automated pre-flight production audit script
├── templates/                       # OSCR Deliverable HTML document templates (OAR, TAR, R&P, IE Pack)
└── wrangler.toml                    # Cloudflare D1 & R2 binding configuration
```

---

## 🛢️ Database & Data Isolation

Beacon Compliance utilizes **Cloudflare D1** for relational data persistence and **Cloudflare R2** for encrypted blob storage.

### Core Relational Tables (`migrations/0001_initial_schema.sql`)

- `users`: Trustee accounts, role definitions, and password hashes.
- `runs`: Pipeline execution runs and statutory year-end metadata.
- `documents`: Raw and scrubbed document records with Cloudflare R2 object keys.
- `transactions`: Ingested transaction records with scrubbed descriptions and integer pence representations (`amount_pence`).
- `classification_rules`: Tier 1 pattern rules and Tier 2 trustee-learned classification mappings.
- `financial_state`: Node 3 calculated Receipts & Payments totals per fund.
- `deliverables`: Status tracking for the 4 OSCR packages.
- `approvals`: Cryptographic HMAC signatures recorded per trustee role.
- `audit_log`: End-to-end execution logs (`input_hash`, `output_hash`, node status).
- `ie_deliveries`: Signed time-limited download URLs for Independent Examiners.
- `notifications`: Critical alert dispatches.
- `memory_summaries` & `memory_facts`: Cognitive memory Tiers 2 & 3 (non-financial facts ONLY).
- `embeddings`: Vector embeddings for hybrid dense+sparse RRF retrieval.

### Precision Monetary Storage
Monetary figures are stored as 64-bit signed integers representing exact value in **pence** (e.g., `£150.25` is stored as `15025`). All domain calculations are executed using `decimal.Decimal`. Floating-point arithmetic for monetary values is strictly prohibited.

---

## 🔑 Environment Configuration & Secrets

Copy `.env.template` to `.env` and populate the required environment variables:

```bash
# Core Environment
APP_ENV=production
CHARITY_NUMBER=SC054652
CHARITY_NAME="Potter's House Christian Mission UK"

# Security & Encryption
AES_256_GCM_SECRET=your_32_byte_minimum_encryption_secret_key!
TRUSTEE_SIGNATURE_SALT=your_random_salt_for_hmac_signoff

# Cloudflare Bindings
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_D1_DATABASE_ID=ae9bc1a9-395d-468a-891e-172587c73189
CLOUDFLARE_R2_BUCKET_NAME=beacon-compliance-r2-prod

# LLM Providers & Observability
GROQ_API_KEY=gsk_your_groq_api_key
OPENROUTER_API_KEY=sk-or-your_openrouter_api_key
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-your_public_key_here
LANGFUSE_SECRET_KEY=sk-lf-your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 🚀 Local Quick Start & Verification

### 1. Prerequisites
- **Python**: Version `3.11` or higher (with `uv` package manager)
- **Node.js**: Version `18` or higher (with `npm`)

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment and install dependencies using uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install
```

### 4. Running Locally
In terminal 1 (Backend API):
```bash
cd backend
uvicorn src.api.main:app --reload --port 8000
```

In terminal 2 (Frontend Dashboard):
```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to access the Trustee Compliance Dashboard.

---

## 🧪 Automated Testing & Pre-Flight Audits

### 1. Pytest Backend Test Suite
Run the 62 unit & integration tests covering encryption, financial boundaries, PII scrubbing, node calculations, LangGraph pipeline execution, telemetry, authentication (Google OAuth, 2FA/TOTP), email service, and FastAPI routes:

```bash
# From project root
python -m pytest -v --tb=short
```

### 2. AST Financial Boundary Check
Verify zero AST violations of the 5 financial boundary rules across all Python modules:

```bash
python .agent/.agents/skills/beacon-financial-boundary/scripts/verify_financial_boundary.py backend/src/
```

### 3. Pre-Flight Production Readiness Audit
Run the automated pre-flight audit script to verify environment variables, secret key entropy, document template presence, and D1 database migrations:

```bash
python scripts/deploy_check.py
```

---

## 🚢 CI/CD & Production Deployment

### Backend API (OCI Always-Free VM + Docker + Caddy)
The backend runs as a Docker container on a dedicated OCI Always-Free VM behind Caddy reverse proxy with automated HTTPS via DuckDNS (`https://beacon-compliance.duckdns.org`).

### Database & Storage (Cloudflare D1 & R2)
Apply database migrations to production Cloudflare D1:
```bash
npx wrangler d1 migrations apply beacon-compliance-d1 --remote
```

### Frontend Web App (Vercel / Cloudflare Pages)
Deploy the Next.js frontend to Vercel with environment variable `NEXT_PUBLIC_API_URL` pointing to your deployed backend API endpoint.

---

## 🔒 Security & Compliance Red-Lines

> [!CAUTION]
> **SAFETY-CRITICAL COMPLIANCE POLICY**  
> Beacon Compliance OS enforces 5 non-negotiable compliance Red-Lines across every module:
>
> 1. **No Autonomous Submission**: No automated code path transmits data to OSCR or external bodies without explicit trustee UI invocation.
> 2. **Zero LLM Math**: No LLM computes, estimates, rounds, or evaluates a monetary figure. All math is deterministic Python `Decimal`.
> 3. **Role-Restricted HMAC Sign-Off**: Submission packages require HMAC-SHA256 signatures generated with per-trustee secret keys for Chair, Treasurer, or Secretary roles.
> 4. **PII Boundary Enforcement**: PII is scrubbed at ingest via Presidio + regex before any LLM processing. Telemetry traces pass through mandatory PII sanitization.
> 5. **Income Threshold Hard-Halt**: Gross income $\ge £250,000$ halts Receipts & Payments generation immediately at both ingest and validation layers.

---

## 📄 License & Support

**Potter's House Christian Mission UK**  
Scottish Charitable Incorporated Organisation (SCIO) — SC054652  
Principal Address: 5B Beachmont Court, Dunbar, Scotland, EH42 1YF  
Public Website: [https://www.pottershousemission.org.uk](https://www.pottershousemission.org.uk)

*Copyright © 2026 Potter's House Christian Mission UK. All rights reserved.*
