# RevisionGate logo

## Three directions, one chosen

| Direction | Idea | Verdict |
|---|---|---|
| A. Gate | Two posts and a lintel with a bar across the opening. | Reads as a gate, says nothing about documents, and looks like a capital letter that is not in the name. |
| B. Gate line | Two document sheets side by side with one bar held across both. | Shows the comparison task, but needs explaining before it reads as RevisionGate. |
| **C. Compact RG (chosen)** | The initials R and G on a rounded navy tile. R is neutral, G is teal. | Reads as the product name at a glance and holds up at favicon size. Chosen by the team on November 13 2026. |

Sketches of all three are in `logo/explorations.svg`.

The monogram repeats the wordmark's own split: Revision in the neutral color, Gate in teal. The mark has no check mark, seal, shield, or ribbon. It should never suggest that a packet was certified or that engineering approved anything.

## Files

All in `design/brand/logo/`. Every letter is outlined from Inter (SIL Open Font License), so the files render the same everywhere and need no font.

| File | Use |
|---|---|
| `revisiongate-wordmark.svg` | Horizontal logo on white or light backgrounds. |
| `revisiongate-wordmark-reversed.svg` | Horizontal logo for dark backgrounds. Carries its own navy ground. |
| `revisiongate-wordmark-mono.svg` | One-color horizontal logo. |
| `revisiongate-mark.svg` | Icon only: navy tile, white R, light teal G. |
| `revisiongate-mark-reversed.svg` | Icon only for dark backgrounds: white tile, navy R, teal G, shown on navy. |
| `revisiongate-mark-mono.svg`, `revisiongate-mark-mono-white.svg` | Icon only in one color. The letters are cut out of the tile. |
| `favicon.svg` | Browser icon. Heavier letters and a larger monogram so it holds at 16 px. |
| `../build_logos.py` | Editable master. One geometry generates every file: `python3 design/brand/build_logos.py`. |

The same script writes `frontend/src/design/logoPaths.ts`, which the in-app `Logo.tsx` draws from, and the copies in `frontend/public/brand/`.

## Rules

- **Minimum size.** Wordmark: 96 px wide on screen, 25 mm in print. Mark: 20 px. Below 20 px use `favicon.svg`.
- **Clear space.** Keep an empty margin of one quarter of the tile's width on every side.
- **Light backgrounds.** Navy tile, white R, light teal G. Use on white or the off-white surface `#F5F7F9`.
- **Dark backgrounds.** White tile, navy R, teal G. The navy tile disappears on navy, so never place the standard mark there.
- **One color.** Use the mono files when color is unavailable.
- **Do not** recolor the G red or amber, add a check mark, tilt or stretch the mark, change the tile's corner radius, reset the letters in another typeface, or place the color logo on a photograph.
- **Do not** pair the logo with "certified", "approved", "verified", or similar words.
