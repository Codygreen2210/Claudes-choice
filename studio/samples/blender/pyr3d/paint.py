# The tomb painting for the payoff: a giant statue on a sled, rows of men hauling ropes, and a man standing on the front of the
# sled pouring water on the sand. Drawn flat in the old Egyptian way (profile heads and legs, square shoulders, red-brown men,
# white kilts, black wigs) on cracked limestone plaster.   python3 paint.py OUT.png
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 4096, 1600
rnd = random.Random(7)
img = Image.new('RGB', (W, H), (219, 199, 160)); d = ImageDraw.Draw(img)
SKIN = (150, 70, 40); WIG = (28, 22, 18); KILT = (236, 230, 212); LINE = (60, 36, 24); ROPE = (120, 84, 48); WATER = (52, 98, 150)
STONE = (232, 222, 196); SLED = (138, 92, 52); OCH = (190, 120, 50); GRN = (60, 120, 100)

def poly(pts, fill, out=LINE, w=4):
    d.polygon([tuple(map(int, p)) for p in pts], fill=fill)
    if out: d.line([tuple(map(int, p)) for p in pts] + [tuple(map(int, pts[0]))], fill=out, width=w, joint='curve')
def ell(c, rx, ry, fill, out=LINE, w=4):
    d.ellipse([c[0] - rx, c[1] - ry, c[0] + rx, c[1] + ry], fill=fill, outline=out, width=w)
def seg(a, b, wd, fill, out=LINE):
    a = np.array(a, float); b = np.array(b, float); t = b - a; n = np.array([-t[1], t[0]]) / (np.linalg.norm(t) + 1e-9) * wd / 2
    poly([a + n, b + n, b - n, a - n], fill, out, 3); ell(a, wd / 2, wd / 2, fill, None); ell(b, wd / 2, wd / 2, fill, None)

def man(x, y, s, lean=0.0, pose='pull', face=1, kilt=KILT):
    """y = ground line; s = height in px. Profile head and legs, shoulders square to us."""
    f = face; hip = (x + f * lean * s * 0.1, y - s * 0.47); sh = (x + f * lean * s * 0.32, y - s * 0.80)
    # legs: a long stride, back leg straight
    seg(hip, (x - f * s * 0.20, y - s * 0.02), s * 0.075, SKIN); seg(hip, (x + f * s * 0.17, y - s * 0.02), s * 0.08, SKIN)
    for fx in (x - f * s * 0.20, x + f * s * 0.17): poly([(fx - f * s * 0.03, y), (fx + f * s * 0.09, y), (fx + f * s * 0.02, y - s * 0.05), (fx - f * s * 0.03, y - s * 0.05)], SKIN, LINE, 3)
    # torso: square shoulders, narrow waist
    poly([(sh[0] - s * 0.13, sh[1]), (sh[0] + s * 0.13, sh[1]), (hip[0] + s * 0.07, hip[1]), (hip[0] - s * 0.07, hip[1])], SKIN)
    # kilt
    poly([(hip[0] - s * 0.09, hip[1] - s * 0.03), (hip[0] + s * 0.09, hip[1] - s * 0.03), (hip[0] + f * s * 0.16, hip[1] + s * 0.20), (hip[0] - f * s * 0.12, hip[1] + s * 0.19)], kilt)
    d.line([(hip[0] - s * 0.09, hip[1] - s * 0.01), (hip[0] + s * 0.09, hip[1] - s * 0.01)], fill=LINE, width=4)
    # head: profile with a black wig and an eye
    hc = (sh[0] + f * s * 0.05, sh[1] - s * 0.10)
    seg((sh[0] + f * 0.01 * s, sh[1]), hc, s * 0.06, SKIN)
    ell(hc, s * 0.065, s * 0.075, SKIN)
    poly([(hc[0] + f * s * 0.06, hc[1] - s * 0.01), (hc[0] + f * s * 0.095, hc[1] + s * 0.02), (hc[0] + f * s * 0.06, hc[1] + s * 0.03)], SKIN, LINE, 3)
    poly([(hc[0] - f * s * 0.085, hc[1] + s * 0.07), (hc[0] - f * s * 0.08, hc[1] - s * 0.06), (hc[0] + f * s * 0.02, hc[1] - s * 0.09), (hc[0] + f * s * 0.05, hc[1] - s * 0.04),
          (hc[0] - f * s * 0.01, hc[1] - s * 0.03), (hc[0] - f * s * 0.02, hc[1] + s * 0.08)], WIG, None)
    ell((hc[0] + f * s * 0.035, hc[1] - s * 0.01), s * 0.014, s * 0.008, (250, 245, 235), LINE, 2)
    # arms
    if pose == 'pull':    # both arms reach forward and down to the rope
        rp = (sh[0] + f * s * 0.34, sh[1] + s * 0.12); seg((sh[0] + f * s * 0.10, sh[1] + s * 0.02), rp, s * 0.06, SKIN)
        seg((sh[0] - f * s * 0.10, sh[1] + s * 0.02), (rp[0] - f * s * 0.10, rp[1] + s * 0.02), s * 0.06, SKIN); return rp
    if pose == 'pour':    # a jar held out front, tipped, water running down
        jc = (sh[0] + f * s * 0.30, sh[1] + s * 0.06)
        seg((sh[0] + f * s * 0.10, sh[1] + s * 0.02), (jc[0] - f * s * 0.05, jc[1] - s * 0.04), s * 0.06, SKIN)
        seg((sh[0] - f * s * 0.10, sh[1] + s * 0.03), (jc[0] - f * s * 0.08, jc[1] + s * 0.07), s * 0.06, SKIN)
        ang = math.radians(-40 * f); cs, sn = math.cos(ang), math.sin(ang)
        jar = [(-0.07, -0.10), (0.07, -0.10), (0.10, 0.02), (0.06, 0.12), (-0.06, 0.12), (-0.10, 0.02)]
        poly([(jc[0] + s * (px * cs - py * sn), jc[1] + s * (px * sn + py * cs)) for px, py in jar], OCH)
        mouth = (jc[0] + f * s * 0.11, jc[1] - s * 0.06); return mouth
    if pose == 'carry':   # a jar on the shoulder
        jc = (sh[0] - f * s * 0.02, sh[1] - s * 0.12); ell(jc, s * 0.07, s * 0.09, OCH)
        seg((sh[0] + f * s * 0.10, sh[1] + s * 0.02), (jc[0] + f * s * 0.07, jc[1] + s * 0.02), s * 0.06, SKIN); return jc
    if pose == 'clap':
        seg((sh[0] + f * s * 0.10, sh[1] + s * 0.02), (sh[0] + f * s * 0.22, sh[1] - s * 0.18), s * 0.06, SKIN)
        seg((sh[0] - f * s * 0.10, sh[1] + s * 0.02), (sh[0] + f * s * 0.18, sh[1] - s * 0.20), s * 0.06, SKIN); return None

# ---- plaster: blotches and grain
arr = np.array(img).astype(np.float32)
yy, xx = np.mgrid[0:H, 0:W]
def vnoise(sc, seed):
    r = np.random.RandomState(seed); g = r.rand(H // sc + 3, W // sc + 3)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((W + 3 * sc, H + 3 * sc), Image.BICUBIC); return np.array(im)[:H, :W] / 255.0
n1 = vnoise(160, 1) * 0.6 + vnoise(40, 2) * 0.3 + vnoise(8, 3) * 0.1
arr *= (0.88 + 0.2 * n1)[..., None]
img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)

# ---- frame bands: a block border on top, ground lines under each row
TOP = 130
for i in range(0, W, 64):
    c = [(40, 80, 140), (170, 50, 30), (210, 160, 40), (30, 110, 90)][(i // 64) % 4]
    d.rectangle([i + 6, 30, i + 58, 92], fill=c, outline=LINE, width=3)
d.line([(0, 104), (W, 104)], fill=LINE, width=6); d.line([(0, 22), (W, 22)], fill=LINE, width=6)
d.rectangle([0, H - 60, W, H], fill=(150, 60, 35)); d.line([(0, H - 62), (W, H - 62)], fill=LINE, width=6)

# ---- the statue on its sled (left), facing right
GL = H - 150                 # main ground line
sx0, sx1 = 260, 1480
poly([(sx0, GL - 70), (sx1 - 40, GL - 70), (sx1 + 60, GL - 150), (sx1 + 90, GL - 140), (sx1 + 10, GL - 20), (sx0, GL - 20)], SLED)
for k in range(6): d.line([(sx0 + 40 + k * 200, GL - 70), (sx0 + 40 + k * 200, GL - 20)], fill=LINE, width=4)
# statue: a huge seated figure in profile, white stone, black wig, hands on knees
bx, by = 520, GL - 70
poly([(bx, by), (bx + 760, by), (bx + 760, by - 90), (bx, by - 90)], STONE)                                   # base
poly([(bx + 60, by - 90), (bx + 380, by - 90), (bx + 380, by - 560), (bx + 60, by - 560)], STONE)              # throne block
poly([(bx + 380, by - 380), (bx + 700, by - 380), (bx + 700, by - 90), (bx + 600, by - 90), (bx + 600, by - 300), (bx + 380, by - 300)], STONE)   # lap + shins
poly([(bx + 600, by - 90), (bx + 740, by - 90), (bx + 740, by - 120), (bx + 600, by - 120)], STONE)            # feet
poly([(bx + 170, by - 380), (bx + 420, by - 380), (bx + 440, by - 760), (bx + 190, by - 760)], STONE)           # torso
poly([(bx + 380, by - 700), (bx + 470, by - 560), (bx + 600, by - 390), (bx + 560, by - 370), (bx + 420, by - 520), (bx + 340, by - 650)], STONE)  # arm to knee
ell((bx + 330, by - 860), 115, 125, STONE)
poly([(bx + 150, by - 650), (bx + 190, by - 980), (bx + 360, by - 1010), (bx + 440, by - 930), (bx + 330, by - 880), (bx + 260, by - 700)], WIG, None)
ell((bx + 405, by - 870), 18, 10, (250, 245, 235), LINE, 3)
poly([(bx + 330, by - 740), (bx + 380, by - 740), (bx + 370, by - 660), (bx + 345, by - 650)], (90, 70, 40))   # beard
for k in range(5): d.line([(bx + 70, by - 130 - k * 80), (bx + 370, by - 130 - k * 80)], fill=(200, 188, 160), width=3)
# men on the sled: the water pourer at the front (the payoff), one clapping the beat on the statue's knees
mouth = man(sx1 - 10, GL - 74, 300, 0.2, 'pour', 1)
wx, wy = mouth
pts = []
for k in range(26):
    t = k / 25; pts.append((wx + 30 * t + 12 * math.sin(t * 9), wy + (GL + 10 - wy) * t))
for off in (-9, 0, 9): d.line([(px + off, py) for px, py in pts], fill=WATER, width=7)
for k in range(9): ell((wx + 30 + rnd.uniform(-60, 90), GL + rnd.uniform(-10, 20)), rnd.uniform(6, 14), rnd.uniform(4, 9), WATER, None)
man(bx + 560, by - 380, 250, 0.0, 'clap', 1)
# water carriers walking behind the sled
for k, xx_ in enumerate((60, 190)):
    man(xx_, GL - 10, 290, 0.05, 'carry', 1)

# ---- four rows of men hauling ropes, leaning toward the right
rows = [GL - 30, GL - 330, GL - 630, GL - 930]
rope_y = {}
for r, gy in enumerate(rows):
    s = 230; y_rope = gy - s * 0.66
    d.line([(sx1 + 70, GL - 140), (1700, y_rope)], fill=ROPE, width=8)
    d.line([(1700, y_rope), (W - 120, y_rope - 40)], fill=ROPE, width=8)
    if r < 3: d.line([(0, gy + 18), (W, gy + 18)] if r == 0 else [(1640, gy + 18), (W, gy + 18)], fill=LINE, width=5)
    for i in range(14):
        x_ = 1800 + i * 160 + (r % 2) * 40
        if x_ > W - 150: break
        man(x_, gy, s, 0.55, 'pull', 1)
# a foreman out front with a staff, and columns of marks (made-up signs, not real writing)
man(W - 90, rows[0], 250, 0.0, 'clap', -1)
for c in range(12):
    cx = 1700 + c * 46
    for k in range(5):
        kind = rnd.randint(0, 3); cy = 150 + k * 52
        if kind == 0: ell((cx, cy), 12, 12, None, LINE, 4)
        elif kind == 1: d.line([(cx - 14, cy), (cx - 7, cy - 8), (cx, cy), (cx + 7, cy - 8), (cx + 14, cy)], fill=WATER, width=4)
        elif kind == 2: d.rectangle([cx - 12, cy - 12, cx + 12, cy + 8], outline=LINE, width=4)
        else: d.line([(cx, cy - 16), (cx, cy + 12)], fill=LINE, width=5); d.line([(cx, cy - 16), (cx + 10, cy - 8)], fill=LINE, width=4)
    d.line([(cx + 23, 130), (cx + 23, 410)], fill=LINE, width=3)

# ---- age: fade, flaking patches and a few cracks
arr = np.array(img).astype(np.float32)
base = np.array([219, 199, 160], np.float32)
fade = (vnoise(220, 11) * 0.7 + vnoise(30, 12) * 0.3)
arr = arr * (0.80 + 0.12 * fade[..., None]) + base * (0.20 - 0.12 * fade[..., None])
flake = (vnoise(90, 21) * 0.7 + vnoise(12, 22) * 0.3) > 0.80
arr[flake] = arr[flake] * 0.25 + np.array([205, 186, 150]) * 0.75
img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img)
for k in range(9):
    x_, y_ = rnd.uniform(0, W), rnd.uniform(0, H); pts = [(x_, y_)]
    for j in range(rnd.randint(8, 18)): x_ += rnd.uniform(-40, 40); y_ += rnd.uniform(10, 50); pts.append((x_, y_))
    d.line(pts, fill=(120, 100, 75), width=3)
img = img.filter(ImageFilter.GaussianBlur(0.8))
img.save(sys.argv[1]); print('painting', sys.argv[1], img.size)
