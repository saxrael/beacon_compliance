# Beacon Compliance — Design System Master

**Client/Subject**: Potter's House Christian Mission UK (SCIO, SC054652, Dunbar, Scotland)  
**Charity Motto**: *"Building Lives, Strengthening Homes, Shaping Nations for Christ"*  
**Visual Identity**: Official Charity Crimson Red (`#D6162F`), Royal Scottish Gold (`#D97706`), Warm Scottish Limestone / Pearl Ivory (`#F8F7F4`), Editorial Classical Typography (`Cinzel` / `Inter` / `JetBrains Mono`), Crisp Data Density.
**Default Theme**: **Light Mode** (Primary & Default) with polished Dark Mode option.

---

## 1. Color Palette Tokens

| Token Name | Light Mode Value | Dark Mode Value | Role / Usage |
|---|---|---|---|
| `--color-brand-crimson` | `#D6162F` | `#EF4444` | Primary Brand Crimson, CTAs, highlight trims |
| `--color-brand-crimson-dark` | `#B81026` | `#DC2626` | Crimson hover & active states |
| `--color-brand-gold` | `#D97706` | `#F59E0B` | Secondary Royal Scottish Gold accent, badges, focus rings |
| `--color-brand-gold-dark` | `#B45309` | `#D97706` | Gold hover & active states |
| `--color-bg-light` | `#F8F7F4` | `#090D16` | Warm Scottish limestone background |
| `--color-surface` | `#FFFFFF` | `#111827` | Institutional card surface |
| `--color-surface-muted` | `#F5F5F4` | `#1E293B` | Table headers & inset panels |
| `--color-border` | `#E7E5E4` | `#334155` | Subtle card & divider borders |
| `--color-text-primary` | `#0F172A` | `#F8FAFC` | Main headings & body text (≥ 12:1 contrast) |
| `--color-text-secondary` | `#64748B` | `#94A3B8` | Subheadings, table headers, metadata |
| `--color-success` | `#059669` | `#10B981` | Reconciled / Verified status badge |
| `--color-error` | `#DC2626` | `#EF4444` | Red-Line 5 income halt / audit failure |

---

## 2. Typography Scale

- **Display & Headings**: `Cinzel`, `Playfair Display`, `Georgia`, serif (`font-serif`, weights: 600, 700) for authoritative Scottish SCIO institutional feel.
- **Body & Controls**: `Inter`, system-ui, sans-serif (`font-sans`, weights: 400, 500, 600) for maximum legibility.
- **Data, Hashes & Figures**: `JetBrains Mono`, monospace (`font-mono`, weights: 400, 500, 600) for exact monetary pence and SHA-256 hash alignment.

---

## 3. Brand Assets & Logo Specifications

- **Charity Logo**: `frontend/public/assets/logo.png` (Light mode) and `logo_dark.png` (Dark mode). Bounded strictly in a fixed-height container (`max-h-10 h-10 w-auto object-contain`) to prevent image blowout.
- **Charity Motto**: *"Building Lives, Strengthening Homes, Shaping Nations for Christ"*.
- **SCIO Registration Badge**: `SCIO SC054652 • Dunbar, Scotland`.

---

## 4. Component Design Rules

1. **Card Surfaces**: Clean elevated ivory/white cards (`institutional-card rounded-2xl p-6 border border-stone-200 shadow-card-light transition-all duration-200 hover:shadow-card-elevated`).
2. **Interactive States**: Smooth spring transitions with hover lift (`active:scale-[0.98] transition-all duration-200`).
3. **Brand Header**: Prominent institutional header with official Potter's House crest, motto in serif, and top crimson-gold gradient ribbon.
4. **Monetary Figures**: Strictly rendered in `font-mono` with zero client-side arithmetic per `beacon-financial-boundary`.
5. **Red-Line Banners**: Prominent alert banners for £250,000 threshold breach and unverified HMAC trustee sign-offs.
