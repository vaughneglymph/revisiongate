"""Editable master for the RevisionGate logo: compact RG monogram on a rounded tile.

One geometry generates every SVG, the favicon, the in-app path module, and the
explorations sheet. Letters are outlined from Inter (SIL Open Font License).

Run from the repo root:  python3 design/brand/build_logos.py
Needs fontTools and brotli (to read the woff2 the frontend already ships).
"""
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "logo"
PUBLIC = ROOT / "frontend/public/brand"
FONT = ROOT / "frontend/node_modules/@fontsource-variable/inter/files/inter-latin-wght-normal.woff2"
NAVY, TEAL, TEAL_ON_NAVY, WHITE = "#132238", "#007F7A", "#4FD1C5", "#FFFFFF"

# Tunable geometry
GRID, RADIUS = 48, 10          # mark tile
MONO_WEIGHT, MONO_WIDTH = 760, 0.66   # monogram weight and width as a share of the tile
FAV_GRID, FAV_RADIUS, FAV_WEIGHT, FAV_WIDTH = 32, 7, 820, 0.72
TRACK = -0.045                 # monogram letter spacing in em
WORD_SIZE, WORD_WEIGHT, WORD_TRACK = 30, 680, -0.02

num = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
_fonts = {}
def font(weight):
    if weight not in _fonts:
        _fonts[weight] = instantiateVariableFont(TTFont(FONT), {"wght": weight})
    return _fonts[weight]

def draw(weight, text, size, x, y, track, make_pen):
    f = font(weight)
    glyphs, cmap, scale = f.getGlyphSet(), f.getBestCmap(), size / f["head"].unitsPerEm
    pens = []
    for ch in text:
        glyph = glyphs[cmap[ord(ch)]]
        pen = make_pen(glyphs)
        glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        pens.append(pen)
        x += glyph.width * scale + track
    return pens, x - track

def outline(weight, text, size, x=0.0, y=0.0, track=0.0):
    pens, end = draw(weight, text, size, x, y, track, lambda g: SVGPathPen(g, ntos=num))
    return [p.getCommands() for p in pens], end

def bounds(weight, text, size, track):
    box = None
    pens, _ = draw(weight, text, size, 0, 0, track, lambda g: BoundsPen(g))
    for p in pens:
        b = p.bounds
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    return box

def tile(n, r):
    s = n - 2 * r
    return f"M{r} 0h{s}a{r} {r} 0 0 1 {r} {r}v{s}a{r} {r} 0 0 1-{r} {r}h-{s}a{r} {r} 0 0 1-{r}-{r}v-{s}a{r} {r} 0 0 1 {r}-{r}z"

def monogram(grid, width_share, weight):
    """R and G outlines, scaled to width_share of the tile and centered on it."""
    x0, _, x1, _ = bounds(weight, "RG", 100, TRACK * 100)
    size = 100 * grid * width_share / (x1 - x0)
    x0, y0, x1, y1 = bounds(weight, "RG", size, TRACK * size)
    (r, g), _ = outline(weight, "RG", size, (grid - (x0 + x1)) / 2, (grid - (y0 + y1)) / 2, TRACK * size)
    return r, g

R, G = monogram(GRID, MONO_WIDTH, MONO_WEIGHT)
TILE = tile(GRID, RADIUS)

def mark(kind, dx=0, dy=0):
    move = f' transform="translate({dx} {dy})"' if dx or dy else ""
    if kind == "color":
        body = f'<path fill="{NAVY}" d="{TILE}"/><path fill="{WHITE}" d="{R}"/><path fill="{TEAL_ON_NAVY}" d="{G}"/>'
    elif kind == "reversed":
        body = f'<path fill="{WHITE}" d="{TILE}"/><path fill="{NAVY}" d="{R}"/><path fill="{TEAL}" d="{G}"/>'
    else:  # one color: letters are cut out of the tile
        body = f'<path fill="{kind}" fill-rule="evenodd" d="{TILE}{R}{G}"/>'
    return f"<g{move}>{body}</g>"

def svg(w, h, body, title="RevisionGate"):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(w)} {num(h)}" width="{num(w)}" height="{num(h)}" role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n'

def wordmark(kind, word, accent, ground=None):
    pad = 12 if ground else 0
    # outline() returns one path per character; join each word into a single path
    revision, rev_end = outline(WORD_WEIGHT, "Revision", WORD_SIZE, 60 + pad, 34.5 + pad, WORD_TRACK * WORD_SIZE)
    gate, end = outline(WORD_WEIGHT, "Gate", WORD_SIZE, rev_end + WORD_TRACK * WORD_SIZE, 34.5 + pad, WORD_TRACK * WORD_SIZE)
    a, b = "".join(revision), "".join(gate)
    w, h = round(end + 4 + pad), 48 + 2 * pad
    back = f'<rect width="{w}" height="{h}" fill="{ground}"/>' if ground else ""
    return svg(w, h, back + mark(kind, pad, pad) + f'<path fill="{word}" d="{a}"/><path fill="{accent}" d="{b}"/>')

def favicon():
    r, g = monogram(FAV_GRID, FAV_WIDTH, FAV_WEIGHT)
    return svg(FAV_GRID, FAV_GRID, f'<path fill="{NAVY}" d="{tile(FAV_GRID, FAV_RADIUS)}"/><path fill="{WHITE}" d="{r}"/><path fill="{TEAL_ON_NAVY}" d="{g}"/>')

def explorations():
    label = lambda x, title, note, weight=650: (f'<text x="{x}" y="150" text-anchor="middle" font-size="13" font-weight="{weight}">{title}</text>'
                                                 f'<text x="{x}" y="168" text-anchor="middle" font-size="11" fill="#4F6074">{note}</text>')
    gate = ('<g transform="translate(42 28) scale(2)"><path fill="#132238" d="M6 6h36v6H36v30h-6V12H18v30h-6V12H6z"/>'
            '<rect fill="#007F7A" x="18" y="24" width="12" height="5" rx="1"/></g>')
    line = ('<g transform="translate(222 28) scale(2)"><path fill="#132238" d="M11 6h10v13.5H10.5v9H21V42H6V11z"/>'
            '<path fill="#132238" d="M27 6h10l5 5v31H27V28.5h10.5v-9H27z"/><rect fill="#007F7A" x="12" y="21" width="24" height="6" rx="1"/></g>')
    chosen = '<rect x="366" y="14" width="168" height="166" rx="10" fill="#FFFFFF" stroke="#007F7A" stroke-width="2"/>'
    rg = f'<g transform="translate(402 28) scale(2)">{mark("color")}</g>'
    body = ('<rect width="540" height="190" fill="#F5F7F9"/><g font-family="Inter, system-ui, sans-serif" fill="#132238">'
            + gate + label(90, "A. Gate", "Posts, lintel, bar") + line + label(270, "B. Gate line", "Two sheets, one bar across both")
            + chosen + rg + label(450, "C. Compact RG (chosen)", "Initials on a tile") + "</g>")
    return svg(540, 190, body, "Three RevisionGate logo directions")

files = {
    "revisiongate-wordmark.svg": wordmark("color", NAVY, TEAL),
    "revisiongate-wordmark-reversed.svg": wordmark("reversed", WHITE, TEAL_ON_NAVY, NAVY),
    "revisiongate-wordmark-mono.svg": wordmark(NAVY, NAVY, NAVY),
    "revisiongate-mark.svg": svg(GRID, GRID, mark("color")),
    "revisiongate-mark-reversed.svg": svg(GRID + 24, GRID + 24, f'<rect width="{GRID + 24}" height="{GRID + 24}" fill="{NAVY}"/>' + mark("reversed", 12, 12)),
    "revisiongate-mark-mono.svg": svg(GRID, GRID, mark(NAVY)),
    "revisiongate-mark-mono-white.svg": svg(GRID, GRID, mark(WHITE)),
    "favicon.svg": favicon(),
    "explorations.svg": explorations(),
}
OUT.mkdir(parents=True, exist_ok=True)
for name, content in files.items():
    (OUT / name).write_text(content)
    print(f"wrote {name:38} {len(content):6} bytes")
PUBLIC.mkdir(parents=True, exist_ok=True)
for name in ("favicon.svg", "revisiongate-mark.svg", "revisiongate-wordmark-reversed.svg"):
    (PUBLIC / name).write_text(files[name])
(ROOT / "frontend/src/design/logoPaths.ts").write_text(
    "// Generated by design/brand/build_logos.py. Do not edit by hand.\n"
    f'export const logoPaths = {{\n  tile: "{TILE}",\n  r: "{R}",\n  g: "{G}",\n}} as const;\n')
print("wrote frontend/public/brand copies and frontend/src/design/logoPaths.ts")
