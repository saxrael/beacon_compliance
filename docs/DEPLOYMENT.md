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
npx wrangler d1 migrations apply beacon-compliance-d1 --remote
```

#### Cloudflare API Token & Account ID Configuration (Required for CI/CD)
> [!IMPORTANT]
> **R2 (Buckets) vs D1 (Databases) Scope Distinction**:
> Admin permissions on **R2 Buckets** (Object Storage) do **NOT** grant access to **D1 Databases** (Relational SQLite). If your token only has Workers R2 permissions, calls to `/accounts/.../d1/database/.../query` fail with Cloudflare Error `7403`.

To resolve Cloudflare API Code 7403 (`The given account is not valid or is not authorized to access this service`), update your API Token under **Cloudflare Dashboard** -> **My Profile** -> **API Tokens**:

1. **`CLOUDFLARE_ACCOUNT_ID`**: Found in Cloudflare Dashboard URL (`dash.cloudflare.com/<ACCOUNT_ID>`) or under Account Overview on the right sidebar.
2. **`CLOUDFLARE_API_TOKEN`**: Must include **D1 -> Edit** permission explicitly:
   - **Account** -> **D1** -> **Edit** *(Required for `wrangler d1 migrations apply`)*
   - **Account** -> **Workers R2 Storage** -> **Edit** *(Required for R2 Storage Buckets)*
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

## 4. FastAPI Backend Deployment (Oracle Cloud Infrastructure — OCI Always-Free VM)

The backend is deployed as a Docker container on a dedicated **OCI Always-Free VM** (1 OCPU, 1GB RAM, Ubuntu 22.04 LTS). Both Presidio SpaCy NLP and deterministic regex engines run natively with zero OOM pressure.

### Step 1: Launch a Dedicated OCI Compute Instance
> [!IMPORTANT]
> **New Instance Required**: You MUST launch a new compute instance specifically for Beacon Compliance to ensure dedicated 1GB RAM resources.

1. Log into **Oracle Cloud Console** -> **Compute** -> **Instances** -> Click **Create Instance**.
2. **Instance Name**: `Beacon Compliance`.
3. **Image**: Select `Ubuntu 22.04 LTS` (or `Ubuntu 24.04 LTS`).
4. **Shape**: Select `VM.Standard.A1.Flex` (1 OCPU, 1 GB RAM) or `VM.Standard.E2.1.Micro` (1 OCPU, 1 GB RAM).
5. **Networking (VCN)**:
   - You can select an **existing VCN** from your compartment OR select **Create new virtual cloud network**. (Using an existing VCN is completely fine as long as you open ports on its Security List).
   - Ensure **Assign a public IPv4 address** is set to **Yes**.
6. **Add SSH Keys**: Generate an SSH key pair or upload your existing public key (`~/.ssh/id_rsa.pub`). Save the private key securely on your local machine.
7. Click **Create**. Once active, note the **Public IP Address** (e.g. `129.159.x.x`).

---

### Step 2: Open Ingress Ports in OCI VCN Security List & VM Firewall
1. In Oracle Cloud Console, navigate to **Networking** -> **Virtual Cloud Networks** -> Select the VCN assigned to `beacon-compliance-vm`.
2. Click **Security Lists** -> Select the **Default Security List** (or the active Security List for your subnet).
3. Click **Add Ingress Rules**:
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: `TCP`
   - **Destination Port Range**: `8000, 80, 443`
4. SSH into your new VM (`ssh ubuntu@<OCI_PUBLIC_IP>`) and open host firewall ports:
   ```bash
   sudo ufw allow 8000/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

---

### Step 3: OCI VM Instance Preparation (Docker Setup)
On your OCI Ubuntu VM instance:
```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```
*(Log out of SSH and log back in for `docker` group membership to take effect)*.

---

### Step 4: Dynamic DNS & Automated Caddy HTTPS Reverse Proxy
1. **Register DuckDNS Subdomain**: Go to [duckdns.org](https://www.duckdns.org/), create a free domain e.g. `beacon-compliance-api.duckdns.org`, and point it to your OCI VM Public IP (`129.x.x.x`).
2. **Install Caddy on OCI VM**:
   ```bash
   sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
   sudo apt update && sudo apt install caddy
   ```
3. **Automated Caddy & Docker Compose Deployment**:
   The GitHub Actions workflow automatically creates a project directory at `~/beacon_compliance` on your OCI VM containing `docker-compose.yml` and `.env`, and reloads Caddy automatically on every push!

4. **Useful Machine Commands on OCI VM**:
   ```bash
   # Navigate to project directory
   cd ~/beacon_compliance

   # View container logs
   docker compose logs -f

   # Check container status
   docker compose ps

   # Restart backend service
   docker compose restart
   ```

---

### Step 5: Complete GitHub Secrets Matrix & Cleanup

#### GitHub Secrets to ADD (Settings ➔ Secrets and variables ➔ Actions):
| Secret Name | Description / Value |
|---|---|
| `OCI_HOST` | OCI VM Public IP Address (e.g. `129.159.x.x`) |
| `OCI_USERNAME` | `ubuntu` |
| `OCI_SSH_KEY` | Contents of your private SSH key (`id_rsa`) |
| `DUCKDNS_DOMAIN` | Your DuckDNS domain (e.g. `beacon-compliance-api.duckdns.org`) |
| `SMTP_HOST` | Direct SMTP Server (e.g. `smtp.gmail.com` or `mail.pottershouse.org.uk`) |
| `SMTP_PORT` | `587` (STARTTLS) or `465` (SSL) |
| `SMTP_USERNAME` | SMTP account email |
| `SMTP_PASSWORD` | SMTP password / App password |
| `SMTP_USE_TLS` | `true` |
| `AES_256_GCM_SECRET` | 32-byte production encryption secret |
| `TRUSTEE_SIGNATURE_SALT` | Trustee HMAC signature salt |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account ID |
| `CLOUDFLARE_D1_DATABASE_ID` | `ae9bc1a9-395d-468a-891e-172587c73189` |
| `CLOUDFLARE_R2_BUCKET_NAME` | `beacon-compliance-r2-prod` |
| `R2_ACCESS_KEY_ID` | R2 Access Key ID |
| `R2_SECRET_ACCESS_KEY` | R2 Secret Access Key |
| `ALLOWED_ORIGINS` | `https://your-vercel-app.vercel.app,http://localhost:3000` |
| `GROQ_API_KEY` | Groq API Key |
| `OPENROUTER_API_KEY` | OpenRouter API Key |
| `NOTIFICATION_FROM_EMAIL` | `testbackend00@gmail.com` |
| `LANGFUSE_ENABLED` | `false` (or `true` if enabled) |
| `LANGFUSE_PUBLIC_KEY` | Langfuse Public Key |
| `LANGFUSE_SECRET_KEY` | Langfuse Secret Key |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` |

#### Secrets to REMOVE from GitHub Secrets:
- **`RENDER_DEPLOY_HOOK_URL`**: Obsolete. Delete from GitHub Secrets.
- **`RESEND_API_KEY`**: Obsolete. Resend is replaced by direct SMTP. Delete from GitHub Secrets.

---

### Step 6: Update `NEXT_PUBLIC_API_URL` on Vercel
1. Go to **Vercel Dashboard** ➔ Select your Frontend Project ➔ **Settings** ➔ **Environment Variables**.
2. Set `NEXT_PUBLIC_API_URL` to `https://beacon-compliance.duckdns.org` (or `http://<OCI_PUBLIC_IP>:8000`).
3. Trigger a redeploy on Vercel.

---

## 5. Next.js Frontend Deployment (Cloudflare Pages / Vercel)

### Build & Export Static Web App
```bash
cd frontend
npm install
npm run build
```

Deploy the `.next` or `out` folder to Cloudflare Pages or Vercel.

#### Vercel GitHub Actions Secrets Configuration
To ensure automated deployment passes, configure the following 3 secrets in **GitHub Repository Settings -> Secrets and variables -> Actions**:

1. **`VERCEL_TOKEN`**: Generate under Vercel Dashboard -> **Account Settings** -> **Tokens**.
2. **`VERCEL_ORG_ID`**: Found in Vercel Dashboard -> **Team Settings** -> **General** (or `.vercel/project.json` `orgId`).
3. **`VERCEL_PROJECT_ID`**: Found in Vercel Dashboard -> Select Project -> **Settings** -> **General** -> **Project ID** (`prj_...`).

## 6. Trustee Onboarding & Verification

1. Provision trustee secrets for Chair, Secretary, and Treasurer roles.
2. Verify that trustee sign-off HMAC modal functions correctly via `POST /api/signoff/approve`.
3. Confirm that gross income $\ge £250,000$ hard-halt alert banner triggers reliably on high-income test payloads (Red-Line 5).
