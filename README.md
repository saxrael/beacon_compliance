# Beacon Compliance OS

<p align="center">
  <img src="assets/scio_header_banner.png" alt="Beacon Compliance OS - Potter's House Christian Mission UK Header Banner" width="100%" />
</p>

> **Beacon Compliance is an agentic OSCR-compliance webapp for Potter's House Christian Mission UK (SCIO, SC054652). It deterministically computes statutory accounts, drafts narrative reports, tracks filing deadlines, and provides an interactive chat assistant—all under 5 strict compliance red-lines.**

![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=flat-square)
![Tests](https://img.shields.io/badge/pytest-52%2F52%20passed-success?style=flat-square)
![Preflight Audit](https://img.shields.io/badge/audit-100%25%20passed-success?style=flat-square)
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

Beacon Compliance OS is a domain-specific compliance operating system built strictly to automate OSCR (Office of the Scottish Charity Regulator) statutory reporting for **Potter's House Christian Mission UK (SC054652)**.

The core pipeline is implemented as an idempotent, deterministic **LangGraph state machine (`BeaconComplianceGraph`)** that governs data ingestion, transaction classification, narrative synthesis, deterministic arithmetic, hallucination auditing, and package assembly.

### LangGraph Pipeline Topology

```mermaid
graph TD
    A[Raw Document / Bank Statement Ingest] -->|Presidio + Regex Scrubbing| B[Node 1: Ingest & PII Filter]
    B -->|Ingest Income Check < £250k| C[Node 2: 3-Tier Classifier]
    C -->|Tier 1: Rules / Tier 2: Trustee / Tier 2.5: Isolated LLM| D[Node 3: Deterministic Accounting Engine]
    D -->|Python Decimal Arithmetic| E[Node 4: Gemma 4 26B Narrative Writer]
    E -->|Tokens & [FIGURE_INJECTED] Placeholders| F[Node 5: Hallucination Auditor]
    F -->|Zero Discrepancy Gate| G[Node 6: Deliverable Package Assembler]
    G -->|HMAC Keyed Sign-off| H[4 OSCR Submission Packages]
```

### Deterministic vs. Probabilistic Boundary Matrix

To guarantee strict compliance with Scottish charity law and eliminate LLM math hallucinations:

- **Deterministic Primitives (Python `Decimal`)**: Monetary totals, gross receipts, gross payments, fund balances, income threshold checks, SHA-256 content hashes, and per-trustee HMAC sign-offs.
- **Probabilistic Assistance (Gemma 4 26B A4B & `openai/gpt-oss-20b`)**: Transaction categorization suggestions (strictly restricted to `{category, confidence, reasoning}`) and narrative synthesis for the 4 statutory Trustees' Annual Report (TAR) fields using `[FIGURE_INJECTED]` token placeholders.

---

## ⚡ Key Features

- **5 Mandatory Compliance Red-Lines**: Hard security and regulatory boundaries built directly into code.
- **4 OSCR Submission Packages**:
  1. **Deliverable 1 (OAR)**: OSCR Online Annual Return Pre-Population Data Sheet.
  2. **Deliverable 2 (TAR)**: Trustees' Annual Report with statutory narrative fields.
  3. **Deliverable 3 (R&P)**: Receipts & Payments Accounts matrix and Statement of Balances reconciliation.
  4. **Deliverable 4 (IE Pack)**: Independent Examiner Review Package with audit logs and SHA-256 verification hashes.
- **Dynamic Dark/Light Theme System**: Seamless toggle between Light Mode and Dark Mode with adaptive brand tokens, CSS glassmorphism, and dynamic logo swapping (`logo.png` vs `logo_dark.png`).
- **Authentic Brand Integration**: Embedded logo graphics, letterhead header banners (`scio_header_banner.png`), trustee signature seals (`trustee_seal.png`), and official brand palette (Crimson Red `#D6162F`, Royal Gold `#F5D345`, Scottish Slate `#0F172A`).
- **Per-Trustee HMAC Authentication**: Cryptographic sign-off using `hmac.new(trustee_secret, message, hashlib.sha256)` for Chair, Treasurer, and Secretary roles.
- **Automated PII Scrubbing**: Structural Presidio + regex scrubber redacts sort codes, bank account numbers, emails, phone numbers, and postcodes prior to any LLM eligibility.

---

## 🛠️ Technology Stack

| Layer | Technologies | Purpose & Details |
|---|---|---|
| **Backend Engine** | Python 3.11+, FastAPI, LangGraph, Pydantic v2 | REST API, state machine orchestration, deterministic Decimal accounting |
| **Frontend UI** | Next.js 16+ (App Router), TypeScript, Tailwind CSS, Lucide Icons | Responsive trustee compliance dashboard with dynamic dark/light mode toggle |
| **AI Models** | Gemma 4 26B A4B & `openai/gpt-oss-20b` (via Groq) | Narrative synthesis and Tier 2.5 transaction categorization |
| **Relational Database** | Cloudflare D1 (Serverless SQLite) | 14 relational tables (transactions, funds, audit logs, deliverables) |
| **Object Storage** | Cloudflare R2 | Encrypted document and blob storage (AES-256-GCM) |
| **Telemetry & Observability** | Langfuse 2.0+ | PII-guarded LLM tracing and audit logging |

---

## 📁 Repository Structure

```
beacon_compliance/
├── assets/                          # Primary brand graphics (logo.png, logo_dark.png, trustee_seal.png)
├── backend/
│   ├── pyproject.toml               # Python dependencies and uv build configuration
│   ├── src/
│   │   ├── agents/                  # LangGraph nodes (ingest, classify, calculator, writer, auditor, assembler)
│   │   ├── api/                     # FastAPI endpoints (ingest, classify, pipeline, signoff, deliverables, chat)
│   │   ├── core/                    # Security, PII scrubber, crypto, financial arithmetic, memory, retrieval
│   │   └── db/                      # Cloudflare D1 and R2 client interfaces
│   └── tests/                       # Complete pytest test suite (47 unit & integration tests)
├── config/
│   ├── charity_profile.yaml         # SC054652 profile & fund definitions
│   └── fund_classifier.yaml        # Tier 1 deterministic classification matrix
├── docs/                            # Comprehensive specifications (PRD.md, TRD.md, security_doc.md, DEPLOYMENT.md)
├── frontend/                        # Next.js 16+ Trustee Web Application
│   ├── design-system/MASTER.md      # Master design system specification
│   ├── public/assets/               # Mirrored web assets (logo.png, logo_dark.png, logo_mark.png, favicon.ico)
│   └── src/                         # Next.js app pages, components, context (ThemeContext), hooks
├── migrations/                      # Cloudflare D1 SQL schema migrations (0001_initial_schema.sql)
├── render.yaml                      # Render.com backend deployment configuration
├── scripts/
│   └── deploy_check.py              # Automated pre-flight production audit script
├── templates/                       # OSCR Deliverable HTML document templates (OAR, TAR, R&P, IE Pack)
└── wrangler.toml                    # Cloudflare D1 & R2 binding configuration
```

---

## 🛢️ Database & Data Isolation

Beacon Compliance utilizes **Cloudflare D1** for relational data persistence and **Cloudflare R2** for encrypted blob storage.

### Core Relational Tables (`migrations/0001_initial_schema.sql`)

- `charity_profile`: Statutory charity details (SC054652).
- `fund_definitions`: Unrestricted General and Restricted Mission funds.
- `bank_accounts` & `bank_statements`: Statement metadata and closing balances.
- `raw_transactions`: Ingested transaction records with scrubbed descriptions and integer pence representations (`amount_pence`).
- `classified_transactions`: Tier 1/2/2.5 classification history with confidence scores.
- `deliverable_packages`: Compiled deliverables with SHA-256 content hashes.
- `trustee_signoffs`: Cryptographic HMAC signatures recorded per role.

### Precision Monetary Storage
Monetary figures are stored as 64-bit signed integers representing exact value in **pence** (e.g., `£150.25` is stored as `15025`). All domain calculations are executed using `decimal.Decimal`. Floating-point arithmetic is strictly prohibited.

---

## 🔑 Environment Configuration & Secrets

Copy `.env.template` to `.env` and fill in the required environment variables:

```bash
# Core Environment
APP_ENV=production
CHARITY_NUMBER=SC054652

# Security & Encryption
AES_256_GCM_SECRET=your_32_byte_minimum_encryption_secret_key!
TRUSTEE_SIGNATURE_SALT=your_random_salt_for_hmac_signoff

# Cloudflare Bindings
CLOUDFLARE_D1_DATABASE_ID=beacon-compliance-d1-prod-id
CLOUDFLARE_R2_BUCKET_NAME=beacon-compliance-r2-prod

# LLM Providers & Observability
GROQ_API_KEY=gsk_your_groq_api_key
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## 🚀 Local Quick Start & Verification

### 1. Prerequisites
- **Python**: Version `3.11` or higher (with `uv` installed)
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
Run the 47 unit & integration tests covering encryption, financial boundaries, PII scrubbing, node calculations, LangGraph pipeline execution, and FastAPI routes:

```bash
# From project root
python -m pytest backend/tests -v --tb=short
```

### 2. Pre-Flight Production Readiness Audit
Run the automated pre-flight audit script to verify environment variables, secret key entropy, document template presence, and D1 database migrations:

```bash
python scripts/deploy_check.py
```

---

## 🚢 CI/CD & Production Deployment

### Backend API (Render.com)
The backend is configured for deployment via `render.yaml`:
```bash
# Web service specification
type: web
name: beacon-compliance-backend
env: python
buildCommand: cd backend && uv pip install -e .
startCommand: uvicorn backend.src.api.main:app --host 0.0.0.0 --port $PORT
```

### Database & Storage (Cloudflare D1 & R2)
Apply database migrations to production:
```bash
npx wrangler d1 migrations apply beacon-compliance-d1 --remote
```

### Frontend Web App (Vercel)
Deploy the Next.js frontend to Vercel with environment variable `NEXT_PUBLIC_API_BASE_URL` pointing to your deployed Render API.

---

## 🔒 Security & Compliance Red-Lines

> [!CAUTION]
> **SAFETY-CRITICAL COMPLIANCE POLICY**  
> Beacon Compliance OS enforces 5 non-negotiable compliance Red-Lines across every module:
>
> 1. **No Autonomous Submission**: No automated code path transmits data to OSCR or external bodies without explicit trustee UI invocation.
> 2. **Zero LLM Math**: No LLM computes, estimates, rounds, or evaluates a monetary figure. All math is deterministic Python `Decimal`.
> 3. **Role-Restricted HMAC Sign-Off**: Submission packages require HMAC-SHA256 signatures generated with per-trustee secret keys for Chair, Treasurer, or Secretary roles.
> 4. **PII Boundary Enforcement**: PII is scrubbed at ingest via Presidio + regex before any LLM processing.
> 5. **Income Threshold Hard-Halt**: Gross income $\ge £250,000$ halts Receipts & Payments generation immediately at both ingest and validation layers.

---

## 📄 License & Support

**Potter's House Christian Mission UK**  
Scottish Charitable Incorporated Organisation (SCIO) — SC054652  
Principal Address: 5B Beachmont Court, Dunbar, Scotland, EH42 1YF  
Public Website: [https://www.pottershousemission.org.uk](https://www.pottershousemission.org.uk)

*Copyright © 2026 Potter's House Christian Mission UK. All rights reserved.*
