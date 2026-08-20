# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** CityBoost
**Updated:** 2026-08-07
**Category:** Government Portal / Civic Services (city ticket system)
**Style:** **Modern Civic** — light, airy, trustworthy; large rounded cards, soft multi-layer shadows, display font for headings, navy + emerald accent.
**Stack:** Vue 3 + Vite + TypeScript + Tailwind CSS (class-based dark mode) + Pinia + Leaflet + Heroicons.

> This file documents the design system **as implemented** in `frontend/` (tokens in
> `tailwind.config.js` + `src/style.css`). Treat it as the source of truth; code wins over
> this doc if they ever drift. **App is fully Russian — cyrillic support is mandatory for fonts.**

---

## Global Rules

### Color Palette

Tailwind scales, resolved through `tailwind.config.js`. Navy is the brand, emerald is the CTA accent.

| Role | Scale | Base hex | CSS Variable / Token | Usage |
|------|-------|----------|----------------------|-------|
| Primary (navy) | `primary` 50–900 | `#2B6CB0` (500) | `--color-primary-500` | Brand, links, active pills, focus rings |
| Accent / CTA (emerald) | `accent` 50–900 | `#10B981` (500) | `--color-accent-500` | **Main CTAs only** (`Новая заявка`, submit) |
| Page canvas | `canvas` | `#F6F8FB` | `--color-canvas` | Page background (light) |
| Page canvas (dark) | `canvas.dark` | `#0B1220` | `--color-canvas-dark` | Page background (dark) |
| Surface | `surface` | `#FFFFFF` | — | Cards (dark: `#1A202C`) |
| Success | `success` | `#10B981` | `--color-success` | Done states |
| Warning | `warning` | `#F59E0B` | `--color-warning` | In-work states |
| Error | `error` | `#EF4444` | `--color-error` | Destructive, errors |
| Info | `info` | `#3B82F6` | `--color-info` | New/info states |

Status→color mapping: NEW = blue/info tint, IN_WORK = amber tint, DONE = emerald tint, CLOSED = gray tint.

### Typography

- **Display / headings (`font-display`):** **Manrope** (500–800) — cyrillic ✓
- **Body / UI (`font-sans`):** **Inter** (400–800) — cyrillic ✓
- Headings auto-use `font-display` (global `h1–h5` rule in `style.css`). Page titles are `text-3xl font-bold tracking-tight`.
- Loaded in `index.html` via Google Fonts (`Inter` + `Manrope`).

### Spacing

Tailwind default scale (0.25rem base). Common rhythm: page padding `px-4 sm:px-6 py-8`; card padding `p-5`/`p-6`/`p-8`; section gaps `mb-6`–`mb-8`.

### Radii

- Cards: `rounded-2xl`; buttons: `rounded-lg`; pills/chips/badges: `rounded-full`; stat icon tiles: `rounded-2xl`.

### Shadows

Multi-layer soft shadows (defined in `tailwind.config.js` + CSS vars):

| Token | Value | Usage |
|-------|-------|-------|
| `shadow-card` | `0 1px 2px rgb(16 24 40/.04), 0 1px 3px rgb(16 24 40/.08)` | Default card |
| `shadow-card-hover` | `0 8px 24px -6px rgb(16 24 40/.12), 0 2px 6px -2px rgb(16 24 40/.06)` | `.card-hover` lift |
| `shadow-dropdown` | `0 8px 16px -4px rgb(16 24 40/.1), 0 2px 4px -2px rgb(16 24 40/.05)` | Dropdowns, menus |
| `shadow-modal` | `0 24px 48px -12px rgb(16 24 40/.18), 0 8px 16px -8px rgb(16 24 40/.1)` | Modals |
| `shadow-emerald-glow` | `0 8px 20px -6px rgb(16 185 129/.4)` | `.btn-accent` hover |

Dark mode swaps shadow colors to near-black via `.dark` CSS vars.

### Dark Mode

- Strategy: `class` (`.dark` on `<html>`), toggled from `AppHeader` (remembered in localStorage).
- Dark surface = `gray-800` cards on `canvas-dark` (`#0B1220`) body.
- Every component ships paired `dark:` classes — never ship light-only UI.

---

## Component Specs (implemented as utility classes in `src/style.css`)

### Buttons

| Class | Look | Usage |
|-------|------|-------|
| `.btn-accent` | Emerald `bg-accent-500`, hover `accent-600` + emerald glow | **Main CTAs**: create ticket, submit forms, login/register |
| `.btn-primary` | Navy `bg-primary-600`, hover `700` | Secondary actions, confirmations, nav |
| `.btn-secondary` | White + gray border | Tertiary, cancel, non-destructive |
| `.btn-danger` | Red | Destructive (ban, delete) |
| `.btn-success` | Emerald (via Tailwind `emerald-*`) | Success confirmations |
| `.btn-ghost` | Transparent, gray hover | Icon-only / subtle |
| Sizes | `.btn-sm` (xs, `rounded-md`), `.btn-lg` (`text-base rounded-xl`) | |

All: `inline-flex items-center justify-center gap-2 rounded-lg text-sm font-semibold`, 150ms transitions, `active:scale-[0.98]`, focus ring `focus-visible:ring-2 ring-offset-2`, `disabled:opacity-50`.

### Cards

- `.card` = white/gray-800 `rounded-2xl border-gray-200 shadow-card`.
- `.card-hover` = `.card` + hover lift: `shadow-card-hover`, `-translate-y-0.5`, border shifts navy, `cursor-pointer`, 200ms.
- Optional sections `.card-header` / `.card-body` / `.card-footer` with hairline `border-gray-100` dividers.

### Forms

- `.form-input` — `rounded-lg border-gray-200`, focus: `border-primary-400` + soft navy ring `ring-primary-500/15`.
- `.form-label` (small, medium weight, `mb-1.5`), `.form-textarea` (`min-h-[100px]`), `.form-error` (red, icon + text below field), `.form-input-error` (red border variant).
- Validation is **inline** (per-field), never placeholder-only labels.

### Badges (status)

`.badge-new` (blue tint), `.badge-in-work` (amber), `.badge-done` (emerald), `.badge-closed` (gray) — pill `rounded-full text-xs font-semibold`, tinted bg + colored text in light & dark.

### Tables

`.table-wrap` (used by admin views): header row `bg-slate-50 dark:bg-gray-800/60`, uppercase tracking-wider labels, `td` with `border-t border-gray-100`, row hover `bg-gray-50/50`. Wrapped in `.card overflow-hidden rounded-2xl`.

### Stats

`.stat-card` (card + `flex items-center gap-4 px-6 py-5`), `.stat-icon` (`w-12 h-12 rounded-2xl` tinted tile), `.stat-value` (Manrope `text-2xl font-bold`), `.stat-label` (gray, small).

### Empty / error states

`.empty-state-*`: centered `py-16`, tinted `rounded-2xl` icon tile (`bg-primary-50`), Manrope title, gray text. Errors use a red-tinted tile + `ExclamationTriangleIcon` (SVG, never emoji).

### Page headers

`.page-header` / `.page-title` (Manrope `text-3xl font-bold tracking-tight`) / `.page-subtitle` (gray `text-sm mt-1`).

### Skeletons

`.skeleton` = `bg-gray-200 dark:bg-gray-700 rounded animate-pulse`; `SkeletonCard`/`SkeletonTable`/`SkeletonDetail` build on `.card`.

### Logo mark

`w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700` + white `TicketIcon` (header + auth + footer). Wordmark `font-display font-extrabold`.

### Header

Translucent `bg-white/80 dark:bg-gray-900/80` + `backdrop-blur-lg`, hairline bottom border, `sticky top-0 z-50`. Nav links gray → navy pill active; emerald `Новая заявка` CTA on the right.

---

## Motion

- Duration 150–300ms, `transition-all duration-150` default; buttons 150ms, cards 200ms, menus/dropdowns 200–300ms.
- Page transitions: 200ms fade + translateY(8px).
- **`prefers-reduced-motion: reduce`** global block in `style.css` neutralizes all animation/transition (page, dropdown, mobile menu, toasts, skeletons).
- Hover relies on transform/shadow (no layout shift); mobile uses `active:scale` feedback.

---

## Anti-Patterns (Do NOT Use)

- ❌ **Emojis as icons** — use Heroicons SVG exclusively
- ❌ **Removing focus rings** — always `focus-visible:ring-2` with a visible ring
- ❌ **Instant state changes (0ms)** — always 150–300ms transitions
- ❌ **Decorative-only animation** or animating width/height — animate opacity/transform
- ❌ **Relying on hover alone** for interaction (mobile has no hover)
- ❌ **Raw hex in components** — use Tailwind tokens / CSS vars
- ❌ **Placeholder-only labels** — visible labels required
- ❌ **Serif display font** — Manrope is the display font (EB Garamond rejected: no cyrillic, wrong mood)
- ❌ **Low-contrast gray-on-gray text** — keep 4.5:1 minimum
- ❌ **Layout-shifting hovers** — use transform/shadow, not width/height

---

## Pre-Delivery Checklist

Before delivering any UI code, verify:

- [ ] No emojis used as icons (use Heroicons SVG)
- [ ] All icons from one consistent set (Heroicons 24)
- [ ] `cursor-pointer` on all clickable elements
- [ ] Hover states with smooth transitions (150–300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard navigation (`focus-visible:ring-2`)
- [ ] `prefers-reduced-motion` respected
- [ ] Dark mode parity — every screen verified in `.dark`
- [ ] Responsive: 375px, 768px, 1024px, 1440px
- [ ] No horizontal scroll on mobile
- [ ] Cyrillic text renders correctly (Manrope/Inter)
