"""More shared pieces for the trend Shorts: teeth, candy, cells and viruses, the body clock, turkey and plates, octopus."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

ENAMEL = ramp('#f8f6ee', '#d4cfbe', '#ffffff')
DENTIN = ramp('#f0dca8', '#c8b078', '#fff0c8')
GUMS = ramp('#f08a9a', '#c05a6a', '#ffb8c4')
SPIT = ramp('#d8f0ff', '#9fcfee', '#ffffff')
CALC = ramp('#ffffff', '#cfd8e0', '#ffffff')
CELLC = ramp('#ffc0d0', '#e08aa0', '#ffe4ec')
VIRUS = ramp('#e2483d', '#a82a26', '#ff8070')
INSUL = ramp('#4fc0ff', '#2a8ad0', '#a8e4ff')
SUGARC = ramp('#ffffff', '#d8dde4', '#ffffff')
FATC = ramp('#ffe9a8', '#e0c070', '#fff6d8')
ROAST = ramp('#c8783a', '#8a4a1e', '#f0a868')
OCTO = ramp('#e2685a', '#a83a32', '#ff9a88')
CANDYS = [ramp('#e2483d'), ramp('#ffd23f'), ramp('#3fbf6a'), ramp('#7a4fd0'), ramp('#ff8a2a'), ramp('#3d7fd8')]


# ------------------------------------------------------------------ teeth
def tooth(cv, x, y, s, weak=0.0, refill=0.0, hole=0.0, T=0.0, seed=1):
    """A big molar, cut in half: enamel shell, dentin inside, gums at the base.
    weak: chalky weak spots in the enamel; refill: those spots being packed back; hole: a real cavity."""
    crown = smooth(40 * s, circle(x - 90 * s, y - 120 * s, 120 * s), circle(x + 90 * s, y - 120 * s, 120 * s), rbox(x, y, 200 * s, 150 * s, 60 * s))
    roots = union(capsule(x - 110 * s, y + 80 * s, x - 140 * s, y + 380 * s, 70 * s, 35 * s), capsule(x + 110 * s, y + 80 * s, x + 140 * s, y + 380 * s, 70 * s, 35 * s))
    body = smooth(30 * s, crown, roots)
    bb = (x - 260 * s, y - 280 * s, x + 260 * s, y + 440 * s)
    cv.shape(body, bb, ENAMEL)
    inner = offset(body, 0, 0, -40 * s)
    cv.shape(lambda X, Y: np.maximum(inner(X, Y), Y - (y + 460 * s)), bb, DENTIN, ow=0, shadow=0, alpha=0.9)
    rng = np.random.default_rng(seed)
    for k in range(6):                                                       # weak spots on the biting surface
        px, py = x + rng.uniform(-170, 170) * s, y - 200 * s - rng.uniform(-20, 40) * s
        if weak > 0:
            cv.shape(rotell(px, py, 34 * s, 22 * s, rng.uniform(0, 180)), (px - 40 * s, py - 40 * s, px + 40 * s, py + 40 * s),
                     ramp('#cfc6a8', '#a89a78', '#e8e0c8'), ow=0, shadow=0, alpha=weak * (1 - refill))
        if refill > 0:
            disc(cv, px, py, 30 * s * refill, CALC, ow=2, alpha=0.9 * refill)
    if hole > 0:
        cv.shape(rotell(x + 40 * s, y - 210 * s, 70 * s * hole, 60 * s * hole, 0), (x - 60 * s, y - 290 * s, x + 140 * s, y - 130 * s), ramp('#3a2a20'), ow=4)
    box(cv, x, y + 260 * s, 330 * s, 110 * s, GUMS, r=80 * s)


def acid_drops(cv, lt, x, y, w, n=10, a=1.0):
    for j in range(n):
        ph = (lt * 1.1 + j / n) % 1
        drop(cv, x - w / 2 + (j / n) * w, y - 260 + ph * 220, 13, a=a * (1 - ph))


# ------------------------------------------------------------------ candy, blood, cells
def candy(cv, x, y, s, kind=0, rot=0.0):
    c = CANDYS[kind % len(CANDYS)]
    if kind % 3 == 0:                                                        # wrapped round candy
        cv.shape(poly([(x - 110 * s, y - 40 * s), (x - 60 * s, y), (x - 110 * s, y + 40 * s)]), (x - 120 * s, y - 50 * s, x - 50 * s, y + 50 * s), c)
        cv.shape(poly([(x + 110 * s, y - 40 * s), (x + 60 * s, y), (x + 110 * s, y + 40 * s)]), (x + 50 * s, y - 50 * s, x + 120 * s, y + 50 * s), c)
        disc(cv, x, y, 60 * s, c)
    elif kind % 3 == 1:                                                      # candy bar
        cv.shape(rotell(x, y, 130 * s, 40 * s, rot), (x - 140 * s, y - 140 * s, x + 140 * s, y + 140 * s), ramp('#6e4122', '#4e2414', '#a8603a'))
        cv.shape(rotell(x, y, 80 * s, 42 * s, rot), (x - 90 * s, y - 90 * s, x + 90 * s, y + 90 * s), c)
    else:                                                                    # candy corn
        cv.shape(poly([(x - 60 * s, y + 50 * s), (x + 60 * s, y + 50 * s), (x, y - 80 * s)]), (x - 70 * s, y - 90 * s, x + 70 * s, y + 60 * s), ramp('#ff8a2a'))
        cv.shape(inter(poly([(x - 60 * s, y + 50 * s), (x + 60 * s, y + 50 * s), (x, y - 80 * s)]), lambda X, Y: (y + 20 * s) - Y),
                 (x - 70 * s, y, x + 70 * s, y + 60 * s), ramp('#ffd23f'), ow=0, shadow=0)


def vessel(cv, y, x0=-1000, x1=1000, r=170, a=1.0):
    box(cv, (x0 + x1) / 2, y, (x1 - x0) / 2, r, ramp('#d8343a', '#9a1f24', '#ff6a6a'), r=r * 0.9, alpha=a)
    box(cv, (x0 + x1) / 2, y, (x1 - x0) / 2, r * 0.72, ramp('#ff9a9a', '#e06a6a', '#ffc8c8'), r=r * 0.65, ow=0, shadow=0, alpha=a)


def sugar_cube(cv, x, y, s=1.0, a=1.0):
    cv.shape(rbox(x, y, 22 * s, 22 * s, 6 * s), (x - 26 * s, y - 26 * s, x + 26 * s, y + 26 * s), SUGARC, ow=3, alpha=a)


def cell(cv, x, y, r, T=0.0, door=0.0, fill=0.0, col=None, seed=0):
    col = CELLC if col is None else col
    wob = 1 + 0.03 * np.sin(T * 3 + seed)
    cv.shape(rotell(x, y, r * wob, r / wob, 0), (x - r * 1.1, y - r * 1.1, x + r * 1.1, y + r * 1.1), col)
    disc(cv, x + r * 0.2, y - r * 0.1, r * 0.3, ramp('#c0607a', '#8a3a50', '#e090a8'), ow=3, shadow=0)
    if door > 0:
        cv.shape(rotell(x - r * 0.95, y, r * 0.12, r * 0.3 * door, 0), (x - r * 1.1, y - r * 0.4, x - r * 0.8, y + r * 0.4), ramp('#3a1a2a'), ow=3, shadow=0)
    for k in range(int(fill)):
        a = k * 2.4
        sugar_cube(cv, x - r * 0.3 + np.cos(a) * r * 0.35, y + np.sin(a) * r * 0.45, 0.8)


def virus(cv, x, y, r, T=0.0, seed=0, col=None):
    col = VIRUS if col is None else col
    for k in range(12):
        a = k * np.pi / 6 + 0.2 * np.sin(T * 2 + seed)
        p0 = (x + np.cos(a) * r * 0.85, y + np.sin(a) * r * 0.85); p1 = (x + np.cos(a) * r * 1.35, y + np.sin(a) * r * 1.35)
        line(cv, [p0, p1], r * 0.1, col, ow=2.5, flat=False)
        disc(cv, p1[0], p1[1], r * 0.14, ramp('#ffd23f'), ow=2.5)
    cv.shape(circle(x, y, r), (x - r * 1.1, y - r * 1.1, x + r * 1.1, y + r * 1.1), col, ow=4)
    for k in range(3):
        a = k * 2.1 + seed
        dot(cv, x + np.cos(a) * r * 0.45, y + np.sin(a) * r * 0.45, r * 0.12, (np.array([0.5, 0.1, 0.1], np.float32),) * 3)


def fighter(cv, x, y, r, T, seed=0):
    """A white blood cell: big pale blob with a lumpy nucleus and a determined face."""
    blobs = [circle(x + np.cos(k * 1.3 + T * 2 + seed) * r * 0.25, y + np.sin(k * 1.7 + T * 2) * r * 0.2, r * 0.75) for k in range(4)]
    cv.shape(smooth(r * 0.3, *blobs), (x - r * 1.3, y - r * 1.3, x + r * 1.3, y + r * 1.3), ramp('#f4f6ff', '#c8d0e8', '#ffffff'))
    cv.shape(smooth(r * 0.1, circle(x - r * 0.2, y + r * 0.2, r * 0.25), circle(x + r * 0.15, y + r * 0.25, r * 0.22)), (x - r, y - r, x + r, y + r), ramp('#9a7ad8'), ow=3, shadow=0)
    for sx in (-1, 1):
        dot(cv, x + sx * r * 0.25, y - r * 0.2, r * 0.08)
        line(cv, [(x + sx * r * 0.4, y - r * 0.42), (x + sx * r * 0.12, y - r * 0.32)], r * 0.06, INKC)


# ------------------------------------------------------------------ clocks, sun
def wall_clock(cv, x, y, r, hour_ang, min_ang, col=None):
    disc(cv, x, y, r, RED if col is None else col)
    disc(cv, x, y, r * 0.84, ramp('#ffffff', '#dfe4ea', '#ffffff'), ow=3)
    for k in range(12):
        a = k * np.pi / 6
        line(cv, [(x + np.cos(a) * r * 0.7, y + np.sin(a) * r * 0.7), (x + np.cos(a) * r * 0.78, y + np.sin(a) * r * 0.78)], r * 0.04, INKC)
    line(cv, [(x, y), (x + np.sin(hour_ang) * r * 0.42, y - np.cos(hour_ang) * r * 0.42)], r * 0.07, INKC)
    line(cv, [(x, y), (x + np.sin(min_ang) * r * 0.65, y - np.cos(min_ang) * r * 0.65)], r * 0.045, INKC)
    disc(cv, x, y, r * 0.06, DARK, ow=0)


def sun(cv, x, y, r, T=0.0, a=1.0):
    cv.glow(circle(x, y, r), (x - r * 2.5, y - r * 2.5, x + r * 2.5, y + r * 2.5), '#ffd23f', r * 0.6, 0.6 * a)
    disc(cv, x, y, r, YELLOW, alpha=a)


def moon(cv, x, y, r, a=1.0):
    cv.shape(subtract(circle(x, y, r), circle(x + r * 0.45, y - r * 0.2, r * 0.85)), (x - r, y - r, x + r, y + r), ramp('#fff4c0', '#d8c880', '#ffffff'), alpha=a)


# ------------------------------------------------------------------ turkey, plates
def roast_turkey(cv, x, y, s, T=0.0):
    box(cv, x, y + 120 * s, 380 * s, 40 * s, ramp('#e8eef3'), r=30 * s)                     # platter
    cv.shape(smooth(40 * s, rotell(x, y, 300 * s, 190 * s, 0), circle(x - 60 * s, y - 80 * s, 150 * s)), (x - 320 * s, y - 250 * s, x + 320 * s, y + 200 * s), ROAST)
    for sx in (-1, 1):
        line(cv, [(x + sx * 200 * s, y - 40 * s), (x + sx * 330 * s, y - 150 * s)], 60 * s, ROAST, ow=4, flat=False)
        disc(cv, x + sx * 345 * s, y - 165 * s, 32 * s, ramp('#ffffff'), ow=3)
    for k in range(3):
        ph = (T * 0.6 + k / 3) % 1
        line(cv, [(x - 80 * s + k * 80 * s, y - 280 * s - ph * 120 * s), (x - 70 * s + k * 80 * s, y - 330 * s - ph * 120 * s)], 8 * s, flat(hexc('#ffffff')), a=1 - ph)


def plate(cv, x, y, s, items=1.0, T=0.0):
    cv.shape(ellipse(x, y, 330 * s, 110 * s), (x - 340 * s, y - 120 * s, x + 340 * s, y + 120 * s), ramp('#ffffff', '#d8dde4', '#ffffff'))
    piles = [(-150, ROAST, 90), (0, ramp('#f4f1ea'), 110), (140, ramp('#c03a3a'), 70), (60, ramp('#3fa84a'), 60), (-60, ramp('#e0a050'), 80)]
    n = int(len(piles) * items + 0.999)
    for dx, col, r in piles[:n]:
        cv.shape(rotell(x + dx * s, y - 30 * s, r * s, r * 0.6 * s, 0), (x + (dx - r) * s, y - 100 * s, x + (dx + r) * s, y + 40 * s), col)


# ------------------------------------------------------------------ octopus
def octopus(cv, x, y, s, T, col=None, swim=0.0, xray=0.0, brains=0.0, hearts=0.0, blood=0.0):
    col = OCTO if col is None else col
    for k in range(8):                                                       # arms: wavy, curling at the tips
        a0 = np.pi * (0.15 + 0.7 * k / 7)
        pts = []
        for u in np.linspace(0, 1, 12):
            a = a0 + 0.5 * np.sin(T * 2.2 + k + u * 4) * u + swim * (np.pi / 2 - a0) * 0.8 * u
            L = 520 * s * u
            pts.append((x + np.cos(a) * L * 0.9, y + 120 * s + np.sin(a) * L))
        line(cv, pts, 46 * s * (1 - 0.6 * np.linspace(0, 1, 12).mean()), col, ow=4, flat=False)
        if brains > 0:
            px, py = pts[4]
            disc(cv, px, py, 26 * s, ramp('#ffd23f'), ow=3, alpha=brains)
    head = rotell(x, y - 120 * s, 230 * s, 280 * s * (1 + 0.04 * np.sin(T * 2)), 0)
    cv.shape(head, (x - 250 * s, y - 420 * s, x + 250 * s, y + 180 * s), col, alpha=1 - 0.5 * xray)
    for sx in (-1, 1):
        disc(cv, x + sx * 90 * s, y + 10 * s, 44 * s, ramp('#ffffff'), ow=3, alpha=1 - 0.5 * xray)
        cv.shape(rbox(x + sx * 90 * s, y + 14 * s, 28 * s, 10 * s, 5 * s), (x + sx * 90 * s - 30 * s, y, x + sx * 90 * s + 30 * s, y + 30 * s), DARK, ow=0, shadow=0, alpha=1 - 0.5 * xray)
    if brains > 0:
        brain(cv, x, y - 200 * s, 0.55 * s * (0.8 + 0.2 * brains))
    if hearts > 0:
        for j, (dx, dy, sc) in enumerate(((-110, -30, 0.45), (110, -30, 0.45), (0, -110, 0.6))):
            beat = 0 if (j == 2 and swim > 0.5) else 0.15 * max(0, np.sin(T * 8 + j))
            heart_icon(cv, x + dx * s, y + dy * s, sc * s * hearts, beat)
    if blood > 0:
        for k in range(10):
            a = k * 0.63 + T
            disc(cv, x + np.cos(a) * 150 * s, y - 120 * s + np.sin(a) * 200 * s, 18 * s, ramp('#3d7fd8', '#2a559a', '#7fb4ff'), ow=2, alpha=blood)
