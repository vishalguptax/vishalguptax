#!/usr/bin/env python3
"""
Hand-authored neofetch-style info card (840 x 880, same canvas as the ASCII
portrait so they line up side by side). Each line fades/slides in on a short
stagger. Edit LINES below when your details change, then re-run.

    python scripts/make_info_card.py            # writes info-card.svg
    STATIC=1 python scripts/make_info_card.py   # frozen frame for previews
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")
STATIC = bool(os.environ.get("STATIC"))

W, H = 840, 880
PAD, TITLEBAR_H = 28, 30
BG, BG2, FRAME = "#0d1117", "#111722", "#30363d"
MUTED, INK = "#7d8590", "#e6edf3"
GREEN, CYAN, YELLOW, PINK = "#39d353", "#56d4dd", "#e3b341", "#ff7b72"

FS = 21          # font size
LH = 34          # line height
KEY_W = 13       # key column width in chars

# (kind, key, value)  kind: head | rule | kv | gap | sub | bullet | palette
LINES = [
    ("head", "vishal", "github"),
    ("rule", "", ""),
    ("kv", "Role", "Senior Frontend Engineer"),
    ("kv", "Now", "BinaryVeda · Keus smart-home IoT"),
    ("kv", "Prev", "Tech Lead (FE) · vDoIT Technologies"),
    ("kv", "Uptime", "4+ years · web, mobile & AI"),
    ("kv", "Location", "Ambikapur, India"),
    ("gap", "", ""),
    ("kv", "Frontend", "TypeScript, React, Next.js, Svelte"),
    ("kv", "UI", "Tailwind, shadcn/ui, TanStack Query"),
    ("kv", "Backend", "Node, Express, MongoDB, Postgres"),
    ("kv", "Realtime", "NATS, WebSockets, WebRTC"),
    ("kv", "AI", "Claude Code, MCP, agents, RAG"),
    ("kv", "Shipping", "VS Code ext, MCP servers, skills"),
    ("gap", "", ""),
    ("sub", "Highlights", ""),
    ("bullet", "", "Micro-frontends: 15+ runtime modules"),
    ("bullet", "", "Web + Android + iOS, one codebase"),
    ("bullet", "", "Sub-100ms NATS control layer"),
    ("bullet", "", "LangChain RAG, ~25% faster replies"),
    ("bullet", "", "Mentored 10-15 engineers"),
    ("gap", "", ""),
    ("palette", "", ""),
]

CHAR_W = FS * 0.6
STAGGER, DUR = 0.11, 0.45

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="{FS}">',
    "<style>"
    + ("" if STATIC else
       f".ln{{opacity:0;animation:in {DUR}s ease-out both}}"
       "@keyframes in{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:translateX(0)}}"
       "@media (prefers-reduced-motion: reduce){.ln{opacity:1!important;animation:none!important}}")
    + f".k{{fill:{GREEN};font-weight:700}}.v{{fill:{INK}}}.m{{fill:{MUTED}}}"
    "</style>",
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
    f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{20 + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
p.append(f'<text x="{W / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
         f'vishal@github: ~$ neofetch</text>')

y = TITLEBAR_H + PAD + LH * 0.7
n = 0
for kind, key, val in LINES:
    if kind == "gap":
        y += LH * 0.5
        continue
    attrs = f'class="ln" style="animation-delay:{0.2 + n * STAGGER:.2f}s"' if not STATIC else ""
    k, v = html.escape(key), html.escape(val)
    if kind == "head":
        body = (f'<text x="{PAD}" y="{y:.1f}" font-size="{FS + 3}" font-weight="700">'
                f'<tspan fill="{GREEN}">{k}</tspan><tspan fill="{INK}">@</tspan>'
                f'<tspan fill="{GREEN}">{v}</tspan></text>')
    elif kind == "rule":
        body = f'<text x="{PAD}" y="{y:.1f}" class="m">{"-" * 17}</text>'
    elif kind == "kv":
        body = (f'<text x="{PAD}" y="{y:.1f}"><tspan class="k">{k}</tspan><tspan class="m">:</tspan>'
                f'<tspan x="{PAD + KEY_W * CHAR_W:.1f}" class="v">{v}</tspan></text>')
    elif kind == "sub":
        body = f'<text x="{PAD}" y="{y:.1f}" class="k">{k}<tspan class="m">:</tspan></text>'
    elif kind == "bullet":
        body = (f'<text x="{PAD}" y="{y:.1f}"><tspan fill="{YELLOW}">  › </tspan>'
                f'<tspan class="v">{v}</tspan></text>')
    elif kind == "palette":
        cols = ["#484f58", "#ff7b72", "#3fb950", "#e3b341", "#58a6ff", "#bc8cff", "#56d4dd", "#e6edf3"]
        sw = 46
        body = "".join(f'<rect x="{PAD + i * sw}" y="{y - FS + 2:.1f}" width="{sw}" height="{FS + 6}" fill="{c}"/>'
                       for i, c in enumerate(cols))
    p.append(f'<g {attrs}>{body}</g>')
    y += LH
    n += 1

# blinking prompt at the bottom
py = H - PAD - 4
p.append(f'<text x="{PAD}" y="{py}" class="m">vishal@github:~$ </text>')
cx = PAD + len("vishal@github:~$ ") * CHAR_W
p.append(f'<rect x="{cx:.1f}" y="{py - FS + 4}" width="{CHAR_W:.1f}" height="{FS}" fill="{INK}">'
         + ("" if STATIC else
            '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/>')
         + "</rect>")

p.append("</svg>")
svg = "".join(p)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: {W}x{H}, last line y={y:.0f}, {len(svg) // 1024} KB")
