# Beacon Compliance
## Product Requirements Document
### Document 2 of 5 — Project Summary → **PRD** → TRD → Security Document → Prompt Document
### Version 1.0 | Target Charity: Potter's House Christian Mission UK (SCIO, SC054652)

---

## 0. Relationship to the Project Summary

This PRD assumes the Project Summary (Document 1) as settled context and does not re-litigate anything confirmed there. Its job is to specify, functionally and exhaustively, *what every part of the system must do* — deliverable by deliverable, node by node — so that the TRD (Document 3) has an unambiguous functional target to design schemas and infrastructure against, and so the Prompt Document (Document 5) has an unambiguous specification to hold the Antigravity Agent to.

---

## 1. OSCR Regulatory Boundary Analysis

### 1.1 Legal Form
Potter's House Christian Mission UK is a Scottish Charitable Incorporated Organisation (SCIO), charity number SC054652, established under the Charities and Trustee Investment (Scotland) Act 2005 and the SCIO Regulations 2011. SCIOs file exclusively with OSCR — there is no Companies House obligation, no confirmation statement, and trustee liability is capped at the SCIO constitution's indemnity provision.

### 1.2 Estimated Income Tier and Statutory Obligations

| Obligation | Statutory Basis | Threshold / Deadline |
|---|---|---|
| Online Annual Return (OAR) | s.44 Charities & Trustee Investment (Scotland) Act 2005 | All SCIOs — within 9 months of financial year-end, via OSCR Online portal |
| Trustees' Annual Report (TAR) | Charities Accounts (Scotland) Regulations 2006, Reg. 9 | All SCIOs — accompanies accounts |
| Annual Accounts (Receipts & Payments) | 2006 Regs., Reg. 5 & Schedule 1 | Gross income < £250,000 — R&P format mandated |
| Independent Examination Report | 2006 Regs., Reg. 10 | Gross income ≥ £25,000 and < £500,000 |
| Statutory Audit | 2006 Regs., Reg. 10(2) | **Not applicable at estimated scale** — triggered only at ≥£500,000 income or ≥£3.26m assets |

Estimated income band: **£50,000–£200,000**, placing SC054652 firmly in R&P/Independent-Examination territory. If this is ever exceeded (≥£250,000), Beacon halts R&P generation per Red-Line 5 rather than producing a document that would be legally insufficient — full accrual SORP accounting is explicitly out of scope (Project Summary §12).

### 1.3 Receipts & Payments (R&P) Structure
Per Schedule 1 of the 2006 Regulations, the accounts comprise: (a) a Receipts & Payments Account segregated by fund (Unrestricted, Restricted, Endowment); (b) a Statement of Balances reconciling opening/closing bank balances; (c) Notes to the Accounts (accounting policies, trustee remuneration, related-party transactions, material items). Beacon must support at minimum: an Unrestricted General Fund, one or more Restricted Mission Funds, and a Designated Events Fund — the fund set is configuration-driven, not hardcoded, since new funds may be created in future years.

### 1.4 TAR Mandatory Content
Per OSCR's simplified reporting framework for SCIOs under £250k: Reference & administrative information; Trustees' declaration; Structure, governance & management; Objectives & activities; Achievements & performance; Financial review. Field-level generation rules for each are specified in §7 below.

---

## 2. Target Charity Profile

| Field | Value |
|---|---|
| Registered Name | Potter's House Christian Mission UK |
| Charity Number | SC054652 |
| Legal Form | Scottish Charitable Incorporated Organisation (SCIO) |
| Registered Address | 5B Beachmont Court, Dunbar, Scotland, UK |
| Regulatory Jurisdiction | OSCR exclusively |
| Estimated Income Band | £50,000–£200,000 |
| Governing Document | SCIO Constitution (held at OSCR register) |
| Executive Roles (v1) | Chair, Secretary, Treasurer |
| Trustee Accounts (v1) | 2, admin-provisioned |

All values above are held in system configuration, not hardcoded into application logic, to preserve the future multi-tenant path named in the Project Summary without requiring it now.

---

## 3. Deterministic vs. Probabilistic Boundary Matrix

The single highest-risk failure mode in the system is an AI model generating, altering, or interpreting a financial figure. Updated from the original architecture to reflect every classification/extraction refinement closed during scoping:

| Task Type | Execution Mode | Model (if applicable) |
|---|---|---|
| Raw document text/table extraction | DETERMINISTIC (`pdfplumber`, `python-docx`, `openpyxl`, `pandas`) | None |
| Image/scanned document OCR | DETERMINISTIC, confidence-gated (`pytesseract` + `Pillow` + `PyMuPDF`) | None — low-confidence numeric extractions route to mandatory trustee review |
| PII detection & scrubbing | DETERMINISTIC (Presidio + spaCy) | None |
| Transaction fund/category — Tier 1 | DETERMINISTIC (rule/keyword match) | None |
| Transaction fund/category — Tier 2 | HUMAN DECISION, permanently learned into Tier 1 | None |
| Transaction fund/category — Tier 2.5 | PROBABILISTIC SUGGESTION, human-confirmed before use | `openai/gpt-oss-20b` (Groq) |
| All financial arithmetic (sums, reconciliation, totals) | DETERMINISTIC (Python/Decimal) | None — zero exceptions, zero circumstances |
| TAR narrative prose (4 whitelisted fields only) | PROBABILISTIC (LLM, anonymised input only) | Gemma 4 26B A4B |
| Cross-validation & error log | DETERMINISTIC (Python assertions) | None |
| OAR form data population | DETERMINISTIC (Python field mapper) | None |
| Chat agent tool responses | Tool-mediated — underlying data is always deterministic; only response phrasing is generated | Gemma 4 26B A4B |
| Cognitive memory (episodic summary, fact extraction) | PROBABILISTIC, financial facts excluded from autonomous extraction | Gemma 4 26B A4B |
| Knowledge base retrieval | DETERMINISTIC retrieval (hybrid RRF), probabilistic synthesis of the response only | Gemma 4 26B A4B |
| Human review & approval | MANDATORY HUMAN-IN-THE-LOOP, role-restricted | N/A |

---

## 4. OSCR Deliverables — Functional Requirements

### 4.1 Deliverable 1 — Online Annual Return (OAR)
The system produces a pre-population data sheet (field-mapped to OSCR's OAR schema) for trustee review and manual portal entry. **The system must never auto-submit to the OSCR portal under any circumstance** (Red-Line 1). Every field is `DATA_INJECTED` or `FIXED` — no field in the OAR is ever LLM-authored, since it is a structured data submission, not a narrative document.

### 4.2 Deliverable 2 — Trustees' Annual Report (TAR)
Six-section document per §1.4. Document Contract field classification (confirmed in the Project Summary, restated here as the binding functional spec):

| Section | Classification | Detail |
|---|---|---|
| 1. Reference & administrative information | 100% `DATA_INJECTED`/`FIXED` | Charity name, SCIO number, address, trustee names, bankers, IE details — pure lookup |
| 2. Financial review | Mixed | Income/expenditure figures `DATA_INJECTED`; reserves policy `FIXED`/`DATA_INJECTED` (restated, not rewritten, unless trustees actually change policy); principal risks narrative `LLM_DRAFTED` |
| 3. Structure, governance & management | Mixed | Legal form/constitutional basis `FIXED`; trustee recruitment/induction and organisational structure description `LLM_DRAFTED` |
| 4. Objectives & activities | Mixed | Charitable purposes `FIXED`, pulled verbatim from the SCIO constitution — never paraphrased; activities-advanced-purposes narrative `LLM_DRAFTED` |
| 5. Achievements & performance | Mixed, sentence-level | Counts/figures (attendance, outputs) `DATA_INJECTED` via `[FIGURE_INJECTED]` token protocol; connective narrative `LLM_DRAFTED` |
| 6. Trustees' declaration | 100% `FIXED` | Prescribed legal declaration wording; only date/signatory names `DATA_INJECTED` |

Total `LLM_DRAFTED` surface across the entire TAR: exactly four narrative fields (governance description, purposes-to-activities narrative, achievements connective narrative, principal-risks narrative). Every `LLM_DRAFTED` field is subject to Node 4 hallucination-interception validation before merge (§7.4).

### 4.3 Deliverable 3 — Annual Accounts (Receipts & Payments)
Fully deterministic. Produced exclusively by Node 3 (§7.3) from raw bank transaction data, after Tier 1/2/2.5 fund classification (§7.2). Zero LLM touches any figure at any stage. Structure: R&P Account (by fund), Statement of Balances, Notes to the Accounts.

### 4.4 Deliverable 4 — Independent Examiner's Working Paper Pack
Structured evidence package: pre-filled OSCR IE Report template, R&P summary, a sample transaction list, and the system's validation report. Delivered per §7.7 (secure signed R2 link via Resend, 14-day default expiry, regenerable on demand, fully re-usable — never a one-shot attachment).

---

## 5. Compliance Red-Lines (Functional Enforcement Detail)

Restated from the Project Summary with the specific enforcement mechanism each requires:

1. **No autonomous submission or transmission.** Enforced by: no code path in the system ever calls an OSCR API, a banking API, or sends an external message without a preceding trustee-initiated UI action. This applies equally to the IE pack resend (§4.4) and any future notification feature.
2. **No LLM financial arithmetic.** Enforced by: Node 3 and the financial-arithmetic tool layer are the only code paths permitted to touch `Decimal`-typed monetary state; no LLM client in the system is ever constructed with write access to that state, and no tool schema exposed to any LLM includes a monetary field as an output.
3. **Mandatory, role-restricted trustee sign-off.** Enforced by: every deliverable's `submission_package_path` remains `None` until at least two approvals, from trustees holding Chair/Secretary/Treasurer roles, are recorded as SHA-256 commitments in the approvals table.
4. **PII boundary enforcement.** Enforced by: Presidio/spaCy scrubbing runs as the mandatory first stage of every document-processing pipeline; a structural type boundary (separate Pydantic models for pre-scrub vs. LLM-eligible state) makes it a type error, not just a convention violation, for raw PII to reach an LLM client.
5. **Income threshold hard-halt.** Enforced by: Node 3 and Node 4 independently re-check gross income against £250,000; either check failing halts the graph and raises a P0 alert regardless of any other validation state.

---

## 6. System Architecture — Functional Overview

*(Component selection is confirmed in the Project Summary §10; this section specifies what each component must functionally do. Full schemas, API contracts, and infrastructure configuration are TRD scope.)*

- **Frontend (Vercel/Next.js)**: Document upload UI (sectioned categories + description field per Project Summary §3.1), chat interface with live streamed agent step visibility, deliverable review/approval UI, trustee onboarding/password-reset flow, notification display, admin views for unclassified-transaction review (Tier 2/2.5).
- **Backend (Render/FastAPI + LangGraph)**: All node execution, all tool execution, all authentication, all scheduled jobs (deadline tracking, Tier 2/3 memory background processing).
- **Data (Cloudflare D1 + R2)**: D1 holds all relational/audit/approval/embedding data; R2 holds all document and deliverable binary objects, encrypted at rest.
- **Models**: Gemma 4 26B A4B (Node 2, chat agent, memory Tiers 2/3) and `openai/gpt-oss-20b` via Groq (Tier 2.5 classification only) — non-overlapping roles, never mutual fallbacks.
- **Notifications (Resend)**: Severity-routed per Project Summary §5.

---

## 7. Node/Component Functional Specifications

### 7.1 Node 1 — Ingest, OCR, and PII Anonymisation
- Accepts uploads across the seven sectioned categories (Project Summary §3.1).
- Document type detection routes to the correct deterministic extractor (`pdfplumber` for text-layer PDFs, `python-docx` for DOCX, `pandas`/`openpyxl` for CSV/XLSX).
- **OCR routing**: any PDF page returning near-empty text extraction, and any directly-uploaded image file, routes to the OCR sub-pipeline (`PyMuPDF` rasterization → `Pillow` preprocessing → `pytesseract` extraction). Per-word confidence scores are retained; any OCR-derived numeric value below a 90% confidence threshold is flagged for mandatory trustee confirmation before it is treated as verified data, displayed alongside a thumbnail of the source region.
- PII detection (Presidio + spaCy `en_core_web_lg`) runs on all extracted text before any data is eligible to leave this node's boundary; entities are pseudonymised with deterministic placeholder tokens; the real-value mapping is encrypted (AES-256-GCM) and never included in any LLM-eligible payload.
- Income threshold check runs here as the first of Node 3/Node 4's independent checks (Red-Line 5).

### 7.2 Transaction Classification Pipeline (Tier 1 / 2 / 2.5)
As specified in Project Summary §3.5. Functional requirements:
- Tier 1 ruleset is YAML-configured and versioned; every classification decision (which rule matched, or that no rule matched) is logged.
- Tier 2 UI presents unmatched transactions with full context (description, amount, date) for manual trustee assignment; the assignment is written back into the Tier 1 ruleset as a new or refined rule before the transaction proceeds to Node 3.
- Tier 2.5 is only invoked for transactions Tier 1 cannot confidently match; it is a suggestion layer, never authoritative. Its prompt context includes the full transaction description, amount/date as read-only reference, the complete current fund taxonomy, and the 3–5 most similar previously-confirmed classifications retrieved via hybrid RAG. Its output schema is strictly `{category: enum, confidence: float, reasoning: str}` — no monetary field exists in the schema. A failed/malformed structured-output call retries once, then falls back to unclassified-pending-manual-review rather than blocking the pipeline.
- Every Tier 2.5 suggestion requires explicit trustee confirm/override before being written into the ruleset, regardless of stated confidence.

### 7.3 Node 3 — Financial Calculations
- Consumes classified transactions (post Tier 1/2/2.5) and produces the full R&P accounts per Schedule 1.
- All arithmetic in Python `Decimal` — never `float` — to eliminate floating-point rounding risk.
- Fund reconciliation assertion: `opening_balance + receipts - payments == closing_balance` per fund; any non-zero residual halts the graph and logs to the audit trail.
- Statement of Balances reconciles to actual bank statement closing balances; discrepancy > £0.01 triggers a validation error.
- Gift Aid reclaim calculation (25p per £1 for UK-taxpayer declarations, where declaration records are provided).
- Outputs are immutable once set: no node downstream of Node 3 may modify `receipts_payments` or `statement_of_balances` state; any attempt raises a structural violation.

### 7.4 Node 2 — Narrative Synthesis (TAR Writer)
- Generates exactly the four `LLM_DRAFTED` fields identified in §4.2, each via a separate, focused prompt (no cross-contamination between sections).
- System prompt enforces the numeric embargo: the model must never output a financial figure, using `[FIGURE_INJECTED]` wherever a number belongs; figures are injected post-generation by a deterministic function, never by the model.
- Self-consistency check: each field generated twice at low temperature; high divergence between runs flags for human review.
- Revision loop: up to 3 cycles on Node 4 rejection, then mandatory escalation to human review (never silent self-correction).

### 7.5 Node 4 — Cross-Validation & Scrutiny (Auditor)
- Independently re-computes every Node 3 total and asserts equality; any discrepancy is a P0 failure.
- OSCR field completeness check on OAR data.
- TAR section completeness and `[FIGURE_INJECTED]` resolution check.
- Numerical-hallucination regex scan on all `LLM_DRAFTED` fields — any digit/currency/percentage pattern not traceable to verified data triggers a revision flag.
- Factual consistency check: trustee names match config; charity number matches SC054652; year-end date consistent across documents.
- Independent re-confirmation of the £250,000 income threshold (Red-Line 5), regardless of Node 3's own check.
- Confidence score = passed/total checks; ≥0.95 passes to human gate, 0.80–0.94 routes to targeted revision, <0.80 triggers full re-run alert.

### 7.6 Node 5 — Report Assembly
- Assembles all four deliverables per the Document Contract (§4), using version-controlled templates for every `FIXED`/`DATA_INJECTED` field so document *shape* never drifts between runs.
- Produces a password-protected submission package containing all four documents plus the validation report and audit log excerpt.

### 7.7 Node 6 — Human Review Gate
- Graph interrupts after Node 5; execution suspends until role-restricted trustee approvals are recorded.
- Each deliverable displayed with a side-by-side AI-draft-vs-verified-figures comparison.
- Approval protocol: SHA-256 hash of (trustee_id + deliverable_content_hash + timestamp), logged to the approvals table.
- Revision routing: narrative feedback routes to Node 2; financial-item feedback is flagged for manual correction — **never** re-routed to an LLM.
- IE pack delivery (§4.4) is triggered from this gate once the pack itself is approved, using the secure-link mechanism, not before.

### 7.8 Chat Agent
- Tool inventory as finalized in the Project Summary §6, including `get_unclassified_transactions` added during this PRD pass.
- Every regulatory claim traceable to the curated OSCR knowledge base (§7.10); every financial claim traceable to a tool-called D1 record. No open-ended model recall is permitted to stand as an answer to either category of question.
- Live step-streaming to the frontend (SSE) — every tool call and reasoning step the agent takes is visible to the trustee in real time.

### 7.9 Memory Architecture
Three-tier, per Project Summary §10, all processed by Gemma 4 26B A4B:
- **Tier 1 (working memory)**: recent conversation turns read directly from D1, no separate cache layer.
- **Tier 2 (episodic summary)**: background-processed rolling narrative summary of recent activity, run via FastAPI `BackgroundTasks`.
- **Tier 3 (semantic facts)**: autonomous extraction limited to non-financial, non-numeric context (project status, mission trip dates, governance continuity). **Financial facts are never autonomously extracted or cached as LLM-written assertions** — any financial question is always answered live via `query_financial_state`, never from a cached memory fact. This is the one deliberate, mandatory divergence from the reference memory architecture it was adapted from.
- **Tier 4 (deep archive)**: all historical documents/conversation embedded and retrievable via hybrid dense (cosine similarity, computed in Python against D1-stored vectors) + sparse (SQLite FTS5) search, fused by Reciprocal Rank Fusion, accessed only on agent-initiated retrieval, never auto-injected wholesale.

### 7.10 OSCR Knowledge Base
- Four-category taxonomy: `regulatory_requirements`, `financial_governance`, `trustee_procedures`, `sector_context`.
- Sourced via the three-stage external pipeline (Israel-curated outlines → Research Prompt Architect session → RAG Document Engineer session) specified in the Project Summary §7 and finalized in the Prompt Document.
- Retrieval uses the same hybrid RRF mechanism as Tier 4 document archive retrieval.

### 7.11 Notifications
- Resend integration, severity-routed per Project Summary §5: critical alerts to all trustees individually; routine notices to the Secretary only.
- Includes: deadline reminders (escalating as the statutory date approaches, first alert at 60 days out), P0 halt alerts, deliverable-awaiting-approval alerts, first-login password-reset prompts, IE pack delivery/resend confirmations.

### 7.12 Authentication & Onboarding
- Admin-only provisioning script (Israel-run): takes a trustee email, generates an initial password, creates the account.
- Forced password change enforced on first login — no path to the dashboard bypasses this.
- Post-first-login onboarding step: trustee confirms name and executive role (Chair/Secretary/Treasurer); role selection determines approval rights per Red-Line 3.

---

## 8. Non-Functional Requirements

- **Security posture**: governed by the principle in Project Summary §11, fully specified in the Security Document (Document 4).
- **Zero-cost infrastructure**: every component must remain within its provider's free tier at the confirmed 2-trustee scale; any component that cannot (e.g., Render free-tier cold starts) is documented as an accepted tradeoff, not silently absorbed.
- **UX**: frontend must be visually dynamic and modern (Project Summary §10) — explicitly not a static/robotic form-based interface; the live agent-step-streaming UI is a functional requirement, not a cosmetic one.
- **Auditability**: every node execution, every classification decision, every approval, and every notification send is logged with sufficient detail to reconstruct the full decision trail for an Independent Examiner or OSCR, without exposing raw PII in the log itself.
- **Consistency**: the Document Contract (§4.2, Project Summary §8) is the enforced mechanism guaranteeing that identical verified inputs always produce identical `FIXED`/`DATA_INJECTED` output, run over run.

---

## 9. Explicitly Out of Scope for v1

Carried from the Project Summary, restated as binding functional exclusions:
- Multi-tenant support for any charity other than SC054652.
- Statutory audit / full accrual SORP accounting.
- Any autonomous submission to OSCR, a bank, or any third party.
- A dedicated vector database service (Vectorize/Pinecone) — hybrid retrieval is implemented D1-native per Project Summary §10.

---

## 10. Items Deferred to the TRD

The following are acknowledged as real requirements but are schema/infrastructure-level decisions properly resolved in Document 3, not this PRD:
- Exact D1 table schemas and API contracts between frontend and backend.
- Exact LangGraph state machine field definitions and conditional edge logic.
- Exact embedding model choice and chunking parameters for hybrid RAG.
- Exact rate-limit sizing calculations for Gemma 4 26B A4B and `openai/gpt-oss-20b` against projected usage volume.
- Backup/disaster-recovery mechanics for D1/R2 (Security Document territory specifically).

---

## 11. Document Status

No open ambiguities remain in this PRD relative to everything confirmed through the preceding interrogation and the Project Summary. Proceeding to the TRD (Document 3) on your authorization.
