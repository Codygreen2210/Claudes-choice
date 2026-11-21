# Cartoon art for the Halifax Explosion cut-out stage play (Halifax, Nova Scotia, December 6, 1917). Same house look as the
# Emu War and Lake Peigneur plays: flat paint, thick dark outline, a little painted shading, on a transparent sheet so Blender
# can cut it out along its alpha edge.  Also writes art/meta.json (window spots, pivots) for story.py.
#   python3 art.py OUTDIR
import sys, os, math, random, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
SS = 2
INK = (38, 28, 22, 255)
rnd = random.Random(11)
FONT = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
META = {}

class Sheet:
    def __init__(self, w, h):
        self.w, self.h = w, h; self.im = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0)); self.d = ImageDraw.Draw(self.im)
    def P(self, pts): return [(x * SS, y * SS) for x, y in pts]
    def poly(self, pts, fill, ow=6, out=INK):
        self.d.polygon(self.P(pts), fill=fill)
        if ow: self.d.line(self.P(pts) + self.P(pts[:1]), fill=out, width=ow * SS, joint='curve')
    def rect(self, x0, y0, x1, y1, fill, ow=6): self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, ow)
    def ell(self, c, rx, ry, fill, ow=6, out=INK):
        b = [(c[0] - rx) * SS, (c[1] - ry) * SS, (c[0] + rx) * SS, (c[1] + ry) * SS]; self.d.ellipse(b, fill=fill, outline=out if ow else None, width=ow * SS)
    def line(self, pts, w, col=INK): self.d.line(self.P(pts), fill=col, width=int(w * SS), joint='curve')
    def text(self, c, s, size, col, stroke=0, scol=INK):
        f = ImageFont.truetype(FONT, size * SS); self.d.text((c[0] * SS, c[1] * SS), s, font=f, fill=col, anchor='mm', stroke_width=stroke * SS, stroke_fill=scol)
    def save(self, name):
        im = self.im.resize((self.w, self.h), Image.LANCZOS); im.save(os.path.join(OUT, name + '.png')); print(name, im.size)
    def meta(self, name, key, x, y): META.setdefault(name, {})[key] = [x / self.w, 1 - y / self.h]

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
def lerp(a, b, t): return a + (b - a) * t
def shade(c, k): return tuple(int(v * k) for v in c[:3]) + (255,)

SKIN = (232, 186, 150, 255); BOOT = (52, 40, 32, 255)
def head(s, c, face=1, moust=False, hair=(90, 62, 40, 255), sc=1.0):
    x, y = c; S_ = sc
    s.poly([(x - 22 * S_, y + 70 * S_), (x + 22 * S_, y + 70 * S_), (x + 18 * S_, y + 105 * S_), (x - 18 * S_, y + 105 * S_)], SKIN, 5)
    s.ell((x, y + 20 * S_), 62 * S_, 72 * S_, SKIN, 6)
    s.ell((x + face * 64 * S_, y + 22 * S_), 14 * S_, 22 * S_, SKIN, 5)
    s.ell((x - face * 50 * S_, y + 24 * S_), 12 * S_, 18 * S_, SKIN, 5)
    s.ell((x + face * 26 * S_, y + 4 * S_), 8 * S_, 10 * S_, INK, 0); s.line([(x + face * 14 * S_, y - 16 * S_), (x + face * 40 * S_, y - 20 * S_)], 5)
    if moust: s.poly([(x + face * 10 * S_, y + 46 * S_), (x + face * 64 * S_, y + 40 * S_), (x + face * 70 * S_, y + 54 * S_), (x + face * 30 * S_, y + 60 * S_)], (96, 64, 40, 255), 4)
    s.line([(x + face * 22 * S_, y + 70 * S_), (x + face * 46 * S_, y + 66 * S_)], 4)

def hat(s, c, kind, col):
    x, y = c
    if kind == 'visor':                                                    # the dispatcher's green eyeshade
        s.poly([(x - 66, y - 10), (x + 66, y - 10), (x + 66, y + 8), (x - 66, y + 8)], (40, 40, 40, 255), 5)
        s.poly([(x - 10, y - 4), (x + 130, y + 6), (x + 120, y + 34), (x - 10, y + 16)], (70, 150, 90, 220), 5)
        s.poly(blob((x - 4, y - 30), 64, 40, 30)[15:], (70, 50, 34, 255), 5)          # hair on top
    elif kind == 'cap':                                                    # a flat cap
        s.poly(blob((x - 6, y - 14), 76, 44, 40)[19:] + [(x + 70, y - 10)], col, 6); s.poly([(x + 40, y - 18), (x + 128, y - 4), (x + 110, y + 10), (x + 30, y + 2)], shade(col, 0.8), 5)
    elif kind == 'sailor':
        s.poly([(x - 70, y - 30), (x + 74, y - 30), (x + 70, y + 4), (x - 66, y + 4)], (250, 250, 246, 255), 6); s.poly([(x - 66, y - 6), (x + 70, y - 6), (x + 70, y + 8), (x - 66, y + 8)], (30, 40, 70, 255), 4)
    elif kind == 'beret':                                                  # a French sailor's beret with the red pompom
        s.poly(blob((x, y - 18), 80, 30, 40), (30, 44, 90, 255), 6); s.ell((x, y - 52), 18, 16, (210, 40, 40, 255), 5)
    elif kind == 'bonnet':
        s.poly(blob((x - 10, y - 10), 84, 58, 40)[18:] + [(x + 80, y)], col, 6); s.poly([(x - 90, y), (x + 90, y), (x + 80, y + 16), (x - 80, y + 16)], shade(col, 0.8), 5)

def person(name, coat, pants, hatk, hatc, pose, face=1, moust=False, skirt=False, shirt=None, extra=None):
    """a 1917 townsperson, side-on, facing +x if face=1"""
    W, H = 760, 1560; s = Sheet(W, H); x = 360; dark = shade(coat, 0.78)
    if skirt:
        s.poly([(x - 150, 820), (x + 150, 820), (x + 200, 1480), (x - 200, 1480)], pants, 7)
        for k in (-1, 1): s.poly([(x + k * 60 - 50, 1470), (x + k * 60 + 60, 1470), (x + k * 60 + 70, 1520), (x + k * 60 - 50, 1520)], BOOT, 5)
    else:
        for k, dx in enumerate((-48, 52)):
            if pose == 'run':
                a = (x + dx, 860); b = (x + dx + (110 if k else -90), 1200); c_ = (x + dx + (40 if k else -170), 1430)
                s.poly(thick([a, b, c_], 96), pants if k else shade(pants, 0.8), 6); s.poly([(c_[0] - 46, c_[1] - 20), (c_[0] + 70, c_[1] - 10), (c_[0] + 70, c_[1] + 40), (c_[0] - 46, c_[1] + 40)], BOOT, 5)
            else:
                s.poly([(x + dx - 50, 860), (x + dx + 50, 860), (x + dx + 46, 1420), (x + dx - 42, 1420)], pants if k else shade(pants, 0.8), 6)
                s.poly([(x + dx - 46, 1410), (x + dx + 42, 1410), (x + dx + 86, 1490), (x + dx + 86, 1520), (x + dx - 46, 1520)], BOOT, 6)
    s.poly([(x - 150, 470), (x + 150, 470), (x + 168, 900), (x - 168, 900)], coat, 7)
    if shirt:                                                              # white shirt sleeves and a dark vest
        s.poly([(x - 110, 470), (x + 110, 470), (x + 120, 860), (x - 120, 860)], shirt, 5)
        s.poly([(x - 20, 470), (x + 20, 470), (x + 10, 620), (x - 10, 620)], (150, 40, 40, 255), 3)
        for k in range(4): s.ell((x + 60, 560 + k * 70), 9, 9, (220, 200, 120, 255), 2)
    if extra == 'sailor':
        s.poly([(x - 150, 470), (x + 40, 470), (x - 20, 620), (x - 150, 600)], (250, 250, 246, 255), 5); s.line([(x - 140, 500), (x + 10, 500)], 5, (30, 40, 70, 255))
    arm = shirt if shirt else coat
    if pose == 'point':
        s.poly(thick([(x + 130, 500), (x + 260, 470), (x + 380, 380)], 64), arm, 6); s.ell((x + 396, 370), 32, 30, SKIN, 5); s.line([(x + 400, 362), (x + 450, 320)], 14, SKIN)
        s.poly(thick([(x - 130, 500), (x - 170, 680), (x - 120, 820)], 64), arm, 6); s.ell((x - 116, 834), 30, 30, SKIN, 5)
    elif pose == 'tap':
        s.poly(thick([(x + 130, 500), (x + 230, 680), (x + 380, 760)], 64), arm, 6); s.ell((x + 398, 770), 32, 30, SKIN, 5)
        s.poly(thick([(x - 120, 500), (x - 150, 690), (x - 90, 830)], 64), arm, 6); s.ell((x - 86, 844), 30, 30, SKIN, 5)
    elif pose == 'run':
        s.poly(thick([(x + 135, 500), (x + 240, 600), (x + 300, 520)], 64), arm, 6); s.ell((x + 312, 506), 32, 32, SKIN, 5)
        s.poly(thick([(x - 135, 500), (x - 210, 660), (x - 290, 720)], 64), arm, 6); s.ell((x - 302, 728), 32, 32, SKIN, 5)
    elif pose == 'wave':
        s.poly(thick([(x + 135, 500), (x + 215, 340), (x + 245, 170)], 66), arm, 6); s.ell((x + 248, 146), 36, 38, SKIN, 5)
        s.poly(thick([(x - 130, 500), (x - 170, 680), (x - 120, 820)], 64), arm, 6); s.ell((x - 116, 834), 30, 30, SKIN, 5)
    else:
        for sx in (-1, 1): s.poly(thick([(x + sx * 130, 500), (x + sx * 170, 680), (x + sx * 130, 830)], 64), arm, 6); s.ell((x + sx * 128, 846), 30, 30, SKIN, 5)
    hs = Sheet(360, 330); head(hs, (170, 170), face, moust); hat(hs, (170, 112), hatk, hatc)
    hi = hs.im.resize((int(hs.im.width * 1.65), int(hs.im.height * 1.65)), Image.LANCZOS)
    s.im.alpha_composite(hi, (int((x + 6) * SS - hi.width / 2), int(505 * SS - hi.height * 0.86))); s.save(name)

def face_card(name, hatk, hatc, moust=False, hair=None):
    """a head and shoulders that pops up in a window"""
    s = Sheet(420, 420); s.poly([(60, 420), (80, 330), (340, 330), (360, 420)], (110, 80, 70, 255) if not hair else hair, 6)
    hs = Sheet(360, 330); head(hs, (170, 170), 1, moust); hat(hs, (170, 112), hatk, hatc)
    s.im.alpha_composite(hs.im, (int(30 * SS), int(20 * SS))); s.save(name)

# ---------------------------------------------------------------- the two ships, the cargo behind its hull door, the lifeboat
SHIPBLK = (44, 44, 50, 255); RED_W = (170, 50, 40, 255); WHITE = (240, 236, 222, 255)
def montblanc():
    W, H = 2400, 1100; s = Sheet(W, H); nm = 'montblanc'
    s.poly([(80, 640), (2260, 640), (2380, 600), (2200, 1000), (220, 1000), (60, 760)], SHIPBLK, 9)        # hull, bow on the right
    s.poly([(150, 930), (2240, 930), (2200, 1000), (220, 1000)], RED_W, 6)
    s.rect(880, 700, 1520, 900, (26, 22, 20, 255), 6); s.meta(nm, 'hold', 1200, 900)                      # the hold behind the hull door
    for k in range(18): s.ell((200 + k * 115, 680), 8, 8, (90, 90, 96, 255), 0)
    s.rect(820, 420, 1360, 640, WHITE, 7)                                                                    # bridge house
    for k in range(5): s.rect(860 + k * 96, 470, 920 + k * 96, 530, (150, 196, 214, 255), 4)
    s.rect(980, 330, 1200, 420, WHITE, 6)
    s.poly([(1020, 120), (1150, 120), (1160, 420), (1010, 420)], (60, 60, 64, 255), 7); s.rect(1012, 170, 1154, 210, (230, 196, 70, 255), 4)   # funnel
    for mx_ in (520, 1900): s.line([(mx_, 640), (mx_, 90)], 14, (110, 84, 60, 255)); s.line([(mx_ - 120, 230), (mx_ + 120, 230)], 10, (110, 84, 60, 255))
    s.line([(520, 90), (100, 640)], 3); s.line([(1900, 90), (2330, 620)], 3); s.line([(520, 90), (1010, 160)], 3); s.line([(1900, 90), (1150, 160)], 3)
    s.rect(1700, 560, 2150, 640, (120, 90, 60, 255), 5)                                                     # drums of fuel on the fore deck
    for k in range(7): s.ell((1740 + k * 62, 545), 28, 34, (190, 150, 60, 255), 5)
    s.meta(nm, 'fire', 1950, 520); s.meta(nm, 'fire2', 1500, 600); s.meta(nm, 'stack', 1085, 120); s.meta(nm, 'flag', 120, 520)
    s.line([(130, 640), (130, 400)], 8, (110, 84, 60, 255))                                                  # the French flag at the stern
    for k, c in enumerate(((40, 70, 160, 255), (250, 250, 250, 255), (210, 40, 40, 255))): s.rect(140 + k * 60, 400, 200 + k * 60, 500, c, 4)
    s.text((1820, 790), 'MONT-BLANC', 64, WHITE)
    s.save(nm)
    c = Sheet(640, 200); c.rect(0, 0, 640, 200, (40, 32, 26, 255), 0)                                         # the cargo: crates of TNT, drums
    for k in range(5):
        c.rect(10 + k * 126, 70, 128 + k * 126, 196, (196, 150, 90, 255), 5); c.text((69 + k * 126, 134), 'TNT', 40, (180, 30, 30, 255))
    for k in range(4): c.rect(40 + k * 150, 4, 160 + k * 150, 70, (210, 180, 60, 255), 5); c.text((100 + k * 150, 38), 'DANGER', 22, INK)
    c.save('cargo')
    p = Sheet(640, 200); p.rect(0, 0, 640, 200, SHIPBLK, 7)
    for k in range(8):
        for j in range(3): p.ell((40 + k * 80, 40 + j * 60), 7, 7, (90, 90, 96, 255), 0)
    p.save('hullpanel')
def imo():
    W, H = 2200, 1000; s = Sheet(W, H); GR = (120, 124, 120, 255)
    s.poly([(20, 560), (140, 600), (2140, 600), (2140, 720), (1980, 920), (200, 920)], GR, 9)                # hull, bow on the left
    s.poly([(150, 860), (2040, 860), (1980, 920), (200, 920)], RED_W, 6)
    for k in range(16): s.ell((260 + k * 115, 640), 8, 8, (80, 84, 80, 255), 0)
    s.rect(1100, 380, 1640, 600, WHITE, 7)
    for k in range(5): s.rect(1140 + k * 96, 430, 1200 + k * 96, 490, (150, 196, 214, 255), 4)
    s.poly([(1290, 130), (1420, 130), (1430, 380), (1280, 380)], (30, 30, 34, 255), 7); s.rect(1282, 180, 1426, 230, (200, 50, 40, 255), 4)
    for mx_ in (560, 1860): s.line([(mx_, 600), (mx_, 100)], 14, (110, 84, 60, 255)); s.line([(mx_ - 110, 240), (mx_ + 110, 240)], 10, (110, 84, 60, 255))
    s.line([(2100, 600), (2100, 380)], 8, (110, 84, 60, 255))                                                # Norway's flag at the stern
    s.rect(1970, 380, 2096, 470, (200, 40, 40, 255), 4); s.rect(1970, 414, 2096, 436, (250, 250, 250, 255), 0); s.rect(2010, 380, 2030, 470, (250, 250, 250, 255), 0)
    s.rect(1970, 419, 2096, 431, (40, 60, 140, 255), 0); s.rect(2015, 380, 2025, 470, (40, 60, 140, 255), 0)
    s.text((700, 760), 'IMO', 80, WHITE); s.meta('imo', 'stack', 1355, 130); s.save('imo')
def lifeboat():
    s = Sheet(1100, 520); s.poly([(20, 300), (1080, 300), (960, 500), (140, 500)], (190, 150, 100, 255), 8); s.line([(60, 340), (1040, 340)], 6, (150, 110, 70, 255))
    for k in range(4):
        x = 230 + k * 210; s.poly([(x - 60, 300), (x + 60, 300), (x + 50, 170), (x - 50, 170)], (30, 44, 90, 255), 6)
        hs = Sheet(360, 330); head(hs, (170, 170), -1 if k % 2 == 0 else 1, k == 1); hat(hs, (170, 112), 'beret', None)
        hi = hs.im.resize((int(hs.im.width * 0.75), int(hs.im.height * 0.75)), Image.LANCZOS); s.im.alpha_composite(hi, (int((x - 135) * SS), int(-20 * SS)))
    s.save('lifeboat')
    o = Sheet(1400, 200)
    for k in range(2): o.poly(thick([(60 + k * 700, 40), (640 + k * 700, 160)], 18), (170, 130, 80, 255), 4); o.ell((620 + k * 700, 156), 50, 22, (170, 130, 80, 255), 4)
    o.save('oars')

# ---------------------------------------------------------------- talk bubbles, fire, smoke, steam, the cloud, pieces flying
def bubble(name, lines, size, W=900, H=520, tail=1):
    s = Sheet(W, H); s.poly(blob((W / 2, H * 0.42), W * 0.46, H * 0.36, 70), (255, 255, 250, 255), 8)
    s.poly([(W / 2 - 60 * tail, H * 0.7), (W / 2 + 40 * tail, H * 0.72), (W / 2 - 150 * tail, H * 0.97)], (255, 255, 250, 255), 0)
    s.line([(W / 2 + 40 * tail, H * 0.74), (W / 2 - 150 * tail, H * 0.97), (W / 2 - 60 * tail, H * 0.74)], 8)
    for k, ln in enumerate(lines): s.text((W / 2, H * 0.42 + (k - (len(lines) - 1) / 2) * size * 1.1), ln, size, (190, 30, 30, 255) if '!' in ln else INK)
    s.save(name)
def flame(name, seed):
    r = random.Random(seed); s = Sheet(500, 760)
    for col, sc in (((230, 70, 30, 255), 1.0), ((250, 150, 40, 255), 0.72), ((255, 226, 110, 255), 0.42)):
        pts = []
        for k in range(9):
            u = k / 8; x = 250 + (u - 0.5) * 420 * sc; pts.append((x, 740 - (60 + 220 * math.sin(math.pi * u)) * sc))
            if k < 8: pts.append((x + 26 * sc, 740 - (300 + 380 * math.sin(math.pi * (u + 0.06)) + r.random() * 120) * sc))
        s.poly([(250 - 210 * sc, 740)] + pts + [(250 + 210 * sc, 740)], col, 6 if sc == 1.0 else 0)
    s.save(name)
def puff(name, col, seed, W=700, H=520):
    s = Sheet(W, H); r = random.Random(seed)
    for k in range(7):
        c = (W * (0.2 + 0.6 * r.random()), H * (0.35 + 0.35 * r.random())); s.ell(c, W * (0.16 + 0.08 * r.random()), H * (0.2 + 0.08 * r.random()), col, 6)
    for k in range(3): c = (W * (0.3 + 0.4 * r.random()), H * 0.45); s.ell(c, W * 0.12, H * 0.12, shade(col, 1.08 if col[0] < 200 else 0.95), 0)
    s.save(name)
def cloud():
    """the white cloud over the harbour: a rolling column with a wide top"""
    W, H = 1600, 2400; s = Sheet(W, H); r = random.Random(4); WH = (246, 244, 238, 255); GR = (206, 204, 198, 255)
    s.poly([(560, 2400), (1040, 2400), (930, 1100), (670, 1100)], GR, 8)
    for k in range(14): y = 2300 - k * 90; s.ell((800 + 40 * math.sin(k), y), 220 - k * 6, 90, WH if k % 2 else GR, 6)
    for k in range(18):
        a = math.pi * (k / 17); c = (800 + 620 * math.cos(a) * (0.7 + 0.3 * r.random()), 620 - 420 * math.sin(a) * (0.6 + 0.4 * r.random())); s.ell(c, 230 + 60 * r.random(), 180 + 40 * r.random(), WH if k % 2 else GR, 7)
    s.ell((800, 640), 600, 330, WH, 0)
    for k in range(9): c = (800 + 480 * math.cos(k * 0.8), 640 + 200 * math.sin(k * 1.3)); s.ell(c, 160, 110, GR if k % 3 == 0 else WH, 5)
    s.save('cloud')
def debris():
    s = Sheet(700, 420); s.poly([(20, 60), (660, 20), (680, 260), (520, 380), (380, 300), (240, 400), (60, 300)], SHIPBLK, 8); s.line([(40, 340), (640, 330)], 18, RED_W); s.save('chunk')
    s = Sheet(320, 700); s.poly([(40, 20), (280, 20), (290, 680), (30, 680)], (60, 60, 64, 255), 8); s.rect(34, 120, 286, 190, (230, 196, 70, 255), 5); s.save('funnel')
    s = Sheet(900, 160); s.poly([(10, 30), (880, 10), (890, 130), (20, 150)], (176, 134, 88, 255), 6); s.line([(40, 80), (860, 70)], 4, (140, 100, 60, 255)); s.save('plank')
    s = Sheet(400, 400); s.rect(20, 20, 380, 380, (196, 150, 90, 255), 7); s.line([(20, 20), (380, 380)], 10, (150, 110, 60, 255)); s.line([(380, 20), (20, 380)], 10, (150, 110, 60, 255)); s.save('crate')
    s = Sheet(700, 900); A = (40, 40, 44, 255)                                                               # the anchor
    s.poly(thick([(350, 120), (350, 760)], 70), A, 7); s.ell((350, 80), 70, 70, (0, 0, 0, 0), 0); s.ell((350, 80), 70, 70, A, 7); s.ell((350, 80), 32, 32, (60, 70, 90, 0), 0)
    s.poly(thick([(80, 560), (160, 760), (350, 840), (540, 760), (620, 560)], 60), A, 7); s.poly(thick([(200, 260), (500, 260)], 50), A, 6)
    for x_ in (80, 620): s.poly([(x_ - 50, 560), (x_ + 50, 560), (x_, 470)], A, 6)
    s.save('anchor')
    s = Sheet(200, 260); s.poly([(20, 240), (180, 200), (90, 10)], (190, 226, 240, 255), 5); s.line([(70, 180), (100, 60)], 6, (255, 255, 255, 255)); s.save('shard')
    s = Sheet(1600, 560)                                                                                     # rubble: a heap of broken boards
    for k in range(26):
        x = 100 + rnd.random() * 1400; y = 300 + rnd.random() * 200; a = rnd.uniform(-0.8, 0.8); L = 200 + rnd.random() * 300
        col = rnd.choice([(176, 134, 88, 255), (150, 60, 50, 255), (200, 186, 140, 255), (120, 130, 140, 255)])
        s.poly(thick([(x - L / 2 * math.cos(a), y - L / 2 * math.sin(a)), (x + L / 2 * math.cos(a), y + L / 2 * math.sin(a))], 46), col, 5)
    s.poly([(0, 560), (60, 440), (1540, 440), (1600, 560)], (110, 96, 80, 255), 6); s.save('rubble')
    s = Sheet(500, 300)
    for k in range(9): a = math.pi * (0.1 + 0.8 * k / 8); s.line([(250, 290), (250 + 230 * math.cos(a), 290 - 260 * math.sin(a))], 10, (255, 210, 80, 255))
    s.save('sparks')

# ---------------------------------------------------------------- the town: wooden houses (windows for faces), the station, the clock, the calendar
def house(name, body, roof, wins, W=1100, H=1300, kind='gable'):
    s = Sheet(W, H)
    if kind == 'gable':
        s.poly([(60, 520), (W - 60, 520), (W - 60, H - 10), (60, H - 10)], body, 8)
        s.poly([(20, 540), (W / 2, 120), (W - 20, 540)], roof, 8); s.rect(W * 0.66, 160, W * 0.66 + 90, 380, (150, 70, 60, 255), 6)
    else:
        s.poly([(60, 260), (W - 60, 260), (W - 60, H - 10), (60, H - 10)], body, 8); s.rect(30, 200, W - 30, 280, roof, 7)
    for k in range(int((H - 520) / 34)): s.line([(64, 540 + k * 34), (W - 64, 540 + k * 34)], 3, shade(body, 0.85))
    for k, (x, y) in enumerate(wins):
        s.rect(x - 100, y - 110, x + 100, y + 110, (40, 50, 62, 255), 7); s.line([(x, y - 110), (x, y + 110)], 8, WHITE); s.line([(x - 100, y), (x + 100, y)], 8, WHITE)
        s.meta(name, f'w{k}', x, y + 40)
    s.rect(W / 2 - 90, H - 330, W / 2 + 90, H - 12, shade(body, 0.6), 7); s.save(name)
def station():
    W, H = 2400, 1700; s = Sheet(W, H); WD = (196, 172, 128, 255)                                            # the back wall, seen from inside
    s.rect(20, 120, W - 20, H - 10, WD, 9)
    for k in range(int(H / 46)): s.line([(24, 150 + k * 46), (W - 24, 150 + k * 46)], 4, shade(WD, 0.86))
    s.rect(20, 1160, W - 20, H - 10, (130, 96, 64, 255), 7)                                                   # wainscot
    s.rect(1520, 360, 2120, 900, (176, 210, 226, 255), 9); s.line([(1820, 360), (1820, 900)], 10, WHITE); s.line([(1520, 630), (2120, 630)], 10, WHITE)   # window to the harbour
    s.rect(140, 260, 760, 380, (120, 90, 60, 255), 6); s.text((450, 320), 'DISPATCHER', 52, (240, 226, 190, 255))
    s.rect(140, 520, 700, 1000, (232, 226, 206, 255), 6)                                                      # the train sheet board
    s.text((420, 570), 'TRAINS DUE', 44, INK)
    for k, (a, b) in enumerate((('No. 10  SAINT JOHN', '8:55'), ('No. 4  TRURO', '9:30'), ('FREIGHT', '10:10'))):
        s.text((360, 660 + k * 100), a, 34, INK); s.text((620, 660 + k * 100), b, 34, (180, 30, 30, 255) if k == 0 else INK)
    s.meta('st_wall', 'clock', 1150, 470); s.meta('st_wall', 'cal', 1150, 860)
    s.save('st_wall')
    s = Sheet(2800, 560); s.poly([(0, 300), (1400, 20), (2800, 300), (2800, 400), (0, 400)], (110, 60, 50, 255), 9)   # the roof edge and its sign
    s.rect(80, 380, 2720, 470, (120, 86, 56, 255), 7); s.rect(900, 160, 1900, 340, (40, 60, 50, 255), 7); s.text((1400, 252), 'RICHMOND', 110, (240, 226, 190, 255))
    for k in range(14): s.poly([(110 + k * 190, 470), (200 + k * 190, 470), (155 + k * 190, 540)], (120, 86, 56, 255), 4)
    s.save('st_roof')
    s = Sheet(1400, 800); DK = (110, 76, 48, 255)                                                            # the desk with the telegraph sounder
    s.rect(40, 260, 1360, 340, DK, 8); s.rect(80, 340, 300, 790, shade(DK, 0.85), 7); s.rect(1100, 340, 1320, 790, shade(DK, 0.85), 7)
    s.rect(560, 150, 900, 260, (70, 70, 74, 255), 6); s.ell((640, 130), 50, 50, (160, 120, 60, 255), 6); s.ell((820, 130), 50, 50, (160, 120, 60, 255), 6)
    s.rect(960, 210, 1240, 262, (40, 40, 44, 255), 6); s.meta('desk', 'key', 1180, 210)                       # the key's base
    s.poly([(120, 210), (420, 190), (430, 262), (110, 262)], (246, 242, 230, 255), 5); s.line([(150, 222), (390, 210)], 3, (120, 120, 120, 255))
    s.save('desk')
    s = Sheet(500, 120); s.poly([(20, 70), (420, 40), (440, 60), (30, 96)], (60, 60, 64, 255), 6); s.ell((440, 50), 40, 34, (40, 40, 44, 255), 6); s.save('keyarm')
    s = Sheet(600, 600); s.ell((300, 300), 280, 280, (130, 90, 50, 255), 9); s.ell((300, 300), 232, 232, (250, 246, 232, 255), 6)   # the clock
    for k in range(12): a = 2 * math.pi * k / 12; s.line([(300 + 200 * math.sin(a), 300 - 200 * math.cos(a)), (300 + 222 * math.sin(a), 300 - 222 * math.cos(a))], 10 if k % 3 == 0 else 5)
    for k, n in ((0, '12'), (3, '3'), (6, '6'), (9, '9')): a = 2 * math.pi * k / 12; s.text((300 + 160 * math.sin(a), 300 - 160 * math.cos(a)), n, 56, INK)
    s.save('clock')
    s = Sheet(60, 420); s.poly([(30, 0), (52, 300), (30, 420), (8, 300)], INK, 0); s.save('hand_m')
    s = Sheet(70, 300); s.poly([(35, 0), (62, 200), (35, 300), (8, 200)], INK, 0); s.save('hand_h')
    for nm, d in (('cal5', '5'), ('cal6', '6')):
        s = Sheet(460, 560); s.rect(10, 40, 450, 550, (250, 248, 240, 255), 6); s.rect(10, 40, 450, 150, (190, 40, 36, 255), 6); s.text((230, 96), 'DECEMBER', 52, WHITE)
        s.text((230, 320), d, 230, INK); s.text((230, 500), '1917', 70, INK); s.ell((230, 30), 18, 18, (120, 120, 120, 255), 4); s.save(nm)

def pole():
    s = Sheet(500, 2800); BR = (120, 92, 66, 255); s.poly([(220, 2800), (280, 2800), (270, 60), (230, 60)], BR, 7)
    s.rect(40, 180, 460, 240, BR, 6)
    for x in (70, 160, 340, 430): s.ell((x, 160), 18, 26, (120, 170, 140, 255), 4)
    s.save('pole')
def signal():
    s = Sheet(400, 2400); s.rect(170, 260, 230, 2390, (60, 60, 64, 255), 7); s.rect(120, 2330, 280, 2395, (60, 60, 64, 255), 6)
    s.rect(110, 150, 290, 330, (40, 40, 44, 255), 7); s.ell((200, 240), 50, 50, (30, 30, 30, 255), 4); s.save('sigpost')
    s = Sheet(900, 160); s.poly([(20, 30), (880, 50), (880, 110), (20, 130)], (200, 40, 36, 255), 7); s.rect(700, 46, 760, 112, WHITE, 0); s.save('sigarm')
def rocksign():
    s = Sheet(1200, 900); s.rect(140, 300, 200, 890, (110, 84, 60, 255), 6); s.rect(1000, 300, 1060, 890, (110, 84, 60, 255), 6)
    s.rect(30, 60, 1170, 340, (40, 60, 50, 255), 8); s.text((600, 200), 'ROCKINGHAM', 120, (240, 226, 190, 255)); s.save('rocksign')
def pier6():
    s = Sheet(800, 1000); s.rect(370, 300, 430, 1000, (110, 84, 60, 255), 6); s.rect(40, 40, 760, 330, (240, 230, 200, 255), 8); s.text((400, 190), 'PIER 6', 130, INK); s.save('pier6')

# ---------------------------------------------------------------- trains: a locomotive each way, a passenger coach with faces, boxcars, a wheel
def loco(name, face, plow=False):
    W, H = 2000, 1100; s = Sheet(W, H); BL = (34, 34, 38, 255); RD = (150, 40, 36, 255)
    def X(x): return x if face > 0 else W - x
    def poly(pts, *a, **k): s.poly([(X(x), y) for x, y in pts], *a, **k)
    poly([(300, 420), (1500, 420), (1500, 820), (300, 820)], BL, 8)                                          # boiler
    for k in range(3): s.line([(X(400 + k * 400), 420), (X(400 + k * 400), 820)], 6, (70, 70, 74, 255))
    poly([(1500, 200), (1940, 200), (1940, 900), (1500, 900)], RD, 8); poly([(1560, 280), (1700, 280), (1700, 440), (1560, 440)], (230, 200, 120, 255), 6)
    poly([(1460, 160), (1980, 160), (1980, 220), (1460, 220)], BL, 6)
    poly([(420, 160), (540, 160), (560, 420), (400, 420)], BL, 8); poly([(380, 120), (580, 120), (560, 170), (400, 170)], BL, 6)   # smokestack
    s.ell((X(900), 380), 90, 60, BL, 7); s.ell((X(260), 600), 60, 100, (230, 220, 160, 255), 7)               # dome, headlamp
    poly([(240, 820), (1960, 820), (1960, 880), (240, 880)], RD, 6)
    if plow: poly([(40, 1060), (300, 640), (300, 1060)], (140, 146, 150, 255), 8); poly([(60, 1040), (290, 700), (290, 760), (120, 1040)], (210, 214, 218, 255), 0)
    else: poly([(100, 1060), (300, 860), (300, 1060)], RD, 7)                                               # cow catcher
    META[name] = {'wheels': [[X(x) / W, 1 - 960 / H] for x in (560, 900, 1240)], 'small': [[X(x) / W, 1 - 1000 / H] for x in (1650, 1840)], 'stack': [X(480) / W, 1 - 120 / H]}
    s.save(name)
def coach(name, col, label, faces=True, W=2200, H=1000):
    s = Sheet(W, H); s.poly([(60, 180), (W - 60, 180), (W - 40, 240), (40, 240)], shade(col, 0.6), 7)
    s.rect(60, 240, W - 60, 880, col, 8); s.rect(60, 820, W - 60, 900, (40, 40, 44, 255), 6)
    if faces:
        for k in range(8):
            x = 200 + k * 250; s.rect(x - 80, 330, x + 80, 500, (230, 220, 170, 255), 6)
            hs = Sheet(360, 330); head(hs, (170, 170), 1 if k % 2 else -1, k % 3 == 0); hat(hs, (170, 112), rnd.choice(['cap', 'bonnet', 'cap']), rnd.choice([(90, 70, 60, 255), (60, 70, 110, 255), (120, 60, 70, 255)]))
            hi = hs.im.resize((int(hs.im.width * 0.42), int(hs.im.height * 0.42)), Image.LANCZOS); s.im.alpha_composite(hi, (int((x - 75) * SS), int(345 * SS)))
            s.rect(x - 80, 470, x + 80, 500, shade(col, 0.8), 5)
        s.text((W / 2, 640), label, 96, (230, 200, 120, 255))
    else:
        s.rect(W / 2 - 280, 300, W / 2 + 280, 820, shade(col, 0.85), 7); s.line([(W / 2, 300), (W / 2, 820)], 6)
        s.text((W / 2, 560), label, 150 if len(label) < 7 else 120, WHITE, 6)
    META[name] = {'wheels': [[x / W, 1 - 960 / H] for x in (300, 520, W - 520, W - 300)]}
    s.save(name)
def wheel():
    s = Sheet(400, 400); s.ell((200, 200), 190, 190, (150, 40, 36, 255), 9); s.ell((200, 200), 150, 150, (40, 40, 44, 255), 6)
    for k in range(10): a = 2 * math.pi * k / 10; s.line([(200, 200), (200 + 146 * math.cos(a), 200 + 146 * math.sin(a))], 14, (150, 40, 36, 255))
    s.ell((200, 200), 40, 40, (200, 180, 120, 255), 6); s.save('wheel')

# ---------------------------------------------------------------- the blizzard and the tree
def flake():
    s = Sheet(200, 200)
    for k in range(6): a = math.pi * k / 3; s.line([(100, 100), (100 + 86 * math.cos(a), 100 + 86 * math.sin(a))], 14, (255, 255, 255, 255))
    s.ell((100, 100), 20, 20, (255, 255, 255, 255), 0); s.save('flake')
def drift():
    s = Sheet(1800, 460); pts = [(0, 460)] + [(k * 60, 300 - 200 * math.sin(math.pi * k / 30) ** 0.6 + 20 * math.sin(k * 1.7)) for k in range(31)] + [(1800, 460)]
    s.poly(pts, (246, 248, 252, 255), 7); s.poly([(p[0], p[1] + 70) for p in pts[2:-2]] + [(1700, 460), (100, 460)], (214, 224, 236, 255), 0); s.save('drift')
def xtree():
    W, H = 1600, 2600; s = Sheet(W, H); G1 = (40, 110, 66, 255); G2 = (30, 90, 54, 255)
    s.rect(700, 2280, 900, 2590, (110, 76, 48, 255), 8)
    tiers = [(2320, 760), (1960, 640), (1600, 520), (1250, 400), (900, 280), (580, 170)]
    for k, (y, hw) in enumerate(tiers):
        pts = [(800 - hw, y)] + [(800 - hw + 2 * hw * j / 12, y + 30 * (j % 2)) for j in range(13)] + [(800 + hw, y), (800, y - 560)]
        s.poly(pts, G1 if k % 2 else G2, 8)
    lights = []
    for k, (y, hw) in enumerate(tiers):                                                                      # garland and the bulbs' spots
        s.line([(800 - hw * 0.8, y - 140), (800 + hw * 0.7, y - 60)], 12, (230, 196, 70, 255))
        for j in range(5): u = (j + 0.5) / 5; lights.append([(800 - hw * 0.85 + 1.7 * hw * u) / W, 1 - (y - 70 - 40 * math.sin(u * 7)) / H])
    for k in range(18):
        y_, hw_ = tiers[k % 6]; x = 800 + (rnd.random() - 0.5) * 1.5 * hw_; s.ell((x, y_ - 200 - rnd.random() * 120), 34, 34, rnd.choice([(210, 40, 40, 255), (240, 200, 60, 255), (70, 110, 200, 255)]), 5)
    META['xtree'] = {'lights': lights, 'top': [0.5, 1 - 60 / H], 'tag': [0.68, 1 - 1700 / H]}; s.save('xtree')
    s = Sheet(500, 500); pts = []
    for k in range(10): a = -math.pi / 2 + math.pi * k / 5; r = 230 if k % 2 == 0 else 100; pts.append((250 + r * math.cos(a), 260 + r * math.sin(a)))
    s.poly(pts, (255, 220, 80, 255), 8); s.save('star')
    s = Sheet(1000, 680); s.poly([(140, 40), (960, 40), (960, 640), (140, 640), (20, 340)], (250, 244, 226, 255), 9); s.ell((110, 340), 30, 30, (120, 100, 80, 255), 5)
    s.text((560, 150), 'TO: BOSTON', 86, (190, 30, 30, 255)); s.text((560, 300), 'FROM:', 64, INK); s.text((560, 400), 'NOVA SCOTIA', 80, INK); s.text((560, 540), 'THANK YOU', 78, (30, 110, 60, 255))
    s.save('tag')

# ---------------------------------------------------------------- waves (the harbour), and the painted backdrop: a winter sky over the Dartmouth side
BLUE = (66, 120, 168, 255); BLUE_D = (46, 92, 136, 255); FOAM = (226, 240, 246, 255)
def waves(name, col, W=4800, H=320, seed=1):
    s = Sheet(W, H); r = random.Random(seed); pts = [(0, H)]
    for k in range(0, W + 1, 120): pts += [(k, 80 + r.random() * 20), (k + 60, 30 + r.random() * 20)]
    pts.append((W, H)); s.poly(pts, col, 6)
    for k in range(40): x = r.random() * W; y = 120 + r.random() * 150; s.line([(x, y), (x + 70, y - 8)], 6, FOAM)
    s.save(name)
def bigwave():
    W, H = 4800, 900; s = Sheet(W, H); pts = [(0, H)]
    for k in range(0, W + 1, 300): pts += [(k, 260), (k + 120, 60), (k + 220, 150)]
    pts.append((W, H)); s.poly(pts, BLUE, 8)
    for k in range(0, W, 300): s.poly([(k + 120, 60), (k + 220, 150), (k + 180, 170), (k + 100, 110)], FOAM, 0)
    for k in range(30): x = rnd.random() * W; y = 300 + rnd.random() * 500; s.line([(x, y), (x + 120, y - 10)], 8, FOAM)
    s.save('bigwave')
def backdrop():
    W, H = 4600, 2074; px = np.zeros((H, W, 3), np.float32); cut = int(H * (7.2 - 1.15) / 7.2)
    y = np.linspace(0, 1, cut)[:, None]
    px[:cut] = (np.array([150, 176, 204]) * (1 - y) + np.array([226, 228, 226]) * y)[:, None, :]
    px[cut:] = np.array([84, 126, 162])
    im = Image.fromarray(px.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for k in range(7):
        cx = rnd.random() * W; cy = 110 + rnd.random() * 360
        for j in range(5): r = 80 + rnd.random() * 90; d.ellipse([cx + j * 90 - r, cy - r * 0.55, cx + j * 90 + r, cy + r * 0.55], fill=(240, 240, 238))
    hz = cut                                                                                                # the Dartmouth shore: low hills, trees, little houses
    pts = [(0, hz)] + [(x, hz - 150 - 90 * math.sin(x / 520) - 40 * math.sin(x / 170)) for x in range(0, W + 1, 40)] + [(W, hz)]
    d.polygon(pts, fill=(112, 128, 118))
    for k in range(60):
        cx = rnd.random() * W; h_ = 60 + rnd.random() * 70; base = hz - 40 - rnd.random() * 90
        d.polygon([(cx - 30, base), (cx, base - h_), (cx + 30, base)], fill=(70, 96, 82))
    for k in range(22):
        cx = rnd.random() * W; base = hz - 20 - rnd.random() * 60; c = rnd.choice([(196, 90, 70), (226, 210, 160), (170, 180, 196), (240, 236, 226)])
        d.rectangle([cx - 34, base - 46, cx + 34, base], fill=c); d.polygon([(cx - 42, base - 46), (cx, base - 82), (cx + 42, base - 46)], fill=(80, 60, 56))
    d.rectangle([0, hz, W, hz + 26], fill=(150, 186, 210))
    for k in range(40): x = rnd.random() * W; yy = hz + 40 + rnd.random() * (H - hz - 60); d.line([(x, yy), (x + 80, yy - 6)], fill=(200, 226, 236), width=5)
    im = im.filter(ImageFilter.GaussianBlur(1.2)); im.save(os.path.join(OUT, 'backdrop.png')); print('backdrop', im.size)

if __name__ == '__main__':
    person('coleman', (60, 56, 52, 255), (52, 50, 56, 255), 'visor', None, 'tap', moust=True, shirt=(244, 240, 230, 255))
    person('coleman_go', (60, 56, 52, 255), (52, 50, 56, 255), 'visor', None, 'run', moust=True, shirt=(244, 240, 230, 255))
    person('sailor', (30, 40, 70, 255), (30, 40, 70, 255), 'sailor', None, 'run', extra='sailor')
    person('sailor_pt', (30, 40, 70, 255), (30, 40, 70, 255), 'sailor', None, 'point', extra='sailor')
    person('man', (110, 80, 60, 255), (70, 64, 60, 255), 'cap', (96, 90, 84, 255), 'point', moust=True)
    person('woman', (120, 60, 70, 255), (60, 56, 70, 255), 'bonnet', (70, 60, 90, 255), 'point', skirt=True)
    person('man2', (70, 90, 80, 255), (60, 60, 64, 255), 'cap', (60, 70, 66, 255), 'wave')
    face_card('face_a', 'cap', (96, 90, 84, 255), True); face_card('face_b', 'bonnet', (120, 60, 70, 255), hair=(120, 60, 70, 255)); face_card('face_c', 'cap', (60, 70, 110, 255), hair=(60, 70, 110, 255))
    montblanc(); imo(); lifeboat()
    bubble('bub_blow', ["IT'S GOING", 'TO BLOW!'], 92); bubble('bub_run', ['RUN!'], 170, 700, 460, -1); bubble('bub_huh', ['?'], 230, 460, 420)
    flame('flame_a', 1); flame('flame_b', 2); flame('flame_c', 3)
    puff('smoke', (70, 66, 64, 255), 3); puff('smoke2', (96, 92, 88, 255), 5); puff('steam', (244, 244, 242, 255), 7)
    cloud(); debris()
    house('house_a', (196, 90, 70, 255), (80, 60, 56, 255), [(300, 760), (800, 760), (300, 1040)])
    house('house_b', (226, 206, 150, 255), (90, 70, 60, 255), [(300, 500), (800, 500), (300, 830), (800, 830)], kind='flat')
    house('house_c', (150, 170, 196, 255), (70, 60, 60, 255), [(300, 760), (800, 760), (800, 1040)])
    station(); pole(); signal(); rocksign(); pier6()
    loco('loco_l', 1); loco('loco_r', -1, plow=True)
    coach('coach', (60, 100, 70, 255), 'INTERCOLONIAL'); coach('box_boston', (150, 60, 44, 255), 'BOSTON', False, 1800)
    coach('box_food', (130, 80, 50, 255), 'FOOD', False, 1800); coach('box_med', (200, 196, 186, 255), 'MEDICINE', False, 1800)
    wheel(); flake(); drift(); xtree()
    waves('waves', BLUE); waves('waves2', BLUE_D, seed=3); bigwave(); backdrop()
    json.dump(META, open(os.path.join(OUT, 'meta.json'), 'w'), indent=1)
