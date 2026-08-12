# Beacon Compliance — Design System Master

**Client/Subject**: Potter's House Christian Mission UK (SCIO, SC054652, Dunbar, Scotland)  
**Charity Motto**: *"Building Lives, Strengthening Homes, Shaping Nations for Christ"*  
**Visual Identity**: Official Charity Crimson Red (`#D6162F`) & Royal Gold (`#F5D345`), Deep Scottish Slate, Glassmorphic Surfaces, Crisp Data Density.

---

## 1. Color Palette Tokens

| Token Name | Hex Code / Value | Role / Usage |
|---|---|---|
| `--color-brand-crimson` | `#D6162F` | Primary Brand Red accent, header borders, primary action CTAs |
| `--color-brand-gold` | `#F5D345` | Secondary Royal Gold accent, badge highlights, focus glow |
| `--color-bg-dark` | `#0F172A` | Primary app dark background (Slate 900) |
| `--color-surface` | `#1E293B` | Card & Container surface background (Slate 800) |
| `--color-surface-glass` | `rgba(30, 41, 59, 0.75)` | Glassmorphism card surface with `backdrop-filter: blur(12px)` |
| `--color-border` | `#334155` | Subtle border for cards and tables (Slate 700) |
| `--color-text-primary` | `#F8FAFC` | Main heading and high-contrast text (Slate 50) |
| `--color-text-secondary` | `#94A3B8` | Subheadings, table headers, and metadata labels (Slate 400) |
| `--color-success` | `#10B981` | Reconciled / Verified status badge (Emerald 500) |
| `--color-error` | `#EF4444` | Income threshold halt alert / audit fail badge (Red 500) |

---

## 2. Typography Scale

- **Display & Headings**: Inter / Outfit (`font-sans`, weights: 600, 700)
- **Data & Tables**: JetBrains Mono / Roboto Mono (`font-mono`, weights: 400, 500) for exact monetary pence and SHA-256 hash alignment.

---

## 3. Brand Assets & Logo Specifications

- **Charity Logo**: `assets/logo.jpg` and `frontend/public/assets/logo.jpg` (Mirror of official public website logo).
- **Charity Motto**: "Building Lives, Strengthening Homes, Shaping Nations for Christ".
- **SCIO Registration Badge**: SC054652 (Dunbar, Scotland).

---

## 4. Component Design Rules

1. **Card Surfaces**: Glassmorphic cards (`bg-slate-800/80 backdrop-blur-md border border-slate-700/60 rounded-xl shadow-xl`).
2. **Interactive States**: Hover transitions (`transition-all duration-200 hover:border-red-500/50 hover:shadow-red-500/10`).
3. **Brand Gradients**: `.brand-gradient` (`linear-gradient(135deg, #D6162F 0%, #F5D345 100%)`).
4. **Monetary Figures**: Displayed strictly in mono font with currency symbol prefix (£). Zero client-side computation per `beacon-financial-boundary`.
5. **Red-Line Banners**: Prominent alert banners for £250,000 threshold breach and unverified HMAC trustee sign-off.

