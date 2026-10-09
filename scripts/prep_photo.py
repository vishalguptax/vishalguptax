#!/usr/bin/env python3
"""
Prep a portrait photo for clean ASCII conversion (run once per photo):
  1. remove the background (rembg, human-segmentation model)
  2. boost local contrast with CLAHE so a flatly-lit face gets real
     highlights and shadows
  3. keep the subject mask as alpha (background -> blank) and
     square-crop around the subject

    pip install -r scripts/requirements-portrait.txt
    python scripts/prep_photo.py source-photo.jpg [source-prepped.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

src = Image.open(INP).convert("RGBA")
# a PNG that already has transparency is treated as pre-cut
alpha_in = np.array(src.split()[-1])
if alpha_in.min() < 250:
    cut = src
else:
    cut = remove(src, session=new_session(os.environ.get("REMBG_MODEL", "u2net_human_seg")))

rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

# local contrast
clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8))
gray = clahe.apply(gray)

# stretch tones over the subject only: skin toward light, hair/clothes dark
lo, hi = np.percentile(gray[alpha > 128], [3, 97])
tone = np.clip((gray.astype(np.float32) - lo) / max(hi - lo, 1), 0, 1)

# emphasise facial lines (brows, eyes, mouth) that averaging would wash out
fine = cv2.GaussianBlur(gray, (0, 0), 1.5).astype(np.float32)
coarse = cv2.GaussianBlur(gray, (0, 0), 6).astype(np.float32)
lines = np.clip((coarse - fine) / 40.0, 0, 1)
out = np.clip(tone - 0.45 * lines, 0, 1) * 255

mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = out * mask + 255.0 * (1.0 - mask)

ys, xs = np.where(alpha > 20)
side = max(xs.max() - xs.min(), ys.max() - ys.min()) + 40
cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
canvas = np.full((side, side), 255, np.uint8)
amask = np.zeros((side, side), np.uint8)
x0, y0 = cx - side // 2, cy - side // 2
sx0, sy0 = max(x0, 0), max(y0, 0)
sx1, sy1 = min(x0 + side, out.shape[1]), min(y0 + side, out.shape[0])
canvas[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = out[sy0:sy1, sx0:sx1].astype(np.uint8)
amask[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = alpha[sy0:sy1, sx0:sx1]

# grayscale + alpha: make_ascii_svg.py uses the alpha to blank the background
Image.merge("LA", (Image.fromarray(canvas), Image.fromarray(amask))).save(OUT)
print("wrote", OUT, canvas.shape)
