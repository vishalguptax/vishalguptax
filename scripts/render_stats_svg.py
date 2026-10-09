#!/usr/bin/env python3
"""
Wide streak / numbers card from data/contributions.json (refreshed daily).
Canvas is 1720 x 520 and is shown at width 860 in the README (2x for crisp
text). Six tiles slide in and count up to their real values (pre-rendered
frames toggled with SMIL <set> -- GitHub runs SMIL, never JS), then a
monthly bar chart grows in on the right.

    python scripts/render_stats_svg.py [data.json] [output.svg]
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "stats.svg")

BG, BG2, TILE, FRAME = "#0d1117", "#111722", "#161b22", "#30363d"
MUTED, INK, GREEN, BAR = "#7d8590", "#e6edf3", "#39d353", "#26a641"

W, H = 1720, 520
PAD, GAP, TITLEBAR_H = 32, 20, 44
COLS, ROWS = 3, 2
TILES_W = 1040
TILE_W = (TILES_W - GAP * (COLS - 1)) / COLS
TOP = TITLEBAR_H + PAD
TILE_H = (H - TOP - PAD - GAP * (ROWS - 1)) / ROWS
CHART_X = PAD + TILES_W + GAP
CHART_W = W - CHART_X - PAD

TILE_STAGGER, SLIDE_DUR, COUNT_DUR, FRAMES = 0.15, 0.45, 1.2, 16
BAR_START = TILE_STAGGER * COLS * ROWS + 0.4
BAR_STAGGER, BAR_DUR = 0.06, 0.6


def short(d):
    return datetime.date.fromisoformat(d).strftime("%b %-d")


def span(s):
    return f'{short(s["start"])} – {short(s["end"])}' if s["length"] else "start one today"


data = json.load(open(SRC))
user = data.get("username", "vishalguptax")
cur, lng, best = data["current_streak"], data["longest_streak"], data["best_day"]
n_days = len(data["days"])

tiles = [
    ("current streak", cur["length"], " days", span(cur), GREEN),
    ("longest streak", lng["length"], " days", span(lng), INK),
    ("contributions", data["total_contributions"], "", "in the last year", INK),
    ("active days", data["active_days"], f" / {n_days}", f'{data["active_days"] / n_days:.0%} of the year', INK),
    ("best day", best["count"], "", short(best["date"]), INK),
    ("avg / active day", data["avg_per_active_day"], "", "contributions", INK),
]


def fmt(v, like):
    return f"{v:,.1f}" if isinstance(like, float) else f"{int(round(v)):,}"


p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    "<style>"
    f".t{{opacity:0;animation:in {SLIDE_DUR}s ease-out both}}"
    "@keyframes in{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}"
    f".b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_DUR}s ease-out both}}"
    "@keyframes grow{to{transform:scaleY(1)}}"
    "@media (prefers-reduced-motion: reduce){.t,.b{opacity:1!important;transform:none!important;animation:none!important}}"
    "</style>",
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
    f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="20" fill="url(#bg)"/>',
    f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="20" fill="none" stroke="{FRAME}" stroke-width="2"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}" stroke-width="2"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i * 24}" cy="{TITLEBAR_H / 2}" r="8" fill="{dot}"/>')
p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 7}" fill="{MUTED}" font-size="20" text-anchor="middle">'
         f'vishal@github: ~$ ./stats.sh</text>')

for i, (label, value, suffix, caption, accent) in enumerate(tiles):
    col, row = i % COLS, i // COLS
    x = PAD + col * (TILE_W + GAP)
    y = TOP + row * (TILE_H + GAP)
    start = i * TILE_STAGGER
    count_start = start + SLIDE_DUR * 0.6
    p.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
    p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{TILE_W:.1f}" height="{TILE_H:.1f}" rx="14" '
             f'fill="{TILE}" stroke="{FRAME}" stroke-width="2"/>')
    p.append(f'<text x="{x + 26:.1f}" y="{y + 44:.1f}" fill="{MUTED}" font-size="24">$ {label}</text>')
    num_y = y + 112
    for k in range(1, FRAMES + 1):
        v = value * (1 - (1 - k / FRAMES) ** 3)
        t_on = count_start + COUNT_DUR * (k - 1) / FRAMES
        t_off = count_start + COUNT_DUR * k / FRAMES
        anim = f'<set attributeName="opacity" to="1" begin="{t_on:.3f}s"/>'
        if k < FRAMES:
            anim += f'<set attributeName="opacity" to="0" begin="{t_off:.3f}s"/>'
        p.append(f'<text x="{x + 26:.1f}" y="{num_y:.1f}" opacity="0" font-size="60" font-weight="700" fill="{accent}">'
                 f'{fmt(v, value)}<tspan font-size="26" font-weight="400" fill="{MUTED}">{suffix}</tspan>{anim}</text>')
    p.append(f'<text x="{x + 26:.1f}" y="{y + TILE_H - 22:.1f}" fill="{MUTED}" font-size="22">{caption}</text>')
    p.append("</g>")

# monthly bars
monthly = data["monthly"][-12:]
ch_y, ch_h = TOP, H - TOP - PAD
p.append(f'<g class="t" style="animation-delay:{BAR_START - 0.3:.2f}s">'
         f'<rect x="{CHART_X}" y="{ch_y}" width="{CHART_W}" height="{ch_h}" rx="14" fill="{TILE}" stroke="{FRAME}" stroke-width="2"/>'
         f'<text x="{CHART_X + 26}" y="{ch_y + 44}" fill="{MUTED}" font-size="24">$ contributions / month</text></g>')
plot_top, plot_bot = ch_y + 96, ch_y + ch_h - 50
plot_l, plot_r = CHART_X + 26, CHART_X + CHART_W - 26
slot = (plot_r - plot_l) / len(monthly)
bar_w = slot * 0.62
peak = max(m["total"] for m in monthly) or 1
for i, m in enumerate(monthly):
    h = max(3, (plot_bot - plot_top) * m["total"] / peak)
    bx = plot_l + i * slot + (slot - bar_w) / 2
    delay = BAR_START + i * BAR_STAGGER
    p.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - h:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="4" '
             f'fill="{GREEN if m["total"] == peak else BAR}" style="animation-delay:{delay:.2f}s">'
             f'<title>{m["month"]}: {m["total"]}</title></rect>')
    mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
    p.append(f'<text x="{bx + bar_w / 2:.1f}" y="{plot_bot + 32}" fill="{MUTED}" font-size="20" text-anchor="middle">{mon}</text>')
    if m["total"] == peak:
        p.append(f'<text class="t" style="animation-delay:{delay + BAR_DUR:.2f}s" x="{bx + bar_w / 2:.1f}" '
                 f'y="{plot_bot - h - 12:.1f}" fill="{INK}" font-size="20" text-anchor="middle">{peak:,}</text>')

p.append("</svg>")
svg = "".join(p)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {W}x{H}, {len(svg) // 1024} KB")
