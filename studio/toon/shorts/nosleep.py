#!/usr/bin/env python3
"""What happens if you never sleep. Opens on him jolting wide awake at his desk, eyes red and twitching; loops back into it
(the last line plays over him nodding off, right before the jolt)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body2 import *          # noqa: F401,F403

DESK = ramp('#a8693a', '#6e4122', '#d08f58')
MUG = ramp('#ffffff', '#d8dde4', '#ffffff')
CAN = ramp('#3fbf6a', '#25804a', '#7fe8a0')
BAGS = flat(hexc('#7a4a8a'))
VEIN = flat(hexc('#e2302a'))
BLOB = ramp('#b07aff', '#7a4ad0', '#d8c0ff')
SEPIA = ('#e8d8b0', '#c8b088')
GX, GY, GS = 0, 900, 1.4


def tired_eyes(cv, x, y, s, veins=1.0, bags=1.0):
    """Dark bags under wide eyes, red veins in the whites (for face='shock')."""
    for sx in (-1, 1):
        ex, ey = x + sx * 36 * s, y - 772 * s
        cv.shape(subtract(ellipse(ex, ey + 34 * s, 30 * s, 13 * s), ellipse(ex, ey + 26 * s, 32 * s, 12 * s)),
                 (ex - 34 * s, ey + 14 * s, ex + 34 * s, ey + 50 * s), BAGS, ow=0, shadow=0, flat=True, alpha=0.75 * bags)
        if veins > 0:
            for a in (0.4, 2.6, 3.6, 5.6):
                line(cv, [(ex + np.cos(a) * 22 * s, ey + np.sin(a) * 22 * s), (ex + np.cos(a + 0.25) * 12 * s, ey + np.sin(a + 0.25) * 12 * s)],
                     2.2 * s, VEIN, a=veins)


def room(cv, T, day, night=True):
    """His room at night: window, a fast-spinning clock, a LIKE & SUBSCRIBE poster and the day calendar."""
    cv.background('#3a3458', '#22203a', vignette=0.3)
    box(cv, -370, -610, 120, 150, WOOD, r=8)
    box(cv, -370, -610, 104, 134, ramp('#0e1838', '#0a1028', '#1a2a5a') if night else ramp('#7fc0f0'), r=4, ow=0, shadow=0)
    if night:
        moon(cv, -340, -650, 40)
    else:
        sun(cv, -340, -650, 40, T)
    line(cv, [(-370, -744), (-370, -476)], 8, WOOD, ow=0); line(cv, [(-474, -610), (-266, -610)], 8, WOOD, ow=0)
    wall_clock(cv, 370, -620, 85, T * 2.0, T * 24.0)
    sub_poster(cv, -400, -280, 0.8, T=T)
    box(cv, 400, -290, 105, 120, ramp('#ffffff', '#d8dde4', '#ffffff'), r=8)
    box(cv, 400, -385, 105, 26, ramp('#e2302a'), r=6, shadow=0)
    label(cv, 'DAY', 400, -378, 30, (255, 255, 255), stroke=0)
    label(cv, str(day), 400, -260, 110, (40, 34, 50), stroke=0)
    label(cv, 'TO DO: SUBSCRIBE', 400, -195, 18, (200, 40, 40), stroke=0)


def desk_guy(cv, T, face='shock', jx=0.0, jy=0.0, tilt=0.0, veins=1.0, look=(0, 0), alpha_copies=0):
    left = reach(-1, -110, (225 - GY) / GS)
    right = reach(1, 160, (180 - GY) / GS)
    guy(cv, GX + jx, GY + jy, GS, face=face, arms=(left, right), tilt_head=tilt, look=look)
    if face == 'shock':
        tired_eyes(cv, GX + jx + tilt * 30 * GS, GY + jy, GS, veins=veins)


def desk(cv, T, steam=1.0):
    box(cv, 0, 600, 700, 370, DESK, r=10)
    line(cv, [(-560, 250), (560, 250)], 6, flat(hexc('#d08f58')), a=0.7)
    for sx in (-1, 1):                                                         # drawers, with stickers on them (Easter eggs)
        box(cv, sx * 290, 640, 200, 120, ramp('#9a5e32', '#6e4122', '#c08050'), r=10, shadow=0)
        box(cv, sx * 290, 560, 50, 10, STEEL, r=5, shadow=0)
    thumb_icon(cv, -290, 660, 44)
    sticky(cv, 290, 670, 0.9, ["DON'T", 'FORGET TO', 'SUBSCRIBE'])
    box(cv, 250, 175, 46, 56, MUG, r=10)                                     # his mug, with a little SUB label
    cv.shape(subtract(circle(305, 170, 28), circle(305, 170, 15)), (275, 140, 335, 200), MUG, ow=3, shadow=0)
    box(cv, 250, 180, 34, 16, SUBRED, r=4, ow=0, shadow=0)
    label(cv, 'LIKE+SUB', 250, 186, 15, (255, 255, 255), stroke=0)
    for q in range(2):
        ph = (T * 0.7 + q / 2) % 1
        cloud(cv, 245 + 20 * np.sin(T * 2 + q), 100 - 90 * ph, 18 + 14 * ph, a=0.6 * (1 - ph) * steam)
    for i, x in enumerate((-330, -280, -385)):                                 # empty energy drink cans
        box(cv, x, 190 - (i == 2) * 0, 22, 44, CAN, r=6)
        line(cv, [(x - 16, 180), (x + 16, 180)], 4, flat(hexc('#ffffff')), a=0.8)
    sub_phone(cv, -150, 195, 0.45, T)


# ---------------------------------------------------------------- beats

def b0_hook(lt, dur, T):
    """lt < 0: he's nodding off at the desk. At lt = -0.25 he jolts awake; frame one is wide eyes, shaking."""
    cv = Canvas(0, 0, 1.0)
    room(cv, T, 1)
    awake = lt > -0.25
    if not awake:
        k = ease(float(np.clip((lt + 2.6) / 2.2, 0, 1)))
        desk_guy(cv, T, face='closed', jy=30 * k, tilt=-0.35 * k)
    else:
        jx, jy = shake(lt, -0.25, amt=18, dur=2.5, freq=38)
        desk_guy(cv, T, face='shock', jx=jx, jy=jy, look=(0.4 * np.sin(T * 9), 0))
    desk(cv, T)
    if awake:
        hook_text(cv, 'NO SLEEP!', lt + 0.25, y=-790, size=160, color=(255, 236, 80))
    return cv


def b1_brain(lt, dur, T):
    """Inside his head: the front of the brain dims, the THINKING meter drains."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1030', '#0a0618', vignette=0.35)
    k = ease(float(np.clip((lt - 0.4) / (dur * 0.7), 0, 1)))
    brain(cv, 0, -220, 1.3)
    cv.shape(smooth(40, circle(-150, -250, 150), circle(-200, -150, 120)), (-360, -420, 20, -10), ramp('#1a1030'), ow=0, shadow=0, flat=True, alpha=0.6 * k)
    label(cv, 'FRONT', -230, -480, 52, (255, 200, 210))
    meter(cv, 0, 120, 520, 1 - 0.75 * k, YELLOW if k < 0.5 else ramp('#e2483d'), 'THINKING')
    badge(cv, 'DAY 1', y=-720, col=(127, 210, 255), w=260)
    neon_sign(cv, 0, 720, 'SUBSCRIBE', '#ff3a6a', T)
    return cv


def b2_seeing(lt, dur, T):
    """Day two: purple blobs that aren't there drift round the room. Even the poster's thumb starts waving."""
    cv = Canvas(0, 0, 1.0)
    room(cv, T, 2, night=False)
    desk_guy(cv, T, face='shock', look=(np.sin(T * 1.7), -0.5 + 0.5 * np.cos(T * 1.3)), veins=1.0)
    desk(cv, T, steam=0.4)
    k = float(np.clip(lt / 0.8, 0, 1))
    for q in range(4):                                                         # things that aren't there
        bx = 330 * np.sin(T * 0.6 + q * 1.7); by = -520 + 160 * np.cos(T * 0.8 + q * 2.3)
        cv.shape(smooth(20, circle(bx, by, 52), circle(bx + 30 * np.sin(T * 3 + q), by + 40, 30)), (bx - 70, by - 70, bx + 90, by + 110), BLOB, alpha=0.65 * k)
        for ex in (-16, 16):
            disc(cv, bx + ex, by - 8, 9, ramp('#ffffff'), ow=2, shadow=0, alpha=k)
            dot(cv, bx + ex, by - 6, 4, a=k)
    thumb_icon(cv, -400, -320 + 10 * np.sin(T * 8), 44)                       # the poster thumb waving at him
    return cv


def b3_micro(lt, dur, T):
    """Close on his face: eyes drop shut for a split second, the screen blinks dark, then snap open."""
    cv = Canvas(0, -170, 2.0)
    room(cv, T, 3)
    ph = (lt % 1.3) / 1.3
    shut = 0.35 < ph < 0.65
    desk_guy(cv, T, face='closed' if shut else 'shock', jy=14 * shut, tilt=-0.15 * shut)
    desk(cv, T, 0.2)
    if shut:
        cv.flash('#000000', 0.55)
        label(cv, 'ZZZ', 120, -360, 40, (220, 230, 255))
    badge(cv, 'DAY 3', y=-500, col=(127, 210, 255), w=150)
    return cv


def b4_thirty(lt, dur, T):
    """A blackout timer counting up to 30 seconds while his head nods."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#0a0a14', '#000000', vignette=0.4)
    k = float(np.clip(lt / (dur * 0.8), 0, 1))
    secs = 1 + int(29 * k)
    disc(cv, 0, -250, 230, ramp('#ffffff', '#d8dde4', '#ffffff'))
    for t in range(12):
        a = t * np.pi / 6
        line(cv, [(np.sin(a) * 185, -250 - np.cos(a) * 185), (np.sin(a) * 210, -250 - np.cos(a) * 210)], 6, flat(hexc('#3a3a4a')))
    a = 2 * np.pi * secs / 60
    line(cv, [(0, -250), (np.sin(a) * 170, -250 - np.cos(a) * 170)], 12, flat(hexc('#e2302a')))
    dot(cv, 0, -250, 14)
    badge(cv, f'{secs} SEC', y=90, col=(255, 236, 80), w=300)
    if k > 0.97:
        hook_text(cv, '30 SECONDS', lt, y=-760, size=130, pop_t=dur * 0.78, color=(255, 236, 80))
    neon_sign(cv, 0, 720, 'HIT LIKE', '#3fa9ff', T)
    return cv


def b5_unreal(lt, dur, T):
    """Day four: three of him, half see-through, and the whole room wobbles like it's melting."""
    import cv2
    cv = Canvas(0, 0, 1.0)
    room(cv, T, 4)
    k = float(np.clip(lt / 0.8, 0, 1))
    desk_guy(cv, T, face='shock', jx=50 * np.sin(T * 1.5) * k, look=(np.sin(T * 2), 0))
    desk(cv, T, 0.3)
    w = 14 * k
    if w > 0.5:
        H_, W_ = cv.img.shape[:2]
        yy, xx = np.mgrid[0:H_, 0:W_].astype(np.float32)
        mx = xx + w * np.sin(yy / 60 + T * 4)
        my = yy + w * 0.6 * np.sin(xx / 80 + T * 3)
        cv.img = np.ascontiguousarray(cv2.remap(cv.img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
    hook_text(cv, "WHAT'S REAL?", lt, y=-790, size=130, pop_t=dur * 0.4, color=(200, 150, 255))
    return cv


def b6_fair(lt, dur, T):
    """1963: a science fair table, a tri-fold poster board, a tired teen beside it."""
    cv = Canvas(0, 0, 1.0)
    cv.background(*SEPIA, vignette=0.3)
    box(cv, 0, -300, 330, 230, ramp('#ffffff', '#e0dccb', '#ffffff'), r=10)     # middle panel
    for sx in (-1, 1):
        cv.shape(poly([(sx * 330, -530), (sx * 520, -490), (sx * 520, -110), (sx * 330, -70)]), (min(sx * 330, sx * 520) - 4, -534, max(sx * 330, sx * 520) + 4, -66),
                 ramp('#f4f0e4', '#d8d0bc', '#ffffff'), ow=4)
    label(cv, 'HOW LONG CAN', 0, -440, 48, (40, 34, 50), stroke=0)
    label(cv, 'YOU STAY', 0, -380, 48, (40, 34, 50), stroke=0)
    label(cv, 'AWAKE?', 0, -300, 84, (200, 40, 40), stroke=0)
    wall_clock(cv, 0, -160, 50, T * 0.5, T * 6)
    sub_button(cv, 425, -330, 150, size=22)                                    # an Easter egg pinned to the side panel
    thumb_icon(cv, -425, -330, 44)
    guy(cv, -250, 820, 1.0, face='shock', arms=((14, 0), (60, 60)))
    tired_eyes(cv, -250, 820, 1.0, veins=0.8)
    box(cv, 120, 330, 420, 40, ramp('#3d7fd8', '#2a559a', '#7fb4ff'), r=8)       # the table
    box(cv, 120, 560, 380, 220, ramp('#3d7fd8', '#2a559a', '#7fb4ff'), r=8, alpha=0.95)
    badge(cv, '1963', y=-720, col=(255, 236, 80), w=260)
    cv.flash('#c8a878', 0.12)
    return cv


def b7_days(lt, dur, T):
    """The count: hours run up to 264 and the calendar flips to day 11."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1c1838', '#0c0a1c', vignette=0.35)
    k = ease(float(np.clip(lt / (dur * 0.55), 0, 1)))
    hours = int(round(264 * k))
    day = 1 + min(10, int(hours / 24))
    box(cv, 0, -230, 260, 300, ramp('#ffffff', '#d8dde4', '#ffffff'), r=20)
    box(cv, 0, -470, 260, 60, ramp('#e2302a'), r=14, shadow=0)
    label(cv, 'DAY', 0, -455, 64, (255, 255, 255), stroke=0)
    label(cv, str(day if k < 1 else 11), 0, -170, 300, (40, 34, 50), stroke=0)
    label(cv, 'TO DO: SUBSCRIBE', 0, 20, 34, (200, 40, 40), stroke=0)
    badge(cv, f'{hours} HOURS', y=200, col=(255, 236, 80), w=420)
    if k >= 1:
        hook_text(cv, '11 DAYS', lt, y=-780, size=170, pop_t=dur * 0.6, color=(255, 236, 80))
    return cv


def b8_sleep(lt, dur, T):
    """He finally sleeps. Moon to sun, and he's back to normal."""
    cv = Canvas(0, 0, 1.0)
    k = float(np.clip(lt / (dur * 0.8), 0, 1))
    cv.background('#1c2a4a' if k < 0.6 else '#6fa8dc', '#0e1630' if k < 0.6 else '#bfe0ff', vignette=0.3)
    box(cv, 0, 100, 700, 860, ramp('#b07a48', '#8a5a30', '#d09a68'), r=0, ow=0, shadow=0)
    box(cv, -400, -520, 95, 95, WOOD, r=10)
    sub_phone(cv, -400, -520, 0.75, T)
    bed(cv, T, 60, -110, 0.72, face='snore', blanket=True)
    label(cv, 'LIKE  &  SUBSCRIBE', 60, -440, 26, (120, 150, 200), a=0.8, stroke=0)
    for q in range(3):
        ph = (T * 0.5 + q / 3) % 1
        label(cv, 'Z', 220 + 50 * ph, -380 - 200 * ph, int(50 + 40 * ph), (220, 230, 255), a=1 - ph)
    doormat(cv, 60, 760, 0.9)
    if k > 0.6:
        badge(cv, 'BACK TO NORMAL', y=-720, col=(127, 255, 160), w=620)
    return cv


# the cut that goes INSIDE him: into his head to the brain (screen px)
DIVE = {1: (540, 793)}

BEATS = [b0_hook, b1_brain, b2_seeing, b3_micro, b4_thirty, b5_unreal, b6_fair, b7_days, b8_sleep]

if __name__ == '__main__':
    run(BEATS)
