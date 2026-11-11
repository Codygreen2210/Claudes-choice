#!/usr/bin/env python3
"""Goosebumps. Opens on him stepping into freezing wind, his arm going bumpy; inside the skin: a hair in its pocket, the
tiny muscle hooked to it, the brain fires down a nerve, the muscles squeeze, hairs stand, skin bunches into bumps; a
furry animal puffs its coat (warm air trapped, looks bigger), the scared cat; we have little fur, just bumps; fear or a
song sets it off too; the squeeze wakes hair stem cells. Loops back into the wind.
Facts: Hsu & Lin, Cell 2020 (via Salon, Jul 2020; Science News Explores): arrector pili muscles pull hairs upright; cold
and emotions like fear trigger the sympathetic nerve; the same squeeze links to hair stem cells and can drive new hair
growth. Fur erection for warmth/aggression in animals: Darwin, cited there."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403
import scared as SC

DIVE = {1: (540, 560)}
ICE = (150, 220, 255)
GRN = (120, 255, 140)
EPI = ramp('#f8c8b0', '#d8a088', '#ffe0d0')
DERM = ramp('#f0a090', '#c06a5a', '#ffc0b0')
FOLL = ramp('#e8907a', '#a85848', '#ffb8a0')
MUSC = ramp('#e2483d', '#a82a26', '#ff8070')
HAIR = ramp('#4a3020', '#2a1810', '#7a5a40')
NERVE = ramp('#ffe14d', '#c8a020', '#fff4a0')
STEM = ramp('#7affd0', '#30b890', '#c8fff0')
FURC = ramp('#ff9a40', '#c86418', '#ffc890')
GX, GY = 0, 640


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def wind_lines(cv, T, n=9, a=0.8, cx=0, cy=0):
    for k in range(n):
        u = (T * 1.6 + k / n) % 1
        y = cy - 800 + k * 190 + 30 * np.sin(T * 3 + k)
        x = cx + 700 - 1600 * u
        line(cv, [(x, y), (x - 160, y + 10), (x - 260, y - 14)], 8, flat(hexc('#ffffff')), a=a * np.sin(np.pi * u))
    for k in range(18):                                                    # snow
        x = cx + 600 - ((T * 420 + k * 173) % 1300); y = cy - 900 + ((T * 160 + k * 251) % 1800)
        dot(cv, x, y, 6 + k % 3 * 3, flat(hexc('#ffffff')), a=0.85)


def outside(cv, T):
    cv.background('#9ab8d8', '#d8e6f4', vignette=0.25)
    box(cv, 0, GY + 220, 1000, 240, ramp('#f4f8ff', '#c8d4e4', '#ffffff'), r=0, ow=0, shadow=0)     # snowy ground
    box(cv, -400, GY - 300, 130, 300, ramp('#c86a4a', '#8a4428', '#e89070'), r=6)                   # the house he stepped out of
    box(cv, -330, GY - 170, 60, 160, ramp('#6a3a20', '#40200c', '#8a5a40'), r=8)                     # open door
    cv.glow(rbox(-330, GY - 170, 60, 160, 8), (-420, GY - 360, -240, GY + 20), '#ffd58a', 50, 0.5)


def arm_close(cv, T, bump=1.0, hairs=1.0):
    """Close on his forearm: skin, a field of hairs, bumps rising round each."""
    cv.background('#3a5a7a', '#1a2a3a', vignette=0.35)
    cv.shape(rbox(0, 0, 1200, 300, 300), (-1260, -320, 1260, 320), SKIN, ow=5)
    rr = np.random.default_rng(5)
    for k in range(70):
        x, y = rr.uniform(-560, 560), rr.uniform(-240, 240)
        if abs(y) > 280 - 40 * (abs(x) / 600) ** 2:
            continue
        if bump > 0:
            cv.shape(circle(x, y, 18 * bump), (x - 24, y - 24, x + 24, y + 24), SKIN, ow=2, alpha=bump)
        ang = np.radians(-160 + 70 * hairs + 6 * np.sin(T * 6 + k))
        line(cv, [(x, y), (x + 50 * np.cos(ang), y + 50 * np.sin(ang))], 4, flat(hexc('#3a2418')), a=0.9)


def skin_cut(cv, T, squeeze=0.0, nerve=0.0, stem=0.0, zoom_hair=False, labels=None):
    """Cross-section: epidermis on top, dermis below, a hair in its pocket (follicle), the little muscle from follicle up to
    the skin, a nerve wrapped on it. squeeze 0..1 tilts the hair upright and pulls a bump up."""
    cv.background('#2a0e14', '#12060a', vignette=0.4)
    q = ease(np.clip(squeeze, 0, 1))
    for fx in (-360, 0, 360):
        bump = 50 * q
        top = [(fx - 180, -330), (fx - 70, -330 - bump * 0.6), (fx, -330 - bump), (fx + 70, -330 - bump * 0.6), (fx + 180, -330)]
        cv.shape(poly(top + [(fx + 180, -230), (fx - 180, -230)]), pbox(top + [(fx + 180, -230), (fx - 180, -230)], 4), EPI, ow=0, shadow=0)
    box(cv, 0, 80, 560, 330, DERM, r=0, ow=0, shadow=0)
    box(cv, 0, -330 + 1, 560, 4, ramp('#c06a5a'), r=0, ow=0, shadow=0, a=0.4) if False else None
    for i, fx in enumerate((-360, 0, 360)):
        tilt = np.radians(-35 + 33 * q)                                    # hair from slanted to upright
        bx, by = fx - 40, 160                                              # the root bulb
        ux, uy = np.sin(tilt), -np.cos(tilt)
        top = (bx + ux * 520, by + uy * 520)
        foll = [(bx - 34, by + 20), (bx + 34, by + 20), (bx + ux * 470 + 26, by + uy * 470), (bx + ux * 470 - 26, by + uy * 470)]
        cv.shape(poly(foll), pbox(foll, 6), FOLL, ow=3)
        disc(cv, bx, by, 44, FOLL, ow=3)
        line(cv, [(bx, by), top, (top[0] + ux * 220, top[1] + uy * 220)], 12, HAIR, ow=2, flat=False)
        mx0, my0 = bx + ux * 230 + 24, by + uy * 230                       # the tiny muscle: from the follicle up to the skin
        mx1, my1 = fx + 130, -240 - 30 * q
        mm = ((mx0 + mx1) / 2 + 10 - 18 * q, (my0 + my1) / 2 + 20)
        line(cv, [(mx0, my0), mm, (mx1, my1)], 22 - 6 * q + 10 * q, MUSC, ow=3, flat=False)
        if squeeze > 0.05:
            cv.glow(polyline([(mx0, my0), mm, (mx1, my1)], 14), bbox_of([(mx0, my0), (mx1, my1)], 60), '#ff5040', 30, 0.5 * q)
        if nerve > 0:
            pts = [(fx + 260, 420), (fx + 200, 200), mm]
            cv.glow(polyline(pts, 8), bbox_of(pts, 50), '#ffe14d', 26, 0.7 * nerve)
            line(cv, pts, 9, NERVE, ow=2, flat=False)
            u = (T * 2 + i * 0.3) % 1
            p = (pts[0][0] + (pts[1][0] - pts[0][0]) * min(u * 2, 1), pts[0][1] + (pts[1][1] - pts[0][1]) * min(u * 2, 1)) if u < 0.5 else \
                (pts[1][0] + (mm[0] - pts[1][0]) * (u * 2 - 1), pts[1][1] + (mm[1] - pts[1][1]) * (u * 2 - 1))
            disc(cv, p[0], p[1], 14, NERVE, ow=0, alpha=nerve)
        if stem > 0:                                                       # hair stem cells waking up near the bulb
            for k in range(5):
                a = k * 1.25 + T * 1.5
                sx_, sy_ = bx + ux * 140 + 46 * np.cos(a), by + uy * 140 + 30 * np.sin(a)
                cv.glow(circle(sx_, sy_, 14), (sx_ - 50, sy_ - 50, sx_ + 50, sy_ + 50), '#7affd0', 26, stem * (0.6 + 0.4 * np.sin(T * 7 + k)))
                disc(cv, sx_, sy_, 13, STEM, ow=2, alpha=stem)


def furball(cv, x, y, s, T, puff=0.0, scared=0.0):
    """An orange cat side-on. puff 0..1 fluffs every hair out; arched back when scared."""
    arch = 70 * scared * s
    R = (1 + 0.55 * puff)
    n = 46
    for k in range(n):                                                     # the fur, spikes round the body outline
        a = k / n * 2 * np.pi
        bxk, byk = x + 190 * s * np.cos(a), y - arch * max(0, -np.sin(a)) + 110 * s * np.sin(a)
        L = (26 + 46 * puff) * s
        line(cv, [(bxk, byk), (bxk + np.cos(a) * L, byk + np.sin(a) * L * 1.1 + 4 * np.sin(T * 10 + k) * puff)], (16 + 6 * puff) * s, FURC, ow=2)
    cv.shape(ellipse(x, y - arch * 0.5, 190 * s * (1 + 0.1 * puff), (110 * s + arch * 0.5)), (x - 260 * s, y - 220 * s, x + 260 * s, y + 160 * s), FURC, ow=4)
    for lx in (-120, -60, 70, 130):                                        # legs, stiff when scared
        line(cv, [(x + lx * s, y + 70 * s), (x + lx * s * (1 + 0.05 * scared), y + 210 * s)], 30 * s, FURC, ow=3)
    hx, hy = x + 220 * s, y - 120 * s - arch * 0.3
    for k in range(20):
        a = k / 20 * 2 * np.pi
        line(cv, [(hx + 80 * s * np.cos(a), hy + 76 * s * np.sin(a)), (hx + (80 + 22 * puff) * s * np.cos(a), hy + (76 + 22 * puff) * s * np.sin(a))], 12 * s, FURC, ow=2)
    cv.shape(circle(hx, hy, 82 * s), (hx - 90 * s, hy - 90 * s, hx + 90 * s, hy + 90 * s), FURC, ow=4)
    for ex in (-40, 30):
        pts = [(hx + (ex - 26) * s, hy - 60 * s), (hx + ex * s, hy - 140 * s), (hx + (ex + 26) * s, hy - 62 * s)]
        cv.shape(poly(pts), pbox(pts, 4), FURC, ow=4)
    for ex in (-26, 34):
        disc(cv, hx + ex * s, hy - 10 * s, (16 + 8 * scared) * s, ramp('#e8ff9a', '#9ab830', '#ffffff'), ow=3)
        disc(cv, hx + ex * s, hy - 10 * s, (6 if scared else 11) * s, DARK, ow=0, shadow=0)
    if scared > 0.3:                                                       # hiss mouth
        cv.shape(ellipse(hx + 10 * s, hy + 40 * s, 26 * s, 20 * s), (hx - 20 * s, hy + 15 * s, hx + 40 * s, hy + 65 * s), ramp('#6a1a28'), ow=3)
    tx = x - 200 * s
    tail = [(tx, y - 20 * s), (tx - 70 * s, y - 120 * s - 60 * scared * s), (tx - 50 * s, y - 230 * s - 40 * scared * s)]
    line(cv, tail, (22 + 16 * puff) * s, FURC, ow=3)


def hug_arms(k):
    """arms at his sides (k=0) wrapping round himself (k=1), blended in angle space so nothing flips"""
    k = ease(k)
    a0, a1 = (reach(-1, -60, -420), reach(1, 60, -420)), (reach(-1, 120, -560), reach(1, -120, -560))
    return tuple(tuple(a0[i][j] * (1 - k) + a1[i][j] * k for j in range(2)) for i in range(2))


# ---------------------------------------------------------------- beats
def b0_hook(lt, dur, T):
    """He steps out the door into the wind; his arm goes bumpy. The camera rides in on his arm."""
    k = ease(float(np.clip((lt + 0.3) / 1.6, 0, 1)))
    cv = Canvas(-80 + 60 * k, GY - 600 + 30 * k, 1.25 + 0.35 * k)
    outside(cv, T)
    step = float(np.clip((lt + 1.2) / 1.0, 0, 1))
    wx = -330 + 260 * ease(step)
    shiver = 5 * np.sin(T * 40) if lt > -0.3 else 0
    guy(cv, wx + shiver, GY, 1.0, face='shock' if lt > -0.3 else 'calm',
        arms=hug_arms(float(np.clip((lt + 0.6) / 0.4, 0, 1))))
    wind_lines(cv, T, cx=cv.cx, cy=cv.cy)
    for j in range(int(np.clip((lt + 0.2) * 14, 0, 26))):                  # bumps pop up on his arms
        bx = wx + (-90 + 180 * ((j * 37) % 26) / 26)
        by = GY - 560 + 18 * np.sin(j * 1.7)
        dot(cv, bx, by, 5, flat(hexc('#e8a080')), a=0.9)
    hook_text(cv, 'BRRR!', lt, y=-800, size=160, color=ICE, pop_t=-0.25 if lt < 0 else 0.0)
    return cv


def b1_pocket(lt, dur, T):
    cv = Canvas(0, -40, 1.0 + 0.1 * ease(np.clip(lt / dur, 0, 1)))
    skin_cut(cv, T)
    slabel(cv, 'HAIR POCKET', 0, -760, 110, YEL, a=ease(np.clip((lt - 0.3) / 0.3, 0, 1)))
    return cv


def b2_muscle(lt, dur, T):
    cv = Canvas(40, -60, 1.7)
    skin_cut(cv, T, squeeze=0.05 * np.sin(T * 4) ** 2)
    x, y = W2(cv, 260, -150)
    arrows(cv, [((x, y), (150, -50))], YEL, 14)
    slabel(cv, 'TINY MUSCLE', 0, -760, 110, (255, 120, 110))
    return cv


def b3_nerve(lt, dur, T):
    cv = Canvas(0, -260, 0.75)
    skin_cut(cv, T, nerve=ease(np.clip((lt - 0.6) / 0.5, 0, 1)))
    brain(cv, 0, -880, 0.7, hot=0.3 + 0.3 * np.sin(T * 8) ** 2)
    pts = [(80, -760), (300, -560), (460, -200), (620, 420)]
    line(cv, pts, 14, NERVE, ow=3, flat=False)
    u = np.clip(lt / 0.8, 0, 1); i_ = min(int(u * 3), 2); f = u * 3 - i_
    p = (pts[i_][0] + (pts[i_ + 1][0] - pts[i_][0]) * f, pts[i_][1] + (pts[i_ + 1][1] - pts[i_][1]) * f)
    cv.glow(circle(*p, 22), (p[0] - 80, p[1] - 80, p[0] + 80, p[1] + 80), '#fff4a0', 40, 1.0)
    disc(cv, p[0], p[1], 20, NERVE, ow=0)
    slabel(cv, 'COLD!', 0, -760, 130, ICE)
    return cv


def b4_squeeze(lt, dur, T):
    sx_, sy_ = shake(lt, 0.3, 18, 0.4)
    cv = Canvas(sx_, -60 + sy_, 1.05)
    skin_cut(cv, T, squeeze=float(np.clip((lt - 0.2) / 0.6, 0, 1)), nerve=1.0)
    hook_text(cv, 'SQUEEZE!', lt, y=-760, size=140, pop_t=0.25, color=(255, 100, 90))
    return cv


def b5_stand(lt, dur, T):
    if lt < dur * 0.5:
        cv = Canvas(0, -140, 1.15)
        skin_cut(cv, T, squeeze=1.0, nerve=0.6)
        slabel(cv, 'HAIRS STAND UP', 0, -760, 100, YEL)
        return cv
    cv = Canvas(0, 0, 1.0)
    arm_close(cv, T, bump=ease(np.clip((lt - dur * 0.5) / 0.4, 0, 1)), hairs=1.0)
    hook_text(cv, 'BUMPS!', lt - dur * 0.5, y=-760, size=150, color=YEL)
    return cv


def b6_fur(lt, dur, T):
    cv = Canvas(40, 40, 1.15)
    cv.background('#9ab8d8', '#d8e6f4', vignette=0.25)
    box(cv, 0, 470, 900, 260, ramp('#f4f8ff', '#c8d4e4', '#ffffff'), r=0, ow=0, shadow=0)
    wind_lines(cv, T, n=6, a=0.6, cx=cv.cx, cy=cv.cy)
    pf = ease(np.clip((lt - 0.4) / 0.8, 0, 1))
    furball(cv, 0, 120, 1.1, T, puff=pf)
    if pf > 0.5:
        for k in range(8):                                                 # trapped warm air shimmer
            a = k * 0.8 + T
            dot(cv, 30 + 260 * np.cos(a), 100 + 160 * np.sin(a), 16, flat(hexc('#ffb070')), a=0.4)
    sbadge(cv, 'WARM AIR TRAPPED' if lt < dur * 0.6 else 'LOOKS BIGGER', -760, (255, 170, 90))
    return cv


def b7_cat(lt, dur, T):
    sx_, sy_ = shake(lt, 0.2, 16, 0.3)
    cv = Canvas(40 + sx_, 60 + sy_, 1.1)
    cv.background('#f8e0b8', '#e8c090', vignette=0.25)
    box(cv, 0, 480, 900, 240, WOOD, r=0, ow=0, shadow=0)
    k = ease(np.clip((lt - 0.15) / 0.35, 0, 1))
    furball(cv, -40, 150, 0.9 + 0.35 * k, T, puff=k, scared=k)
    SC.ghost(cv, 400, -120, 0.7, T, a=0.9)
    hook_text(cv, '2X SIZE!', lt, y=-760, size=140, pop_t=0.3, color=(255, 140, 60))
    return cv


def b8_noFur(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    arm_close(cv, T, bump=1.0, hairs=1.0)
    slabel(cv, 'NOT MUCH FUR', 0, -760, 110, YEL)
    return cv


def b9_song(lt, dur, T):
    cv = Canvas(0, GY - 620, 1.3)
    cv.background('#2a1a4a', '#120a24', vignette=0.4)
    for k in range(6):                                                     # light beams
        a = -1.2 + k * 0.48 + 0.1 * np.sin(T + k)
        pts = [(0, -1100), (np.cos(a) * 1400, -1100 + np.sin(a + 1.6) * 1800), (np.cos(a + 0.12) * 1400, -1100 + np.sin(a + 1.72) * 1800)]
        cv.shape(poly(pts), pbox(pts, 4), ramp('#ff7ad0' if k % 2 else '#7ad0ff'), ow=0, shadow=0, alpha=0.18)
    guy(cv, 0, GY, 1.0, face='happy', arms=(reach(-1, -160, -900), reach(1, 160, -900)))
    for k in range(8):                                                     # music notes
        u = (T * 0.6 + k / 8) % 1
        nx, ny = -360 + k * 100 + 30 * np.sin(T * 2 + k), GY - 500 - u * 700
        aa = float(np.sin(np.pi * u)); NC = ramp('#ffe678', '#c8a830', '#fff4c0')
        disc(cv, nx, ny, 22, NC, ow=3, alpha=aa)
        line(cv, [(nx + 18, ny), (nx + 18, ny - 80)], 8, NC, ow=2, a=aa)
        line(cv, [(nx + 18, ny - 80), (nx + 46, ny - 60)], 8, NC, ow=2, a=aa)
    for j in range(22):
        bx = -90 + 180 * ((j * 37) % 22) / 22
        dot(cv, bx, GY - 700 + 14 * np.sin(j * 1.7), 6, flat(hexc('#e8a080')), a=ease(np.clip(lt / 0.6, 0, 1)))
    sbadge(cv, 'FEAR OR MUSIC', -760, (255, 122, 208))
    return cv


def b10_stem(lt, dur, T):
    cv = Canvas(-40, 40, 1.5)
    skin_cut(cv, T, squeeze=0.6 + 0.4 * np.sin(T * 3) ** 2, nerve=1.0, stem=ease(np.clip((lt - 0.4) / 0.5, 0, 1)))
    slabel(cv, 'HAIR GROWERS WAKE UP', 0, -760, 82, (122, 255, 208))
    return cv


BEATS = [b0_hook, b1_pocket, b2_muscle, b3_nerve, b4_squeeze, b5_stand, b6_fur, b7_cat, b8_noFur, b9_song, b10_stem]

if __name__ == '__main__':
    run(BEATS)
