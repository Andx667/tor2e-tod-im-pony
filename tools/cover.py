#!/usr/bin/env python3
"""Malt das Titelbild von „Tod im Tänzelnden Pony“: Bree bei Nacht im Herbstregen, der Bree-Hill
als dunkler Rücken, warme Fenster, vorn der Hag mit seiner Lücke und eine Gestalt mit Laterne auf
dem Weg. Rein prozedural (numpy, OpenCV), anschließend malerisch nachbearbeitet.

    python3 tools/cover.py            # -> assets/cover-de.jpg
"""
import os
import numpy as np
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "cover-de.jpg")
W, H = 2400, 1600
rng = np.random.default_rng(11)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def C(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def noise(scale, octaves=5, seed=0, pers=0.5, stretch=1.0):
    r = np.random.default_rng(seed)
    out = np.zeros((H, W), np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        cw = max(2, int(W / scale * 2 ** o / stretch)); ch = max(2, int(H / scale * 2 ** o))
        out += amp * cv2.resize(r.random((ch, cw)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
        tot += amp; amp *= pers
    out /= tot
    return np.clip((out - out.min()) / (out.max() - out.min() + 1e-6), 0, 1)


def lerp(a, b, t):
    return a + (b - a) * t


def blend(img, col, mask):
    return img * (1 - mask[..., None]) + col * mask[..., None]


def poly_mask(polys, ss=2):
    m = np.zeros((H * ss, W * ss), np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.round(np.array(p) * ss).astype(np.int32)], 255, cv2.LINE_AA)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def glow(img, cx, cy, r, col, strength):
    g = np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * r * r)))
    return blend(img, col, np.clip(g * strength, 0, 1))


# ======================= Himmel =======================
t = np.clip(yy / (H * 0.55), 0, 1)
img = lerp(C("#141a22"), C("#3a4250"), t[..., None])
clouds = np.clip((noise(600, 6, 1, stretch=2.4) - 0.42) * 2.4, 0, 1)
img = blend(img, C("#55606d"), clouds * 0.45 * (1 - t) + clouds * 0.25)
# Mondschein hinter Wolken, rechts oben
img = glow(img, W * 0.78, H * 0.16, 160, C("#b9c2c8"), 0.55 * (0.5 + 0.5 * clouds))

# ======================= Bree-Hill =======================
hz = H * 0.52
xs = np.linspace(0, W, 60)
ridge = hz - 330 * np.exp(-((xs - W * 0.62) / (W * 0.28)) ** 2) - 40 * np.sin(xs / 210)
hillp = [(x, y) for x, y in zip(xs, ridge)] + [(W, H), (0, H)]
m = poly_mask([hillp])
hilltex = noise(180, 5, 3)
img = blend(img, lerp(C("#151a1c"), C("#262c2c"), hilltex[..., None]), m)

# ======================= Bree: Dächer und Fenster =======================
houses = []
r = np.random.default_rng(5)
for i in range(46):
    x = r.uniform(W * 0.08, W * 0.92)
    base = hz + r.uniform(40, 260) - 120 * np.exp(-((x - W * 0.62) / (W * 0.28)) ** 2)
    w = r.uniform(90, 190); h = r.uniform(60, 110)
    houses.append((base, x, w, h))
houses.sort()
for base, x, w, h in houses:
    depth = np.clip((base - hz) / 300, 0, 1)
    body = [(x - w / 2, base), (x + w / 2, base), (x + w / 2, base - h), (x - w / 2, base - h)]
    roof = [(x - w / 2 - 14, base - h + 2), (x + w / 2 + 14, base - h + 2), (x + w * 0.1, base - h - h * 0.7), (x - w * 0.2, base - h - h * 0.7)]
    img = blend(img, lerp(C("#1d2121"), C("#2e2b27"), depth), poly_mask([body]))
    img = blend(img, lerp(C("#151818"), C("#231f1c"), depth), poly_mask([roof]))
    for k in range(int(r.integers(0, 3))):
        wx = x - w / 2 + r.uniform(18, w - 30); wy = base - h + r.uniform(18, h - 34)
        win = [(wx, wy), (wx + 16, wy), (wx + 16, wy + 20), (wx, wy + 20)]
        img = blend(img, C("#f0b45a"), poly_mask([win]) * 0.95)
        img = glow(img, wx + 8, wy + 10, 38, C("#d98a35"), 0.35)

# Das Pony: größeres Haus mit vielen Fenstern, links der Mitte
px, pb, pw, ph = W * 0.36, hz + 300, 420, 190
img = blend(img, C("#2a2622"), poly_mask([[(px - pw / 2, pb), (px + pw / 2, pb), (px + pw / 2, pb - ph), (px - pw / 2, pb - ph)]]))
img = blend(img, C("#1b1917"), poly_mask([[(px - pw / 2 - 26, pb - ph + 4), (px + pw / 2 + 26, pb - ph + 4), (px + 90, pb - ph - 120), (px - 120, pb - ph - 120)]]))
for row in range(2):
    for k in range(5):
        wx = px - pw / 2 + 36 + k * 76; wy = pb - ph + 30 + row * 82
        img = blend(img, C("#f6c06a"), poly_mask([[(wx, wy), (wx + 26, wy), (wx + 26, wy + 34), (wx, wy + 34)]]))
        img = glow(img, wx + 13, wy + 17, 60, C("#e09440"), 0.32)
# ein offenes Fenster oben rechts, kalt
img = blend(img, C("#3b4652"), poly_mask([[(px + 150, pb - ph + 30), (px + 176, pb - ph + 30), (px + 176, pb - ph + 64), (px + 150, pb - ph + 64)]]))

# ======================= Vordergrund: Weg und Hag =======================
fg = H * 0.80
ground = [(0, fg), (W, fg - 30), (W, H), (0, H)]
img = blend(img, lerp(C("#1a1814"), C("#0f0e0c"), np.clip((yy - fg) / (H - fg), 0, 1)[..., None]), poly_mask([ground]))
# Weg, nass glänzend, von unten in die Lücke
road = [(W * 0.52, H), (W * 0.80, H), (W * 0.64, fg - 6), (W * 0.60, fg - 6)]
rm = poly_mask([road])
img = blend(img, C("#2b2a27"), rm)
img = blend(img, C("#7b6a52"), rm * np.clip((noise(40, 3, 9) - 0.6) * 3, 0, 1) * 0.5)
# Hag: dichte Büsche links und rechts der Lücke
bush = noise(60, 5, 7)
for x0, x1 in ((0, W * 0.59), (W * 0.655, W)):
    top = fg - 170 + 60 * noise(90, 4, 8)[int(fg) - 1]
    xsel = (xx >= x0) & (xx <= x1)
    edge = fg - 150 - 70 * bush
    mask = (xsel & (yy > edge) & (yy < fg + 40)).astype(np.float32)
    mask = cv2.GaussianBlur(mask, (0, 0), 2.2)
    img = blend(img, lerp(C("#07090a"), C("#2a3022"), np.clip(bush * 1.3 - 0.2, 0, 1)[..., None]), mask)

# Gestalt mit Laterne in der Lücke: erst das Licht, dann die dunkle Gestalt davor
fx, fy = W * 0.622, fg - 8
lx, ly = fx + 40, fy - 70
img = glow(img, lx - 20, ly - 20, 190, C("#d08a3a"), 0.55)
body = [(fx - 30, fy), (fx + 30, fy), (fx + 21, fy - 130), (fx + 9, fy - 160), (fx - 9, fy - 160), (fx - 23, fy - 130)]
hood = [(fx - 18, fy - 156), (fx + 18, fy - 156), (fx + 7, fy - 196), (fx - 9, fy - 196)]
arm = [(fx + 14, fy - 120), (fx + 22, fy - 126), (fx + 42, fy - 84), (fx + 36, fy - 80)]
img = blend(img, C("#070707"), poly_mask([body, hood, arm]))
img = glow(img, lx, ly, 26, C("#ffd58a"), 1.0)
img = blend(img, C("#fff0c8"), np.clip(1 - ((xx - lx) ** 2 + (yy - ly) ** 2) / 49, 0, 1))
# Widerschein auf dem nassen Weg
img = glow(img, lx - 10, fg + 120, 110, C("#9a6a33"), 0.30)

# ======================= Regen, Dunst, Malstrich =======================
rain = np.zeros((H, W), np.float32)
for _ in range(2600):
    x, y = rng.uniform(0, W), rng.uniform(0, H); L = rng.uniform(30, 70)
    cv2.line(rain, (int(x), int(y)), (int(x - L * 0.18), int(y + L)), float(rng.uniform(0.15, 0.45)), 1, cv2.LINE_AA)
img = blend(img, C("#9aa6b0"), np.clip(rain, 0, 1) * 0.35)
mist = noise(400, 4, 21) * np.exp(-((yy - hz - 160) / 220) ** 2)
img = blend(img, C("#4a5258"), mist * 0.28)
# Vignette
vig = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2
img = img * (1 - np.clip(vig - 0.35, 0, 1)[..., None] * 0.55)

out = np.clip(img * 255, 0, 255).astype(np.uint8)[..., ::-1]
out = cv2.edgePreservingFilter(out, flags=1, sigma_s=40, sigma_r=0.25)
grain = (rng.normal(0, 4, (H, W, 1))).astype(np.float32)
out = np.clip(out.astype(np.float32) + grain, 0, 255).astype(np.uint8)
cv2.imwrite(OUT, out, [cv2.IMWRITE_JPEG_QUALITY, 88])
print("ok:", OUT)
