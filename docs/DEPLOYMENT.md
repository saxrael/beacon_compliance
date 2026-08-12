# Beacon Compliance — Production Deployment Guide

**Target Charity**: Potter's House Christian Mission UK (SCIO, SC054652, Dunbar, Scotland)
**Infrastructure**: Cloudflare D1 (Relational SQLite), Cloudflare R2 (AES-256-GCM Encrypted Object Storage), FastAPI Python Backend, Next.js 16+ Tailwind Frontend.

---

## 1. Pre-Flight Verification

Before deploying to production, run the automated pre-flight readiness audit:

```bash
python scripts/deploy_check.py
```

Ensure the output displays `RESULT: Production Readiness Audit PASSED`.

---

## 2. Cloudflare D1 & R2 Setup

### Step 1: Create Cloudflare D1 Relational Database
```bash
npx wrangler d1 create beacon-compliance-d1
```
Copy the generated `database_id` into `wrangler.toml` and `.env`.

### Step 2: Automated Idempotent Database Migrations
Wrangler tracks applied migration SQL files in the `d1_migrations` table in Cloudflare D1. Migrations execute automatically in CI/CD before deployment:

```bash
# Manual CLI migration execution (if needed)
npx wrangler d1 migrations apply beacon-compliance-d1 --remote --account-id=<ACCOUNT_ID>
```

#### Cloudflare API Token & Account ID Configuration (Required for CI/CD)
To prevent Cloudflare API Code 7403 (`The given account is not valid or is not authorized to access this service`), verify the following in GitHub Repository Secrets:

1. **`CLOUDFLARE_ACCOUNT_ID`**: Found in Cloudflare Dashboard URL (`dash.cloudflare.com/<ACCOUNT_ID>`) or under Account Overview on the right sidebar.
2. **`CLOUDFLARE_API_TOKEN`**: Create under **Cloudflare Dashboard** -> **My Profile** -> **API Tokens** with these permissions:
   - **Account** -> **D1** -> **Edit**
   - **Account** -> **Workers R2 Storage** -> **Edit**
   - **Account** -> **Workers Scripts** -> **Edit**
   - **Account** -> **Account Details** -> **Read**
   - **Account Resources**: Include -> *All accounts* (or select your specific account).

### Step 3: Create Cloudflare R2 Object Storage Bucket
```bash
npx wrangler r2 bucket create beacon-compliance-r2-prod
```

---

## 3. Environment Variables Configuration

Copy `.env.template` to `.env` (or set secrets in Cloudflare Workers Dashboard):

```bash
cp .env.template .env
```

Use the safe credentials protocol to populate required production keys:
- `AES_256_GCM_SECRET`: Minimum 32-byte secret for R2 encryption at rest.
- `TRUSTEE_SIGNATURE_SALT`: Secret salt for per-trustee HMAC sign-off.
- `GROQ_API_KEY`: API key for Gemma 4 26B and gpt-oss-20b classification models.
- `RESEND_API_KEY`: API key for trustee notification emails.

---

## 4. FastAPI Backend Deployment

### Local Development / Server Hosting
```bash
uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 5. Next.js Frontend Deployment (Cloudflare Pages / Vercel)

### Build & Export Static Web App
```bash
cd frontend
npm install
npm run build
```

Deploy the `.next` or `out` folder to Cloudflare Pages or Vercel.

---

## 6. Trustee Onboarding & Verification

1. Provision trustee secrets for Chair, Secretary, and Treasurer roles.
2. Verify that trustee sign-off HMAC modal functions correctly via `POST /api/signoff/approve`.
3. Confirm that gross income $\ge £250,000$ hard-halt alert banner triggers reliably on high-income test payloads (Red-Line 5).
