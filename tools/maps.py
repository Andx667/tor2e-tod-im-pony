"""Zeichnet die Karten von „Tod im Tänzelnden Pony“ (Loremaster- und Spielerfassung), das
Routendiagramm und die beiden Schaubilder (Personen, Beweise).

Helfer (rough, blob, label, num, frame …) übernommen aus tools/maps.py von Graufieber und der Finsterwacht.

Optional step: the rendered JPGs are committed in assets/maps and assets/diagrams, so the PDF build
never needs this. Run it only after changing a map:

    pip install playwright pillow && playwright install chromium
    python3 tools/maps.py
"""
import random, math
from playwright.sync_api import sync_playwright

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "assets", "maps") + os.sep
SVG = os.path.join(D, "svg") + os.sep
INK, RED = "#3a2716", "#8a2e1e"
W, H = 800, 600
GM = True


def rough(pts, closed=False, jit=2.2, seg=14, seed=1):
    """Hand-drawn polyline: subdivide each segment and jitter the points."""
    r = random.Random(seed)
    P = pts + ([pts[0]] if closed else [])
    out = []
    for (x1, y1), (x2, y2) in zip(P, P[1:]):
        n = max(1, int(math.hypot(x2 - x1, y2 - y1) / seg))
        for i in range(n):
            t = i / n
            out.append((x1 + (x2 - x1) * t + r.uniform(-jit, jit), y1 + (y2 - y1) * t + r.uniform(-jit, jit)))
    out.append(P[-1] if not closed else out[0])
    d = f"M{out[0][0]:.1f} {out[0][1]:.1f}"
    for (ax, ay), (bx, by) in zip(out, out[1:]):
        d += f" Q{ax:.1f} {ay:.1f} {(ax + bx) / 2:.1f} {(ay + by) / 2:.1f}"
    d += f" L{out[-1][0]:.1f} {out[-1][1]:.1f}"
    return d + (" Z" if closed else "")


def blob(cx, cy, rx, ry, irr=0.08, n=28, seed=1, a0=0, a1=360):
    r = random.Random(seed)
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        k = 1 + r.uniform(-irr, irr)
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts


def path(d, w=1.6, col=INK, dash=None, fill="none", op=1):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<path d="{d}" fill="{fill}" stroke="{col}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round" opacity="{op}"{da}/>'


def label(x, y, txt, size=24, anchor="middle", rot=0, col=INK, style=""):
    tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
    return f'<text x="{x}" y="{y}" font-family="TeX Gyre Chorus" font-size="{size}" fill="{col}" text-anchor="{anchor}"{tr} {style}>{txt}</text>'


def num(x, y, n):
    if not GM:
        return ""
    return (f'<circle cx="{x}" cy="{y}" r="13" fill="#efe2c4" stroke="{RED}" stroke-width="1.6"/>'
            f'<text x="{x}" y="{y + 5.5}" font-family="TeX Gyre Pagella" font-weight="700" font-size="16" fill="{RED}" text-anchor="middle">{n}</text>')


def hachures(pts, out=True, length=12, every=1, seed=3, w=1.1):
    """Short strokes pointing outward from a polygon edge (cliffs, earthworks)."""
    r = random.Random(seed)
    s = ""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    for i, (x1, y1) in enumerate(pts[:-1]):
        x2, y2 = pts[i + 1]
        n = int(math.hypot(x2 - x1, y2 - y1) / 9)
        for j in range(0, n, every):
            t = j / max(n, 1)
            x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            dx, dy = x - cx, y - cy
            L = math.hypot(dx, dy) or 1
            k = length * r.uniform(0.6, 1.25) * (1 if out else -1)
            s += path(f"M{x:.1f} {y:.1f} L{x + dx / L * k:.1f} {y + dy / L * k:.1f}", w)
    return s


def trees(cx, cy, n, spread, seed):
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = cx + r.uniform(-spread, spread), cy + r.uniform(-spread * 0.6, spread * 0.6)
        s += path(rough([(x - 5, y + 4), (x, y - 6), (x + 5, y + 4)], jit=0.6, seg=5, seed=r.randint(0, 999)), 1.2)
    return s


def compass(x, y):
    return (f'<g transform="translate({x} {y})">'
            + path(rough([(0, -38), (7, 0), (0, 38), (-7, 0)], closed=True, jit=0.7, seg=8, seed=5), 1.4)
            + path("M0 -38 L7 0 L0 0 Z", 0.5, fill=INK, op=0.85)
            + path(rough([(-30, 0), (30, 0)], jit=0.6, seed=6), 1)
            + f'<text x="0" y="-44" font-family="TeX Gyre Pagella" font-weight="700" font-size="16" fill="{INK}" text-anchor="middle">N</text></g>')


def cartouche(x, y, title, sub, w=250):
    return (path(rough([(x, y), (x + w, y), (x + w, y + 64), (x, y + 64)], closed=True, jit=1.2, seed=9), 1.5, fill="#efe2c4", op=0.95)
            + path(rough([(x + 6, y + 6), (x + w - 6, y + 6), (x + w - 6, y + 58), (x + 6, y + 58)], closed=True, jit=0.9, seed=10), 0.8)
            + label(x + w / 2, y + 33, title, 30, col=RED)
            + label(x + w / 2, y + 52, sub, 17))


def frame(content, seed):
    r = random.Random(seed)
    edge = []
    for (x1, y1), (x2, y2) in zip([(6, 6), (W - 6, 6), (W - 6, H - 6), (6, H - 6)], [(W - 6, 6), (W - 6, H - 6), (6, H - 6), (6, 6)]):
        n = 40
        for i in range(n):
            t = i / n
            edge.append((x1 + (x2 - x1) * t + r.uniform(-3.5, 3.5), y1 + (y2 - y1) * t + r.uniform(-3.5, 3.5)))
    clip = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in edge) + " Z"
    stains = "".join(
        f'<circle cx="{r.uniform(60, W - 60):.0f}" cy="{r.uniform(60, H - 60):.0f}" r="{r.uniform(30, 90):.0f}" fill="url(#stain)" opacity="{r.uniform(0.25, 0.55):.2f}"/>'
        for _ in range(6))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 2}" height="{H * 2}">
<defs>
 <clipPath id="torn"><path d="{clip}"/></clipPath>
 <filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" seed="{seed}"/>
  <feColorMatrix values="0 0 0 0 0.35  0 0 0 0 0.25  0 0 0 0 0.12  0 0 0 0.22 0"/>
 </filter>
 <filter id="blot" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="4" seed="{seed + 3}"/>
  <feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.32  0 0 0 0 0.15  0 0 0 0.55 -0.12"/>
 </filter>
 <filter id="ink" x="-5%" y="-5%" width="110%" height="110%">
  <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="{seed + 7}" result="n"/>
  <feDisplacementMap in="SourceGraphic" in2="n" scale="3" xChannelSelector="R" yChannelSelector="G"/>
 </filter>
 <radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset="55%" stop-color="#e8d8b3" stop-opacity="0"/><stop offset="100%" stop-color="#7a5528" stop-opacity="0.55"/></radialGradient>
 <radialGradient id="stain"><stop offset="0%" stop-color="#b08850" stop-opacity="0"/><stop offset="80%" stop-color="#a07840" stop-opacity="0.25"/><stop offset="100%" stop-color="#8a6230" stop-opacity="0"/></radialGradient>
 <radialGradient id="lamp"><stop offset="0%" stop-color="#e8a33a" stop-opacity="0.95"/><stop offset="100%" stop-color="#e8a33a" stop-opacity="0"/></radialGradient>
 <radialGradient id="pale"><stop offset="0%" stop-color="#cfe3e6" stop-opacity="1"/><stop offset="100%" stop-color="#9fc4cc" stop-opacity="0"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="#ffffff"/>
<g clip-path="url(#torn)">
 <rect width="{W}" height="{H}" fill="#e9dbb9"/>
 <rect width="{W}" height="{H}" filter="url(#blot)"/>
 {stains}
 <g filter="url(#ink)" opacity="0.92">{content}</g>
 <rect width="{W}" height="{H}" filter="url(#grain)"/>
 <rect width="{W}" height="{H}" fill="url(#vig)"/>
</g>
<path d="{clip}" fill="none" stroke="#6b4a24" stroke-width="1.2" opacity="0.5"/>
</svg>'''




BROWN = "#6b4a24"
WATER = "#c9c8b0"


def reeds(cx, cy, n, sx, sy, seed, col=INK, w=0.9):
    """Schilfbüschel: kurze, leicht geneigte Striche mit Kolben."""
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = cx + r.uniform(-sx, sx), cy + r.uniform(-sy, sy)
        h = r.uniform(9, 16)
        lean = r.uniform(-3, 3)
        s += path(f"M{x:.1f} {y:.1f} Q{x + lean / 2:.1f} {y - h / 2:.1f} {x + lean:.1f} {y - h:.1f}", w, col=col)
        if r.random() < 0.35:
            s += f'<ellipse cx="{x + lean:.1f}" cy="{y - h:.1f}" rx="1.3" ry="2.8" fill="{col}" transform="rotate({lean * 4:.0f} {x + lean:.1f} {y - h:.1f})"/>'
    return s


def waves(x0, y0, x1, y1, n, seed, op=0.45):
    """Wasser: kurze Wellenstriche verteilt über ein Rechteck."""
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = r.uniform(x0, x1), r.uniform(y0, y1)
        L = r.uniform(10, 22)
        s += path(f"M{x:.1f} {y:.1f} q{L / 4:.1f} -3 {L / 2:.1f} 0 t{L / 2:.1f} 0", 0.8, op=op)
    return s


def willows(cx, cy, n, spread, seed):
    """Weiden: runde Krone mit hängenden Strichen."""
    r = random.Random(seed)
    s = ""
    for _ in range(n):
        x, y = cx + r.uniform(-spread, spread), cy + r.uniform(-spread * 0.6, spread * 0.6)
        s += path(rough(blob(x, y, 9, 7, irr=0.15, n=10, seed=r.randint(0, 999), a0=180, a1=360), jit=0.6, seg=4, seed=r.randint(0, 999)), 1.1)
        for k in range(4):
            dx = -7 + k * 4.6
            s += path(f"M{x + dx:.1f} {y - 2:.1f} q1 6 {r.uniform(-1, 1):.1f} {r.uniform(9, 13):.1f}", 0.8)
    return s


def house(x, y, w, h, seed, fill="#d9c69e", lw=2.2):
    return path(rough([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], closed=True, jit=1.0, seed=seed), lw, fill=fill)



def hedge(pts, seed, gap=None):
    """Der Bree-Hag: Graben (Doppellinie) mit Buschwerk auf der Innenseite.
    gap = (i0, i1): Punkte i0..i1 bleiben ohne Buschwerk (Lücke, nur in der Loremaster-Karte)."""
    r = random.Random(seed)
    s = path(rough(pts, closed=True, jit=1.2, seed=seed), 2.0)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    inner = [(x + (cx - x) * 0.06, y + (cy - y) * 0.06) for x, y in pts]
    s += path(rough(inner, closed=True, jit=1.2, seed=seed + 1), 1.0, op=0.8)
    for i, (x, y) in enumerate(inner):
        if gap and gap[0] <= i <= gap[1]:
            continue
        for _ in range(2):
            bx, by = x + r.uniform(-6, 6), y + r.uniform(-6, 6)
            s += path(rough(blob(bx + (cx - bx) * 0.05, by + (cy - by) * 0.05, 5, 4, irr=0.2, n=8, seed=r.randint(0, 999)), closed=True, jit=0.5, seg=4, seed=r.randint(0, 999)), 0.9, fill="#b9b08a", op=0.9)
    return s


def smial(x, y, seed):
    """Hobbithöhle: runde Tür in einen Hang."""
    return (path(rough(blob(x, y, 9, 7, irr=0.08, n=12, seed=seed, a0=180, a1=360), jit=0.5, seg=4, seed=seed + 1), 1.4)
            + f'<circle cx="{x}" cy="{y - 2}" r="3.2" fill="none" stroke="{INK}" stroke-width="1.1"/>')


def hill(cx, cy, rx, ry, seed, n=60):
    """Hügel: Umriss und kurze Schraffen nach außen."""
    pts = blob(cx, cy, rx, ry, irr=0.07, n=30, seed=seed)
    return path(rough(pts, closed=True, jit=1.0, seed=seed + 1), 1.2, op=0.8) + hachures(pts, True, 9, 2, seed + 2, 0.9)


# ---------------- Das Bree-land ----------------
HALO = 'stroke="#e9dbb9" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'


def hl(x, y, txt, size=24, anchor="middle", rot=0, col=INK):
    """Beschriftung mit Pergament-Hof, damit sie auch über Bäumen und Linien lesbar bleibt."""
    return label(x, y, txt, size, anchor, rot, col, HALO)


def breeland():
    s = ""
    # Der Chetwood im Nordosten und Osten
    s += trees(640, 100, 70, 150, 1200) + trees(730, 250, 30, 60, 1201) + trees(520, 60, 25, 70, 1202)
    # Bree-Hill
    s += hill(350, 255, 95, 66, 1210)
    # Die Große Oststraße und der Greenway
    road = [(0, 360), (90, 352), (150, 350), (210, 352), (262, 382), (300, 420), (380, 438), (480, 440), (600, 448), (700, 440), (800, 450)]
    s += path(rough(road, jit=1.2, seed=1220), 1.3) + path(rough([(x, y + 11) for x, y in road], jit=1.2, seed=1221), 1.3)
    green = [(40, 600), (70, 520), (95, 440), (110, 365)]
    s += path(rough(green, jit=1.2, seed=1222), 1.1, dash="6 4")
    # Bree im Hag, am Westhang des Hügels
    hag = blob(225, 330, 105, 72, irr=0.05, n=30, seed=1230)
    s += hedge(hag, 1231, gap=(23, 25) if GM else None)
    for k, (x, y) in enumerate([(190, 312), (210, 300), (232, 296), (178, 334), (200, 340), (226, 328), (250, 316), (262, 340),
                                (276, 300), (160, 316)]):
        s += house(x - 7, y - 5, 14, 10, 1240 + k, lw=1.2)
    s += house(220, 348, 22, 14, 1255, fill="#c9a86a", lw=1.8)  # das Pony
    # Wege zwischen den Dörfern
    for k, wp in enumerate([[(300, 300), (360, 330), (420, 328)], [(470, 330), (520, 316), (540, 304)],
                            [(548, 290), (552, 230), (556, 182)], [(300, 280), (400, 210), (500, 180), (546, 166)]]):
        s += path(rough(wp, jit=1.0, seed=1290 + k), 0.9, dash="2 4")
    # Staddle an den Südosthängen
    for k, (x, y) in enumerate([(420, 316), (438, 330), (456, 318), (446, 304), (470, 334)]):
        s += smial(x, y, 1260 + k)
    # Combe in einem tiefen Tal
    s += path(rough([(500, 230), (520, 270), (530, 320), (540, 380)], jit=1.4, seed=1270), 1.0, op=0.6)
    s += path(rough([(560, 228), (566, 272), (568, 322), (572, 380)], jit=1.4, seed=1271), 1.0, op=0.6)
    for k, (x, y) in enumerate([(536, 292), (550, 306), (544, 322), (556, 286)]):
        s += house(x - 6, y - 4, 12, 9, 1272 + k, lw=1.1)
    # Archet am Rand des Chetwood
    for k, (x, y) in enumerate([(546, 160), (562, 150), (574, 168), (556, 176)]):
        s += house(x - 6, y - 4, 12, 9, 1280 + k, lw=1.1)
    s += trees(120, 480, 8, 40, 1295)
    if GM:
        # Lücke im Hag (Nordost)
        gx, gy = hag[24]
        s += path(rough([(gx - 10, gy - 6), (gx + 10, gy + 6)], jit=0.4, seed=1300), 2.4, col=RED)
        # Lager der Ranger am Rand des Chetwood
        s += f'<circle cx="640" cy="236" r="9" fill="url(#lamp)"/>' + path(rough(blob(640, 236, 26, 18, irr=0.1, n=14, seed=1310), closed=True, jit=0.6, seed=1311), 1.2, dash="4 3", col=RED)
        # Lager der Südländer in einer Senke vor dem Hag
        s += path(rough(blob(372, 168, 24, 14, irr=0.1, n=14, seed=1320), closed=True, jit=0.6, seed=1321), 1.2, dash="4 3", col=RED)
        s += f'<circle cx="372" cy="168" r="6" fill="url(#lamp)"/>'
    # Beschriftung zuletzt, mit Hof
    s += hl(700, 50, "Chetwood", 34) + hl(352, 262, "Bree-Hill", 26, col=BROWN)
    s += hl(26, 340, "Oststraße", 18, anchor="start") + hl(780, 480, "nach Osten", 17, anchor="end")
    s += hl(62, 556, "Greenway", 18, rot=-72)
    s += hl(160, 246, "Bree", 30) + hl(208, 378, "Prancing Pony", 13, col=BROWN)
    s += hl(86, 318, "Westtor", 15, col=BROWN) + hl(304, 456, "Südtor", 15, anchor="start", col=BROWN)
    s += hl(450, 362, "Staddle", 21) + hl(552, 356, "Combe", 21) + hl(598, 150, "Archet", 21, anchor="start")
    s += hl(150, 140, "Bree-land", 34, col=BROWN)
    if GM:
        s += num(250, 360, 1) + num(286, 450, 2) + num(66, 388, 3)
        gx, gy = hag[24]
        s += num(gx - 6, gy - 30, 4) + hl(gx + 12, gy - 44, "Lücke", 15, anchor="start", col=RED)
        s += num(410, 292, 5) + num(510, 270, 6) + num(530, 130, 7)
        s += num(676, 226, 8) + hl(640, 272, "Lager der Ranger", 15, col=RED)
        s += num(408, 158, 9) + hl(372, 142, "Südländer", 15, col=RED)
    s += compass(300, 530)
    s += cartouche(28, 24, "Das Bree-land", "Herbst TA 2968" if GM else "Bree, Staddle, Combe und Archet", 280)
    s += label(772, 588, "Skizze für den Loremaster · nicht maßstabsgetreu" if GM else "nicht maßstabsgetreu", 15, anchor="end", col=BROWN)
    return frame(s, 71)


# ---------------- Das Prancing Pony: Obergeschoss und Stallhof ----------------
def pony():
    s = ""
    wall = lambda pts, sd, w=3.0: path(rough(pts, jit=0.7, seed=sd), w)
    # Außenmauern des Flügels
    s += path(rough([(70, 70), (730, 70), (730, 320), (70, 320)], closed=True, jit=0.8, seed=1400), 3.4, fill="#e3d2ab", op=0.9)
    # Gang
    s += wall([(70, 170), (730, 170)], 1401, 2.0) + wall([(70, 215), (730, 215)], 1402, 2.0)
    s += label(240, 199, "Gang", 18, col=BROWN)
    # Treppen: links zum Schankraum, rechts die Hintertreppe zum Hof
    for k in range(6):
        s += path(f"M{84 + k * 9} 176 L{84 + k * 9} 210", 1.0)
    for k in range(5):
        s += path(f"M{688 + k * 8} 222 L{688 + k * 8} 262", 1.0)
    # Zimmer zum Hof hin (unten): 3, 4, 5 (Fenn), 6
    xs = [150, 280, 410, 540, 670]
    for k, x in enumerate(xs):
        s += wall([(x, 215), (x, 320)], 1410 + k, 2.2)
    for k, x in enumerate(xs[:-1]):
        # Türen zum Gang
        s += path(f"M{x + 40} 215 L{x + 70} 215", 3.2, col="#e3d2ab") + path(f"M{x + 40} 215 Q{x + 44} 236 {x + 70} 240", 0.9, op=0.7)
    s += label(215, 290, "Zimmer 3", 17) + label(345, 290, "Zimmer 4", 17) + label(605, 290, "Zimmer 6", 17)
    s += label(475, 310, "Zimmer 5 · Fenn", 15)
    # Kammern zur Straße (oben)
    for k, x in enumerate([200, 330, 460, 590]):
        s += wall([(x, 70), (x, 170)], 1420 + k, 2.2)
    s += label(135, 116, "Treppe zum", 14, col=BROWN) + label(135, 133, "Schankraum ↓", 14, col=BROWN)
    s += label(265, 125, "Kammer", 15, col=BROWN) + label(395, 125, "Kammer", 15, col=BROWN)
    s += label(525, 125, "Kammer", 15, col=BROWN) + label(660, 125, "Wäsche", 15, col=BROWN)
    s += label(110, 260, "Butterburs", 13, col=BROWN) + label(110, 276, "Kammer", 13, col=BROWN)
    # Fenns Zimmer: Herd, Tisch, Truhe, Fenster zum Hof
    s += path(rough([(524, 226), (538, 226), (538, 262), (524, 262)], closed=True, jit=0.5, seed=1430), 1.6, fill="#bfa77a")  # Herd an der Ostwand
    s += path(rough([(424, 232), (454, 232), (454, 248), (424, 248)], closed=True, jit=0.5, seed=1431), 1.2, fill="#d9c69e")  # Tisch
    s += path(rough([(502, 270), (530, 270), (530, 286), (502, 286)], closed=True, jit=0.5, seed=1432), 1.2, fill="#cdb78c")  # Truhe
    s += path("M455 320 L500 320", 5, col="#9fb7bd") + path("M455 320 L500 320", 1.0)  # Fenster
    s += label(690, 404, "Hintertreppe zum Hof", 12, col=BROWN)
    # Stallhof
    s += path(rough([(70, 330), (730, 330), (730, 562), (70, 562)], closed=True, jit=1.0, seed=1440), 1.2, dash="6 4", op=0.7)
    s += label(250, 548, "Stallhof", 24)
    s += path(rough([(445, 334), (510, 334), (510, 352), (445, 352)], closed=True, jit=0.6, seed=1441), 1.0, fill="#b9b08a", op=0.8)
    s += label(560, 350, "Beet", 13, col=BROWN, anchor="start")
    s += path(rough([(270, 450), (330, 450), (330, 470), (270, 470)], closed=True, jit=0.6, seed=1442), 1.6, fill="#9fb7bd")
    s += label(300, 494, "Trog", 16)
    s += house(560, 420, 165, 130, 1443, fill="#d9c69e", lw=2.2) + label(645, 500, "Stall", 22)
    for k in range(4):
        s += path(rough([(578 + k * 38, 430), (578 + k * 38, 550)], jit=0.6, seed=1444 + k), 0.6, op=0.6)
    if GM:
        s += num(506, 244, 1) + num(462, 346, 2) + num(500, 346, 3) + num(439, 268, 4) + num(482, 280, 5)
        s += num(150, 193, 6) + label(135, 162, "Gästebuch: unten", 12, col=RED)
        # Edrics Weg: aus Zimmer 4 über den Gang in Zimmer 5 und zurück
        s += path(rough([(350, 262), (338, 232), (345, 200), (450, 196), (468, 210), (466, 228)], jit=0.6, seed=1450), 1.4, dash="5 4", col=RED)
        s += label(370, 188, "Edric, nach Mitternacht", 13, col=RED, anchor="start")
        # Lily und Tom im Hof, Lilys Rückweg über die Hintertreppe
        s += f'<circle cx="430" cy="420" r="5" fill="{RED}"/><circle cx="446" cy="424" r="5" fill="{RED}"/>'
        s += label(410, 446, "Lily und Tom, Mitternacht", 13, col=RED, anchor="middle")
        s += path(rough([(452, 410), (560, 390), (660, 350), (700, 268), (640, 200), (560, 196)], jit=0.6, seed=1451), 1.0, dash="2 4", col=RED)
        s += label(520, 372, "Lilys Rückweg, halb eins", 12, col=RED, anchor="middle")
        s += label(300, 520, "Edric wäscht die Stiefel (Morgengrauen)", 12, col=RED)
    s += compass(60, 520)
    s += cartouche(260, 6, "Das Prancing Pony", "Obergeschoss und Stallhof" if GM else "Obergeschoss, wie Butterbur es beschreibt", 300)
    s += label(772, 586, "Skizze für den Loremaster · nicht maßstabsgetreu" if GM else "", 15, anchor="end", col=BROWN)
    return frame(s, 83)


# ---------------- Edrics Hof in Archet (nur Loremaster) ----------------
def hof():
    s = ""
    # rote Äcker (punktiert)
    r = random.Random(1500)
    for k in range(9):
        s += path(rough([(40, 420 + k * 16), (260, 400 + k * 16)], jit=1.0, seed=1501 + k), 0.7, op=0.5, col="#8a3a22")
    for k in range(7):
        s += path(rough([(560, 440 + k * 18), (780, 424 + k * 18)], jit=1.0, seed=1520 + k), 0.7, op=0.5, col="#8a3a22")
    s += label(150, 560, "rote Äcker", 18, col=BROWN)
    # Chetwood im Norden
    s += trees(90, 125, 14, 50, 1530) + trees(400, 95, 20, 70, 1531) + trees(560, 80, 22, 70, 1532) + trees(720, 120, 20, 60, 1533)
    s += hl(690, 40, "Chetwood", 26)
    # Hofzaun
    s += path(rough([(150, 150), (650, 150), (650, 400), (150, 400)], closed=True, jit=1.4, seed=1540), 1.2, dash="3 3")
    # Haus
    s += house(380, 190, 170, 110, 1541)
    s += label(465, 250, "Haus", 22)
    s += path("M430 300 L460 300", 3.4, col="#e9dbb9")  # Tür
    # Werkstatt mit Hobelbank
    s += house(190, 190, 140, 90, 1542)
    s += label(260, 240, "Werkstatt", 20)
    s += path(rough([(212, 262), (262, 262), (262, 272), (212, 272)], closed=True, jit=0.4, seed=1543), 1.1, fill="#cdb78c")
    # Sägegrube und Holzstapel
    s += path(rough([(230, 320), (330, 320), (330, 350), (230, 350)], closed=True, jit=0.6, seed=1544), 1.6, fill="#bfa77a")
    s += label(280, 376, "Sägegrube", 17)
    for k in range(5):
        s += f'<circle cx="{560 + k * 14}" cy="{340 + (k % 2) * 8}" r="6" fill="none" stroke="{INK}" stroke-width="1.1"/>'
    s += label(600, 380, "Holzstapel", 16)
    # Wege: nach Combe/Bree (Süden), in den Wald (Norden), von Osten (Südländer)
    s += path(rough([(445, 400), (440, 470), (430, 540), (420, 600)], jit=1.2, seed=1550), 1.2)
    s += label(452, 470, "nach Combe und Bree", 15, anchor="start")
    s += path(rough([(300, 150), (290, 110), (300, 60), (290, 10)], jit=1.2, seed=1551), 1.0, dash="4 4")
    s += hl(310, 104, "Pfad in den Wald", 14, anchor="start", col=BROWN)
    if GM:
        s += num(220, 330, 1) + num(470, 322, 2) + num(286, 266, 3) + num(520, 214, 4)
        s += label(237, 256, "Hobelbank", 11, col=RED)
        s += path(rough([(790, 260), (720, 270), (670, 280), (560, 260)], jit=0.8, seed=1560), 1.3, dash="5 4", col=RED)
        s += label(780, 240, "Südländer, Tag 4", 15, col=RED, anchor="end")
        s += hl(286, 130, "Edrics Flucht", 14, col=RED, anchor="end")
    s += compass(735, 520)
    s += cartouche(28, 24, "Edrics Hof", "in Archet, am Rand des Chetwood", 280)
    s += label(772, 586, "Skizze für den Loremaster · nicht maßstabsgetreu", 15, anchor="end", col=BROWN)
    return frame(s, 97)


# ---------------- Sauber gezeichnete Schaubilder ----------------
FONT = 'font-family="TeX Gyre Pagella"'
GREY, LINE, DRED, DINK = "#6f665c", "#9a9088", "#7a2a1f", "#2b2420"
CA, CC, CB = "#4e7a3a", "#7a2a1f", "#3e5f86"
PARCH = "#f7f1e6"


def svg_open(w, h, scale=4):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w * scale}" height="{h * scale}">',
            '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0 0L10 5L0 10z" fill="{LINE}"/></marker>'
            '<marker id="r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0 0L10 5L0 10z" fill="{DRED}"/></marker></defs>',
            f'<rect width="{w}" height="{h}" fill="#ffffff"/>']


def txt(x, y, t, size=10.5, col=DINK, weight=400, anchor="start", italic=False):
    st = ' font-style="italic"' if italic else ""
    return f'<text x="{x}" y="{y}" {FONT} font-size="{size}" font-weight="{weight}" fill="{col}" text-anchor="{anchor}"{st}>{t}</text>'


def box(x, y, w, h, stroke=LINE, fill=PARCH, sw=1.1):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def route():
    bw, bh, gap, x0, top = 250, 40, 22, 40, 12
    stages = [("Der Streit im Pony", "Tag 1 · Herbstmarkt · Mord nach Mitternacht"),
              ("Spuren in Bree", "Tag 2 · Tatort · Harnils Bitte · Zeugen"),
              ("Wege durchs Bree-land", "Staddle · Combe · Chetwood"),
              ("Archet", "Tag 4 vormittags · Edrics Hof"),
              ("Das Thing am Hecken-Tor", "Tag 4 · Sonnenuntergang · Westtor")]
    legs = ["in der Nacht", "ab Mittag", "Reihenfolge frei", "gut drei Stunden"]
    Hs = top * 2 + len(stages) * bh + (len(stages) - 1) * gap
    Ws = 420
    cx = x0 + bw / 2
    out = svg_open(Ws, Hs)
    ys = [top + i * (bh + gap) for i in range(len(stages))]
    for i, ((name, sub), y) in enumerate(zip(stages, ys)):
        climax = i == len(stages) - 1
        out.append(box(x0, y, bw, bh, DRED if climax else LINE, "#f6e7e3" if climax else PARCH, 1.8 if climax else 1.1))
        out.append(txt(cx, y + 17, name, 13.5, DRED if climax else DINK, 700, "middle"))
        out.append(txt(cx, y + 32, sub, 10.5, GREY, 400, "middle"))
        if i < len(legs):
            out.append(f'<path d="M{cx} {y + bh} V{y + bh + gap - 2}" stroke="{LINE}" stroke-width="1.2" marker-end="url(#a)"/>')
            out.append(txt(cx + 8, y + bh + gap / 2 + 4, legs[i], 10.5, GREY, italic=True))
    y2, y3 = ys[2] + bh / 2, ys[3] + bh / 2
    px = x0 + bw + 40
    out.append(f'<path d="M{x0 + bw} {y2} H{px} V{y3} H{x0 + bw + 3}" fill="none" stroke="{DRED}" stroke-width="1.2" stroke-dasharray="5 4" marker-end="url(#r)"/>')
    out.append(txt(px + 8, (y2 + y3) / 2 - 4, "die Südländer", 11, DRED, italic=True))
    out.append(txt(px + 8, (y2 + y3) / 2 + 10, "jagen das Buch", 11, DRED, italic=True))
    out.append("</svg>")
    return "\n".join(out), Ws * 4, Hs * 4


def personen():
    W_, H_ = 760, 470
    out = svg_open(W_, H_, 3)
    cols = [130, 380, 630]
    # Fenn
    out.append(box(250, 12, 260, 50))
    out.append(txt(380, 33, "Osric Fenn", 14, DINK, 700, "middle"))
    out.append(txt(380, 51, "das Opfer · Kundschafter für „R.“", 11, GREY, 400, "middle"))
    out.append(f'<path d="M380 62 V84 M130 84 H630 M130 84 V108 M380 84 V108 M630 84 V108" fill="none" stroke="{LINE}" stroke-width="1.2"/>')
    sus = [("Harnil", "angeklagt · unschuldig", CA), ("Hob Ferny", "falsche Fährte · Dieb", LINE), ("Edric Brambleby", "der Täter", CC)]
    for cx, (n, r, c) in zip(cols, sus):
        strong = c != LINE
        out.append(box(cx - 110, 108, 220, 50, c, "#eef2e6" if c == CA else ("#f6e7e3" if c == CC else PARCH), 1.8 if strong else 1.1))
        out.append(txt(cx, 129, n, 14, DINK, 700, "middle"))
        out.append(txt(cx, 147, r, 11, GREY, 400, "middle"))
    wit = [[("Mat Goatleaf", "sah Harnil um zehn gehen", "schläft danach selbst"),
            ("Iorlas", "Alibi: im Lager vor zwölf", "zählt vor Bree nur einfach")],
           [("Garth und Wenric", "Fenns Begleiter, Hobs Kontakt", "jagen das Notizbuch"),
            ("Wat Rushlight", "verwahrt Fenns Wagen", "die Südländer wollten ihn")],
           [("Lily Brockhouse", "sah den Hinkenden, halb eins", "war mit Tom im Stallhof"),
            ("Tom Tunnelly", "sah Edric Stiefel waschen", "redet nach Lilys Aussage"),
            ("Marigold Brambleby", "Edrics Frau", "kennt das Versteck")]]
    for cx, ws in zip(cols, wit):
        left = cx - 110
        last = 176 + (len(ws) - 1) * 96 + 36
        out.append(f'<path d="M{left + 16} 158 V{last}" stroke="{LINE}" stroke-width="1.2" fill="none"/>')
        for k, (n, a, b) in enumerate(ws):
            y = 176 + k * 96
            out.append(f'<path d="M{left + 16} {y + 36} H{left + 32}" stroke="{LINE}" stroke-width="1.2"/>')
            out.append(box(left + 32, y, 188, 72))
            out.append(txt(left + 44, y + 22, n, 12.5, DINK, 700))
            out.append(txt(left + 44, y + 42, a, 10.5, GREY))
            out.append(txt(left + 44, y + 58, b, 10.5, DRED if b == "jagen das Notizbuch" else GREY))
    out.append(f'<path d="M490 212 H505 V133 H514" fill="none" stroke="{DRED}" stroke-width="1.2" stroke-dasharray="5 4" marker-end="url(#r)"/>')
    out.append("</svg>")
    return "\n".join(out), W_ * 3, H_ * 3


def beweise():
    rows = [("1 · Die Wunden: Mitternacht, keine Klinge", "Tatort · Healing", "A"),
            ("2 · Das Fenster: Schlamm nur innen", "Tatort · Scan, Hunting", "A"),
            ("3 · Harnils Stiefel: Walderde", "Torwächterhütte · Scan", "A"),
            ("4 · Das Wort des Rangers", "Chetwood · Council", "A"),
            ("5 · Roter Lehm aus Archet", "Tatort · Explore", "C"),
            ("6 · Das Gästebuch: Zimmer 4", "Schankraum", "C"),
            ("7 · Der hinkende Schatten", "Lily · Courtesy, Enhearten", "AC"),
            ("8 · Die Stiefel am Trog", "Tom Tunnelly", "C"),
            ("9 · Hobs Botgänge", "Hob · Insight, Persuade", "B"),
            ("10 · Die Karte aus dem Wagen", "Combe · Scan, Craft", "CB"),
            ("11 · Brief an Fenn", "Combe", "B"),
            ("12 · Die Lücke im Hag", "Bree, Nordost · Explore, Hunting", "CB"),
            ("13 · Lehm in den Nähten", "Edrics Hof · Scan", "C"),
            ("14 · Fenns Notizbuch", "Werkstatt · Scan oder Marigold", "CB"),
            ("15 · Das Wort des Südländers", "Gefangener · Awe, Persuade", "CB")]
    W_, rh, y0 = 760, 26, 70
    H_ = y0 + len(rows) * rh + 44
    out = svg_open(W_, H_, 3)
    colx = {"A": 520, "C": 610, "B": 700}
    heads = [("A", "nicht Harnil", CA, "#eef2e6"), ("C", "Edric war es", CC, "#f6e7e3"), ("B", "Spitzel Fenn", CB, "#e9eef4")]
    for k, h, c, f in heads:
        x = colx[k]
        out.append(box(x - 42, 12, 84, 46, c, f, 1.8))
        out.append(txt(x, 32, k, 14, DINK, 700, "middle"))
        out.append(txt(x, 49, h, 9.5, GREY, 400, "middle"))
    out.append(txt(20, 54, "Beweis", 10.5, GREY, 700) + txt(290, 54, "Fundort · Wurf", 10.5, GREY, 700))
    out.append(f'<path d="M20 {y0 - 4} H740" stroke="{LINE}" stroke-width="1.2"/>')
    tot = {"A": 0, "B": 0, "C": 0}
    for i, (n, src, m) in enumerate(rows):
        y = y0 + i * rh
        if i % 2 == 0:
            out.append(f'<rect x="20" y="{y - 4}" width="720" height="{rh}" fill="{PARCH}"/>')
        out.append(txt(26, y + 13, n, 11.5, DINK))
        out.append(txt(290, y + 13, src, 10.5, GREY))
        for k in m:
            tot[k] += 1
            out.append(f'<circle cx="{colx[k]}" cy="{y + 9}" r="6" fill="{dict(A=CA, B=CB, C=CC)[k]}"/>')
    yb = y0 + len(rows) * rh
    out.append(f'<path d="M20 {yb - 4} H740" stroke="{LINE}" stroke-width="1.2"/>')
    out.append(txt(26, yb + 18, "Wege zum Schluss", 12, DINK, 700))
    for k in "ACB":
        out.append(txt(colx[k], yb + 18, str(tot[k]), 13, DINK, 700, "middle"))
    out.append("</svg>")
    return "\n".join(out), W_ * 3, H_ * 3


if __name__ == "__main__":
    os.makedirs(SVG, exist_ok=True)
    DIA = os.path.join(ROOT, "assets", "diagrams") + os.sep
    os.makedirs(DIA, exist_ok=True)
    jobs = []
    for gm in (True, False):
        GM = gm
        suf = "" if gm else "-players"
        jobs += [("map-breeland" + suf, breeland()), ("map-pony" + suf, pony())]
    GM = True
    jobs.append(("map-hof", hof()))
    from PIL import Image
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W * 2, "height": H * 2})
        for name, svg in jobs:
            open(SVG + name + "-de.svg", "w").write(svg)
            pg.set_content(f'<html><body style="margin:0;background:#fff">{svg}</body></html>', wait_until="load")
            pg.screenshot(path=D + name + "-de.png", clip={"x": 0, "y": 0, "width": W * 2, "height": H * 2})
        for out, fn in ((os.path.join(ROOT, "assets", "route-de"), route), (DIA + "personen-de", personen), (DIA + "beweise-de", beweise)):
            svg, rw, rh = fn()
            open(out + ".svg", "w").write(svg)
            pg.set_viewport_size({"width": rw, "height": rh})
            pg.set_content(f'<html><body style="margin:0;background:#fff">{svg}</body></html>', wait_until="load")
            pg.screenshot(path=out + ".png", clip={"x": 0, "y": 0, "width": rw, "height": rh})
            pg.set_viewport_size({"width": W * 2, "height": H * 2})
        b.close()
    for name, _ in jobs:
        Image.open(D + name + "-de.png").convert("RGB").save(D + name + "-de.jpg", quality=88)
        os.remove(D + name + "-de.png")
    print("ok")
