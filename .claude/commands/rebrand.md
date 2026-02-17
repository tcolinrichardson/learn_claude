# Rebrand HTML Project — Evidence Action

Apply Evidence Action branding to an HTML-based project. Works for any standalone HTML application in this workspace using Evidence Action branding.

**Working example:** `meta-analysis-calculator.html` is fully branded and can be used as a reference for patterns, CSS structure, and canvas color usage.

---

## Brand Reference (pre-extracted — do NOT re-parse the PDF)

### Primary Colors
| Name | Hex | CSS Variable | Usage |
|------|-----|-------------|-------|
| Ink | `#20253a` | `--ea-ink` | Headers, body text, dark backgrounds |
| Magenta | `#e600a0` | `--ea-magenta` | Accent only — CTAs, highlights (use sparingly) |
| Kale Green | `#05545a` | `--ea-kale` | Secondary dark, focus rings, links |
| Blue | `#d5f4f7` | `--ea-blue` | Light accents, card borders |
| Light Blue | `#ecfafb` | `--ea-light-blue` | Subtle backgrounds, hover states |
| Cool Gray | `#f8f8fa` | `--ea-cool-gray` | Page background, section fills |
| White | `#ffffff` | — | Primary background, text on dark |

### Secondary Colors (use a few at a time, not all at once)
| Name | Hex | CSS Variable |
|------|-----|-------------|
| Stratosphere | `#5e93fb` | `--ea-stratosphere` |
| Green | `#5dd9b3` | `--ea-green` |
| Neutral Pink | `#fe6e87` | `--ea-neutral-pink` |
| Tangerine | `#feca90` | `--ea-tangerine` |
| Purple | `#bc9ed2` | `--ea-purple` |
| Beige | `#f2ede8` | `--ea-beige` |
| Lemongrass | `#f4f252` | — |
| Neutral Purple | `#5c5161` | `--ea-neutral-purple` |
| Pink | `#ffb9ef` | — |

### Semantic Colors (derived from brand palette)
| Purpose | Hex | CSS Variable |
|---------|-----|-------------|
| Error / danger | `#c0275e` | `--ea-error` |
| Error background | `#fce8f0` | `--ea-error-bg` |
| Success | `#05545a` (Kale) | reuse `--ea-kale` |
| Warning / moderate | `#feca90` (Tangerine) | reuse `--ea-tangerine` |

### Typography
| Role | Font Family | Weights | CSS Variable | Fallbacks |
|------|-------------|---------|-------------|-----------|
| Headlines | T-Star TW | Regular (400), Bold (700) | `--font-headline` | `'JetBrains Mono', monospace` |
| Body | T-Star Pro | Light (300), Regular (400), Medium (500), Bold (700) | `--font-body` | `'Roboto Condensed', 'Segoe UI', sans-serif` |
| Monospace | — | — | `--font-mono` | `'JetBrains Mono', 'Courier New', monospace` |

**Typography rules:** min 16px digital, 1.15 line spacing, WCAG AA contrast required.

### Font Files (in project)
| File | Path | ~Size |
|------|------|-------|
| T-Star TW Regular | `Logos and Fonts/Fonts/T-Star TW/WOFF2/T-StarTW-Regular.woff2` | 38KB |
| T-Star TW Bold | `Logos and Fonts/Fonts/T-Star TW/WOFF2/T-StarTW-Bold.woff2` | 39KB |
| T-Star Pro Light | `Logos and Fonts/Fonts/T-Star/WOFF2/T-Star-Light.woff2` | 40KB |
| T-Star Pro Regular | `Logos and Fonts/Fonts/T-Star/WOFF2/T-Star-Regular.woff2` | 43KB |
| T-Star Pro Medium | `Logos and Fonts/Fonts/T-Star/WOFF2/T-Star-Medium.woff2` | 43KB |
| T-Star Pro Bold | `Logos and Fonts/Fonts/T-Star/WOFF2/T-Star-Bold.woff2` | 44KB |

**Total font payload:** ~247KB raw, ~385KB as base64.

### @font-face Mapping
When embedding fonts, use these exact declarations:

| File | font-family | font-weight | font-style |
|------|-------------|-------------|------------|
| T-StarTW-Regular.woff2 | `'T-Star TW'` | `normal` | `normal` |
| T-StarTW-Bold.woff2 | `'T-Star TW'` | `bold` | `normal` |
| T-Star-Light.woff2 | `'T-Star Pro'` | `300` | `normal` |
| T-Star-Regular.woff2 | `'T-Star Pro'` | `normal` | `normal` |
| T-Star-Medium.woff2 | `'T-Star Pro'` | `500` | `normal` |
| T-Star-Bold.woff2 | `'T-Star Pro'` | `bold` | `normal` |

All declarations should use `font-display: swap;` and `src: url('data:font/woff2;base64,...')` for standalone files.

### Logo Files (in project)
| Variant | Path | Use |
|---------|------|-----|
| White horizontal lockup | `Logos and Fonts/Logos/PNG/Horizontal-Lockup_White@4x.png` | Dark backgrounds (header) |
| Full-color horizontal lockup | `Logos and Fonts/Logos/PNG/Horizontal-Lockup@4x.png` | Light backgrounds |
| White icon only | `Logos and Fonts/Logos/PNG/Icon_White@4x.png` | Favicon, small spaces |

**Logo rules:** Maintain clear space of 2x the width of the "e" in the wordmark. Do not modify, recolor, or distort. Use white version on Ink backgrounds.

### Reference
- Brand guidelines PDF: `Staff Brand Guidelines_2024.pdf` (pages 8-13)
- Live website: https://www.evidenceaction.org/

---

## Phase 1: Current State Audit

Analyze the target HTML project (skip asset discovery — everything is above):

1. **CSS Audit** — Grep for all hex colors, rgb(), rgba(), font-family declarations
   - List all unique colors currently in use
   - Note whether CSS custom properties already exist
   - Flag inline styles in HTML and JavaScript

2. **JavaScript Style References** — Search for:
   - Canvas drawing contexts (fillStyle, strokeStyle, font)
   - Dynamic style assignments (element.style.x)
   - innerHTML/template literals containing style or color attributes

3. **Scope Assessment** — Estimate:
   - Number of unique colors to replace
   - Inline styles that need migration
   - Canvas/SVG elements with hardcoded colors

**Output:** Present the audit. Map each old color → new brand color. Get user approval before proceeding.

## Phase 2: User Decisions

Ask only what's needed. Skip questions where the answer is obvious. Common decisions:

- **Font strategy:** Embed as base64 (standalone) or link externally?
- **Logo placement:** Header, footer, both?
- **Accent color usage:** Which elements get Magenta? (CTAs, badges, highlights)
- **Semantic mapping:** How to handle success/warning/error colors with brand palette?
- **Scope:** Full redesign (layout + colors + typography) or colors-only?

## Phase 3: Implementation

Execute systematically. For large files (>50KB), use a Python transformation script for atomic changes. For smaller files, direct edits are fine:

### 3a. CSS Foundation
1. Add `:root` block with all `--ea-*` custom properties (use table above)
2. Add `@font-face` declarations — base64-embed WOFF2 files if standalone
3. Replace all hardcoded colors with `var(--ea-*)` references
4. Update all `font-family` declarations to use `var(--font-headline)` / `var(--font-body)`

### 3b. HTML Structure
1. Embed logo (base64 if standalone) in header/footer
2. Update semantic elements if layout is changing
3. Replace inline styles with CSS classes

### 3c. JavaScript & Canvas References
1. Update all canvas fillStyle/strokeStyle to brand hex values
2. Update canvas `ctx.font` strings to brand font families (e.g., `"14px 'T-Star Pro', 'Roboto Condensed', sans-serif"`)
3. Add `window.devicePixelRatio` scaling to all canvas elements for crisp rendering on HiDPI/Retina displays
4. Add text truncation (via `ctx.measureText()`) for long labels in canvas renders
5. Update template literal style attributes
6. Replace hardcoded color strings in innerHTML/dynamic styles

### 3d. Documentation
1. Update text that references colors by name (e.g., "blue diamond" → "teal diamond")
2. Update alt text for rebranded elements

### Implementation Rules
- **Atomic** — Single script applies all changes at once. No partial/inconsistent states.
- **Zero old colors** — After transformation, grep every old color to confirm removal.
- **Visual only** — No behavioral changes. Preserve all functionality.
- **Maintain architecture** — Standalone stays standalone. Embed assets as base64.
- **WCAG AA** — All text/background combos must meet 4.5:1 contrast minimum.

## Phase 4: Verification

1. Grep confirms zero legacy color values
2. No console.log/error/warn introduced
3. File opens and functions in browser
4. Brand fonts render correctly
5. Logo displays at correct size with clear space
6. Canvas/SVG uses brand colors
7. Responsive breakpoints still work
8. Print styles updated (if they exist)

## Update Tracking

After completion, update `issues.md` with:
- Complete list of what changed
- Old → new color mapping
- File size impact
- Decisions made during the process
