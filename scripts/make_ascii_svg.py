#!/usr/bin/env python3
"""
Convert the prepped portrait into a monochrome ASCII-art SVG that "types"
itself in row by row (SMIL clip wipe + block cursor), then freezes.
Canvas is 840 x 880 to match info-card.svg.

    python scripts/make_ascii_svg.py [source-prepped.png] [portrait.svg]
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame for previews
"""
import html
import os
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "portrait.svg")
STATIC = bool(os.environ.get("STATIC"))

W, H = 840, 880
PAD, TITLEBAR_H, STATUS_H = 20, 30, 34
ART_W = W - 2 * PAD
ART_H = H - TITLEBAR_H - STATUS_H - 2 * 6

COLS = int(os.environ.get("COLS", 150))
CELL_W = ART_W / COLS
CELL_H = CELL_W * 15 / 8          # monospace glyph aspect
ROWS = int(ART_H // CELL_H)
RAMP = " .`:-=+*cs#%@"            # sparse -> dense
# light-on-dark terminal: bright skin -> dense glyphs, dark hair/clothes -> sparse
# (set INVERT=1 for the classic dark-on-paper mapping)
INVERT = bool(os.environ.get("INVERT"))
ZOOM = float(os.environ.get("ZOOM", 0.82))   # <1 crops in on the head

CONTRAST = float(os.environ.get("CONTRAST", 1.05))
GAMMA = float(os.environ.get("GAMMA", 1.0))
FLOOR = float(os.environ.get("FLOOR", 0.14))  # density below this -> blank

BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK = "#7d8590", "#c9d1d9"
ROW_DUR = 5.5 / ROWS

src = Image.open(SRC)
alpha = src.getchannel("A") if "A" in src.getbands() else Image.new("L", src.size, 255)
im = ImageEnhance.Contrast(src.convert("L")).enhance(CONTRAST)
# zoom: square crop centred horizontally, anchored near the top (head)
side = int(im.width * ZOOM)
zx = (im.width - side) // 2
zy = int((im.height - side) * 0.1)
im = im.crop((zx, zy, zx + side, zy + side))
alpha = alpha.crop((zx, zy, zx + side, zy + side))
# fit the square image into the art box (rows*cell_h may be < cols*cell_w)
art_px_h = ROWS * CELL_H
crop_h = im.height * min(1.0, art_px_h / ART_W)
top = (im.height - crop_h) * 0.3
box = (0, int(top), im.width, int(top + crop_h))
im = im.crop(box).resize((COLS, ROWS), Image.LANCZOS)
alpha = alpha.crop(box).resize((COLS, ROWS), Image.LANCZOS)
px, pa = im.load(), alpha.load()

rows = []
for y in range(ROWS):
    line = []
    for x in range(COLS):
        lum = (px[x, y] / 255.0) ** GAMMA
        dens = (1.0 - lum) if INVERT else lum
        if pa[x, y] < 128 or dens < FLOOR:
            line.append(" ")
            continue
        idx = int(dens * (len(RAMP) - 1) + 0.5)
        line.append(RAMP[max(0, min(len(RAMP) - 1, idx))])
    rows.append("".join(line).rstrip().ljust(COLS))

art_top = TITLEBAR_H + 6 + (ART_H - ROWS * CELL_H) / 2
p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
    f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
         f'vishal@github: ~$ ./portrait.sh</text>')

fs = CELL_H * 0.86
for ry, line in enumerate(rows):
    row_y = art_top + ry * CELL_H
    text = (f'<text xml:space="preserve" x="{PAD}" y="{row_y + CELL_H * 0.74:.1f}" fill="{INK}" '
            f'font-size="{fs:.2f}" textLength="{ART_W}" lengthAdjust="spacing">{html.escape(line)}</text>')
    if STATIC or not line.strip():
        p.append(text)
        continue
    d = ry * ROW_DUR
    p.append(f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
             f'<animate attributeName="width" from="0" to="{ART_W}" begin="{d:.3f}s" dur="{ROW_DUR:.3f}s" fill="freeze"/>'
             f'</rect></clipPath><g clip-path="url(#r{ry})">{text}</g>')
    p.append(f'<rect y="{row_y + 1:.1f}" width="{CELL_W:.2f}" height="{CELL_H - 2:.2f}" fill="{INK}" opacity="0">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W}" begin="{d:.3f}s" dur="{ROW_DUR:.3f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0.85" begin="{d:.3f}s"/>'
             f'<set attributeName="opacity" to="0" begin="{d + ROW_DUR:.3f}s"/></rect>')

sy = H - STATUS_H
p.append(f'<line x1="0" y1="{sy}" x2="{W}" y2="{sy}" stroke="{FRAME}"/>')
ty = sy + 22
label = "vishal@github:~$ whoami "
p.append(f'<text x="{PAD}" y="{ty}" fill="{MUTED}" font-size="13">{label}<tspan fill="{INK}">Vishal Gupta</tspan></text>')
cx = PAD + len(label + "Vishal Gupta ") * 13 * 0.6
p.append(f'<rect x="{cx:.1f}" y="{ty - 12}" width="8" height="14" fill="{INK}">'
         + ("" if STATIC else '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>')
         + "</rect>")
p.append("</svg>")
svg = "".join(p)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {W}x{H}, {COLS}x{ROWS} chars, {len(svg) // 1024} KB")
