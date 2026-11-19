# Cartoon art for the cardboard cut-out stage play (Great Emu War, Western Australia, 1932). Every figure is drawn flat with a thick dark
# outline and simple painted shading, on a transparent sheet, so Blender can cut it out of cardboard along its alpha edge.
#   python3 art.py OUTDIR
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
SS = 2                                     # draw at 2x, shrink for smooth edges
INK = (38, 28, 22, 255)
rnd = random.Random(4)

class Sheet:
    def __init__(self, w, h):
        self.w, self.h = w, h; self.im = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def P(self, pts): return [(x * SS, y * SS) for x, y in pts]
    def poly(self, pts, fill, ow=6, out=INK):
        self.d.polygon(self.P(pts), fill=fill)
        if ow: self.d.line(self.P(pts) + self.P(pts[:1]), fill=out, width=ow * SS, joint='curve')
    def ell(self, c, rx, ry, fill, ow=6, out=INK):
        b = [(c[0] - rx) * SS, (c[1] - ry) * SS, (c[0] + rx) * SS, (c[1] + ry) * SS]; self.d.ellipse(b, fill=fill, outline=out if ow else None, width=ow * SS)
    def line(self, pts, w, col=INK): self.d.line(self.P(pts), fill=col, width=int(w * SS), joint='curve')
    def save(self, name, pad=0):
        im = self.im.resize((self.w, self.h), Image.LANCZOS); im.save(os.path.join(OUT, name + '.png')); print(name, im.size)

def blob(c, rx, ry, n=60, jag=0.0, seed=0, start=0.0):
    r = random.Random(seed); pts = []
    for k in range(n):
        a = start + 2 * math.pi * k / n; j = 1.0 + jag * (r.random() - 0.5) * (1 if k % 2 else -0.4)
        pts.append((c[0] + rx * j * math.cos(a), c[1] + ry * j * math.sin(a)))
    return pts
def thick(pts, w):
    """a thick stroke as a polygon (both sides of a polyline)"""
    L = []; R = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]; tx, ty = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n; ww = w[i] if isinstance(w, (list, tuple)) else w
        L.append((x + nx * ww / 2, y + ny * ww / 2)); R.append((x - nx * ww / 2, y - ny * ww / 2))
    return L + R[::-1]
def shade(sh, pts, col, k=0.78):
    """a darker crescent along the bottom-right of a shape (painted shading)"""
    cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
    sh2 = [(cx + (x - cx) * 0.92 + 6, cy + (y - cy) * 0.92 + 8) for x, y in pts]
    dark = tuple(int(c * k) for c in col[:3]) + (255,)
    return dark

# ---------------------------------------------------------------- the emu (facing left), standing; head and neck are a separate piece so they can bob
def emu():
    W, H = 1000, 1500; s = Sheet(W, H)
    BODY = (112, 92, 72, 255); DARKF = (70, 56, 44, 255); LEG = (96, 92, 86, 255); NECK = (96, 112, 128, 255)
    # legs (back leg darker), backward knees, three toes
    for k, (x0, col) in enumerate(((470, (78, 74, 70, 255)), (560, LEG))):
        hip = (x0, 820); knee = (x0 + 60, 1070); ank = (x0 - 10, 1330)
        s.poly(thick([hip, knee, ank], [44, 34, 26]), col)
        for dx, dy in ((-95, 40), (-30, 52), (45, 38)):
            s.poly(thick([ank, (ank[0] + dx, ank[1] + dy)], [22, 14]), col)
            s.poly([(ank[0] + dx - 6, ank[1] + dy - 6), (ank[0] + dx * 1.18, ank[1] + dy + 4), (ank[0] + dx + 4, ank[1] + dy + 8)], (40, 36, 32, 255), 3)
        for j in range(5): s.line([(knee[0] - 16 + j * 2, knee[1] + 40 + j * 45), (knee[0] + 14 - j * 3, knee[1] + 52 + j * 45)], 3, (60, 56, 52, 255))
    # body: a big shaggy mop of feathers, droopy at the back
    body = []
    for k in range(80):
        a = 2 * math.pi * k / 80; rx, ry = 330, 250; r = 1.0 + (0.11 if k % 2 else -0.02) + 0.05 * math.sin(a * 5)
        x = 470 + rx * r * math.cos(a); y = 640 + ry * r * math.sin(a)
        if math.sin(a) > 0.2: y += 70 * math.sin(a) ** 3 * (1 + 0.3 * (k % 3))          # shaggy fringe hangs down
        if math.cos(a) > 0.6: x += 40; y += 30                                          # rump droops
        body.append((x, y))
    s.poly(body, BODY, 7)
    for k in range(70):                                                                  # feather strokes
        x = 210 + rnd.random() * 520; y = 470 + rnd.random() * 380
        s.line([(x, y), (x + 30 + rnd.random() * 30, y + 40 + rnd.random() * 50)], 5, DARKF if k % 3 else (150, 128, 104, 255))
    # neck (separate piece)
    n = Sheet(420, 760)
    neck = [(250, 720), (200, 520), (150, 330), (140, 210), (150, 150)]
    n.poly(thick(neck, [96, 78, 62, 52, 48]), NECK, 7)
    for k in range(40):
        u = rnd.random(); j = min(int(u * 4), 3); f = u * 4 - j; (ax, ay), (bx, by) = neck[j], neck[j + 1]
        x = ax + (bx - ax) * f + (rnd.random() - 0.5) * 30; y = ay + (by - ay) * f; n.line([(x, y), (x + 6, y + 14)], 4, (60, 72, 86, 255))
    # head: dark fluffy crown, grey beak, big cartoon eye
    n.ell((150, 125), 78, 64, (66, 72, 82, 255), 7)
    n.poly([(92, 118), (12, 140), (10, 152), (92, 150)], (150, 140, 128, 255), 6)
    n.line([(14, 146), (90, 136)], 3)
    n.ell((150, 108), 30, 32, (255, 250, 236, 255), 5); n.ell((142, 112), 14, 16, (190, 70, 30, 255), 0); n.ell((140, 114), 7, 8, INK, 0)
    n.ell((136, 104), 4, 4, (255, 255, 255, 255), 0)
    for k in range(9): n.line([(130 + k * 10, 66), (126 + k * 11, 48 - 6 * (k % 2))], 5, (50, 54, 60, 255))
    s.save('emu_body'); n.save('emu_neck')

# ---------------------------------------------------------------- a soldier in 1932 Australian Army khaki: slouch hat, tunic, breeches, puttees
KHAKI = (150, 128, 86, 255); KHAKI_D = (118, 98, 64, 255); SKIN = (232, 186, 150, 255); BOOT = (82, 52, 32, 255); BRASS = (214, 176, 72, 255)
def head(s, c, hat='slouch', moust=True, face=1):
    x, y = c
    s.poly([(x - 22, y + 70), (x + 22, y + 70), (x + 18, y + 105), (x - 18, y + 105)], SKIN, 5)                       # neck
    s.ell((x, y + 20), 62, 72, SKIN, 6)                                                                                # head
    s.ell((x + face * 64, y + 22), 14, 22, SKIN, 5)                                                                  # nose (cartoon, sticks out)
    s.ell((x - face * 50, y + 24), 12, 18, SKIN, 5)                                                                  # ear
    s.ell((x + face * 26, y + 4), 8, 10, INK, 0); s.line([(x + face * 14, y - 16), (x + face * 40, y - 20)], 5)    # eye, brow
    if moust: s.poly([(x + face * 10, y + 46), (x + face * 64, y + 40), (x + face * 70, y + 54), (x + face * 30, y + 60)], (96, 64, 40, 255), 4)
    s.line([(x + face * 22, y + 70), (x + face * 46, y + 66)], 4)                                                    # mouth
    if hat == 'slouch':
        s.poly([(x - 120, y - 18), (x + 128, y - 22), (x + 110, y - 2), (x - 60, y + 4)], KHAKI, 6)                    # brim
        s.poly([(x - face * 120, y - 18), (x - face * 112, y - 96), (x - face * 70, y - 30)], KHAKI_D, 6)              # side brim turned up
        s.poly([(x - 66, y - 22), (x - 58, y - 92), (x + 50, y - 96), (x + 68, y - 22)], KHAKI, 6)                     # crown
        s.poly([(x - 64, y - 40), (x + 66, y - 42), (x + 66, y - 24), (x - 66, y - 22)], (90, 70, 46, 255), 4)         # band
        s.ell((x - face * 104, y - 60), 14, 14, BRASS, 4)                                                                # badge
        s.line([(x - 50, y + 4), (x - 30, y + 80), (x + 30, y + 86)], 3, (90, 70, 46, 255))                              # chin strap
    else:                                                                                                                # officer's peaked cap
        s.poly([(x - 70, y - 30), (x - 64, y - 80), (x + 76, y - 84), (x + 74, y - 30)], KHAKI, 6)
        s.poly([(x - 72, y - 34), (x + 76, y - 34), (x + 76, y - 18), (x - 72, y - 18)], (94, 58, 40, 255), 4)
        s.poly([(x + face * 10, y - 20), (x + face * 110, y - 6), (x + face * 100, y + 6), (x + face * 6, y - 4)], (40, 30, 24, 255), 4)
        s.ell((x, y - 56), 12, 12, BRASS, 4)
def soldier(name, hat='slouch', pose='stand'):
    W, H = 700, 1560; s = Sheet(W, H); x = 330
    # legs: breeches flare at the thigh, puttees wrapped to the knee, boots
    for k, dx in enumerate((-48, 52)):
        s.poly([(x + dx - 50, 860), (x + dx + 50, 860), (x + dx + 78, 1000), (x + dx + 40, 1110), (x + dx - 38, 1110), (x + dx - 62, 1000)], KHAKI if k else KHAKI_D, 6)
        s.poly([(x + dx - 36, 1100), (x + dx + 38, 1100), (x + dx + 34, 1420), (x + dx - 30, 1420)], (128, 108, 74, 255), 6)
        for j in range(9): s.line([(x + dx - 34, 1120 + j * 34), (x + dx + 34, 1140 + j * 34)], 3, (92, 76, 50, 255))
        s.poly([(x + dx - 36, 1410), (x + dx + 36, 1410), (x + dx + 80, 1490), (x + dx + 80, 1520), (x + dx - 40, 1520)], BOOT, 6)
    # tunic with four pockets and brass buttons, belt with ammo pouches
    s.poly([(x - 150, 470), (x + 150, 470), (x + 170, 870), (x - 170, 870)], KHAKI, 7)
    for px, py in ((-90, 520), (90, 520), (-100, 720), (100, 720)):
        s.poly([(x + px - 50, py), (x + px + 50, py), (x + px + 50, py + 90), (x + px - 50, py + 90)], KHAKI_D, 4); s.ell((x + px, py + 18), 9, 9, BRASS, 3)
    for j in range(4): s.ell((x, 520 + j * 85), 10, 10, BRASS, 3)
    s.poly([(x - 172, 760), (x + 172, 760), (x + 172, 808), (x - 172, 808)], (110, 92, 58, 255), 5)
    for px in (-120, -60, 60, 120): s.poly([(x + px - 26, 750), (x + px + 26, 750), (x + px + 26, 830), (x + px - 26, 830)], (128, 108, 70, 255), 4)
    s.poly([(x - 150, 470), (x - 60, 470), (x - 40, 520), (x - 150, 500)], KHAKI_D, 5); s.poly([(x + 150, 470), (x + 60, 470), (x + 40, 520), (x + 150, 500)], KHAKI_D, 5)
    # arms
    if pose == 'point':        # one arm pointing ahead, the other holding binoculars at the chest
        s.poly(thick([(x + 130, 500), (x + 280, 470), (x + 420, 440)], 70), KHAKI, 6); s.ell((x + 440, 436), 32, 30, SKIN, 5)
        s.poly([(x + 452, 420), (x + 520, 400), (x + 524, 414), (x + 456, 436)], SKIN, 4)
        s.poly(thick([(x - 130, 500), (x - 130, 660), (x - 30, 640)], 70), KHAKI, 6)
        s.poly([(x - 60, 600), (x + 20, 600), (x + 20, 680), (x - 60, 680)], (40, 34, 30, 255), 5); s.ell((x - 10, 650), 30, 30, SKIN, 5)
    else:                      # arms down, hands at the sides
        for sx in (-1, 1):
            s.poly(thick([(x + sx * 140, 500), (x + sx * 170, 700), (x + sx * 175, 840)], 68), KHAKI, 6); s.ell((x + sx * 175, 866), 32, 36, SKIN, 5)
    hs = Sheet(340, 330); head(hs, (170, 160), hat)                     # big cartoon head, drawn small then scaled up
    hi = hs.im.resize((int(hs.im.width * 1.65), int(hs.im.height * 1.65)), Image.LANCZOS)
    s.im.alpha_composite(hi, (int((x + 6) * SS - hi.width / 2), int(505 * SS - hi.height * 0.86)))
    s.save(name)

# ---------------------------------------------------------------- the Lewis gun on its tripod (facing right): fat finned barrel jacket, flat pan magazine on top
def lewis():
    W, H = 1300, 640; s = Sheet(W, H); GM = (52, 54, 56, 255); GL = (88, 92, 96, 255); WOOD = (128, 82, 44, 255)
    for a, b in (((520, 330), (300, 610)), ((560, 330), (760, 610)), ((540, 330), (540, 615))): s.poly(thick([a, b], 26), (70, 60, 50, 255), 6)
    s.poly([(120, 300), (330, 268), (360, 300), (350, 360), (150, 380), (110, 350)], WOOD, 7)                         # stock
    s.poly([(330, 262), (700, 252), (700, 350), (330, 360)], GM, 7)                                                    # receiver
    s.poly([(420, 350), (470, 350), (460, 430), (420, 430)], WOOD, 6)                                                  # pistol grip
    s.poly([(700, 232), (1150, 240), (1170, 262), (1170, 328), (1150, 350), (700, 362)], GL, 7)                        # barrel jacket
    for k in range(12): s.line([(730 + k * 36, 244), (730 + k * 36, 352)], 4, (60, 64, 68, 255))
    s.poly([(1170, 272), (1270, 276), (1270, 312), (1170, 316)], GM, 6)                                                # muzzle
    s.ell((520, 228), 190, 40, GM, 7); s.ell((520, 220), 60, 16, GL, 4)                                                # pan magazine
    for k in range(10): s.line([(370 + k * 30, 222), (380 + k * 30, 246)], 3, (30, 30, 32, 255))
    s.save('lewis')

# ---------------------------------------------------------------- a 1930s farm truck (facing right) with a gun on the tray
def truck():
    W, H = 1800, 900; s = Sheet(W, H); BODY = (74, 86, 62, 255); BODY_D = (54, 64, 46, 255); TRAY = (140, 104, 66, 255)
    s.poly([(120, 430), (980, 430), (980, 610), (120, 610)], TRAY, 7)                                                  # tray
    for k in range(6): s.line([(150 + k * 150, 440), (150 + k * 150, 600)], 4, (100, 72, 44, 255))
    s.poly([(980, 250), (1240, 250), (1300, 420), (1300, 640), (980, 640)], BODY, 7)                                    # cab
    s.poly([(1010, 280), (1210, 280), (1260, 420), (1010, 420)], (170, 200, 214, 255), 6)                               # window
    s.poly([(1300, 420), (1640, 440), (1680, 520), (1680, 640), (1300, 640)], BODY, 7)                                  # bonnet
    for k in range(5): s.line([(1380 + k * 50, 470), (1380 + k * 50, 600)], 4, BODY_D)
    s.poly([(1660, 450), (1720, 460), (1720, 640), (1660, 640)], (40, 40, 40, 255), 6)                                  # grille
    s.ell((1650, 470), 34, 34, (244, 232, 170, 255), 6)                                                                 # headlamp
    for cx in (330, 1450):                                                                                              # mudguards and wheels
        s.poly(blob((cx, 650), 190, 120, 40)[20:] + [(cx + 190, 650)], BODY_D, 7)
        s.ell((cx, 690), 140, 140, (30, 30, 30, 255), 7); s.ell((cx, 690), 70, 70, (150, 150, 140, 255), 6); s.ell((cx, 690), 18, 18, (60, 60, 60, 255), 4)
        for k in range(8):
            a = 2 * math.pi * k / 8; s.line([(cx + 20 * math.cos(a), 690 + 20 * math.sin(a)), (cx + 66 * math.cos(a), 690 + 66 * math.sin(a))], 6, (70, 70, 66, 255))
    s.save('truck')

# ---------------------------------------------------------------- scenery: painted backdrop, a row of wheat, a fence, a gum tree, the sun and a cloud
def backdrop():
    W, H = 3600, 1800; im = Image.new('RGB', (W, H)); px = np.zeros((H, W, 3), np.float32)
    y = np.linspace(0, 1, H)[:, None]
    sky = np.array([110, 170, 220]) * (1 - y) + np.array([214, 226, 228]) * y
    px[:] = sky[:, None, :] if sky.ndim == 2 else sky
    hz = int(H * 0.56)
    for yy in range(hz, H):                                                                                              # wheat fields in bands
        t = (yy - hz) / (H - hz); px[yy] = np.array([214, 178, 92]) * (1 - t) + np.array([196, 150, 64]) * t
    im = Image.fromarray(px.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for k in range(7):                                                                                                   # far hills
        cx = rnd.random() * W; d.ellipse([cx - 600, hz - 120 - rnd.random() * 80, cx + 600, hz + 160], fill=(150, 160, 120))
    d.rectangle([0, hz, W, H], fill=None)
    for k in range(5):                                                                                                   # field furrow stripes
        yy = hz + 60 + k * 140; d.line([(0, yy), (W, yy + 40)], fill=(186, 146, 70), width=10)
    for k in range(260):                                                                                                 # brush dabs
        x = rnd.random() * W; yy = hz + rnd.random() * (H - hz); c = (226 + rnd.randint(-20, 10), 188 + rnd.randint(-20, 10), 96)
        d.line([(x, yy), (x + 30, yy - 16)], fill=c, width=6)
    for k in range(6):                                                                                                   # painted clouds
        cx = rnd.random() * W; cy = 160 + rnd.random() * 420
        for j in range(5): r = 90 + rnd.random() * 90; d.ellipse([cx + j * 90 - r, cy - r * 0.6, cx + j * 90 + r, cy + r * 0.6], fill=(246, 246, 242))
    for k in range(9):                                                                                                   # far gum trees
        cx = rnd.random() * W; d.rectangle([cx - 8, hz - 160, cx + 8, hz], fill=(150, 140, 120))
        for j in range(4): d.ellipse([cx - 90 + j * 30, hz - 260 + (j % 2) * 40, cx + 10 + j * 30, hz - 160 + (j % 2) * 40], fill=(110, 130, 96))
    im = im.filter(ImageFilter.GaussianBlur(1.2)); im.save(os.path.join(OUT, 'backdrop.png')); print('backdrop', im.size)
def wheat_row():
    W, H = 2400, 420; s = Sheet(W, H); G = (222, 182, 90, 255); G2 = (196, 152, 66, 255)
    pts = [(0, H)]
    for k in range(0, W + 1, 40):
        top = 110 + 50 * math.sin(k * 0.013) + rnd.random() * 40
        pts += [(k, top + 40), (k + 12, top - 10 - rnd.random() * 30), (k + 26, top + 38)]
    pts.append((W, H)); s.poly(pts, G, 6)
    for k in range(120): x = rnd.random() * W; y = 200 + rnd.random() * 200; s.line([(x, y), (x + 6, y - 60)], 4, G2)
    s.save('wheat')
def fence():
    W, H = 2400, 380; s = Sheet(W, H); WD = (140, 108, 72, 255)
    for k in range(9): x = 60 + k * 285; s.poly([(x - 18, 40 + (k % 2) * 10), (x + 18, 36), (x + 22, H - 10), (x - 22, H - 10)], WD, 6)
    for y in (110, 190, 270): s.line([(40, y), (W - 40, y + 6)], 5, (80, 80, 80, 255))
    s.save('fence')
def sun():
    s = Sheet(700, 700); c = (350, 350)
    pts = []
    for k in range(32): r = 330 if k % 2 == 0 else 250; a = 2 * math.pi * k / 32; pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
    s.poly(pts, (250, 196, 64, 255), 7); s.ell(c, 200, 200, (252, 222, 96, 255), 7); s.save('sun')
def gumtree():
    s = Sheet(1000, 1600); BARK = (214, 204, 186, 255)
    s.poly([(450, 1600), (560, 1600), (540, 900), (620, 600), (590, 590), (500, 860), (420, 620), (395, 630), (470, 960)], BARK, 7)
    for c, r in (((500, 520), 240), ((330, 640), 180), ((690, 600), 200), ((520, 330), 200), ((340, 420), 150), ((700, 400), 150)):
        s.poly(blob(c, r, r * 0.72, 40, 0.35, int(c[0])), (104, 128, 92, 255), 7)
    s.save('gumtree')

emu(); soldier('soldier', 'slouch', 'stand'); soldier('major', 'cap', 'point'); lewis(); truck(); backdrop(); wheat_row(); fence(); sun(); gumtree()
