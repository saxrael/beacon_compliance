# Beacon Compliance — Required Design Assets & Document Template Specification

This document provides the exact specification, filenames, formats, dimensions, and purposes for all branding assets and OSCR deliverable document templates.

---

## 1. Required Design & Branding Assets

Place all required graphic assets in both `assets/` (root) and `frontend/public/assets/`.

| Filename | Format | Recommended Dimensions / Specs | Visual Description & Usage |
|---|---|---|---|
| `logo.png` | **PNG** (transparent background) | `600px x 200px` (or `3:1` ratio), 300 DPI | **Primary Charity Logo** (Full color logo for Potter's House Christian Mission UK). Displayed in header navigation, deliverable HTML/PDF headers, and report covers. |
| `logo_dark.png` | **PNG** (transparent background) | `600px x 200px` (or `3:1` ratio), 300 DPI | **Dark Mode Logo** (White/Light gold variant for dark background UI header). |
| `logo_mark.svg` / `logo_mark.png` | **SVG** / **PNG** | `512px x 512px` (`1:1` square) | **Icon Logo Mark** (Square emblem or cross/beacon icon). Used for mobile navigation, favicon, and avatar badges. |
| `favicon.ico` | **ICO** / **PNG** | `32px x 32px` / `64px x 64px` | **Browser Favicon** for Next.js web application. |
| `trustee_seal.png` | **PNG** (transparent background) | `400px x 400px` (`1:1` square) | **Official Trustee Signature Seal** (Official stamp or crest watermark placed alongside trustee HMAC sign-off certificates). |
| `scio_header_banner.png` | **PNG** / **JPG** | `1200px x 400px` (`3:1` aspect ratio) | **Charity Letterhead Header Banner** for print and PDF cover pages. |

---

## 2. Deliverable Document Templates (`templates/`)

Beacon Compliance generates 4 OSCR deliverable packages. The system uses HTML/CSS templates in `templates/` to render clean, verifiable documents for submission and trustee sign-off:

1. **[`templates/oar_template.html`](file:///c:/Users/Israel/Documents/Projects/Beacon%20Compliance/beacon_compliance/templates/oar_template.html)**:
   - **Deliverable 1: OSCR Online Annual Return (OAR) Data Sheet**
   - Contains pre-populated charity identity (SC054652), gross receipts, gross payments, net movement, and SHA-256 content verification hash.

2. **[`templates/tar_template.html`](file:///c:/Users/Israel/Documents/Projects/Beacon%20Compliance/beacon_compliance/templates/tar_template.html)**:
   - **Deliverable 2: Trustees' Annual Report (TAR)**
   - Renders the 6 statutory sections: Reference & Admin, Structure/Governance, Objectives, Achievements (with `[FIGURE_INJECTED]` tokens expanded), Financial Review, and Trustee HMAC Sign-off declaration block.

3. **[`templates/rnp_account_template.html`](file:///c:/Users/Israel/Documents/Projects/Beacon%20Compliance/beacon_compliance/templates/rnp_account_template.html)**:
   - **Deliverable 3: Receipts & Payments Accounts**
   - Renders fund-segregated receipts & payments matrix (Unrestricted General, Restricted Mission) and Statement of Balances reconciliation table.

4. **[`templates/ie_pack_template.html`](file:///c:/Users/Israel/Documents/Projects/Beacon%20Compliance/beacon_compliance/templates/ie_pack_template.html)**:
   - **Deliverable 4: Independent Examiner (IE) Pack**
   - Compiles audit logs, PII scrubbing verification counts, OCR low-confidence flags, and SHA-256 hashes for all included packages for trustee & examiner submission.
