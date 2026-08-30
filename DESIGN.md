---
name: Panelglot
description: A dark, tool-dense Clip Studio Paint-style workspace for translating manga/webtoon pages
colors:
  void-black: "#0a0a0c"
  panel-charcoal: "#16161a"
  panel-raised: "#1e1e24"
  panel-sunken: "#0d0d0f"
  hairline: "#2a2a32"
  hairline-strong: "#3a3a44"
  signal-white: "#eceef2"
  ash-secondary: "hsl(28, 10%, 62%)"
  ash-tertiary: "hsl(28, 8%, 42%)"
  survey-orange: "#f6821f"
  survey-orange-strong: "#ff9843"
  survey-orange-soft: "rgba(246, 130, 31, 0.14)"
  alert-red: "#e5484d"
  alert-red-soft: "rgba(229, 72, 77, 0.14)"
  confirm-green: "#3dd68c"
typography:
  display:
    fontFamily: "Chakra Petch, ui-sans-serif, system-ui, sans-serif"
    fontWeight: 600
  body:
    fontFamily: "IBM Plex Sans, ui-sans-serif, system-ui, sans-serif"
    fontWeight: 400
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, SFMono-Regular, monospace"
    fontWeight: 400
rounded:
  sm: "4px"
  md: "7px"
  lg: "11px"
components:
  button-primary:
    backgroundColor: "{colors.survey-orange}"
    textColor: "#17110a"
    rounded: "{rounded.md}"
    padding: "6px 14px"
  button-primary-hover:
    backgroundColor: "{colors.survey-orange-strong}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ash-secondary}"
    rounded: "{rounded.md}"
    padding: "6px 11px"
  button-ghost-hover:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.signal-white}"
  field-input:
    backgroundColor: "{colors.panel-sunken}"
    textColor: "{colors.signal-white}"
    rounded: "{rounded.sm}"
    padding: "6px 10px"
---

# Design System: Panelglot

## Overview

**Creative North Star: "The Survey Map HUD"**

Panelglot reads like a field-survey instrument, not a consumer web app: a near-black
workspace with orange topographic contour lines drifting behind every panel, as if the
canvas were a terrain map the tool is scanning for text. The aesthetic exists because the
product's job is literally detection and mapping — finding text regions on a page and
plotting their coordinates — so the chrome plays the same game the pipeline does. It is a
tool for sustained, close-up work (reading dense manga panels, tuning detector thresholds),
so density and legibility win over whitespace or decoration. The interface commits fully to
dark: there is no light mode, because the product's use scene (a desk, focused work,
image-heavy content) has no reason to want one.

Confirmed anti-references: no light consumer-SaaS look (soft pastels, rounded card grids,
generous whitespace); no gradient text or glassmorphism; no emoji standing in for icons.

**Key Characteristics:**
- Void-black base with a live orange-on-charcoal contour map drifting behind opaque panels
- One accent color, used sparingly and only for action/state, never decoration
- Dense, collapsible tool panels (Clip Studio Paint / Photoshop density, not marketing-page spacing)
- Every icon is a hand-drawn single-stroke SVG; nothing borrowed from an icon font or emoji

## Colors

A near-monochrome dark palette (void black through warm ash grays) with exactly one accent
hue, reserved for signal.

### Primary
- **Survey Orange** (`#f6821f`): the one accent. Primary buttons, the active tool in the
  rail, focus rings, text selection, and the "index contour" lines in the topo backdrop
  (every 5th contour, per `TopoBackground.vue`). Nothing else in the UI is this hue.
- **Survey Orange Strong** (`#ff9843`): hover state for anything using Survey Orange as a
  background fill.

### Neutral
- **Void Black** (`#0a0a0c`): the outermost background — what the topo contour backdrop
  paints onto. Never used as a panel fill; panels always sit visually above it.
- **Panel Charcoal** (`#16161a`): the standard surface for chrome — headers, docks, tool
  rails, filmstrip.
- **Panel Raised** (`#1e1e24`): hover/raised state for interactive chrome (button hover,
  active row).
- **Panel Sunken** (`#0d0d0f`): recessed surfaces — form fields, the canvas viewport's void,
  anything meant to read as "below" the panel plane.
- **Hairline** (`#2a2a32`) / **Hairline Strong** (`#3a3a44`): borders and dividers. Strong is
  for a border that needs to read on hover or focus; regular is the resting state.
- **Signal White** (`#eceef2`): primary text.
- **Ash Secondary** (`hsl(28 10% 62%)`) / **Ash Tertiary** (`hsl(28 8% 42%)`): secondary and
  tertiary text. Both are warm grays tinted toward the accent's hue (28°), never neutral
  gray — this is deliberate (see the Warm Gray Rule below).
- **Alert Red** (`#e5484d`) / **Alert Red Soft** (`rgba(229,72,77,0.14)`): errors only.
- **Confirm Green** (`#3dd68c`): success/verified states only (a saved endpoint that has
  actually worked, a finished translation).

### Named Rules
**The One Signal Rule.** Survey Orange is the only saturated color in the system. If
something new needs emphasis, reach for weight, size, or position before reaching for a new
color — a second accent color is almost always the wrong fix.

**The Warm Gray Rule.** Secondary/tertiary text is never neutral (`#888`-style) gray — it's
tinted toward the accent's hue at low chroma (`hsl(28 ...)`). Flat neutral gray next to a
warm accent reads as mismatched/cheap; a same-hue-family gray reads as one deliberate
palette.

## Typography

**Display Font:** Chakra Petch (with ui-sans-serif, system-ui fallback)
**Body Font:** IBM Plex Sans (with ui-sans-serif, system-ui fallback)
**Label/Mono Font:** IBM Plex Mono (with ui-monospace, SFMono-Regular fallback)

**Character:** Chakra Petch is an angular, technical display face chosen specifically to
match the HUD/survey-instrument aesthetic — it should never be swapped for a rounder or
more humanist face without reconsidering the whole North Star. IBM Plex Sans carries body
text: legible and neutral at small sizes, without competing with the display face. IBM Plex
Mono is reserved for anything that reads as data — coordinates, percentages, thresholds,
model names.

### Hierarchy
- **Display** (Chakra Petch, 600, 15px, tight tracking): app wordmark, dialog titles.
- **Section label** (uppercase, 12px, 600, 0.03em tracking, Ash Secondary): collapsible
  right-dock section headers (`RightDock.vue`'s `summary` elements).
- **Body** (IBM Plex Sans, 400, 13px): field labels, buttons, general UI text.
- **Data/mono** (IBM Plex Mono, 400, 11–13px, tabular-nums): zoom percentage, numeric
  threshold fields, endpoint base URLs, file sizes.

### Named Rules
**The Mono-For-Numbers Rule.** Any value the user is meant to read precisely or compare
(zoom %, a threshold, a base URL) renders in `--font-mono` with `tabular-nums`. Prose never
does.

## Layout

A fixed-height app shell (`h-screen`, no page scroll): a 56px top bar, a body row that
fills the remaining height, and a bottom filmstrip. The body row is three regions: a
narrow (~52px) left tool rail, a flexible center canvas viewport, and a fixed 300px right
dock. All three are independently scrollable/clippable; only the canvas viewport and the
right dock's section bodies scroll internally. There is no responsive breakpoint story yet
— the shell assumes a desktop-width viewport (it is a desktop creative-tool workflow, not a
content site).

Spacing inside dock sections runs on a tight rhythm: 12px gaps between fields, 14px
horizontal section padding, 4–16px vertical section padding. This is deliberately denser
than a typical marketing/content layout — it matches the tool-panel density of Photoshop/
Clip Studio Paint, where screen real estate is scarce and the user is doing repeated,
close-range adjustments rather than reading prose.

## Elevation & Depth

Hybrid: panels are flat at rest (no ambient shadow — a charcoal panel simply sits on the
void, distinguished by fill color and hairline borders, not elevation) and shadows appear
only for content that genuinely floats above the page — the canvas image itself, and
modal/popover surfaces (Save Story dialog, the results-gallery lightbox).

### Shadow Vocabulary
- **panel** (`0 10px 28px -10px rgba(0,0,0,.55), 0 2px 8px rgba(0,0,0,.4)`): reserved for
  chrome that could visually float (currently declared, sparingly used).
- **pop** (`0 16px 40px -12px rgba(0,0,0,.65), 0 4px 12px rgba(0,0,0,.45)`): the loaded page
  image on the canvas, and modal dialogs — anything that should read as sitting above
  everything else.

### Named Rules
**The Flat-Chrome Rule.** Docks, bars, and rails never carry a shadow. Depth is reserved for
the one thing the user is actually looking at (the page image) and true overlays (dialogs).
A shadow on ordinary chrome would compete with that signal.

## Shapes

Small, consistent corner radii throughout: 4px (`sm`, form fields/inputs), 7px (`md`, most
buttons and interactive chrome), 11px (`lg`, larger containers — currently declared,
lightly used). Radii never scale up for "important" elements; importance is carried by
color and weight, not by rounding more aggressively. Borders are hairline (1–1.5px) and
low-contrast at rest, brightening to `hairline-strong` or the accent on hover/focus rather
than thickening.

## Components

Every component is hand-styled inline (no component-library dependency) against the CSS
custom properties above, so any new component should reach for `var(--color-*)` /
`var(--font-*)` /`var(--radius-*)` rather than hardcoding a hex or px value.

### Buttons
- **Shape:** `border-radius: 7px` (`--radius-md`) on every button variant.
- **Primary** (`.btn-accent`, `AppHeader.vue`): `background: var(--color-accent)`,
  `color: #17110a` (near-black text on the bright accent, never white), `padding: 6px 14px`,
  `font-weight: 600`. Hover: `background: var(--color-accent-strong)`.
- **Ghost** (`.btn-ghost`): transparent background, `1px solid var(--color-border)`,
  `color: var(--color-text-secondary)`. Hover: border brightens to
  `--color-border-strong`, fill becomes `--color-surface-raised`, text brightens to
  `--color-text`. Used for every non-primary action (Upload, Export, Save as Story, Clear,
  Preview OCR, the Stories nav link).
- **Tool-rail icon buttons** (`ToolRail.vue` `.tool-btn`): 36×36px square, no border at
  rest; active state is `background: var(--color-accent-soft)`,
  `color: var(--color-accent-strong)` — a tinted fill, not an outline or underline.

### Inputs / Fields (`LabeledSelect.vue`, `LabeledInput.vue`)
- **Style:** `background: var(--color-surface-sunken)`, `1px solid var(--color-border)`,
  `border-radius: 4px` (`--radius-sm`), `padding: 6px 10px`, `font-size: 13px`. A recessed
  fill (sunken, not the panel's own charcoal) is what visually reads as "editable" against
  the surrounding chrome.
- **Focus:** border becomes `var(--color-accent)`; no glow/ring, the browser's native
  `:focus-visible` outline (also accent-colored, see the global rule in `main.css`) supplies
  the rest.
- **Label:** always a separate `<label>` above the field, 12px, `--color-text-secondary`,
  never a placeholder-as-label.

### Collapsible sections (`RightDock.vue`'s `<details>`)
- Every settings group is a native `<details>`/`<summary>` — no custom disclosure widget.
  `summary` is an uppercase 12px label with a hand-drawn chevron (two rotated border edges,
  not an icon glyph) that rotates 90° open. This keeps the whole dock keyboard-accessible
  for free.

### Cards / Thumbnails (`PageFilmstrip.vue`, `stories.vue`)
- **Corner style:** 4px (`--radius-sm`).
- **Border:** 1.5px, `--color-border` at rest, `--color-accent` when selected/active — the
  border color IS the selection indicator, no separate checkmark or glow.
- **Status badges** (filmstrip thumbnails): a small 15px circle bottom-right, colored by
  state (`--color-accent` processing, `--color-success` finished, `--color-danger` error) —
  color alone carries the state, no icon+color redundancy needed at that size.

### Icons (`Icon.vue`)
A single component with a name-keyed path map — every icon is hand-authored inline SVG,
24×24 viewBox, `stroke="currentColor"`, `stroke-width="1.75"`, round caps/joins, no fill
except the rare solid dot (e.g. the alert triangle's center point). This is a hard
constraint, not a style preference: emoji and icon fonts render inconsistently across
platforms and instantly read as an unstyled/default UI.

## Do's and Don'ts

### Do:
- **Do** reach for `var(--color-*)` custom properties for every color; never hardcode a hex
  value in a component even if it matches an existing token.
- **Do** keep Survey Orange (`--color-accent`) to primary actions, active/selected state,
  and verified/success-adjacent signals only.
- **Do** use `--font-mono` with `tabular-nums` for any numeric value the user reads
  precisely.
- **Do** author new icons as inline SVG through `Icon.vue`'s path map, matching the
  existing 24px/1.75 stroke-weight/round-cap convention.
- **Do** keep chrome (bars, docks, rails) flat and reserve shadow (`--shadow-pop`) for the
  canvas image and true overlays (dialogs, lightboxes).

### Don't:
- **Don't** introduce a second saturated accent color. If two states need to be
  distinguished, use `--color-success` (confirm-green) or `--color-danger` (alert-red) —
  the palette is deliberately three-signal-colors-total, not open-ended.
- **Don't** use emoji or an icon-font glyph anywhere in the product UI — every icon goes
  through `Icon.vue`.
- **Don't** add a shadow to ordinary chrome (headers, docks, rails, buttons) — shadow is
  reserved per the Flat-Chrome Rule.
- **Don't** use plain neutral gray for secondary/tertiary text — it must be hue-tinted per
  the Warm Gray Rule.
- **Don't** round corners past 11px (`--radius-lg`) for emphasis — importance is carried by
  color/weight, not radius.
