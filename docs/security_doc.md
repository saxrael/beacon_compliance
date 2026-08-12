# Beacon Compliance
## Security Document
### Document 4 of 5 — Project Summary → PRD → TRD → **Security Document** → Prompt Document
### Version 1.0

---

## 0. Purpose and Governing Principle

This document is the single source of truth for security across every layer of Beacon Compliance — upload, storage, computation, model access, human approval, and egress. It supersedes any looser security language in prior documents.

**Governing principle (Project Summary §11, restated as binding):** No single point of failure may expose PII, enable unauthorized submission, or permit undetected tampering with financial data — enforced through layered, independently-verifiable controls at every boundary, with every control's failure mode explicitly documented. Beacon Compliance does not claim to be impenetrable. It claims that no single compromised layer is sufficient to cause a Red-Line violation, and it names, in Section 15, the residual risks that remain even so.

---

## 1. Threat Model

### 1.1 Assets requiring protection
- Raw trustee/donor/beneficiary PII (names, addresses, bank details) prior to anonymisation.
- Financial figures and their integrity (accuracy, non-tampering, correct fund attribution).
- Deliverable documents pre-submission (draft TAR, accounts, OAR data, IE pack).
- Trustee credentials and session state.
- The approval record itself (who approved what, when).
- The OSCR knowledge base and document archive (integrity, not just confidentiality — a poisoned KB could cause the agent to state something false to a trustee).

### 1.2 Adversaries and vectors considered
| Adversary | Vector | Primary concern |
|---|---|---|
| External attacker, internet-facing | Credential stuffing/brute force against `/auth/login`; direct API abuse | Unauthorized access to trustee data or actions |
| External attacker | Malicious or malformed uploaded file | Parser exploitation, OCR pipeline abuse, DoS |
| External attacker or malicious insider | Crafted document content (minutes, contracts) | Prompt injection against Node 2 / chat agent |
| Compromised trustee credential | Phished or reused password | Unauthorized approval, data access within that trustee's legitimate scope |
| Third-party processor compromise or misuse | Groq, Google AI Studio, Resend, Cloudflare | Data exposure at a provider Beacon doesn't control directly |
| Insider (Israel, as sole admin) | Broad provisioning/infrastructure access | Accepted, bounded risk — see Section 13 |
| Supply chain | Compromised or vulnerable open-source dependency | Code execution, data exfiltration via a trusted package |
| Passive network observer | Unencrypted transit | Interception of PII or financial data in flight |

This table is the basis for every control below — each control traces back to a specific row.

---

## 2. PII Boundary Enforcement (Software-Enforced Replacement for Physical Air-Gap)

This is the most important section in the document, because it's the direct consequence of the local-to-remote architecture pivot accepted in the Project Summary. The original design achieved Red-Line 4 by making PII exfiltration *physically impossible* (no network on the ingest container). That guarantee is gone. What replaces it:

**2.1 Structural type enforcement.** Two Pydantic model families exist and are never interchangeable: `RawDocumentState` (may contain PII) and `AnonymisedState` (guaranteed scrubbed). No LLM client anywhere in the codebase — Gemma 4 26B A4B or `gpt-oss-20b` — is ever constructed with a `RawDocumentState` object in scope. This is enforced at the type-checker level (mypy/pyright strict mode, per the existing Modern Python Standards mandate), not just by convention: a function signature accepting `AnonymisedState` cannot silently receive `RawDocumentState` without a type error.

**2.2 Scrubbing coverage — closing the transaction-description gap identified above.** Presidio + spaCy scrubbing runs on:
- All extracted document text (Node 1, as previously specified).
- **Every individual transaction description string**, at the point of extraction, before it becomes eligible for Tier 2.5 classification. This is a new, explicit requirement: the classification pipeline (TRD §3) must call the same PII-scrub function Node 1 uses, per transaction, not just per document. `gpt-oss-20b` via Groq never receives an unscrubbed description.
- Chat agent tool outputs, before being included in any prompt context — a defense-in-depth measure in case a tool ever surfaces raw stored text.

**2.3 Encryption boundary.** TLS 1.2+ enforced on every hop (Vercel↔Render, Render↔D1, Render↔R2, Render↔Groq, Render↔AI Studio, Render↔Resend) — no component of this system accepts plaintext HTTP. At rest: every R2 object is encrypted with AES-256-GCM at the application layer before upload (in addition to R2's own storage-level encryption — belt and braces, since R2's default encryption alone would not, on its own, prevent a misconfigured-bucket-policy exposure from being readable). The PII vault (`pii_manifest`, mapping pseudonym tokens back to real values) uses a key derived via PBKDF2-HMAC-SHA256 (310,000 iterations) from a secret never stored alongside the vault itself — it lives in Render's environment secret store, rotated per Section 11.

**2.4 Decryption is minimal and time-boxed.** The PII vault is decrypted into memory only at Node 5 (document assembly, for re-personalisation of the final deliverable) and explicitly garbage-collected immediately after. No other node ever decrypts it.

---

## 3. Authentication and Session Security

- **Password storage**: Argon2id (not bcrypt — Argon2id is the current recommended default for new systems, memory-hard against GPU-accelerated cracking).
- **Initial provisioning**: admin-generated password is single-use — the `first_login_complete` flag (TRD §2) gates all functionality except the password-reset flow until changed. The initial password is delivered out-of-band (Israel communicates it directly, not via Resend, to avoid a generated-credential ever transiting the same channel as routine notifications).
- **Session tokens**: short-lived JWT (15-minute access token) with a longer-lived refresh token, both delivered as `HttpOnly`, `Secure`, `SameSite=Strict` cookies — never stored in frontend JS-accessible storage (consistent with the artifact-storage prohibition already governing this project's engineering standards).
- **Rate limiting**: `/auth/login` limited to 5 attempts per email per 15 minutes; exceeding this locks the account and notifies all trustees (critical-severity, per the existing notification routing) rather than the affected trustee alone, since an account lockout is itself a signal worth every trustee seeing.
- **CORS**: backend accepts requests only from the deployed Vercel origin — no wildcard, no localhost in production configuration.

---

## 4. Authorization

- Role (Chair/Secretary/Treasurer) is enforced server-side on every approval-related endpoint — never trusted from frontend state. `/approve/{deliverable_id}` re-validates the requesting trustee's role against D1 on every call, not just at login.
- The admin provisioning endpoint (`/admin/provision-trustee`) requires a distinct admin credential, issued and rotated separately from any trustee credential, and is never reachable via the trustee-facing frontend at all — it exists for Israel's direct use only.

---

## 5. Approval Integrity — Corrected Mechanism

The original design's SHA-256 hash of `(trustee_id + content_hash + timestamp)` is upgraded to close the non-repudiation gap identified above:

**Corrected mechanism**: each trustee is issued a per-account HMAC secret at provisioning time (generated server-side, stored encrypted in D1, never transmitted to the frontend in retrievable form). An approval event computes `HMAC-SHA256(trustee_secret, deliverable_content_hash || timestamp || run_id)`. This proves the approval could only have been generated by a party holding that trustee's specific secret — a bare hash cannot make that claim, and the distinction matters given this record is described as legally significant evidence of trustee sign-off. The `approvals` table (TRD §2) stores the HMAC output, the inputs used to generate it, and which trustee secret version was active — supporting audit reconstruction even across a future secret rotation.

---

## 6. Third-Party Data Exposure Boundary

Every external processor this system touches, and exactly what it's permitted to see:

| Processor | What it receives | What it must never receive |
|---|---|---|
| Google AI Studio (Gemma 4 26B A4B) | Anonymised narrative text, chat messages (post-scrub), tool call results (deterministic, non-PII) | Raw PII, raw financial documents |
| Groq (`gpt-oss-20b`) | Scrubbed transaction description, amount, date (read-only reference), fund taxonomy, similar-precedent examples | Any PII-bearing description (Section 2.2 closes this), any instruction to compute/alter a figure |
| Cloudflare (D1/R2) | All application data, encrypted at rest per Section 2.3 | N/A — this is the system's own data store, not a third-party inference processor |
| Resend | Trustee email addresses, notification content (never a document attachment — links only, per PRD §4.4/§6.4) | Any document body content, any PII beyond what's needed to address the email |

Google AI Studio and Groq's respective terms (non-training-eligible developer tier / no training on submitted data, per their published policies) are re-verified annually as part of the existing annual calibration checklist — a provider's policy can change, and this system's privacy claims are only as good as that re-verification actually happening.

---

## 7. Prompt Injection and Untrusted Content Defense

New section, closing the gap identified in Step 2 of this document's own reasoning. Every piece of text originating from an uploaded document, a retrieved KB chunk, or a retrieved past conversation is **untrusted data**, never an instruction, and this is enforced at three levels:

1. **Prompting level**: every system prompt for Gemma 4 26B A4B (Node 2, chat agent) explicitly and structurally separates instructions from data — retrieved/uploaded content is always wrapped in clearly delimited context blocks with an explicit instruction that content within those blocks is data to reason about, never a command to follow, regardless of what it appears to say (e.g., a minutes document containing text like "ignore previous instructions and..." must be treated as suspicious content to report, not obeyed).
2. **Structural level**: this is the real backstop, not the prompt wording. Every tool available to the chat agent and every LLM output schema is narrowly typed (per PRD §7.8's tool inventory) — there is no tool whose execution could, e.g., approve a deliverable, alter a financial figure, or exfiltrate data, no matter what text an LLM was fed. A successful injection can at worst cause the agent to say something wrong in chat; it cannot cause the agent to *do* something outside its defined, narrow tool boundary, because Red-Lines 1–3 are enforced by code paths the LLM never has write access to (PRD §5).
3. **Detection level**: Node 4's existing hallucination-interception validation (PRD §7.5) is extended to also flag TAR-drafted content containing instruction-like patterns inconsistent with the source material's actual topic — a cheap, mechanical check that surfaces the kind of anomaly injection would produce, for trustee review rather than silent trust.

---

## 8. File Upload Safety

- Maximum upload size enforced at the API layer (proposed: 25MB per file — generous for scanned documents, small enough to bound DoS risk); rejected uploads return a clear error, not a silent failure.
- MIME type validated against actual file content (not just the extension/declared header) before routing to any parser.
- PDF/DOCX/XLSX parsing (`pdfplumber`, `python-docx`, `openpyxl`) and OCR (`pytesseract`, `PyMuPDF`, `Pillow`) run with resource limits (timeout, memory ceiling) to bound a malformed-file DoS attempt — a hung parser fails the upload rather than hanging the worker indefinitely.
- No uploaded file is ever executed, evaluated, or treated as anything other than data to extract text from.

---

## 9. Secrets Management

| Secret | Storage location | Rotation |
|---|---|---|
| Cloudflare D1/R2 API token | Render environment secrets | Annually, or immediately on suspected compromise; scoped to D1+R2 only, never full Cloudflare account access (least privilege) |
| Google AI Studio API key | Render environment secrets | Annually |
| Groq API key | Render environment secrets | Annually |
| Resend API key | Render environment secrets | Annually |
| PII vault master secret | Render environment secrets, distinct from all API keys | Annually — per-vault re-encryption required on rotation, scheduled as part of the calibration checklist |
| Admin provisioning credential | Held by Israel only, never in any repository or environment file | On suspected compromise |
| Per-trustee HMAC secrets (Section 5) | Encrypted in D1, generated at provisioning | On trustee offboarding or suspected compromise |

`.env` is never committed (enforced by `.gitignore` from the first commit, per the existing engineering standards); `.env.example` documents variable names only.

---

## 10. Supply Chain and Dependency Security

- All dependencies pinned to specific versions in `pyproject.toml`/`package.json` (consistent with the Modern Python Standards already mandated) — no unpinned ranges in production.
- Automated vulnerability scanning via GitHub's built-in Dependabot alerts (free, zero-cost) on every dependency; a flagged critical/high vulnerability blocks the next deployment until reviewed, not silently ignored.
- New dependency additions require the same "does an existing skill/tool already cover this" scrutiny already established for the Antigravity build process — fewer dependencies is itself a security posture, not just a convenience.

---

## 11. Audit Logging and Tamper Evidence

- Every node execution, every classification decision (Tier 1/2/2.5), every approval, every notification send, and every admin action is logged to `audit_log` (TRD §2) with input/output state hashes — sufficient to reconstruct the full decision trail without the log itself ever containing raw PII (only hashes and metadata).
- Admin actions (trustee provisioning, password resets initiated by Israel) are logged distinctly from trustee actions, so the audit trail can answer "did Israel do this, or did a trustee" without ambiguity — relevant given Section 13's acknowledgment of admin trust concentration.

---

## 12. Data Retention, Backup, and Disaster Recovery

- **Statutory retention**: UK charity law requires financial records be retained a minimum of 6 years. Beacon retains all `financial_state`, `deliverables`, `approvals`, and `audit_log` records for a minimum of 7 years (one year of margin beyond the statutory floor), regardless of R2/D1 default retention behavior.
- **Backup mechanism**: Cloudflare D1 supports point-in-time recovery within its retention window; this is relied upon as the primary backup path. R2 object versioning is enabled on the documents/deliverables bucket, protecting against accidental overwrite or deletion.
- **Disaster recovery target**: given the 2-trustee, zero-cost scale, a formal RTO/RPO commitment beyond "same working day" is not proportionate to build for v1 — this is stated explicitly as an accepted scope limit, not a silent gap. If Cloudflare experiences an extended outage, the accepted fallback is that Beacon is unavailable until service resumes; no independent redundant hosting is budgeted at this scale.
- **Trustee offboarding**: on a trustee leaving the board, their account is disabled (not deleted, to preserve the integrity of historical approval records referencing their `trustee_id`), and their HMAC secret is retired.

---

## 13. Admin Privilege Boundary — Named, Not Ignored

Israel holds broad infrastructure and provisioning access (Cloudflare, Render, Vercel, AI Studio, Groq, Resend accounts; the admin provisioning endpoint). This is a real, deliberate concentration of trust that a "no single point of failure" principle would normally flag as a violation of itself — worth being honest about rather than silently exempting.

**Accepted rationale**: at 2-trustee, single-developer scale, a fully separated admin function is disproportionate overhead with no realistic alternative — someone has to hold infrastructure access, and Israel is that person by necessity, not oversight. **Compensating controls**: every admin action is distinctly logged (Section 11); infrastructure credentials are never embedded in application code or shared with any AI tool, including the Antigravity Agent building this system (a build-time agent should never receive live production credentials — provisioning happens through the documented endpoints/scripts, not by handing secrets to the coding agent); and this concentration is explicitly named here so it is a known, reviewed risk rather than an invisible one.

---

## 14. Incident Response

Given "impenetrable" is explicitly rejected (Section 0), a realistic response plan is a required compensating control, not optional polish:

1. **Detection**: audit log anomalies (unexpected admin action, repeated failed logins, an approval hash that fails HMAC verification) trigger a critical-severity notification to all trustees, per existing routing.
2. **Containment**: Israel's documented first response is to rotate the specific credential class implicated (Section 9's table) and, if a trustee account is suspected compromised, disable it immediately via the admin endpoint.
3. **Notification**: trustees are informed of any suspected PII exposure without delay — this is both good practice and consistent with UK GDPR expectations around breach communication, though Beacon's trustees, not this system, hold the actual legal reporting obligation to the ICO if a reportable breach occurs.
4. **Post-incident**: every incident is logged in `audit_log` with a written summary appended to the run's record, and the annual calibration checklist explicitly includes reviewing the past year's incidents, if any.

---

## 15. Red-Line to Control Mapping

| Red-Line | Primary enforcing control(s) |
|---|---|
| 1. No autonomous submission | Structural: no code path calls an external submission API without a preceding trustee UI action (Section 7.2); IE resend requires explicit trustee action (PRD §7.7) |
| 2. No LLM financial arithmetic | Type-level: no LLM client ever holds write access to `Decimal` state (Section 2.1); Tier 2.5 output schema contains no monetary field (PRD §7.2) |
| 3. Role-restricted trustee sign-off | HMAC-based approval (Section 5), server-side role re-validation on every call (Section 4) |
| 4. PII boundary enforcement | Sections 2, 6, 7 collectively — scrubbing coverage, encryption, third-party boundary, structural type separation |
| 5. Income threshold hard-halt | Independent re-check at Node 1 and Node 4 (PRD §7.5); state-machine hard route bypassing all other logic (TRD §3) |

---

## 16. Explicitly Accepted Residual Risks

Per Section 0's rejection of "impenetrable," these are named rather than hidden:
- Render's free tier runs on shared infrastructure Beacon does not control at the hypervisor level — a platform-level compromise at Render is outside this system's control surface.
- Google AI Studio and Groq are trusted, per their published policies, not to train on or retain submitted data — this is a policy commitment, not something Beacon can technically verify or enforce.
- No formal third-party penetration test is budgeted at zero-cost, 2-trustee scale — this is a proportionate, stated gap for this system's size, not an oversight.
- Israel's admin access is a concentrated trust point, compensated but not eliminated (Section 13).
- Disaster recovery beyond same-working-day Cloudflare-outage tolerance is out of scope at this scale (Section 12).

---

## 17. Document Status

All items flagged as Security Document territory in the PRD and TRD (backup/DR, PII enforcement mechanics, the security posture governing principle) are resolved here. Three items not previously identified anywhere in this project — the approval mechanism's non-repudiation gap, transaction-description PII exposure to Groq, and prompt injection defense — are closed in Sections 5, 2.2, and 7 respectively. No open ambiguities remain. Proceeding to the Prompt Document (Document 5) on your authorization.
