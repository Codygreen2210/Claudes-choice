# Cartoon art for the Lake Peigneur cut-out stage play (Louisiana, November 20, 1980). Same house look as the Emu War play:
# flat paint, thick dark outline, a little painted shading, on a transparent sheet so Blender can cut it out along its alpha edge.
#   python3 art.py OUTDIR
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
SS = 2
INK = (38, 28, 22, 255)
rnd = random.Random(7)
FONT = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'

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
    def text(self, c, s, size, col, stroke=0, scol=INK):
        f = ImageFont.truetype(FONT, size * SS); self.d.text((c[0] * SS, c[1] * SS), s, font=f, fill=col, anchor='mm', stroke_width=stroke * SS, stroke_fill=scol)
    def save(self, name):
        im = self.im.resize((self.w, self.h), Image.LANCZOS); im.save(os.path.join(OUT, name + '.png')); print(name, im.size)

def blob(c, rx, ry, n=60, jag=0.0, seed=0, start=0.0):
    r = random.Random(seed); pts = []
    for k in range(n):
        a = start + 2 * math.pi * k / n; j = 1.0 + jag * (r.random() - 0.5) * (1 if k % 2 else -0.4)
        pts.append((c[0] + rx * j * math.cos(a), c[1] + ry * j * math.sin(a)))
    return pts
def thick(pts, w):
    L = []; R = []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]; tx, ty = b[0] - a[0], b[1] - a[1]; n = math.hypot(tx, ty) or 1
        nx, ny = -ty / n, tx / n; ww = w[i] if isinstance(w, (list, tuple)) else w
        L.append((x + nx * ww / 2, y + ny * ww / 2)); R.append((x - nx * ww / 2, y - ny * ww / 2))
    return L + R[::-1]

SKIN = (232, 186, 150, 255); BOOT = (70, 48, 32, 255)
def head(s, c, face=1, moust=False):
    x, y = c
    s.poly([(x - 22, y + 70), (x + 22, y + 70), (x + 18, y + 105), (x - 18, y + 105)], SKIN, 5)
    s.ell((x, y + 20), 62, 72, SKIN, 6)
    s.ell((x + face * 64, y + 22), 14, 22, SKIN, 5)
    s.ell((x - face * 50, y + 24), 12, 18, SKIN, 5)
    s.ell((x + face * 26, y + 4), 8, 10, INK, 0); s.line([(x + face * 14, y - 16), (x + face * 40, y - 20)], 5)
    if moust: s.poly([(x + face * 10, y + 46), (x + face * 64, y + 40), (x + face * 70, y + 54), (x + face * 30, y + 60)], (96, 64, 40, 255), 4)
    s.line([(x + face * 22, y + 70), (x + face * 46, y + 66)], 4)
def hardhat(s, c, col, lamp=True):
    x, y = c
    s.poly([(x - 92, y - 2), (x + 96, y - 4), (x + 98, y + 14), (x - 94, y + 16)], col, 6)                       # brim
    s.poly(blob((x, y - 2), 72, 64, 40)[20:] + [(x + 72, y - 2)], col, 6)                                        # dome (top half)
    s.line([(x, y - 62), (x, y - 6)], 5, tuple(int(v * 0.75) for v in col[:3]) + (255,))
    if lamp:
        s.ell((x + 30, y - 30), 22, 20, (90, 90, 96, 255), 5); s.ell((x + 34, y - 30), 12, 12, (255, 244, 170, 255), 3)

# ---------------------------------------------------------------- people: a salt miner (pick on the shoulder, or arms up) and a rig hand
def worker(name, suit, hat, pose='pick', moust=False):
    W, H = 700, 1560; s = Sheet(W, H); x = 330; dark = tuple(int(v * 0.78) for v in suit[:3]) + (255,)
    for k, dx in enumerate((-48, 52)):
        s.poly([(x + dx - 50, 860), (x + dx + 50, 860), (x + dx + 46, 1420), (x + dx - 42, 1420)], suit if k else dark, 6)
        s.poly([(x + dx - 46, 1410), (x + dx + 42, 1410), (x + dx + 86, 1490), (x + dx + 86, 1520), (x + dx - 46, 1520)], BOOT, 6)
    s.poly([(x - 150, 470), (x + 150, 470), (x + 168, 880), (x - 168, 880)], suit, 7)                            # coveralls
    s.poly([(x - 90, 540), (x + 90, 540), (x + 90, 700), (x - 90, 700)], dark, 5)                                # bib pocket
    for sx in (-1, 1): s.ell((x + sx * 70, 520), 12, 12, (200, 190, 150, 255), 3)
    s.poly([(x - 170, 780), (x + 170, 780), (x + 170, 820), (x - 170, 820)], (60, 46, 34, 255), 4)              # belt
    s.poly([(x + 90, 790), (x + 150, 790), (x + 150, 880), (x + 90, 880)], (70, 70, 74, 255), 4)                # lamp battery
    if pose == 'pick':
        s.poly(thick([(x + 130, 500), (x + 190, 650), (x + 120, 760)], 66), suit, 6); s.ell((x + 112, 770), 32, 34, SKIN, 5)
        s.poly(thick([(x - 130, 500), (x - 180, 640), (x - 40, 620)], 66), suit, 6); s.ell((x - 30, 616), 32, 32, SKIN, 5)
        s.line([(x - 30, 616), (x + 210, 300)], 18, (120, 82, 46, 255)); s.line([(x - 30, 616), (x + 210, 300)], 10, (150, 104, 60, 255))
        s.poly([(x + 120, 250), (x + 300, 330), (x + 296, 350), (x + 200, 320), (x + 110, 290)], (110, 112, 116, 255), 5)   # pick head
    elif pose == 'up':
        for sx in (-1, 1):
            s.poly(thick([(x + sx * 135, 500), (x + sx * 215, 340), (x + sx * 245, 170)], 66), suit, 6); s.ell((x + sx * 248, 146), 36, 38, SKIN, 5)
    else:                                                                                                         # arms swinging, running
        s.poly(thick([(x + 135, 500), (x + 240, 600), (x + 300, 520)], 64), suit, 6); s.ell((x + 312, 506), 32, 32, SKIN, 5)
        s.poly(thick([(x - 135, 500), (x - 210, 660), (x - 290, 720)], 64), suit, 6); s.ell((x - 302, 728), 32, 32, SKIN, 5)
    hs = Sheet(340, 330); head(hs, (170, 170), 1, moust); hardhat(hs, (170, 118), hat, lamp=(pose != 'rig'))
    hi = hs.im.resize((int(hs.im.width * 1.65), int(hs.im.height * 1.65)), Image.LANCZOS)
    s.im.alpha_composite(hi, (int((x + 6) * SS - hi.width / 2), int(505 * SS - hi.height * 0.86))); s.save(name)

# ---------------------------------------------------------------- the drilling rig on its barge: a lattice derrick, drill floor, a shed, the pipe going down
def rig():
    W, H = 1000, 1800; s = Sheet(W, H); RED = (196, 60, 46, 255); STEEL = (180, 184, 188, 255); HULL = (70, 74, 80, 255)
    s.poly([(40, 1560), (960, 1560), (920, 1740), (80, 1740)], HULL, 8)                                          # barge hull
    for k in range(6): s.ell((140 + k * 145, 1650), 22, 22, (110, 114, 120, 255), 4)
    s.poly([(120, 1420), (880, 1420), (880, 1560), (120, 1560)], (150, 150, 146, 255), 7)                       # deck
    s.poly([(620, 1250), (900, 1250), (900, 1420), (620, 1420)], (226, 210, 160, 255), 7)                        # dog house
    s.poly([(650, 1290), (740, 1290), (740, 1360), (650, 1360)], (150, 196, 214, 255), 5)
    s.poly([(250, 1300), (600, 1300), (600, 1420), (250, 1420)], (110, 112, 116, 255), 7)                       # drill floor
    L, R_, T = (290, 1300), (560, 1300), (425, 80)
    s.poly([(L[0] - 10, L[1]), (T[0] - 20, T[1]), (T[0] + 20, T[1]), (R_[0] + 10, R_[1])], (0, 0, 0, 0), 0)
    for a_, b_ in (((L[0], L[1]), (T[0] - 18, T[1])), ((R_[0], R_[1]), (T[0] + 18, T[1]))): s.poly(thick([a_, b_], 26), RED, 6)
    for k in range(12):                                                                                           # lattice
        u0 = k / 12; u1 = (k + 1) / 12
        def at(u, side): return (lerp(L[0] if side < 0 else R_[0], T[0] + side * 18, u), lerp(L[1], T[1], u))
        s.line([at(u0, -1), at(u0, 1)], 9, RED if k % 2 else STEEL); s.line([at(u0, -1), at(u1, 1)], 7, STEEL); s.line([at(u0, 1), at(u1, -1)], 7, STEEL)
    s.poly([(T[0] - 70, T[1] - 40), (T[0] + 70, T[1] - 40), (T[0] + 60, T[1] + 20), (T[0] - 60, T[1] + 20)], (90, 92, 96, 255), 6)   # crown
    s.line([(425, 100), (425, 1300)], 6, (60, 60, 60, 255))                                                      # drill line
    s.poly([(395, 520), (455, 520), (455, 620), (395, 620)], (230, 190, 60, 255), 5)                              # travelling block
    s.poly([(415, 1300), (435, 1300), (435, 1560), (415, 1560)], (80, 80, 84, 255), 4)                           # pipe through the floor
    s.save('rig')
def lerp(a, b, t): return a + (b - a) * t

def barge():
    s = Sheet(1400, 380); s.poly([(20, 140), (1380, 140), (1330, 340), (70, 340)], (150, 70, 44, 255), 8)
    s.poly([(20, 140), (1380, 140), (1380, 190), (20, 190)], (60, 50, 44, 255), 6)
    for k in range(9): s.line([(110 + k * 140, 200), (110 + k * 140, 320)], 5, (120, 54, 34, 255))
    s.poly([(200, 60), (560, 60), (560, 140), (200, 140)], (150, 140, 120, 255), 6); s.poly([(640, 80), (1000, 80), (1000, 140), (640, 140)], (128, 118, 98, 255), 6)   # pipe stacks
    for k in range(5): s.ell((240 + k * 70, 100), 26, 26, (100, 96, 86, 255), 4)
    s.save('barge')
def tug():
    s = Sheet(1100, 760); s.poly([(30, 470), (1070, 470), (980, 700), (110, 700)], (196, 50, 40, 255), 8)
    s.poly([(30, 470), (1070, 470), (1070, 520), (30, 520)], (40, 40, 44, 255), 6)
    s.poly([(260, 250), (700, 250), (700, 470), (260, 470)], (240, 236, 222, 255), 7)
    s.poly([(320, 140), (620, 140), (640, 250), (300, 250)], (240, 236, 222, 255), 7)
    for k in range(3): s.poly([(340 + k * 95, 170), (410 + k * 95, 170), (410 + k * 95, 225), (340 + k * 95, 225)], (150, 196, 214, 255), 4)
    s.poly([(760, 120), (850, 120), (860, 470), (750, 470)], (40, 40, 44, 255), 7); s.poly([(756, 160), (856, 160), (858, 200), (754, 200)], (230, 196, 60, 255), 4)
    for k in range(5): s.ell((120 + k * 220, 600), 40, 40, (40, 40, 40, 255), 6)                                    # tyre fenders
    s.save('tug')
def skiff():
    s = Sheet(900, 300); s.poly([(20, 100), (880, 100), (760, 280), (110, 280)], (236, 232, 220, 255), 7)
    s.poly([(20, 100), (880, 100), (880, 140), (20, 140)], (60, 110, 160, 255), 5); s.poly([(700, 40), (780, 40), (790, 110), (690, 110)], (40, 40, 44, 255), 5)
    s.save('skiff')

# ---------------------------------------------------------------- the mine: salt pillar, the cage (floor + front grille, roof), the headframe on top
SALT = (232, 230, 222, 255); SALT_D = (196, 192, 182, 255)
def pillar():
    s = Sheet(560, 1400); s.poly([(40, 0), (520, 0), (500, 1400), (60, 1400)], SALT, 7)
    for k in range(16): y = 60 + k * 84; s.line([(70, y + rnd.random() * 20), (490, y + 20 + rnd.random() * 20)], 4, SALT_D)
    for k in range(6): x = 110 + k * 70; s.line([(x, 30), (x + 10, 1370)], 3, (214, 210, 200, 255))
    s.save('pillar')
def lift():
    s = Sheet(1000, 640); ST = (120, 124, 128, 255)
    s.poly([(20, 540), (980, 540), (980, 620), (20, 620)], (80, 80, 84, 255), 7)                                  # floor
    s.poly([(30, 250), (970, 250), (970, 540), (30, 540)], (150, 154, 158, 255), 7)                              # front grille panel
    for k in range(1, 16): s.line([(30 + k * 59, 254), (30 + k * 59, 536)], 6, (96, 100, 104, 255))
    for k in range(1, 5): s.line([(34, 250 + k * 58), (966, 250 + k * 58)], 6, (96, 100, 104, 255))
    s.save('lift')
def liftroof():
    s = Sheet(1000, 200); s.poly([(0, 60), (1000, 60), (1000, 150), (0, 150)], (120, 124, 128, 255), 7); s.poly([(470, 0), (530, 0), (530, 60), (470, 60)], (90, 90, 94, 255), 5); s.save('liftroof')
def headframe():
    s = Sheet(900, 1500); ST = (70, 76, 84, 255)
    for a_, b_ in (((120, 1480), (430, 200)), ((780, 1480), (470, 200)), ((450, 1480), (450, 200))): s.poly(thick([a_, b_], 30), ST, 6)
    for k in range(6): y = 1300 - k * 200; s.line([(150 + k * 50, y), (750 - k * 50, y)], 12, ST)
    s.ell((450, 200), 150, 150, (60, 64, 70, 255), 8); s.ell((450, 200), 110, 110, (0, 0, 0, 0), 0)
    s.ell((450, 200), 110, 110, (150, 156, 164, 255), 6)
    for k in range(8): a = 2 * math.pi * k / 8; s.line([(450, 200), (450 + 100 * math.cos(a), 200 + 100 * math.sin(a))], 8, ST)
    s.ell((450, 200), 26, 26, ST, 5); s.save('headframe')

# ---------------------------------------------------------------- water: lake waves, tall flood water, the whirlpool (seen from above), a falling sheet of water, splash
BLUE = (66, 132, 186, 255); BLUE_D = (44, 96, 150, 255); FOAM = (226, 240, 246, 255)
def waves(name, col, W=4800, H=320, seed=1):
    s = Sheet(W, H); r = random.Random(seed); pts = [(0, H)]
    for k in range(0, W + 1, 120):
        pts += [(k, 80 + r.random() * 20), (k + 60, 30 + r.random() * 20)]
    pts.append((W, H)); s.poly(pts, col, 6)
    for k in range(40): x = r.random() * W; y = 120 + r.random() * 150; s.line([(x, y), (x + 70, y - 8)], 6, FOAM)
    s.save(name)
def tallwater():
    W, H = 4800, 1600; s = Sheet(W, H); pts = [(0, H)]
    for k in range(0, W + 1, 120): pts += [(k, 70), (k + 60, 24)]
    pts.append((W, H)); s.poly(pts, BLUE, 7)
    for k in range(10): y = 220 + k * 140; s.poly([(0, y), (W, y + 10), (W, y + 60), (0, y + 50)], (58, 120, 176, 255) if k % 2 else (52, 112, 168, 255), 0)
    for k in range(80): x = rnd.random() * W; y = 100 + rnd.random() * (H - 200); s.line([(x, y), (x + 90, y - 6)], 6, (120, 176, 214, 255))
    s.save('tallwater')
def whirl():
    W = 1600; s = Sheet(W, W); c = (W / 2, W / 2)
    s.ell(c, 790, 790, BLUE, 8)
    for arm in range(4):                                                                                          # spiral arms of foam
        pts = []
        for k in range(120):
            u = k / 119; a = arm * math.pi / 2 + u * 3.2 * math.pi; r = 770 * (1 - u) + 60
            pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
        s.line(pts, 30, FOAM); s.line(pts, 14, (170, 210, 232, 255))
    for k in range(5): s.ell(c, 170 - k * 28, 170 - k * 28, (30 + k * 6, 60 + k * 8, 96 + k * 10, 255), 0)            # the dark hole
    s.ell(c, 60, 60, (12, 20, 34, 255), 0); s.save('whirl')
def fallwater():
    """a tall sheet of falling water that tiles top to bottom (the material scrolls it down)"""
    W, H = 600, 1600; im = np.zeros((H, W, 4), np.uint8); im[..., 3] = 255
    x = np.arange(W)[None, :]; y = np.arange(H)[:, None]
    stripe = 0.5 + 0.5 * np.sin(x * 0.09 + 1.6 * np.sin(y * 2 * math.pi / H * 2))
    base = np.array([70, 140, 196]); hi = np.array([214, 236, 246])
    col = base[None, None, :] * (1 - stripe[..., None] ** 6) + hi[None, None, :] * stripe[..., None] ** 6
    im[..., :3] = col.clip(0, 255).astype(np.uint8)
    for k in range(10):                                                                                           # white streaks, wrapped so it tiles
        x0 = rnd.randint(20, W - 20); y0 = rnd.randint(0, H); L = rnd.randint(200, 500)
        for yy in range(y0, y0 + L): im[yy % H, x0 - 4:x0 + 4, :3] = (236, 246, 250)
    Image.fromarray(im).save(os.path.join(OUT, 'fallwater.png')); print('fallwater', (W, H))
def splash():
    s = Sheet(800, 460)
    for k in range(8): s.ell((90 + k * 90, 300 - 70 * math.sin(k * 1.3) ** 2), 80 + 20 * (k % 3), 70 + 20 * (k % 2), FOAM, 6)
    s.save('splash')
def dust():
    s = Sheet(700, 400)
    for k in range(7): s.ell((110 + k * 80, 260 - 40 * math.sin(k)), 90 + 20 * (k % 3), 70 + 15 * (k % 2), (210, 200, 186, 255), 6)
    s.save('dust')

# ---------------------------------------------------------------- land: a live oak with moss, a chunk of island, the math card, the depth sign
def oak():
    s = Sheet(1300, 1300); BARK = (96, 78, 60, 255)
    s.poly([(560, 1300), (720, 1300), (690, 900), (900, 700), (870, 680), (660, 820), (520, 640), (490, 660), (600, 900)], BARK, 7)
    for c, r in (((640, 520), 300), ((380, 620), 230), ((900, 620), 240), ((520, 360), 220), ((800, 380), 220), ((250, 520), 170), ((1060, 520), 170)):
        s.poly(blob(c, r, r * 0.62, 40, 0.3, int(c[0])), (74, 104, 66, 255), 7)
    for k in range(14):                                                                                           # Spanish moss
        x = 200 + rnd.random() * 900; y = 520 + rnd.random() * 200; L = 120 + rnd.random() * 120
        s.poly([(x - 14, y), (x + 14, y), (x + 4, y + L), (x - 4, y + L)], (150, 160, 138, 255), 3)
    s.save('oak')
def island():
    s = Sheet(1500, 900); s.poly([(0, 900), (40, 620), (300, 560), (900, 540), (1300, 580), (1500, 680), (1500, 900)], (110, 150, 80, 255), 7)
    s.poly([(0, 760), (1500, 790), (1500, 900), (0, 900)], (120, 96, 70, 255), 6)
    s.poly([(700, 560), (760, 560), (750, 300), (710, 300)], (96, 78, 60, 255), 6)
    for c, r in (((730, 260), 180), ((600, 320), 130), ((870, 320), 130)): s.poly(blob(c, r, r * 0.6, 30, 0.3, int(c[0])), (74, 104, 66, 255), 6)
    s.save('island')
def mathcard():
    s = Sheet(560, 760); s.poly([(30, 60), (530, 60), (530, 740), (30, 740)], (160, 120, 80, 255), 7)
    s.poly([(70, 120), (490, 120), (490, 700), (70, 700)], (250, 248, 238, 255), 5); s.poly([(200, 30), (360, 30), (360, 100), (200, 100)], (150, 150, 156, 255), 5)
    s.text((280, 300), '2 + 2', 110, INK); s.text((280, 470), '= 5', 130, (200, 40, 40, 255))
    s.line([(110, 600), (450, 600)], 6, (120, 120, 120, 255)); s.save('mathcard')
def sign(name, txt):
    s = Sheet(900, 1000); s.poly([(420, 380), (480, 380), (480, 1000), (420, 1000)], (120, 90, 60, 255), 6)
    s.poly([(30, 40), (870, 40), (870, 420), (30, 420)], (240, 226, 190, 255), 8)
    a, b = txt.split('|'); s.text((450, 160), a, 150, (180, 40, 36, 255)); s.text((450, 320), b, 110, INK); s.save(name)

# ---------------------------------------------------------------- the slab between the lake and the mine, cut into pieces: grass or lake mud on top, dirt, then salt
def strata(name, wm, top='mud', H=300):
    W = int(H * wm); s = Sheet(W, H); r = random.Random(sum(map(ord, name)))
    s.poly([(0, 0), (W, 0), (W, H), (0, H)], (226, 222, 210, 255), 7)                                             # salt
    pts = [(0, 0), (W, 0)] + [(W - k * 60, 120 + 18 * math.sin(k * 0.9) + r.random() * 10) for k in range(int(W / 60) + 2)]
    s.poly(pts, (120, 92, 64, 255), 6)                                                                            # dirt
    s.poly([(0, 0), (W, 0), (W, 36), (0, 36)], (96, 140, 70, 255) if top == 'grass' else (92, 78, 58, 255), 6)
    for k in range(int(W / 25)):                                                                                  # salt crystals
        x = r.random() * W; y = 160 + r.random() * (H - 180); s.line([(x, y), (x + 14, y + 4)], 4, (196, 192, 182, 255))
    s.save(name)

worker('miner', (60, 96, 150, 255), (240, 200, 50, 255), 'pick'); worker('miner_run', (60, 96, 150, 255), (240, 200, 50, 255), 'run', True)
worker('miner_up', (60, 96, 150, 255), (240, 200, 50, 255), 'up'); worker('roughneck', (196, 90, 40, 255), (240, 240, 236, 255), 'rig', True)
rig(); barge(); tug(); skiff(); pillar(); lift(); liftroof(); headframe()
waves('waves', BLUE); waves('waves2', BLUE_D, seed=3); waves('canal', (70, 120, 150, 255), seed=5); tallwater(); whirl(); fallwater(); splash(); dust()
oak(); island(); mathcard(); sign('sign10', '10 FT|DEEP'); sign('sign200', '200 FT|DEEP')
strata('strata_l', 1.9 / 0.7, 'grass'); strata('strata_m', 2.4 / 0.7, 'grass'); strata('strata_d', 3.8 / 0.7); strata('strata_r', 3.7 / 0.7)

def backdrop():
    """top: Louisiana sky and the far shore of the lake; bottom (behind the mine): the salt wall with rooms cut into it"""
    W, H = 3600, 2074; px = np.zeros((H, W, 3), np.float32); cut = int(H * (7.2 - 3.25) / 7.2)
    y = np.linspace(0, 1, cut)[:, None]
    px[:cut] = (np.array([104, 160, 214]) * (1 - y) + np.array([222, 230, 226]) * y)[:, None, :]
    px[cut:] = np.array([206, 202, 192])
    im = Image.fromarray(px.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for k in range(6):
        cx = rnd.random() * W; cy = 120 + rnd.random() * 380
        for j in range(5): r = 80 + rnd.random() * 80; d.ellipse([cx + j * 80 - r, cy - r * 0.6, cx + j * 80 + r, cy + r * 0.6], fill=(246, 246, 242))
    hz = cut - 40                                                                                    # far shore: marsh, cypress, oaks
    d.rectangle([0, hz - 30, W, cut], fill=(118, 146, 104))
    for k in range(26):
        cx = rnd.random() * W; h_ = 120 + rnd.random() * 160
        if k % 3 == 0:
            d.rectangle([cx - 6, hz - h_, cx + 6, hz], fill=(90, 84, 70)); d.polygon([(cx - 50, hz - h_ * 0.4), (cx, hz - h_ - 30), (cx + 50, hz - h_ * 0.4)], fill=(84, 110, 80))
        else:
            for j in range(3): d.ellipse([cx - 120 + j * 60, hz - h_ - (j % 2) * 30, cx + j * 60, hz - h_ + 110], fill=(96, 124, 86))
    d.rectangle([0, cut - 22, W, cut], fill=(98, 150, 190))                                          # a strip of the lake far off
    # the salt wall: drill-and-blast marks, big rooms going back into the dark, a few work lights
    for k in range(24):
        yy = cut + 30 + k * 36; d.line([(0, yy + rnd.randint(-6, 6)), (W, yy + rnd.randint(-6, 6))], fill=(190, 186, 176), width=4)
    for k, cx in enumerate((300, 1000, 1800, 2600, 3300)):
        top = cut + 160; w = 260 + 30 * (k % 2)
        d.rounded_rectangle([cx - w, top, cx + w, H + 40], 60, fill=(120, 116, 108))
        d.rounded_rectangle([cx - w + 70, top + 80, cx + w - 70, H + 40], 50, fill=(70, 66, 60))
        d.rounded_rectangle([cx - w + 150, top + 160, cx + w - 150, H + 40], 40, fill=(36, 34, 30))
        d.ellipse([cx - 22, top + 40, cx + 22, top + 84], fill=(255, 236, 170))
    im = im.filter(ImageFilter.GaussianBlur(1.2)); im.save(os.path.join(OUT, 'backdrop.png')); print('backdrop', im.size)
backdrop()
