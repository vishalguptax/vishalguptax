#!/usr/bin/env python3
"""
Render data/contributions.json as an animated 53-week contribution heatmap.

Boxes pop in on a diagonal sweep (CSS keyframes, play once then freeze),
with month/day labels, a Less -> More legend and a totals footer.
GitHub runs CSS/SMIL inside <img>-embedded SVGs but never JS, so all motion
lives in this file.

    python scripts/render_heatmap_svg.py [data.json] [output.svg]
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "contrib-heatmap.svg")

data = json.load(open(SRC))
days = data["days"]
user = data.get("username", "vishalguptax")

BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK, GREEN = "#7d8590", "#e6edf3", "#39d353"
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

CELL, GAP, RAD = 13, 3, 2.5
PAD, TITLEBAR_H = 20, 30
LEFT = PAD + 32
TOP = TITLEBAR_H + 40

# pad the front so column 0 starts on a Sunday (github's layout)
first = datetime.date.fromisoformat(days[0]["date"])
lead = (first.weekday() + 1) % 7  # Mon=0 -> Sun=0
NW = (lead + len(days) + 6) // 7

W = LEFT + NW * (CELL + GAP) + PAD
GRID_H = 7 * (CELL + GAP)
H = TOP + GRID_H + 52

REVEAL, DUR = 3.2, 0.5
maxorder = (NW - 1) + 6 * 0.55

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    "<style>"
    f".l{{fill:{MUTED};font-size:11px}}"
    f".c{{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop {DUR}s ease-out both}}"
    f".g{{animation:pop {DUR}s ease-out both,flash {DUR + 0.2}s ease-out both}}"
    "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.12)}100%{opacity:1;transform:scale(1)}}"
    "@keyframes flash{0%,45%{filter:brightness(2.3)}100%{filter:brightness(1)}}"
    f".f{{opacity:0;animation:fade .6s ease-out {REVEAL + 0.3:.1f}s both}}"
    "@keyframes fade{to{opacity:1}}"
    "@media (prefers-reduced-motion: reduce){.c,.f{opacity:1!important;animation:none!important}}"
    "</style>",
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
    f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
         f'vishal@github: ~$ ./contributions.sh</text>')

# month labels (skip one that would collide with the previous)
last_m, last_x = None, -99
for wk in range(NW):
    d = first + datetime.timedelta(days=wk * 7 - lead)
    if d.month != last_m:
        last_m = d.month
        x = LEFT + wk * (CELL + GAP)
        if x - last_x >= 30:
            p.append(f'<text class="l" x="{x}" y="{TOP - 9}">{MONTHS[d.month - 1]}</text>')
            last_x = x
for name, r in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
    p.append(f'<text class="l" x="{PAD}" y="{TOP + r * (CELL + GAP) + CELL - 3}">{name}</text>')

for i, c in enumerate(days):
    j = i + lead
    wk, row, lvl = j // 7, j % 7, min(int(c["level"]), 4)
    x, y = LEFT + wk * (CELL + GAP), TOP + row * (CELL + GAP)
    delay = round((wk + row * 0.55) / maxorder * REVEAL, 3)
    cls = "c g" if lvl else "c"
    tip = f'{c["count"]} contribution{"" if c["count"] == 1 else "s"} on {c["date"]}'
    p.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
             f'fill="{COLORS[lvl]}" style="animation-delay:{delay}s"><title>{tip}</title></rect>')

# footer: total + legend
fy = TOP + GRID_H + 26
p.append(f'<g class="f"><text x="{LEFT}" y="{fy}" fill="{INK}" font-size="14" font-weight="700">'
         f'{data["total_contributions"]:,} contributions <tspan fill="{MUTED}" font-weight="400">in the last year'
         f' · {data["active_days"]} active days · longest streak {data["longest_streak"]["length"]}d</tspan></text>')
lx = W - PAD - 5 * (CELL + GAP) - 40
p.append(f'<text class="l" x="{lx - 36}" y="{fy - 1}">Less</text>')
for k, col in enumerate(COLORS):
    p.append(f'<rect x="{lx + k * (CELL + GAP)}" y="{fy - CELL + 1}" width="{CELL}" height="{CELL}" rx="{RAD}" fill="{col}"/>')
p.append(f'<text class="l" x="{lx + 5 * (CELL + GAP) + 4}" y="{fy - 1}">More</text></g>')

p.append("</svg>")
svg = "".join(p)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {W}x{H}, {len(days)} days, {data['total_contributions']:,} contributions, {len(svg) // 1024} KB")
