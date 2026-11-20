#!/usr/bin/env python3
"""GTA 6 launch day (Nov 19 2026). No Rockstar art anywhere: no logo, characters, box art or game scenes; just the world
around the launch, drawn our own way (a generic console, TV, sunset palms, a store line).
Opens on the midnight crowd stampeding into the store; the 13-year wait (2013 -> 2026) and GTA 5's 200M+ copies; the trailer's
90M views in a day; two delays crossed off the calendar; the New Zealand midnight trick; the 200GB+ download breaking an
internet company's record twice; 17M+ copies and ~6M live viewers; 99/100 tying the best-reviewed game ever; the payoff:
an Army unit's four days off to play, if soldiers re-enlist for at least two more years, and some did.
Facts: Kotaku launch live (Nov 19 2026: midnight local launch, Metacritic 99 tying Ocarina of Time, 17M+ copies, ~5.8M live
viewers across Twitch/YouTube/Kick). Engadget live (212GB, Virgin Media download records during preload and launch; the NZ
store/region trick; 13 years since GTA 5). Rockstar Newswire and TechRadar (delayed twice: to May 26 2026, then Nov 19 2026).
PC Gamer (Army: 9th Brigade Engineer Battalion, 4-day pass for soldiers who re-enlist 2-6 years; 20 of 130 eligible took it).
PushSquare/TechRaptor (first trailer: 90M views in 24 hours, YouTube record). GTA 5: 200M+ copies (Take-Two)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from body import *          # noqa: F401,F403
import eas as E

DIVE = {}
NEON_P = (255, 90, 200)
NEON_B = (90, 220, 255)
CONSOLE = ramp('#f4f6fa', '#c8ccd4', '#ffffff')
ARMY = ramp('#6a7a4a', '#4a5a2a', '#8a9a6a')
GOLD = ramp('#ffd23f', '#d09a10', '#fff08a')
PAPER = ramp('#f4f1ea', '#d8d0c0', '#ffffff')


def W2(cv, sx, sy):
    return cv.cx + sx / cv.zoom, cv.cy + sy / cv.zoom


def slabel(cv, txt, sx, sy, size, col, a=1.0):
    x, y = W2(cv, sx, sy); label(cv, txt, x, y, size / cv.zoom, col, a=a)


def sbadge(cv, txt, sy, col):
    x, y = W2(cv, 0, sy); badge(cv, txt, y=y, col=col, x=x)


def sunset(cv):
    """generic neon sunset with palm silhouettes (our own; no game art)"""
    cv.background('#ff7ab0', '#2a1050', vignette=0.3)
    cv.glow(circle(0, -200, 220), (-600, -700, 600, 300), '#ffb050', 160, 0.7)
    disc(cv, 0, -200, 200, ramp('#ffd060', '#ff8a40', '#fff0a0'), ow=0, shadow=0)
    for j in range(5):
        box(cv, 0, -200 + 60 + j * 34, 220, 6 + j * 2, ramp('#ff7ab0'), r=0, ow=0, shadow=0)
    for px, h, lean in ((-420, 760, -0.1), (430, 820, 0.12), (-300, 560, 0.05)):
        P = ramp('#1a0a2a')
        line(cv, [(px, 960), (px + lean * h, 960 - h)], 26, P, ow=0)
        for k in range(6):
            a = np.pi * (0.1 + 0.8 * k / 5)
            tx, ty = px + lean * h, 960 - h
            line(cv, [(tx, ty), (tx + 170 * np.cos(a + np.pi), ty - 40 + 100 * np.sin(a) * 0.5 + 60)], 16, P, ow=0)


def console(cv, x, y, s, glow=0.0, T=0.0):
    cv.shape(rbox(x, y, 70 * s, 220 * s, 30 * s), (x - 90 * s, y - 240 * s, x + 90 * s, y + 240 * s), CONSOLE, ow=4)
    box(cv, x, y, 18 * s, 200 * s, ramp('#1a1e26'), r=8 * s, ow=0, shadow=0)
    if glow > 0:
        cv.glow(rbox(x, y, 18 * s, 200 * s, 8 * s), (x - 200 * s, y - 400 * s, x + 200 * s, y + 400 * s), '#5ab8ff', 60 * s, glow * (0.7 + 0.3 * np.sin(T * 4)))


def tv_game(cv, x, y, s, T, k=1.0):
    """a TV showing our own neon sunset title card"""
    box(cv, x, y + 300 * s, 30 * s, 60 * s, ramp('#2b2f38'), r=6 * s)
    box(cv, x, y, 420 * s, 260 * s, ramp('#2b2f38', '#191c22', '#454b57'), r=26 * s, ow=5)
    box(cv, x, y, 390 * s, 230 * s, ramp('#ff7ab0', '#2a1050', '#ffa0d0'), r=10 * s, ow=0, shadow=0)
    disc(cv, x, y - 20 * s, 110 * s, ramp('#ffd060', '#ff8a40', '#fff0a0'), ow=0, shadow=0)
    label(cv, 'GTA 6', x, y + 40 * s, 150 * s, (255, 255, 255), stroke=12)
    cv.glow(rbox(x, y, 390 * s, 230 * s, 10 * s), (x - 600 * s, y - 500 * s, x + 600 * s, y + 500 * s), '#ff7ab0', 120 * s, 0.45 * k)


def person_run(cv, x, y, s, T, col, ph=0.0):
    """a quick little runner (fan in the crowd)"""
    b = np.sin(T * 12 + ph)
    C = ramp(col)
    disc(cv, x, y - 150 * s + 6 * b * s, 34 * s, SKIN, ow=3)
    cv.shape(rbox(x, y - 70 * s, 40 * s, 52 * s, 20 * s), (x - 50 * s, y - 130 * s, x + 50 * s, y - 10 * s), C, ow=3)
    for sd in (-1, 1):
        line(cv, [(x, y - 20 * s), (x + sd * 30 * s * b, y + 40 * s)], 14 * s, ramp('#2a3a6a'), ow=2)
        line(cv, [(x, y - 100 * s), (x + 40 * s, y - 130 * s - sd * 30 * s * b)], 12 * s, C, ow=2)


def calendar(cv, x, y, s, top, big, col=(30, 30, 40)):
    box(cv, x, y, 220 * s, 250 * s, PAPER, r=20 * s, ow=5)
    box(cv, x, y - 190 * s, 220 * s, 60 * s, ramp('#e2483d', '#a82a26', '#ff8070'), r=20 * s, ow=0, shadow=0)
    label(cv, top, x, y - 190 * s, 60 * s, WHT, stroke=0)
    label(cv, big, x, y + 40 * s, 170 * s, col, stroke=0)


def soldier(cv, x, y, s, face='calm', arms=None, controller=False, T=0.0):
    guy(cv, x, y, s, face=face, arms=arms or (reach(-1, -160, -560), reach(1, 160, -560)))
    hy = y - 820 * s                                                          # an army helmet on top
    cv.shape(ellipse(x, hy, 150 * s, 100 * s), (x - 170 * s, hy - 120 * s, x + 170 * s, hy + 20 * s), ARMY, ow=5)
    box(cv, x, hy + 10 * s, 160 * s, 14 * s, ARMY, r=6 * s)


# ---------------------------------------------------------------- beats
def b0_midnight(lt, dur, T):
    """Frame one: the store doors fly open at midnight and the crowd is already charging in."""
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1040', '#05030e', vignette=0.4)
    box(cv, 0, -100, 520, 520, ramp('#2a2f40', '#161a24', '#3a4256'), r=0, ow=5)            # the storefront
    on = ((lt + 5.3) * 3) % 1 < 0.7                                            # tied to the beat clock: the loop seam stays clean
    label(cv, 'GAME STORE', 0, -540, 110, NEON_B if on else (60, 90, 110), stroke=10)
    cv.glow(rbox(0, -540, 400, 70, 20), (-700, -800, 700, -300), '#5ad8ff', 80, 0.5 if on else 0.15)
    k = float(np.clip((lt + 0.5) / 0.6, 0, 1))
    dw = 200 * ease(k)
    box(cv, -dw - 100, 140, 100, 260, ramp('#9ad0ff', '#5a9ae0', '#d0ecff'), r=6, ow=4, alpha=0.6)   # sliding doors
    box(cv, dw + 100, 140, 100, 260, ramp('#9ad0ff', '#5a9ae0', '#d0ecff'), r=6, ow=4, alpha=0.6)
    cv.glow(rbox(0, 140, 200 * k, 260, 6), (-500, -200, 500, 500), '#fff4c0', 120, 0.6 * k)
    box(cv, 0, 760, 1400, 360, ramp('#3a3f48', '#22262c', '#555b66'), r=0, ow=0, shadow=0)
    cols = ['#e2483d', '#5a9ae0', '#5aff8a', '#ffd23f', '#ff7ab0', '#9a6ad8', '#ff9a40']
    for j in range(14):                                                      # the crowd rushing in
        ph = j * 0.7
        u = ((lt + 0.8) * 0.45 + j / 14 + 0.035) % 1                         # phase keeps every wrap away from the loop seam
        x = (-560 + j * 80) * (1 - u) + (-40 + (j % 5) * 20) * u
        y = 700 - 380 * u + 700 * max(0.0, 0.15 - u) / 0.15               # new runners charge in from below the frame
        if u < 0.9:
            person_run(cv, x, y, 1.6 - 0.8 * u, lt + 5, cols[j % 7], ph)
    tclock = '12:00' if lt > -0.2 else '11:59'
    box(cv, 0, -780, 230, 90, ramp('#0a0a12'), r=20, ow=5)
    label(cv, tclock, 0, -780, 110, (255, 80, 60), stroke=0)
    return cv


def b1_wait(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#2a1a4a', '#100a20', vignette=0.4)
    k = ease(np.clip(lt / (dur * 0.6), 0, 1))
    yr = 2013 + int(13 * k)
    for j in range(6):                                                       # pages flying off
        u = (T * 1.2 + j / 6) % 1
        if k < 1:
            box(cv, 140 + 600 * u, -480 - 300 * u + 200 * u * u, 120, 140, PAPER, r=14, ow=3, alpha=1 - u)
    calendar(cv, 0, -480, 1.2, 'YEAR', str(yr))
    slabel(cv, '%d YEARS' % (yr - 2013), 0, -120, 120, (255, 210, 80))
    m = int(200 * ease(np.clip((lt - dur * 0.45) / (dur * 0.45), 0, 1)))
    for j in range(min(m // 20, 10)):                                         # stacks of copies
        box(cv, -360 + j * 80, 520, 32, 50, ramp('#5a9ae0', '#2a5aa0', '#9ad0ff'), r=6, ow=3)
    if m > 0:
        slabel(cv, '%dM+ COPIES' % m, 0, 700, 100, (154, 208, 255))
    return cv


def b2_trailer(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a1a24', '#06060a', vignette=0.4)
    box(cv, 0, -280, 460, 300, ramp('#101218'), r=30, ow=6)                  # a video player
    k = float(np.clip(lt / 0.5, 0, 1))
    pts = [(-60, -380), (-60, -180), (110, -280)]
    cv.shape(poly(pts), pbox(pts, 6), ramp('#ffffff'), ow=0, shadow=0, alpha=1 - k)
    if k > 0:
        box(cv, 0, -280, 430, 270, ramp('#ff7ab0', '#2a1050', '#ffa0d0'), r=14, ow=0, shadow=0, alpha=k)
        disc(cv, 0, -300, 120, ramp('#ffd060', '#ff8a40', '#fff0a0'), ow=0, shadow=0, alpha=k)
    box(cv, 0, 40, 460, 10, ramp('#3a3f48'), r=5, ow=0, shadow=0)
    box(cv, -460 + 460 * k, 40, 460 * k + 1, 10, ramp('#e2483d'), r=5, ow=0, shadow=0)
    v = int(90000000 * ease(np.clip((lt - 0.2) / (dur * 0.65), 0, 1)))
    slabel(cv, format(v, ','), 0, 110, 120, (255, 236, 80))
    slabel(cv, 'VIEWS IN 1 DAY', 0, 210, 70, WHT)
    sbadge(cv, 'YOUTUBE RECORD', -780, (255, 90, 80))
    return cv


def b3_delay(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#3a1a1a', '#120606', vignette=0.4)
    dates = [('FALL', '2025', -540), ('MAY', '2026', -170), ('NOV', '2026', 200)]
    for i, (m, yy, y) in enumerate(dates):
        calendar(cv, 0, y, 0.75, m, yy)
        x_k = float(np.clip((lt - (0.4 + i * dur * 0.3)) / 0.2, 0, 1))
        if i < 2 and x_k > 0:
            for sd in (-1, 1):
                line(cv, [(-150, y - 150), (-150 + 300 * x_k, y - 150 + 300 * x_k * 1.0)] if sd < 0 else [(150, y - 150), (150 - 300 * x_k, y - 150 + 300 * x_k)], 22, ramp('#e2483d'), ow=3)
        if i == 2 and lt > dur * 0.8:
            pts = [(170 * np.cos(t), y + 30 + 200 * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 30)]
            line(cv, pts, 12, ramp('#5aff8a'), ow=2)
    hook_text(cv, 'DELAYED x2', lt, y=-800, size=130, color=(255, 90, 80), pop_t=dur * 0.45)
    return cv


def b4_zealand(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#0a1a3a', '#030812', vignette=0.4)
    earth_r = 330
    E_x, E_y = 0, -260
    cv.glow(circle(E_x, E_y, earth_r), (E_x - 600, E_y - 600, E_x + 600, E_y + 600), '#5ab8ff', 80, 0.5)
    disc(cv, E_x, E_y, earth_r, ramp('#2a6ad8', '#123a8a', '#6ab0ff'), ow=4)
    # rough land: Australia and New Zealand on the lower right (our own simple blobs)
    cv.shape(ellipse(E_x + 80, E_y + 100, 120, 80), (E_x - 60, E_y, E_x + 220, E_y + 200), ramp('#c8a060', '#9a7a40', '#e8c890'), ow=3)
    nz = [(E_x + 260, E_y + 80), (E_x + 290, E_y + 120), (E_x + 250, E_y + 210), (E_x + 225, E_y + 190)]
    k = (T * 3) % 1 < 0.6
    cv.shape(poly(nz), pbox(nz, 6), ramp('#5aff8a' if k else '#2a8a4a'), ow=3)
    cv.glow(circle(E_x + 260, E_y + 150, 40), (E_x + 100, E_y, E_x + 420, E_y + 300), '#5aff8a', 40, 0.7)
    label(cv, 'NEW ZEALAND', E_x + 120, E_y + 290, 54, (90, 255, 140))
    box(cv, 0, 260, 200, 70, ramp('#0a0a12'), r=20, ow=5)
    label(cv, '12:00', 0, 260, 90, (90, 255, 140), stroke=0)
    console(cv, -300, 560, 0.75, glow=1.0, T=T)
    sbadge(cv, 'PLAY HOURS EARLY', -780, (90, 255, 140))
    return cv


def b5_download(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a2a4a', '#0a1020', vignette=0.4)
    k = ease(np.clip(lt / (dur * 0.8), 0, 1))
    box(cv, 0, -300, 440, 60, ramp('#1a1e26'), r=30, ow=5)
    if k > 0.02:
        box(cv, -440 + 440 * k, -300, 440 * k, 52, ramp('#5aff8a', '#2a9a4a', '#a0ffc0'), r=26, ow=0, shadow=0)
    gb = int(212 * k)
    slabel(cv, '%d GB' % gb, 0, -480, 140, WHT)
    box(cv, 0, 150, 240, 80, ramp('#2b2f38', '#191c22', '#454b57'), r=24, ow=5)   # the home router, working hard
    for sd in (-1, 1):
        line(cv, [(sd * 170, 90), (sd * 220, -120)], 14, ramp('#2b2f38'), ow=3)
    for j in range(6):
        on = ((T * 14 + j * 0.37) % 1) < 0.5
        disc(cv, -150 + j * 60, 180, 12, ramp('#5aff8a') if on else ramp('#204a30'), ow=2)
    for j in range(5):                                                        # it's smoking
        u = (T * 0.7 + j / 5) % 1
        disc(cv, 120 + 40 * np.sin(j + T), 60 - 300 * u, 30 + 50 * u, ramp('#8a8a90', '#5a5a60', '#b0b0b8'), ow=0, shadow=0, alpha=0.6 * (1 - u) * k)
    slabel(cv, 'RECORD x2', 0, 640, 110, (255, 120, 90), a=float(np.clip((lt - dur * 0.6) / 0.3, 0, 1)))
    return cv


def b6_sales(lt, dur, T):
    cv = Canvas(0, 0, 1.0)
    cv.background('#1a3a2a', '#06120a', vignette=0.4)
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    rr = np.random.default_rng(6)
    for j in range(int(30 * k)):                                              # game boxes piling up
        x = rr.uniform(-420, 420); y = -100 - rr.uniform(0, 500) * (j / 30)
        box(cv, x, y, 50, 66, ramp('#ff7ab0', '#c84a80', '#ffa0d0'), r=6, ow=3)
        box(cv, x, y - 20, 40, 14, ramp('#ffd060'), r=3, ow=0, shadow=0)
    slabel(cv, '%sM COPIES' % format(int(17 * k), ','), 0, -760, 120, (255, 236, 80))
    k2 = ease(np.clip((lt - dur * 0.5) / (dur * 0.4), 0, 1))
    if k2 > 0:
        for j in range(12):                                                   # eyes watching live
            x = -440 + (j % 6) * 176; y = 560 + (j // 6) * 120
            cv.shape(ellipse(x, y, 60, 32), (x - 70, y - 40, x + 70, y + 40), WHITE, ow=3, alpha=k2)
            disc(cv, x + 10 * np.sin(T * 2 + j), y, 18, INKC, ow=0, alpha=k2)
        slabel(cv, format(int(5800000 * k2), ','), 0, -640, 90, (154, 208, 255))
        slabel(cv, 'WATCHING LIVE', 0, -550, 64, (154, 208, 255))
    return cv


def b7_score(lt, dur, T):
    cv = Canvas(0, 0, 1.0 + 0.05 * ease(np.clip(lt / dur, 0, 1)))
    cv.background('#2a2a10', '#0a0a04', vignette=0.45)
    k = ease(np.clip(lt / (dur * 0.5), 0, 1))
    sc = int(99 * k)
    cv.glow(circle(0, -300, 260), (-700, -900, 700, 300), '#ffd23f', 160, 0.5 * k)
    disc(cv, 0, -300, 260, GOLD, ow=6)
    disc(cv, 0, -300, 210, ramp('#2a2a10', '#0a0a04', '#4a4a20'), ow=0, shadow=0)
    label(cv, str(sc), 0, -300, 230, (255, 236, 80), stroke=10)
    label(cv, 'OUT OF 100', 0, 20, 70, WHT)
    k2 = float(np.clip((lt - dur * 0.55) / 0.3, 0, 1))
    if k2 > 0:
        box(cv, 0, 560, 90, 100, GOLD, r=10, ow=5, alpha=k2)                    # a trophy
        cv.shape(ellipse(0, 400, 170, 130), (-190, 260, 190, 540), GOLD, ow=5, alpha=k2)
        slabel(cv, 'TIED BEST EVER', 0, -760, 110, (255, 210, 80), a=k2)
    return cv


def b8_army(lt, dur, T):
    cv = Canvas(0, -100, 1.1)
    cv.background('#3a4a2a', '#141a0a', vignette=0.4)
    box(cv, 0, 760, 1400, 360, ramp('#5a4a3a', '#3a2a1a', '#7a6a5a'), r=0, ow=0, shadow=0)
    soldier(cv, -200, 720, 0.85, face='shock' if lt > dur * 0.5 else 'calm',
            arms=(reach(-1, -160, -560), reach(1, 180, -620)))
    k = ease(np.clip((lt - dur * 0.4) / 0.4, 0, 1))
    px, py = 260, -200 + 200 * (1 - k)
    box(cv, px, py, 200, 130, PAPER, r=16, ow=5, alpha=k)                     # the 4-day pass
    label(cv, '4 DAYS OFF', px, py - 30, 66, (40, 60, 30), stroke=0, a=k)
    label(cv, 'TO PLAY', px, py + 50, 54, (40, 60, 30), stroke=0, a=k)
    sbadge(cv, 'U.S. ARMY', -820, (180, 220, 120))
    return cv


def b9_deal(lt, dur, T):
    cv = Canvas(0, -100, 1.1)
    cv.background('#3a4a2a', '#141a0a', vignette=0.4)
    sign = lt < dur * 0.5
    if sign:
        box(cv, 0, -280, 280, 340, PAPER, r=10, ow=5)                          # the contract
        label(cv, 'RE-ENLIST', 0, -540, 70, (40, 40, 48), stroke=0)
        for j in range(5):
            line(cv, [(-200, -420 + j * 70), (200, -420 + j * 70)], 8, ramp('#b0a890'))
        k = float(np.clip(lt / (dur * 0.4), 0, 1))
        pts = [(-180 + 360 * u, -60 + 30 * np.sin(u * 20)) for u in np.linspace(0, k, 30)]
        if len(pts) > 1:
            line(cv, pts, 8, ramp('#1a3a8a'))
        slabel(cv, '+2 YEARS', 0, 560, 140, (255, 120, 90))
    else:
        tv_game(cv, 0, -420, 0.95, T)
        box(cv, 0, 470, 560, 160, ramp('#7a5ad0', '#4f3a9a', '#a890ff'), r=60)   # couch
        soldier(cv, 0, 720, 0.8, face='happy', arms=(reach(-1, -100, -500), reach(1, 100, -500)))
        hook_text(cv, 'DEAL!', lt, y=-800, size=170, color=(255, 210, 80), pop_t=dur * 0.5)
    return cv


BEATS = [b0_midnight, b1_wait, b2_trailer, b3_delay, b4_zealand, b5_download, b6_sales, b7_score, b8_army, b9_deal]

if __name__ == '__main__':
    run(BEATS)
