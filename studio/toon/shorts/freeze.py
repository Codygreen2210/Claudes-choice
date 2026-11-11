#!/usr/bin/env python3
"""Brain freeze. Opens on him mid-gulp of a slushie, then the pain hits his forehead; inside his head: slush smacks the roof
of the mouth, the vessels there squeeze tight then snap open, the big face nerve fires, the brain blames the forehead;
the long name; tongue up / warm sip; it fades in seconds. Loops back into the gulp.
Facts: Houston Methodist ('what causes brain freeze'): cold on the roof of the mouth, vessels constrict then relax,
the rush sets off the trigeminal nerve, referred pain to forehead/temples; sphenopalatine ganglioneuralgia; seconds to
under five minutes; fixes: warm water, tongue on the roof of the mouth, eat slowly."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403

DIVE = {1: (540, 640)}
GRN = (120, 255, 140)
BLU = (140, 210, 255)
SLUSH = ramp('#4fb8ff', '#2a7fd0', '#bfe8ff')
CUPC = ramp('#e8f4ff', '#a8c0d8', '#ffffff')
VES = ramp('#e2483d', '#a82a26', '#ff8070')
NERVE = ramp('#ffe14d', '#c8a020', '#fff4a0')
PAL = ramp('#f59aa8', '#c96478', '#ffc8d0')
TONGUE = ramp('#ff8a9a', '#d05a6a', '#ffc0c8')
GY = 640                     # his feet (world y) in the room shots


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def kitchen(cv):
    cv.background('#ffd9a8', '#ffb978', vignette=0.25)
    box(cv, 0, GY + 200, 900, 220, ramp('#c98a52', '#9a6234', '#e8aa70'), r=0, ow=0, shadow=0)       # floor
    box(cv, -380, GY - 300, 170, 300, ramp('#e8eef4', '#b8c4d0', '#ffffff'), r=20)                  # fridge
    line(cv, [(-250, GY - 520), (-250, GY - 420)], 12, METAL, ow=3, flat=False)
    sticky(cv, -420, GY - 470, 0.8, ['LIKE &', 'SUB'])                                            # the one Easter egg


def cup(cv, x, y, s=1.0, level=0.8, straw_to=None, frost=0.0, T=0.0):
    pts = [(x - 62 * s, y - 120 * s), (x + 62 * s, y - 120 * s), (x + 46 * s, y + 120 * s), (x - 46 * s, y + 120 * s)]
    cv.shape(poly(pts), pbox(pts, 6), CUPC, ow=4, alpha=0.9)
    top = y + 120 * s - 236 * s * level
    sl = [(x - 59 * s + 15 * s * (1 - level), top), (x + 59 * s - 15 * s * (1 - level), top), (x + 44 * s, y + 116 * s), (x - 44 * s, y + 116 * s)]
    cv.shape(poly(sl), pbox(sl, 4), SLUSH, ow=0, shadow=0)
    box(cv, x, y - 128 * s, 70 * s, 14 * s, ramp('#ffffff', '#d0dce8', '#ffffff'), r=8 * s)        # lid
    if straw_to is not None:
        line(cv, [(x + 10 * s, y + 60 * s), (x + 10 * s, y - 140 * s), straw_to], 16 * s, ramp('#ff5a8a', '#c02a5a', '#ff9ab8'), ow=3, flat=False)
    for k in range(int(6 * frost)):
        a = T * 1.3 + k
        dot(cv, x + 70 * s * np.cos(a), y - 60 * s + 90 * s * np.sin(a * 1.7), 5 * s, flat(hexc('#ffffff')), a=0.8)


def head_xray(cv, T, ves=1.0, flow=1.0, nerve=0.0, cold=0.0, fore=0.0, slush=0.0, tongue=0.0, warm=0.0, puzzled=0.0):
    """Front x-ray of his head, centred at (0, 0), r ~ 330. ves: vessel width (0.3 squeezed .. 1.8 wide open)."""
    cv.background('#0e1e33', '#06101d', vignette=0.4)
    cv.shape(ellipse(0, 0, 330, 400), (-340, -410, 340, 410), XRAYC, ow=4, alpha=0.55)
    cv.shape(subtract(ellipse(0, -30, 300, 350), ellipse(0, -30, 270, 320)), (-310, -390, 310, 330), BONEW, ow=0, shadow=0, alpha=0.5)
    brain(cv, 0, -190, 1.05, hot=0.25 * puzzled * (0.5 + 0.5 * np.sin(T * 10)))
    if fore > 0:                                                       # the forehead lights up where he FEELS it
        cv.glow(ellipse(0, -330, 200, 60), (-400, -480, 400, -180), '#ff3a2a', 70, fore * (0.8 + 0.2 * np.sin(T * 12)))
    cv.shape(ellipse(0, 200, 170, 120), (-180, 70, 180, 330), ramp('#5a1f2a', '#3a0f18', '#7a3a48'), ow=3)     # the mouth
    cv.shape(subtract(ellipse(0, 210, 190, 120), ellipse(0, 240, 190, 120)), (-200, 80, 200, 260), PAL, ow=3)   # roof of the mouth
    if tongue > 0:
        ty = 300 - 70 * tongue
        cv.shape(ellipse(0, ty, 130, 60), (-140, ty - 70, 140, ty + 70), TONGUE, ow=3)
    if warm > 0:
        cv.glow(ellipse(0, 130, 170, 40), (-260, 40, 260, 220), '#ffaa40', 50, warm)
    if slush > 0:
        for k in range(14):
            a = k * 0.45 + T * 2
            r = 30 + 60 * ((k * 37) % 7) / 7
            dot(cv, np.cos(a) * r * 1.8, 150 + np.sin(a) * r * 0.5 * slush + 30 * (1 - slush), 18, SLUSH[0] if False else flat(hexc('#7fd0ff')), a=slush)
        if cold > 0:
            cv.glow(ellipse(0, 115, 180, 40), (-260, 40, 260, 200), '#7fd0ff', 50, cold)
    w = 9 * ves                                                        # the vessels just above the roof of the mouth
    for sx in (-1, 1):
        pts = [(sx * (20 + u * 200), 105 - 40 * u * u + 6 * np.sin(u * 9 + T * 3)) for u in np.linspace(0, 1, 9)]
        line(cv, pts, w, VES, ow=2, flat=False)
        for j in range(4):
            u = ((T * 0.8 * flow) + j / 4) % 1
            p = pts[min(int(u * 8), 7)]
            dot(cv, p[0], p[1], max(w * 0.45, 3), flat(hexc('#ffd0c8')), a=0.9 * min(1, flow))
        if cold > 0:
            for j in range(3):
                dot(cv, sx * (60 + 60 * j), 70 + 10 * np.sin(T * 5 + j), 6, flat(hexc('#e8f8ff')), a=cold)
    if nerve > 0:                                                      # the big face nerve, from the mouth up and back
        for sx in (-1, 1):
            pts = [(sx * 150, 110), (sx * 230, 20), (sx * 210, -90), (sx * 120, -150)]
            cv.glow(polyline(pts, 10), bbox_of(pts, 60), '#ffe14d', 30, nerve * 0.8)
            line(cv, pts, 12, NERVE, ow=2, flat=False)
            u = (T * 1.8) % 1; i_ = min(int(u * 3), 2); f = u * 3 - i_
            p = (pts[i_][0] + (pts[i_ + 1][0] - pts[i_][0]) * f, pts[i_][1] + (pts[i_ + 1][1] - pts[i_][1]) * f)
            disc(cv, p[0], p[1], 16, NERVE, ow=0, alpha=nerve)
    if puzzled > 0:
        for k in range(3):
            a = T * 2 + k * 2.1
            label(cv, '?', np.cos(a) * 260, -260 + np.sin(a) * 90, 110, YEL, a=puzzled)


# ---------------------------------------------------------------- beats
MOUTH = (12, -700)            # straw tip at his mouth, his own units


def gulp_scene(cv, lt, T, pain):
    kitchen(cv)
    gx, gy = 0, GY
    hand = (95, -660)
    armR = reach(1, *hand)
    armk = float(np.clip((lt - 0.85) / 0.75, 0, 1)) if lt > 0 else 0.0
    if armk > 0:                                                       # the free hand goes up to his forehead (over ~0.75 s)
        armL = reach_move(-1, ease(armk), (-40, -820))
    else:
        armL = (12.0, 0.0)
    dy = jolt(lt, 0.9, 25) if lt > 0 else 0.0
    guy(cv, gx, gy + dy, 1.0, face='pain' if pain > 0.3 else 'hold', arms=(armL, armR))
    lvl = 0.85 - 0.12 * float(np.clip((lt + 1.0) / 2.0, 0, 1))
    cup(cv, gx + hand[0], gy + hand[1] + 120 + dy, 1.0, lvl, straw_to=(gx + MOUTH[0], gy + MOUTH[1] + dy), frost=1.0, T=T)
    for k in range(5):                                                 # slush rising up the straw
        u = (T * 2.2 + k / 5) % 1
        dot(cv, gx + 105, gy + dy + 80 - 160 * u - 120, 7, flat(hexc('#7fd0ff')), a=0.9)
    if pain > 0:
        cv.glow(ellipse(gx, gy - 810 + dy, 110, 40), (gx - 220, gy - 880 + dy, gx + 220, gy - 740 + dy), '#ff3a2a', 50, pain * 0.9)
        for k in range(6):                                             # the pain flash lines
            a = -np.pi / 2 + (k - 2.5) * 0.4; r0 = 170 + 40 * np.sin(T * 12 + k)
            line(cv, [(gx + np.cos(a) * r0, gy - 800 + dy + np.sin(a) * r0), (gx + np.cos(a) * (r0 + 70), gy - 800 + dy + np.sin(a) * (r0 + 70))], 10,
                 flat(hexc('#ff5040')), a=pain)


def b0_hook(lt, dur, T):
    cv = Canvas(0, GY - 640, 1.45)
    pain = float(np.clip((lt - 0.9) / 0.3, 0, 1)) if lt > 0 else 0.0
    sx_, sy_ = shake(lt, 0.9, 18, 0.6)
    cv.cx += sx_; cv.cy += sy_
    gulp_scene(cv, lt, T, pain)
    hook_text(cv, 'BRAIN FREEZE', lt, y=-800, size=118, color=BLU, pop_t=-0.25 if lt < 0 else 0.0)
    return cv


def b1_smack(lt, dur, T):
    cv = Canvas(0, 60, 1.2)
    sl = ease(np.clip(lt / 0.5, 0, 1))
    sx_, sy_ = shake(lt, 0.45, 20, 0.4)
    cv.cx += sx_; cv.cy += sy_
    head_xray(cv, T, slush=sl, cold=ease(np.clip((lt - 0.5) / 0.4, 0, 1)))
    slabel(cv, 'ROOF OF MOUTH', 0, -760, 96, BLU, a=ease(np.clip((lt - 0.6) / 0.3, 0, 1)))
    return cv


def b2_vessels(lt, dur, T):
    cv = Canvas(0, 90, 1.7 - 0.15 * ease(np.clip(lt / dur, 0, 1)))
    head_xray(cv, T, slush=0.6, cold=0.5)
    slabel(cv, 'BLOOD VESSELS', 0, -760, 100, (255, 120, 110))
    return cv


def b3_squeeze(lt, dur, T):
    cv = Canvas(0, 100, 1.8)
    k = ease(np.clip(lt / 0.8, 0, 1))
    head_xray(cv, T, ves=1.0 - 0.7 * k, flow=1.0 - 0.8 * k, slush=0.8, cold=0.6 + 0.4 * k)
    for sx in (-1, 1):
        arrows(cv, [((sx * 120, 40 - 60 * (1 - k)), (sx * 120, 85)), ((sx * 120, 170 + 60 * (1 - k)), (sx * 120, 125))], BLU, 10)
    hook_text(cv, 'SQUEEZE!', lt, y=-760, size=140, pop_t=0.2, color=BLU)
    return cv


def b4_rush(lt, dur, T):
    k = ease(np.clip((lt - 0.2) / 0.25, 0, 1))
    sx_, sy_ = shake(lt, 0.25, 26, 0.5)
    cv = Canvas(sx_, 100 + sy_, 1.8)
    head_xray(cv, T, ves=0.3 + 1.6 * k, flow=0.2 + 2.8 * k, slush=0.6, cold=0.4 * (1 - k))
    hook_text(cv, 'RUSH!', lt, y=-760, size=150, pop_t=0.25, color=(255, 90, 80))
    return cv


def b5_nerve(lt, dur, T):
    cv = Canvas(0, 0, 1.2)
    n = ease(np.clip(lt / 0.4, 0, 1))
    head_xray(cv, T, ves=1.6, flow=2.0, nerve=n, slush=0.4)
    slabel(cv, 'BIG FACE NERVE', 0, -760, 100, YEL, a=n)
    return cv


def b6_confused(lt, dur, T):
    cv = Canvas(0, -60, 1.2)
    head_xray(cv, T, ves=1.4, flow=1.6, nerve=1.0, slush=0.3, puzzled=ease(np.clip(lt / 0.4, 0, 1)))
    slabel(cv, 'WHERE IS IT?!', 0, -760, 100, YEL)
    return cv


def b7_blame(lt, dur, T):
    cv = Canvas(0, -20, 1.15)
    f = ease(np.clip((lt - 0.3) / 0.4, 0, 1))
    head_xray(cv, T, ves=1.3, flow=1.4, nerve=1.0, slush=0.5, cold=0.6, fore=f)
    arrows(cv, [((0, -180), (0, -300))], (255, 90, 80), 14)
    slabel(cv, 'PAIN FELT HERE', 0, -760, 96, (255, 100, 90), a=f)
    label(cv, 'COLD HIT HERE', 0, 370, 64, BLU, a=ease(np.clip((lt - 1.2) / 0.3, 0, 1)))
    return cv


def b8_name(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#13284a', '#081428', vignette=0.4)
    for k in range(16):                                                # snowflakes drifting
        x = -480 + (k * 137) % 960; y = -900 + ((T * 120 + k * 211) % 1700)
        dot(cv, x, y, 6 + k % 3 * 3, flat(hexc('#e8f8ff')), a=0.6)
    words = ['SPHENO-', 'PALATINE', 'GANGLIO-', 'NEURALGIA']
    for i, w in enumerate(words):
        k = ease(np.clip((lt - 0.15 - i * 0.35) / 0.2, 0, 1))
        if k > 0:
            label(cv, w, 0, -360 + i * 150, 120 * (0.7 + 0.3 * k), YEL if i % 2 == 0 else BLU, a=k)
    slabel(cv, 'THE REAL NAME', 0, -760, 84, WHT)
    return cv


def b9_fix(lt, dur, T):
    half = dur * 0.5
    if lt < half:
        cv = Canvas(0, 160, 1.5)
        k = ease(np.clip(lt / 0.5, 0, 1))
        head_xray(cv, T, ves=1.2 - 0.2 * k, flow=1.2, tongue=k, warm=0.7 * k, fore=0.6 * (1 - k))
        arrows(cv, [((0, 400), (0, 300))], (255, 160, 170), 14)
        slabel(cv, 'TONGUE UP', 0, -760, 110, (255, 160, 170))
        return cv
    cv = Canvas(0, GY - 600, 1.35)
    kitchen(cv)
    u = lt - half
    guy(cv, 0, GY, 1.0, face='calm', arms=(reach(-1, -30, -660), reach(1, 30, -660)))
    box(cv, 0, GY - 600, 70, 70, ramp('#e8a060', '#b06a30', '#ffc890'), r=16)        # the warm mug
    for k in range(3):                                                 # steam
        ph = (u * 0.8 + k / 3) % 1
        line(cv, [(-30 + k * 30 + 10 * np.sin(ph * 6 + k), GY - 690 - ph * 160), (-30 + k * 30 + 10 * np.sin(ph * 6 + k + 1), GY - 720 - ph * 160)], 10,
             flat(hexc('#ffffff')), a=1 - ph)
    slabel(cv, 'SIP SOMETHING WARM', 0, -760, 74, (255, 190, 120))
    return cv


def b10_fade(lt, dur, T):
    cv = Canvas(0, GY - 640, 1.45)
    kitchen(cv)
    k = np.clip(lt / dur, 0, 1)
    face = 'pain' if k < 0.35 else ('worried' if k < 0.7 else 'happy')
    guy(cv, 0, GY, 1.0, face=face, arms=(reach_move(-1, 1 - ease(np.clip(k * 1.6, 0, 1)), (-40, -820)), reach(1, 95, -660)))
    cup(cv, 95, GY - 540, 1.0, 0.7, frost=1.0, T=T)
    sec = max(1, 3 - int(k * 3))
    sbadge(cv, f'{sec}...' if k < 0.85 else 'GONE!', -760, GRN if k >= 0.85 else YEL)
    return cv


BEATS = [b0_hook, b1_smack, b2_vessels, b3_squeeze, b4_rush, b5_nerve, b6_confused, b7_blame, b8_name, b9_fix, b10_fade]

if __name__ == '__main__':
    run(BEATS)
