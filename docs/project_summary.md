# Beacon Compliance
## Project Summary — Master Reference Document
### Prepared for: Israel | Target Charity: Potter's House Christian Mission UK (SCIO, SC054652)
### Document 1 of 5 — Project Summary → PRD → TRD → Security Document → Prompt Document
### Version 1.0

---

## 1. Executive Summary

**Beacon Compliance** is a fully autonomous, agentic compliance-management webapp built for Potter's House Christian Mission UK, a Scottish Charitable Incorporated Organisation (SCIO, charity number SC054652) regulated exclusively by the Office of the Scottish Charity Regulator (OSCR). It replaces what would otherwise be a manual, spreadsheet-and-email annual compliance cycle with a system that ingests source documents (bank statements, meeting minutes, receipts, contracts), deterministically computes statutory financial accounts, drafts regulatory narrative documents, tracks OSCR filing deadlines proactively, and gives trustees a conversational agent capable of answering in-depth financial and regulatory questions at any time — all while enforcing an absolute, architecturally-enforced boundary between what an AI model is permitted to generate (narrative prose) and what must always be deterministic, auditable arithmetic (every financial figure, every submission).

The system is built entirely on zero-cost infrastructure, is designed for exactly two trustee users at launch (expandable later), and is governed throughout by five compliance red-lines that no component — including the conversational agent — is permitted to violate under any circumstance.

Beacon Compliance is single-tenant for v1: built exclusively for SC054652, with charity-specific values held in configuration rather than hardcoded, to keep a future multi-tenant path open without taking on that complexity now.

---

## 2. Why "Beacon"

The name reflects the system's role: a steady point of guidance for trustees navigating statutory obligations, without being tied to a specific denomination or overclaiming what the system does. "Compliance" is kept in the working name for clarity in this planning phase; branding within the product itself can soften this if desired later.

---

## 3. What Beacon Compliance Is — System Description

Beacon Compliance is **not** a document generator that trustees occasionally open at year-end. It is designed and must be built as a **fully autonomous manager** with two integrated surfaces:

### 3.1 Document Intake Interface
Trustees upload source material into explicitly sectioned categories:
- Minutes of Meetings
- Bank Statements
- Receipts / Invoices
- Contracts / Agreements
- Gift Aid Declarations
- Prior Year Accounts
- Other / Supporting Evidence

Every upload carries a free-text description/additional-detail field completed by the uploading trustee. Uploads may be text-native or image-based (photographed receipts, scanned statements) — the ingestion pipeline handles both without treating OCR-sourced and text-native documents as separate categories from the trustee's point of view.

### 3.2 Conversational Agent Interface
A chat interface, visually dynamic in the manner of a modern AI assistant (live step-by-step visibility into what the agent is doing — reading a document, querying financial records, drafting a section — not a static request/response box), through which trustees can ask:
- Deep regulatory questions ("What does OSCR require for our Independent Examiner?")
- Real-time financial state questions ("What's our current balance in the Restricted Mission Fund?")
- Compliance status questions ("Where are we on this year's TAR?", "Who has approved the accounts so far?")

The agent is armed with a defined tool set (Section 6) and a curated OSCR knowledge base (Section 7) rather than relying on open-ended model recall — this is a deliberate, load-bearing design choice, not a limitation: every regulatory or financial claim the agent makes must be traceable to a grounded source (curated KB) or a verified system record (D1), never to the model's own unverified reasoning. **True agentic behaviour — autonomous tool selection, multi-step reasoning, and proactive action within its defined boundaries — is a mandatory system property, not an optional enhancement.**

### 3.3 Onboarding
New trustee accounts are provisioned by Israel (the developer) via a script that takes a trustee's email, generates an initial password, and creates the account. Each trustee must change their password on first login — this is a hard requirement, not a suggestion. Once logged in, a trustee completes onboarding by confirming their name and their executive role within the Potter's House executive council (Chair, Secretary, or Treasurer — the confirmed working role list; see Section 5).

### 3.4 Proactive Compliance Management
Beacon does not wait to be asked. It independently tracks the OSCR filing calendar (9 months post financial year-end for the Online Annual Return, and the dependent deadlines for the TAR, Accounts, and Independent Examiner's Report) and pushes reminders ahead of statutory deadlines, escalating in urgency as a deadline approaches. This proactive capability is a first-class, adequately-scoped requirement for v1 — not a stretch goal.

### 3.5 Transaction Classification Pipeline (Node 3 Fund/Category Assignment)
Before any financial arithmetic runs, every extracted transaction must be assigned to a fund and OSCR receipt/payment category. This is a three-tier pipeline, closed during architecture review to eliminate a gap where an unrecognized transaction had no defined handling path:

- **Tier 1 — Deterministic rule match.** A keyword/pattern ruleset (YAML-configured) classifies the majority of recurring, recognizable transactions. Zero LLM involvement, fully auditable.
- **Tier 2 — Human classification with permanent learning.** Any transaction that doesn't confidently match a rule is surfaced to a trustee in the Review Gate UI for manual assignment. That decision is written back into the Tier 1 ruleset, so the same or similar transaction pattern is recognized automatically in future periods — the manual-classification burden shrinks over time rather than repeating every year.
- **Tier 2.5 — AI-suggested classification, human-confirmed.** For transactions Tier 1 can't confidently match, a small, fast, purpose-built model (`openai/gpt-oss-20b` via Groq, distinct from and never a fallback for Gemma 4 26B A4B) proposes a candidate category using rich context — full transaction description, amount and date as read-only reference, the complete fund/category taxonomy, and the 3–5 most similar previously-confirmed classifications retrieved via the same hybrid RAG infrastructure used elsewhere in the system. Its output schema contains only a category label, confidence score, and reasoning — never a monetary field — so it structurally cannot originate or alter a figure. Every Tier 2.5 suggestion still requires explicit trustee confirm/override before entering the ruleset, identical in spirit to the OCR confidence-gating pattern.

This keeps every downstream arithmetic guarantee (Section 9, Red-Line 2) intact: classification informs *which bucket* a verified figure belongs to, but never computes, alters, or originates the figure itself. `llama-3.1-8b-instant` via OpenRouter is documented as the named contingency path for Tier 2.5 if Groq's structured-output reliability for `gpt-oss-20b` proves inadequate in practice.

---

## 4. The Four OSCR Deliverables Beacon Produces

Unchanged from the original regulatory analysis, restated here as the system's core output:

1. **Online Annual Return (OAR)** — pre-population data sheet only; the system never auto-submits.
2. **Trustees' Annual Report (TAR)** — six-section narrative document, field-level split between fixed/data-injected/LLM-drafted content (see Section 8).
3. **Annual Accounts (Receipts & Payments)** — fully deterministic, fund-segregated statutory accounts.
4. **Independent Examiner's Working Paper Pack** — structured evidence package for the charity's Independent Examiner, delivered securely (Section 6.4).

If gross income is ever calculated at or above £250,000, the system hard-halts and escalates rather than producing an R&P account that would be legally insufficient — accrual-basis SORP accounts are a different regime entirely, outside this system's current scope.

---

## 5. Users, Roles, and Approval Rights

- **Two trustee accounts at launch**, provisioned exclusively by Israel via an admin-only script.
- **Working executive role list**: Chair, Secretary, Treasurer.
- **Approval rights are role-restricted**: only trustees holding the Chair, Secretary, or Treasurer role may formally approve a deliverable. This directly enforces the two-trustee sign-off red-line (Section 9) with real governance meaning, not just a login count.
- **Notification routing is severity-based, not role-based**: critical alerts (deadline reminders, P0 halts, "a deliverable awaits your approval," first-login prompts) go to every registered trustee individually; routine/informational notices (e.g., a document was uploaded) go to the Secretary only, matching that role's conventional administrative function without creating a single point of failure on anything time-sensitive.

---

## 6. Core Capabilities — Agent Tool Inventory

The chat agent's confirmed, final tool set for v1:

| Tool | Purpose | Execution boundary |
|---|---|---|
| `query_financial_state` | Answers balance/spend questions | Reads verified D1 financial records only — never computes |
| `search_documents` | Retrieves relevant content from uploaded documents | Advanced hybrid (dense + sparse) RAG, not naive similarity search |
| `explain_oscr_requirement` | Answers regulatory questions | Grounded exclusively in the curated OSCR knowledge base |
| `get_deliverable_status` | Reports progress on any of the four deliverables | Reads deterministic run state |
| `get_upcoming_deadlines` | Surfaces OSCR filing deadlines on request | Deterministic date logic |
| `get_approval_audit_trail` | Reports who approved what, and when | Reads the cryptographic approvals record |
| `get_ie_package_status` | Reports Independent Examiner pack delivery status; surfaces a resend option | Read-only for the agent — the actual resend is a trustee-initiated action, never autonomous |
| `get_unclassified_transactions` | Reports transactions still awaiting Tier 2/2.5 trustee classification | Reads deterministic pipeline state; surfaces Tier 2.5 suggestions as unconfirmed, never as fact |

### 6.4 Independent Examiner Delivery
The IE working paper pack is stored in object storage as the single source of truth. When ready, the system generates a secure, time-limited signed download link (default validity: **14 days, regenerable on demand**) and emails it to the Independent Examiner via Resend. This is deliberately not a one-shot email attachment: the send event is logged to the audit trail, and any trustee can regenerate or resend the current version from the dashboard at any time, satisfying the requirement that this capability remain genuinely available for future use, not a single historical action.

---

## 7. Knowledge Base Strategy

Beacon's regulatory answers are grounded in a purpose-built, curated knowledge base rather than model recall, sourced through a dedicated three-stage pipeline running in separate, purpose-specific AI Studio sessions (detailed fully in the Prompt Document):

1. Israel curates topic outlines organized under a confirmed four-category taxonomy: `regulatory_requirements`, `financial_governance`, `trustee_procedures`, `sector_context`.
2. A **Research Prompt Architect** session generates a rigorous Gemini Deep Research directive per outline, enforcing depth requirements, source diversity, a jurisdiction-tiered sourcing hierarchy (OSCR-specific material first, UK-wide/Charity Commission E&W material only as a verified-applicable fallback, general nonprofit theory narrowly), and a curated, deduplicated download list of **5–10 sources** per report (scaled down from a larger-system default given Beacon's narrower scope).
3. A **RAG Document Engineer** session transforms the resulting research report(s) into retrieval-optimized Markdown, chunked and structured for the hybrid RAG pipeline, preserving contextualization/scarcity/jurisdiction-variance content with the same rigor as the source pipeline it's adapted from.

---

## 8. Document Generation — Consistency Guarantee

Every generated deliverable is governed by a **Document Contract**: every field in every document is explicitly classified as `FIXED` (never varies — statutory boilerplate, charity identity), `DATA_INJECTED` (deterministic, sourced from verified financial/config records, zero LLM involvement), or `LLM_DRAFTED` (a narrow, explicitly whitelisted set of narrative fields, validated post-generation against source documents before merge).

For the TAR specifically, the confirmed field-level split narrows the LLM-authored surface to exactly four narrative fields (governance description, purposes-to-activities narrative, achievements connective narrative, principal-risks narrative) — every other field across all four deliverables, including every monetary figure, date, name, and statutory declaration, is deterministic. This is what makes "AI-assisted but not AI-probabilistic" an enforceable property of the system rather than a stated intention.

---

## 9. Non-Negotiable Compliance Red-Lines

These apply to every component of the system, including the conversational agent, without exception:

1. **No autonomous submission or transmission.** The system never submits to OSCR, a bank, or any external party, and never autonomously sends an outbound communication (including IE pack resends) without a trustee-initiated action.
2. **No LLM financial arithmetic.** No language model computes, estimates, rounds, or interprets a financial figure at any stage, including within chat responses — the agent retrieves and reports verified figures via tool calls, it never derives them.
3. **Mandatory, role-restricted trustee sign-off.** All four deliverables require explicit, cryptographically-logged approval from trustees holding the Chair, Secretary, or Treasurer role before a submission-ready package is produced.
4. **PII boundary enforcement.** No name, address, date of birth, bank detail, or National Insurance number is transmitted to any external API or exposed to the LLM. Enforced entirely at the application/software layer (see Section 10) given the system's remote-webapp deployment model.
5. **Income threshold hard-halt.** If gross income is calculated at or above £250,000, the system halts R&P account generation and escalates — it does not silently produce a legally insufficient document.

---

## 10. Architecture at a Glance

*(Full detail in the TRD; this section establishes the confirmed shape only.)*

- **Frontend**: Next.js (React) + Tailwind/shadcn, deployed on Vercel — a decoupled, visually rich interface (not the originally-considered Streamlit approach), including a live streamed view of agent reasoning/tool-use steps.
- **Backend**: FastAPI + LangGraph, deployed on Render — stateless, no reliance on local disk persistence.
- **Data**: Cloudflare D1 (relational: users, runs, approvals, audit log, embeddings) and Cloudflare R2 (encrypted document/deliverable object storage) — chosen specifically because Render's free-tier Postgres expires after 30 days and its free web services have no persistent disk, which the original local-Docker design assumed but the remote-webapp requirement rules out.
- **Models**: Two models, each with a fixed, non-overlapping role — never used as fallbacks for one another. **Google Gemma 4 26B A4B** (via Google AI Studio / Gemini API, 256K context window) governs Node 2 narrative synthesis, the chat agent, and both background cognitive-memory processes (Tier 2 episodic summarization and Tier 3 fact extraction) — a single model across every narrative/reasoning surface for operational simplicity, with the tradeoff that background memory processing shares AI Studio rate-limit quota with live chat (accepted as low-risk at 2-trustee scale). **`openai/gpt-oss-20b` via Groq** is used solely and narrowly for Tier 2.5 transaction classification suggestions (Section 3.5) — verified to run through Groq's OpenAI-compatible Structured Outputs feature, so its native Harmony response format never reaches the application layer. `llama-3.1-8b-instant` via OpenRouter is documented as its named contingency.
- **Memory & retrieval**: A three-tier architecture — deterministic tool-called financial state (never cached as an LLM "fact"), on-demand hybrid dense+sparse RAG with Reciprocal Rank Fusion over documents and the OSCR knowledge base, and a rolling conversational summary for older turns, all processed by Gemma 4 26B A4B — adapted from a reference architecture with financial-fact autonomy deliberately stripped out to respect Red-Line 2.
- **Notifications**: Resend, severity-routed per Section 5.
- **Deployment model**: A genuine remote webapp — document upload and agent chat both happen remotely, gated entirely by per-trustee authentication. This is a deliberate departure from the original air-gapped-local-hardware design; the privacy guarantee is now enforced entirely in software (encryption in transit and at rest, strict code-level separation between PII-bearing and LLM-eligible state, full access audit logging) rather than by physical network isolation. This tradeoff is explicitly accepted and will be documented in full in the Security Document.

---

## 11. Security Posture — Governing Principle

Beacon Compliance does not claim to be "impenetrable" — no networked system can honestly make that claim, and asserting it would itself be a liability for a compliance system. The governing standard, to be fully specified in the standalone Security Document, is:

> **No single point of failure may expose PII, enable unauthorized submission, or permit undetected tampering with financial data — enforced through layered, independently-verifiable controls at every boundary, with every control's failure mode explicitly documented.**

---

## 12. Explicitly Out of Scope for v1

- Multi-tenant support for charities other than SC054652 (architecture keeps this open; not built now).
- Statutory audit / full accrual SORP accounting (only relevant if the £250k threshold is breached, at which point the system halts rather than attempting this).
- Any form of autonomous submission to OSCR or any third party.

---

## 13. Remaining Document Sequence

This Project Summary is Document 1 of 5. Each subsequent document is fully scrutinized before the next begins:

1. ~~Project Summary~~ ✅ (this document)
2. **Product Requirements Document (PRD)** — full functional specification, deliverable-by-deliverable and node-by-node
3. **Technical Requirements Document (TRD)** — architecture, schemas, API contracts, state machine, infrastructure configuration
4. **Security Document** — the standalone, cross-cutting security specification referenced in Section 11
5. **Prompt & Workflow Document** — *(revised post-pivot: the build workflow moved from an AI Studio Lead Architect issuing payloads to a direct Antigravity-native workflow using Everything Claude Code (ECC). This document now comprises the root `AGENTS.md`, a workflow-integration overview, and the adapted Research Prompt Architect / RAG Document Engineer prompt pair — the latter two unchanged, since OSCR knowledge-base sourcing remains a separate AI Studio pipeline regardless of which tool builds the application code.)*

---

## 14. Assumptions Log

Recorded per the Zero Assumption Protocol — one default was adopted rather than explicitly confirmed, flagged here for visibility and easy amendment:

- **IE download link expiry: 14 days, regenerable on demand.** Proposed as a sensible default given no strong preference was stated; trivially adjustable before the TRD locks infrastructure specifics.

No other open items remain from the preceding interrogation. Proceeding to the PRD on your authorization.
