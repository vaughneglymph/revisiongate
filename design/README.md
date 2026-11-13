# RevisionGate design

Brand, copy, and interface for the RevisionGate review screen. Built by Claude Fable for the Michigan DevFest build. Integration notes for the logic track are in `handoffs/DESIGN_HANDOFF_FOR_GPT.md`.

## Direction: the bench instrument

RevisionGate should feel like a good measuring tool on an estimator's desk: quiet until something is out of tolerance, then exact about what and where. Three decisions follow from that.

1. **The contradiction is the largest thing on the screen.** Opposing values sit side by side in large monospace type with a not-equal sign between them. Neither value is styled as the wrong one, because the product never picks.
2. **Two kinds of state never share a visual.** Quote readiness lives in the top bar and stays red while blocked. Clarification progress lives in the review pane and turns teal when approved. An approved clarification beside a Blocked label is the intended picture.
3. **Color is never the only signal.** Every status has an icon, a word, and a shape: conflicts have a solid edge, missing requirements a dashed edge, needs-review a dotted edge. A system error is a white panel with a full red outline and a triangle, so it cannot be read as a finding.

Layout: navy top bar (logo, packet, part, readiness); source documents on the left with line numbers and highlighted evidence; findings, questions, and the single primary action on the right. The primary action stays in one bar at the foot of the right pane, so the happy path is three clicks in one place. Below 900 px the panes stack with the review first, and each finding carries its own source passages.

## Tokens

Defined as CSS custom properties on `.rg` in `frontend/src/design/revisiongate.css`.

| Role | Token | Value |
|---|---|---|
| Primary text, top bar | `--rg-navy-900` | `#132238` |
| Secondary text | `--rg-navy-700` | `#2F4159` |
| Muted text | `--rg-slate-600` | `#4F6074` |
| Rules and marks only | `--rg-slate-500` | `#66778B` |
| Borders | `--rg-slate-200` | `#D3DAE2` |
| Neutral tint | `--rg-slate-050` | `#EEF2F6` |
| Work surface | `--rg-surface` | `#F5F7F9` |
| Documents, cards | `--rg-paper` | `#FFFFFF` |
| Primary action | `--rg-teal-600` | `#007F7A` |
| Action hover, links | `--rg-teal-700` | `#006763` |
| Approved text | `--rg-teal-800` | `#00524F` |
| Approved tint | `--rg-teal-050` | `#E3F4F2` |
| Accent on navy | `--rg-teal-on-navy` | `#4FD1C5` |
| Attention | `--rg-amber-700` | `#925B00` |
| Attention tint | `--rg-amber-050` | `#FFF5DE` |
| Blocking, errors | `--rg-red-700` | `#B42318` |
| Blocking tint | `--rg-red-050` | `#FEEFED` |
| Focus ring | `--rg-focus` | `#1D5FD6` |

Type: Inter Variable for interface text; the system monospace stack for part numbers, line IDs, values, and run IDs, with tabular figures. Sizes 11, 12.5, 14, 16, 26 px. Body is 14 px at 1.5 line height; source lines are 14 px at 1.55.

Space and shape: 4 px grid (4, 8, 12, 16, 20, 24). Radius 8 px for cards and buttons, 4 px for small controls, full for pills. One soft shadow. Motion: a spinner only, removed under reduced motion.

The starting palette changed in two places. Muted gray was darkened to `#4F6074` so small labels pass on the off-white surface. Teal `#007F7A` fails as a small accent on navy, so the top bar uses `#4FD1C5`.

## Contrast, measured

Ratios computed from the token values (WCAG 2 formula). Text needs 4.5, graphics and focus rings need 3.

| Pair | Ratio |
|---|---|
| Navy text on surface / on white | 14.89 / 15.99 |
| Secondary navy-700 on white | 10.39 |
| Muted slate-600 on white / surface / slate tint | 6.45 / 6.00 / 5.73 |
| White on teal button / hover | 4.86 / 6.73 |
| Teal link on white | 6.73 |
| Approved text on teal tint | 7.97 |
| Amber on amber tint / on white | 5.21 / 5.65 |
| Red on red tint / on white | 5.88 / 6.57 |
| White on navy bar | 15.99 |
| Bar labels on navy | 8.90 |
| Teal accent on navy | 8.57 |
| Disabled text on disabled fill | 5.28 |
| Text on conflict / located highlight | 11.65 / 12.67 |
| Recorded-run banner text | 8.63 |
| Focus ring on white / surface / navy bar | 5.74 / 5.34 / 9.73 |
| Logo bar against navy sheet | 3.29 |
| Input border on white | 4.59 |

The tightest text pair is white on the teal button at 4.86. Do not lighten the teal.

## Files

| Deliverable | Where |
|---|---|
| Direction and tokens | this file, `frontend/src/design/revisiongate.css` |
| Logo set and usage (compact RG monogram) | `design/brand/logo/`, `design/brand/LOGO_USAGE.md`, `design/brand/build_logos.py` (editable master) |
| Voice guide | `design/copy/VOICE_GUIDE.md` |
| Copy inventory | `design/copy/COPY_INVENTORY.md`, generated from `frontend/src/design/copy.ts` |
| Review screen and components | `frontend/src/design/ReviewScreen.tsx`, `Logo.tsx` |
| State gallery | `frontend/gallery.html`, `frontend/src/design/preview/` |
| Handoff | `handoffs/DESIGN_HANDOFF_FOR_GPT.md` |

## State gallery

`npm --prefix frontend run dev -- --port 5199`, then `http://127.0.0.1:5199/gallery.html`. Twelve states, each with a note on what to check, at full, laptop, and mobile widths. Every state uses hand-written synthetic data and says so on screen. The gallery makes no API or model call and is not evidence of a working integration.

Idle · Analyzing · Conflicting packet · Source awaiting review · Extraction error · No detected blockers pending human review · Edited draft awaiting approval · Stale draft requiring refresh · Approved clarification with quote blocked · Awaiting customer response · Recorded-run replay · Needs review.

## Limits

- The designed screen is wired into `frontend/src/main.tsx`. It loads the packet list from the backend and shows the idle state. No analysis has been run through it yet.
- States after analysis are checked in a browser against synthetic data only. Not checked with a screen reader.
- Light theme only.
