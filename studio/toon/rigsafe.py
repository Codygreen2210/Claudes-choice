"""Rig safety: joint limits, no 360-degree spins, no limbs through the body.

Every rule here comes from studio/RIGGING.md (anatomy ranges, FK/IK practice, slerp shortest path, unrolling,
capsule self-collision, critically damped springs).  guy() in common.py runs every arm through `safe_arm`,
so a Short can't put a limb somewhere a body can't go, even if its numbers are wrong.

House 2D rig (front view, guy's own units: feet at y=0, head centre (hx, -762) r=100):
  shoulder (sx*104, -590); upper arm 125 long (r 41); forearm 135 (r 30); hand disc r 34 at hand + 12 down.
  a1 = shoulder angle, 0 = hanging straight down, + = swings out and up (180 = straight up).
  a2 = elbow bend relative to the upper arm (+ = forearm swings further out).
"""
import math
import numpy as np

# ------------------------------------------------------------------ limits (degrees)
# Shoulder: real elevation reaches ~180 (with the shoulder blade; scapulohumeral rhythm), and the arm can come
# across the chest ~40-50 deg (horizontal adduction).  Past these it reads as dislocated or as going through the body.
A1_LIM = (-40.0, 176.0)
# Elbow: flexion ~140-145, so the forearm can never fold back through the upper arm.  In a front view the bend can
# show on either side (it depends on the unseen upper-arm twist), so the limit is symmetric here.
A2_LIM = (-145.0, 145.0)
KNEE = 12.0          # soft zone: motion slows into a limit instead of hitting a wall (no visible "stop" jitter)

SH_X, SH_Y, L1, L2 = 104.0, -590.0, 125.0, 135.0
HEAD_Y, HEAD_R, HAND_R, UPPER_R, FORE_R = -762.0, 100.0, 34.0, 41.0, 30.0


def wrap180(d):
    """Any angle difference folded into (-180, 180]: the short way round."""
    return (np.asarray(d, float) + 180.0) % 360.0 - 180.0


def soft_clamp(x, lo, hi, knee=KNEE):
    """Identity inside [lo+knee, hi-knee]; beyond, eases asymptotically toward the limit (C1-continuous)."""
    x = float(x)
    a, b = lo + knee, hi - knee
    if x > b:
        return b + knee * math.tanh((x - b) / knee)
    if x < a:
        return a - knee * math.tanh((a - x) / knee)
    return x


def lerp_angle(a, b, k):
    """Blend two joint angles the short way round (never a 350-degree swing for a 10-degree change)."""
    return a + float(wrap180(b - a)) * k


def blend_pose(p, q, k):
    """Blend arm poses ((a1, a2), (a1, a2)) joint by joint, short way round."""
    return tuple((lerp_angle(x[0], y[0], k), lerp_angle(x[1], y[1], k)) for x, y in zip(p, q))


def unroll(angles):
    """Make a sampled angle track continuous: each step takes the short way from the last (Euler-filter idea)."""
    a = np.asarray(angles, float).copy()
    for i in range(1, len(a)):
        a[i] = a[i - 1] + float(wrap180(a[i] - a[i - 1]))
    return a


def flail(T, base, amp=22.0, hz=1.6, seed=0):
    """Panic flailing that stays human: bounded swing (|amp| <= 35 deg), slow enough to read (<= 2.5 Hz),
    two incommensurate sines so it never loops mechanically, and never winds up into a full rotation."""
    amp = min(abs(amp), 35.0) * (1 if amp >= 0 else -1)
    hz = min(hz, 2.5)
    ph = seed * 1.618
    v = 0.72 * math.sin(2 * math.pi * hz * T + ph) + 0.28 * math.sin(2 * math.pi * hz * 2.31 * T + 2.1 * ph)
    return base + amp * v


def spring_follow(target, T, halflife=0.08, window=0.8, dt=1 / 240):
    """Overlapping action / follow-through: a critically damped spring chasing target(t), solved exactly
    (Holden's closed form).  Stateless: it re-simulates a short window ending at T, so frames can render in any order."""
    y = 4.0 * 0.69314718056 / (halflife + 1e-5) / 2.0
    t = T - window
    x = float(target(t)); v = 0.0
    while t < T - 1e-9:
        h = min(dt, T - t)
        t += h
        g = float(target(t))
        j0 = x - g; j1 = v + j0 * y
        e = math.exp(-y * h)
        x = e * (j0 + j1 * h) + g
        v = e * (v - j1 * y * h)
    return x


# ------------------------------------------------------------------ the house arm
def arm_points(sx, a1, a2):
    r1 = math.radians(a1); r2 = math.radians(a1 + a2)
    ex, ey = sx * SH_X + sx * math.sin(r1) * L1, SH_Y + math.cos(r1) * L1
    hx, hy = ex + sx * math.sin(r2) * L2, ey + math.cos(r2) * L2
    return (ex, ey), (hx, hy)


def _seg_circle_dist(p, q, c):
    p, q, c = np.asarray(p, float), np.asarray(q, float), np.asarray(c, float)
    d = q - p
    t = float(np.clip(np.dot(c - p, d) / (np.dot(d, d) + 1e-9), 0, 1))
    return float(np.linalg.norm(p + t * d - c))


def safe_arm(sx, a1, a2, hx=0.0):
    """Clamp one arm to human limits and keep it out of the head and off the far side of the body.
    Returns (a1, a2, in_front): in_front=True means the forearm/hand is at the face and must be drawn over the head."""
    a1 = soft_clamp(a1, *A1_LIM)
    a2 = soft_clamp(float(wrap180(a2)), *A2_LIM)
    head = (hx, HEAD_Y)
    # the upper arm may brush the side of the head when raised, but never pass through it
    for _ in range(12):
        el, _hd = arm_points(sx, a1, a2)
        if _seg_circle_dist((sx * SH_X, SH_Y), el, head) >= HEAD_R + UPPER_R * 0.55:
            break
        a1 -= 3.0                                   # lower the arm a little until the sleeve clears the head
    # the hand can reach across the chest, but not past the far shoulder (that reads as going through him)
    for _ in range(16):
        el, hd = arm_points(sx, a1, a2)
        if sx * hd[0] >= -SH_X:
            break
        a2 *= 0.85
    el, hd = arm_points(sx, a1, a2)
    hand = (hd[0], hd[1] + 12)
    # in front only when the hand is at the face (forehead and below); hands up above the head stay behind it,
    # so a flailing arm never flips draw order at the top of its swing
    touching = math.hypot(hand[0] - hx, hand[1] - HEAD_Y) < HEAD_R + HAND_R * 0.6 or \
        _seg_circle_dist(el, hd, head) < HEAD_R * 0.75
    near_face = touching and hand[1] > HEAD_Y - 45
    return a1, a2, bool(near_face)


def report_arm(sx, a1, a2, hx=0.0):
    """What safe_arm would change, for the checker: list of problems with this raw pose."""
    out = []
    if not (A1_LIM[0] - 0.5 <= a1 <= A1_LIM[1] + 0.5):
        out.append(f'shoulder {a1:.0f} outside {A1_LIM[0]:.0f}..{A1_LIM[1]:.0f}')
    w2 = float(wrap180(a2))
    if abs(w2 - a2) > 1:
        out.append(f'elbow {a2:.0f} wound past a full turn')
    if not (A2_LIM[0] - 0.5 <= w2 <= A2_LIM[1] + 0.5):
        out.append(f'elbow {w2:.0f} folds through the upper arm')
    el, hd = arm_points(sx, a1, w2)
    if _seg_circle_dist((sx * SH_X, SH_Y), el, (hx, HEAD_Y)) < HEAD_R + UPPER_R * 0.55:
        out.append('upper arm through the head')
    if sx * hd[0] < -SH_X:
        out.append('hand past the far shoulder (through the body)')
    return out


# ------------------------------------------------------------------ limit-aware IK for the house arm
_G1, _G2 = np.meshgrid(np.arange(A1_LIM[0], A1_LIM[1] + 0.01, 1.0), np.arange(A2_LIM[0], A2_LIM[1] + 0.01, 1.0))


def _grid_pose(sx, g1, g2, hx):
    r1 = np.radians(g1); r2 = np.radians(g1 + g2)
    ex, ey = sx * SH_X + sx * np.sin(r1) * L1, SH_Y + np.cos(r1) * L1
    hxx, hyy = ex + sx * np.sin(r2) * L2, ey + np.cos(r2) * L2
    # distance from head centre to the upper-arm segment (vectorised point-segment distance)
    px, py = sx * SH_X, SH_Y
    dx, dy = ex - px, ey - py
    t = np.clip(((hx - px) * dx + (HEAD_Y - py) * dy) / (dx * dx + dy * dy), 0, 1)
    dh = np.hypot(px + t * dx - hx, py + t * dy - HEAD_Y)
    return hxx, hyy, dh


def ik_arm(sx, tx, ty, prefer=(12.0, 0.0), hx=0.0):
    """Hand on side sx to (tx, ty) (hand-disc centre, guy units), choosing only poses a body can make:
    inside joint limits, upper arm clear of the head, hand not past the far shoulder.  Among equal reaches it
    prefers the pose closest to `prefer` (the 'preferred angle' idea from Maya IK), so the elbow never flips."""
    hxx, hyy, dh = _grid_pose(sx, _G1, _G2, hx)
    err = (hxx - tx) ** 2 + (hyy + 12 - ty) ** 2
    bad = (dh < HEAD_R + UPPER_R * 0.55) | (sx * hxx < -SH_X)
    cost = err + 4e6 * bad + 0.003 * ((_G1 - prefer[0]) ** 2 + (_G2 - prefer[1]) ** 2)
    i = int(np.argmin(cost))
    a1, a2 = float(_G1.flat[i]), float(_G2.flat[i])
    # refine to 0.1 deg around the winner
    f1, f2 = np.meshgrid(np.arange(a1 - 1, a1 + 1.01, 0.1), np.arange(a2 - 1, a2 + 1.01, 0.1))
    f1 = np.clip(f1, *A1_LIM); f2 = np.clip(f2, *A2_LIM)
    hxx, hyy, dh = _grid_pose(sx, f1, f2, hx)
    err = (hxx - tx) ** 2 + (hyy + 12 - ty) ** 2
    bad = (dh < HEAD_R + UPPER_R * 0.55) | (sx * hxx < -SH_X)
    cost = err + 4e6 * bad + 0.003 * ((f1 - prefer[0]) ** 2 + (f2 - prefer[1]) ** 2)
    j = int(np.argmin(cost))
    return float(f1.flat[j]), float(f2.flat[j])
