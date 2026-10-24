"""The 3D guy, sculpted in code from real anatomy (bones, muscle groups, fat pads), meshed, skinned and exported.

   python3 character.py out_dir

Proportions: adult male, 1.75 m, 7.5 heads tall (head 0.23 m), shoulders 0.40 m, eyes 63 mm apart, face in thirds
(hairline-brow, brow-nose base, nose base-chin).  Forms are signed-distance 'masses' (ellipsoids, tapered capsules)
blended like clay, from big to small: skeleton landmarks, then muscle bellies, then fat and skin, then carving
(sockets, nostrils, mouth, grooves).  Each mass belongs to a bone, so skin weights come from the sculpt itself.
Rest pose: A-pose (arms 40 deg out, elbows 8 deg), facing -z, y up, metres.  Bone lengths match web/main.js.
"""
import json, math, os, sys, time
import numpy as np
from skimage import measure
import trimesh
import fast_simplification

OUT = sys.argv[1] if len(sys.argv) > 1 else 'out'
os.makedirs(OUT, exist_ok=True)
A_DEG, ELB_DEG, LEG_DEG = 40.0, 8.0, 4.0


def v(*a):
    return np.array(a, np.float64)


def nrm(a):
    a = np.asarray(a, float); return a / np.linalg.norm(a)


# ------------------------------------------------------------------ skeleton (rest, world positions)
B = {}


def bone(name, parent, head, tail):
    B[name] = dict(parent=parent, head=np.asarray(head, float), tail=np.asarray(tail, float))


HIP = v(0, 0.95, 0)
HC = v(0, 1.640, 0.0)                         # skull centre (head 0.23 tall: chin 1.525, crown 1.755)
bone('hips', None, HIP, HIP + v(0, 0.11, 0))
bone('spine1', 'hips', HIP + v(0, 0.11, 0.004), HIP + v(0, 0.23, 0.008))
bone('spine2', 'spine1', HIP + v(0, 0.23, 0.008), HIP + v(0, 0.35, 0.006))
bone('chest', 'spine2', HIP + v(0, 0.35, 0.006), HIP + v(0, 0.52, 0))
bone('neck', 'chest', HIP + v(0, 0.52, 0), v(0, 1.590, 0.012))
bone('head', 'neck', v(0, 1.590, 0.012), v(0, 1.755, 0.0))
bone('jaw', 'head', HC + v(0, -0.022, 0.008), HC + v(0, -0.112, -0.078))
EYE = {'R': HC + v(0.0315, 0.002, -0.0745), 'L': HC + v(-0.0315, 0.002, -0.0745)}
EYE_R = 0.0122
for s_, S in ((1, 'R'), (-1, 'L')):                                    # brows ride their own small bones (raise, knit)
    bone('brow' + S, 'head', EYE[S] + v(0.004 * s_, 0.017, -0.012), EYE[S] + v(0.004 * s_, 0.017, -0.032))
for s, S in ((1, 'R'), (-1, 'L')):                                     # R = +x (rig side 'N'), L = -x ('F')
    sh = HIP + v(0.2 * s, 0.455, 0)
    bone('clav' + S, 'chest', HIP + v(0.03 * s, 0.45, -0.01), sh)
    adir = v(s * math.sin(math.radians(A_DEG)), -math.cos(math.radians(A_DEG)), 0)
    el = sh + adir * 0.30
    fdir = nrm(adir + v(0, 0, -math.tan(math.radians(ELB_DEG))))
    wr = el + fdir * 0.27
    bone('uarm' + S, 'clav' + S, sh, el)
    bone('farm' + S, 'uarm' + S, el, wr)
    bone('hand' + S, 'farm' + S, wr, wr + fdir * 0.09)
    u = fdir
    n = nrm(np.cross(u, v(0, 0, 1)) * s)            # palm faces the thigh
    if n[0] * s > 0:
        n = -n
    w = nrm(np.cross(n, u))
    if w[2] > 0:
        w = -w                                       # index toward the front
    # finger bases (knuckles) on a gentle arc; lengths: middle > ring >= index > pinky (beyond the palm)
    for fname, off, ln, back, spr in (('index', -0.0255, 0.074, 0.004, -0.09), ('middle', -0.0085, 0.082, 0.0, -0.02), ('ring', 0.0085, 0.077, 0.003, 0.06), ('pinky', 0.0245, 0.060, 0.012, 0.15)):
        base = wr + u * (0.094 - back) + w * off
        fd = nrm(u + w * spr)                        # fingers fan out a little from the knuckles
        bone(f'{fname}1{S}', 'hand' + S, base, base + fd * ln * 0.46)
        bone(f'{fname}2{S}', f'{fname}1{S}', base + fd * ln * 0.46, base + fd * ln)
    tb = wr + u * 0.022 + w * -0.026 + n * 0.012
    tdir = nrm(u * 0.62 + w * -0.62 + n * 0.3)
    bone('thumb1' + S, 'hand' + S, tb, tb + tdir * 0.046)
    bone('thumb2' + S, 'thumb1' + S, tb + tdir * 0.046, tb + tdir * 0.082)
    hp = HIP + v(0.09 * s, 0, 0)
    ldir = v(s * math.sin(math.radians(LEG_DEG)), -math.cos(math.radians(LEG_DEG)), 0)
    kn = hp + ldir * 0.43
    an = kn + ldir * 0.42
    bone('thigh' + S, 'hips', hp, kn)
    bone('shin' + S, 'thigh' + S, kn, an)
    bone('foot' + S, 'shin' + S, an, an + v(0, -0.06, -0.15))
H = lambda n: B[n]['head']; T = lambda n: B[n]['tail']
BONES = list(B.keys())


# ------------------------------------------------------------------ masses (data, so each is evaluated only where it is)
def frame(axis, front=(0, 0, -1)):
    """columns: x = lateral (axis x front), y = axis, z = front (made perpendicular)."""
    y = nrm(axis); f = np.asarray(front, float); f = f - y * (f @ y)
    if np.linalg.norm(f) < 1e-6:
        f = np.array([1.0, 0, 0]) - y * y[0]
    z = nrm(f); x = np.cross(y, z)
    return np.stack([x, y, z], 1)


class Mass:
    def __init__(self, name, bone_, group, kind, prm, k=0.012, op='add', pad=0.0):
        self.name, self.bone, self.group, self.kind, self.prm, self.k, self.op = name, bone_, group, kind, prm, k, op
        if kind in ('ell', 'lid'):
            c, r, R = prm[:3]
            e = float(np.max(r))
            self.lo, self.hi = c - e, c + e
        else:
            a, b, ra, rb = prm[:4]
            e = max(ra, rb) * (max(prm[4], prm[5]) if kind == 'scone' else 1.0)
            self.lo, self.hi = np.minimum(a, b) - e, np.maximum(a, b) + e
        m = self.k + 0.006 + pad
        self.lo = self.lo - m; self.hi = self.hi + m

    def sd(self, P):
        if self.kind == 'lid':                     # ellipsoid shell kept only above (sign +1) or below (-1) a cut height
            c, r, R, ycut, sg, curv, tilt, side = self.prm
            q = P - c
            k0 = np.linalg.norm(q / r, axis=-1); k1 = np.linalg.norm(q / (r * r), axis=-1)
            e = k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
            e = np.maximum(e, -(np.linalg.norm(q / (r - 0.0022), axis=-1) - 1.0) * float(np.min(r)))   # hollow: a 2 mm skin
            u = np.clip((P[..., 0] - c[0]) * side / 0.0135, -1.6, 1.6)
            cut = c[1] + ycut - sg * curv * u * u + tilt * u
            return smax(e, sg * (cut - P[..., 1]), 0.0009)
        if self.kind == 'ell':
            c, r, R = self.prm
            q = P - c
            if R is not None:
                q = q @ R
            k0 = np.linalg.norm(q / r, axis=-1); k1 = np.linalg.norm(q / (r * r), axis=-1)
            return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)
        if self.kind == 'scone':                    # round cone with an oval cross-section (sx across, sz front-back)
            a, b, ra, rb, sx, sz, R = self.prm
            q = (P - a) @ R
            q = q / np.array([sx, 1.0, sz])
            L = np.linalg.norm(b - a)
            t = np.clip(q[..., 1] / L, 0, 1)
            dd = np.sqrt(q[..., 0] ** 2 + (q[..., 1] - t * L) ** 2 + q[..., 2] ** 2) - (ra + (rb - ra) * t)
            return dd * min(sx, sz)
        a, b, ra, rb = self.prm
        ab = b - a; L2 = ab @ ab
        t = np.clip(((P - a) @ ab) / L2, 0, 1)
        return np.linalg.norm(P - (a + t[..., None] * ab), axis=-1) - (ra + (rb - ra) * t)


MASSES = []


def ell(name, bone_, group, c, r, R=None, k=0.012, op='add'):
    MASSES.append(Mass(name, bone_, group, 'ell', (np.asarray(c, float), np.asarray(r, float), R), k, op))


def lid(name, bone_, group, c, r, ycut, sg, curv, tilt, side, k=0.003):
    MASSES.append(Mass(name, bone_, group, 'lid', (np.asarray(c, float), np.asarray(r, float), None, ycut, sg, curv, tilt, side), k, 'post'))


def scone(name, bone_, group, a, b, ra, rb, sx, sz, k=0.012, op='add'):
    a, b = np.asarray(a, float), np.asarray(b, float)
    MASSES.append(Mass(name, bone_, group, 'scone', (a, b, ra, rb, sx, sz, frame(b - a)), k, op))


def cone(name, bone_, group, a, b, ra, rb, k=0.012, op='add'):
    MASSES.append(Mass(name, bone_, group, 'cone', (np.asarray(a, float), np.asarray(b, float), ra, rb), k, op))


# ================================================================== TORSO
# a male trunk is a box-ish barrel: ribcage on top, a belly that fills the waist (no hourglass), a narrower pelvis
ell('ribcage', 'spine2', 'torso', HIP + v(0, 0.32, 0.014), v(0.136, 0.165, 0.1), frame(v(0, 1, 0.12)), k=0.04)
ell('pelvis', 'hips', 'torso', HIP + v(0, 0.0, 0.01), v(0.142, 0.092, 0.098), k=0.04)
ell('belly', 'spine1', 'torso', HIP + v(0, 0.12, -0.008), v(0.134, 0.125, 0.098), k=0.04)
ell('abs', 'spine1', 'torso', HIP + v(0, 0.17, -0.074), v(0.052, 0.12, 0.024), k=0.03)
cone('lineaAlba', 'spine1', 'torso', HIP + v(0, 0.1, -0.1), HIP + v(0, 0.28, -0.099), 0.003, 0.003, k=0.01, op='sub')
cone('spineGroove', 'spine2', 'torso', HIP + v(0, 0.06, 0.108), HIP + v(0, 0.46, 0.116), 0.005, 0.005, k=0.014, op='sub')
cone('sternum', 'chest', 'torso', HIP + v(0, 0.34, -0.1), HIP + v(0, 0.46, -0.086), 0.004, 0.004, k=0.012, op='sub')
ell('sternalNotch', 'chest', 'torso', HIP + v(0, 0.488, -0.058), v(0.012, 0.009, 0.01), k=0.01, op='sub')
for s, S in ((1, 'R'), (-1, 'L')):
    ell('pec' + S, 'chest', 'torso', HIP + v(0.066 * s, 0.405, -0.07), v(0.068, 0.04, 0.012), frame(v(0.12 * s, 1, -0.3), v(0, 0, -1)), k=0.035)
    cone('pecArm' + S, 'chest', 'torso', HIP + v(0.11 * s, 0.41, -0.066), HIP + v(0.168 * s, 0.39, -0.04), 0.02, 0.017, k=0.02)
    cone('clavicle' + S, 'chest', 'torso', HIP + v(0.02 * s, 0.484, -0.06), HIP + v(0.17 * s, 0.474, -0.006), 0.007, 0.007, k=0.014)
    cone('trapUp' + S, 'chest', 'torso', HIP + v(0.035 * s, 0.56, 0.024), HIP + v(0.16 * s, 0.472, 0.008), 0.03, 0.016, k=0.03)
    ell('scapula' + S, 'chest', 'torso', HIP + v(0.08 * s, 0.37, 0.09), v(0.045, 0.062, 0.012), frame(v(-0.15 * s, 1, 0.1), v(0, 0, 1)), k=0.025)
    ell('lat' + S, 'spine2', 'torso', HIP + v(0.11 * s, 0.31, 0.05), v(0.042, 0.115, 0.045), frame(v(0.3 * s, 1, 0)), k=0.03)
    cone('erector' + S, 'spine1', 'torso', HIP + v(0.025 * s, 0.03, 0.086), HIP + v(0.025 * s, 0.3, 0.094), 0.021, 0.016, k=0.018)
    ell('oblique' + S, 'spine1', 'torso', HIP + v(0.115 * s, 0.07, -0.008), v(0.035, 0.07, 0.07), k=0.03)
    ell('iliac' + S, 'hips', 'torso', HIP + v(0.118 * s, 0.03, -0.035), v(0.02, 0.016, 0.036), k=0.016)
    ell('glute' + S, 'hips', 'torso', HIP + v(0.064 * s, -0.04, 0.07), v(0.074, 0.085, 0.056), frame(v(0.15 * s, 1, 0)), k=0.025)
    for j in range(3):                                         # serratus: fingers of muscle along the ribs
        ell(f'serratus{j}{S}', 'spine2', 'torso', HIP + v(0.126 * s, 0.33 - 0.035 * j, -0.045 + 0.006 * j), v(0.012, 0.011, 0.02), k=0.012)
ell('trapMid', 'chest', 'torso', HIP + v(0, 0.43, 0.088), v(0.06, 0.08, 0.014), k=0.03)
# neck: column, sternocleidomastoids (behind the ear to the sternum), Adam's apple
cone('neck', 'neck', 'torso', HIP + v(0, 0.48, 0.014), HC + v(0, -0.03, 0.014), 0.056, 0.05, k=0.025)
for s, S in ((1, 'R'), (-1, 'L')):
    cone('scm' + S, 'neck', 'torso', HC + v(0.052 * s, -0.04, 0.03), HIP + v(0.014 * s, 0.492, -0.052), 0.0095, 0.009, k=0.02)
ell('adamsApple', 'neck', 'torso', HC + v(0, -0.137, -0.038), v(0.009, 0.013, 0.009), k=0.012)

# ================================================================== HEAD (skull, then face from the bone out)
# landmarks (relative to HC, metres): eyes at mid-head, brow +0.022, nose base -0.045, mouth -0.067, chin -0.115,
# hairline +0.085 (thirds of 0.065-0.07); face depth: glabella z -0.097, cornea -0.086, nose tip -0.118, lips -0.104
G = 'head'
ell('cranium', 'head', G, HC + v(0, 0.026, 0.014), v(0.074, 0.088, 0.096), k=0.02)
ell('parietal', 'head', G, HC + v(0, 0.015, 0.03), v(0.077, 0.07, 0.07), k=0.025)
ell('forehead', 'head', G, HC + v(0, 0.048, -0.056), v(0.055, 0.042, 0.04), k=0.025)
ell('glabella', 'head', G, HC + v(0, 0.022, -0.087), v(0.012, 0.009, 0.01), k=0.012)
scone('faceBlock', 'head', G, HC + v(0, 0.0, -0.022), HC + v(0, -0.07, -0.03), 0.056, 0.043, 1.0, 0.85, k=0.03)
ell('midface', 'head', G, HC + v(0, -0.024, -0.058), v(0.04, 0.036, 0.036), k=0.025)
ell('muzzle', 'head', G, HC + v(0, -0.064, -0.07), v(0.028, 0.026, 0.029), k=0.022)
ell('chin', 'jaw', G, HC + v(0, -0.101, -0.078), v(0.017, 0.014, 0.016), k=0.02)
for s, S in ((1, 'R'), (-1, 'L')):
    ell('browArch' + S, 'head', G, HC + v(0.025 * s, 0.022, -0.082), v(0.022, 0.0075, 0.012), frame(v(0, 1, 0), v(-0.35 * s, 0, -1)), k=0.014)
    ell('temple' + S, 'head', G, HC + v(0.07 * s, 0.018, -0.042), v(0.006, 0.016, 0.014), k=0.02, op='sub')
    ell('zygoma' + S, 'head', G, HC + v(0.047 * s, -0.014, -0.056), v(0.014, 0.011, 0.014), k=0.028)
    ell('buccal' + S, 'head', G, HC + v(0.041 * s, -0.05, -0.054), v(0.015, 0.02, 0.016), k=0.025)
    cone('ramus' + S, 'jaw', G, HC + v(0.049 * s, -0.03, 0.008), HC + v(0.048 * s, -0.076, 0.002), 0.0085, 0.0085, k=0.025)
    cone('mandible' + S, 'jaw', G, HC + v(0.045 * s, -0.08, 0.0), HC + v(0.014 * s, -0.106, -0.07), 0.007, 0.007, k=0.022)
    # eye: socket carved to just clear the ball, then lids added as almond-cut skin shells (upper lid on its own bone)
    ell('socket' + S, 'head', G, EYE[S] + v(0, 0.0, -0.002), v(0.0136, 0.0128, 0.0132), k=0.003, op='sub')
    lid('lidUpper' + S, 'head', G, EYE[S], v(0.0148, 0.0146, 0.0146), 0.0046, 1, 0.0066, 0.0008, s)
    lid('lidLower' + S, 'head', G, EYE[S], v(0.0144, 0.0142, 0.0142), -0.0056, -1, 0.0042, 0.0008, s)
    ell('lidCrease' + S, 'head', G, EYE[S] + v(0.002 * s, 0.0105, -0.0105), v(0.0125, 0.0016, 0.004), k=0.003, op='sub')
    ell('eyeBag' + S, 'head', G, EYE[S] + v(0.0, -0.0135, -0.007), v(0.011, 0.0035, 0.005), k=0.01)
    # ear: rim (helix), bowl (concha), lobe, tragus; top at brow level, lobe at nose base
    ec = HC + v(0.072 * s, -0.012, 0.016)
    en = nrm(v(s, 0, -0.3)); eu = nrm(v(0, 1, 0.15)); ew = nrm(np.cross(eu, en)); ew = ew if ew[2] > 0 else -ew   # out, up, back
    pn = nrm(en - ew * 0.5)                                                                # the auricle flares out toward the back
    Re = np.stack([pn, eu, nrm(np.cross(pn, eu)) * (1 if np.cross(pn, eu)[2] > 0 else -1)], 1)
    ell('earPlate' + S, 'head', G, ec + ew * 0.004 + en * 0.007, v(0.0035, 0.026, 0.0145), Re, k=0.006)
    rim = [ec + eu * (0.0285 * math.sin(a)) + ew * (0.004 + 0.0155 * math.cos(a)) + en * (0.006 + 0.0085 * max(math.cos(a), 0) + 0.002 * (math.sin(a) > 0))
           for a in np.radians([125, 100, 75, 45, 15, -15, -45, -70])]
    for j in range(len(rim) - 1):
        cone(f'helix{j}{S}', 'head', G, rim[j], rim[j + 1], 0.0027, 0.0027, k=0.004)
    cone('antihelix' + S, 'head', G, ec + eu * 0.016 + ew * 0.006 + en * 0.011, ec + eu * -0.012 + ew * 0.008 + en * 0.011, 0.0022, 0.0024, k=0.004)
    ell('concha' + S, 'head', G, ec + eu * -0.003 + ew * 0.0005 + en * 0.0115, v(0.0045, 0.011, 0.0075), Re, k=0.004, op='sub')
    ell('earLobe' + S, 'head', G, ec + eu * -0.025 + ew * 0.004 + en * 0.006, v(0.0045, 0.0085, 0.0075), Re, k=0.006)
    ell('tragus' + S, 'head', G, ec + eu * -0.006 + ew * -0.008 + en * 0.006, v(0.004, 0.0055, 0.0035), k=0.004)
    # nose wings (alae), nostrils, smile line from the wing to the mouth corner
    ell('ala' + S, 'head', G, HC + v(0.0125 * s, -0.04, -0.099), v(0.0076, 0.0072, 0.0095), k=0.006)
    ell('nostril' + S, 'head', G, HC + v(0.0075 * s, -0.0455, -0.106), v(0.0038, 0.0024, 0.0055), frame(v(0, 0, -1), v(0, -1, 0)), k=0.003, op='sub')
    cone('nasolabial' + S, 'head', G, HC + v(0.022 * s, -0.04, -0.094), HC + v(0.03 * s, -0.074, -0.087), 0.0016, 0.0012, k=0.01, op='sub')
    ell('lipUpper' + S, 'head', G, HC + v(0.0095 * s, -0.0638, -0.0962), v(0.0135, 0.0046, 0.0062), k=0.006)
    ell('philtrumCol' + S, 'head', G, HC + v(0.0036 * s, -0.0555, -0.1005), v(0.0028, 0.0075, 0.0028), k=0.006)
    ell('mouthCorner' + S, 'head', G, HC + v(0.0245 * s, -0.0672, -0.0895), v(0.0032, 0.0032, 0.0032), k=0.005, op='sub')
cone('noseBridge', 'head', G, HC + v(0, 0.012, -0.088), HC + v(0, -0.022, -0.11), 0.0065, 0.0085, k=0.01)
ell('noseTip', 'head', G, HC + v(0, -0.033, -0.11), v(0.011, 0.0095, 0.0105), k=0.008)
ell('columella', 'head', G, HC + v(0, -0.0425, -0.104), v(0.004, 0.005, 0.007), k=0.005)
ell('lipTubercle', 'head', G, HC + v(0, -0.0645, -0.0985), v(0.0055, 0.0038, 0.0045), k=0.005)
ell('lipLower', 'jaw', G, HC + v(0, -0.0722, -0.0948), v(0.0185, 0.0056, 0.007), k=0.006)
ell('mentalGroove', 'jaw', G, HC + v(0, -0.0835, -0.098), v(0.012, 0.0025, 0.004), k=0.008, op='sub')
MOUTH_Y = HC[1] - 0.0675
MOUTH_Z = -0.097

# ================================================================== ARMS
HAND = {}
for s, S in ((1, 'R'), (-1, 'L')):
    g = 'arm' + S
    sh, el, wr = H('uarm' + S), H('farm' + S), H('hand' + S)
    au, fu = nrm(el - sh), nrm(wr - el)
    lat = -s * np.cross(v(0, 0, -1), au); lat = nrm(lat)
    fr = nrm(v(0, 0, -1) - au * (v(0, 0, -1) @ au))
    Ra = np.stack([lat, au, fr], 1)
    at = lambda t, f=0.0, l=0.0, sh=sh, au=au, fr=fr, lat=lat: sh + au * t + fr * f + lat * l
    # deltoid: three heads wrapping the shoulder, converging on the deltoid tuberosity (~0.45 down)
    ell('deltAnt' + S, 'uarm' + S, g, at(0.045, 0.026, 0.008), v(0.026, 0.07, 0.022), Ra, k=0.012)
    ell('deltLat' + S, 'uarm' + S, g, at(0.05, 0.0, 0.03), v(0.025, 0.075, 0.024), Ra, k=0.012)
    ell('deltPost' + S, 'uarm' + S, g, at(0.045, -0.026, 0.01), v(0.026, 0.07, 0.022), Ra, k=0.012)
    ell('acromion' + S, 'clav' + S, 'torso', sh + v(0, 0.022, 0.0), v(0.024, 0.012, 0.024), k=0.012)
    cone('humerus' + S, 'uarm' + S, g, at(0.02), at(0.29), 0.034, 0.03, k=0.02)
    ell('biceps' + S, 'uarm' + S, g, at(0.165, 0.02, 0.0), v(0.024, 0.075, 0.025), Ra, k=0.012)
    ell('triceps' + S, 'uarm' + S, g, at(0.14, -0.021, 0.0), v(0.03, 0.095, 0.026), Ra, k=0.012)
    ell('brachialis' + S, 'uarm' + S, g, at(0.235, 0.004, 0.02), v(0.016, 0.045, 0.016), Ra, k=0.01)
    ell('olecranon' + S, 'farm' + S, g, el + fr * -0.024 + au * -0.004, v(0.011, 0.013, 0.01), k=0.008)
    ell('epiLat' + S, 'farm' + S, g, el + lat * 0.03 + fr * -0.006, v(0.008, 0.01, 0.008), k=0.008)
    ell('epiMed' + S, 'farm' + S, g, el - lat * 0.032 + fr * -0.006, v(0.009, 0.011, 0.009), k=0.008)
    # forearm: radius/ulna core, thumb-side extensor mass (brachioradialis), palm-side flexors, flat oval wrist
    hu = nrm(T('hand' + S) - wr)
    hn = nrm(np.cross(hu, v(0, 0, 1)) * s)
    if hn[0] * s > 0:
        hn = -hn
    hw = nrm(np.cross(hn, hu))
    if hw[2] > 0:
        hw = -hw
    HAND[S] = dict(u=hu, n=hn, w=hw)
    Rf = np.stack([hw, fu, hn], 1)                      # x across (thumb side -), y along, z palm side
    af = lambda t, a=0.0, p=0.0, el=el, fu=fu, hw=hw, hn=hn: el + fu * t + hw * a + hn * p
    cone('forearm' + S, 'farm' + S, g, af(0.02), af(0.255), 0.027, 0.019, k=0.02)
    ell('brachiorad' + S, 'farm' + S, g, af(0.05, -0.02, -0.004), v(0.017, 0.07, 0.019), Rf, k=0.012)
    ell('extensors' + S, 'farm' + S, g, af(0.09, -0.006, -0.016), v(0.02, 0.085, 0.016), Rf, k=0.012)
    ell('flexors' + S, 'farm' + S, g, af(0.08, 0.008, 0.016), v(0.022, 0.08, 0.017), Rf, k=0.012)
    ell('wristOval' + S, 'farm' + S, g, af(0.25), v(0.027, 0.03, 0.0175), Rf, k=0.012)
    ell('ulnaHead' + S, 'farm' + S, g, af(0.248, 0.022, -0.009), v(0.0065, 0.007, 0.006), k=0.006)
    # ---- hand (fine mesh)
    gh = 'hand' + S
    ah = lambda t, a=0.0, p=0.0, wr=wr, hu=hu, hw=hw, hn=hn: wr + hu * t + hw * a + hn * p
    Rh = np.stack([hw, hu, hn], 1)
    ell('palm' + S, 'hand' + S, gh, ah(0.05), v(0.041, 0.05, 0.0125), Rh, k=0.008)
    ell('thenar' + S, 'thumb1' + S, gh, ah(0.03, -0.018, 0.009), v(0.016, 0.026, 0.011), Rh, k=0.008)
    ell('hypothenar' + S, 'hand' + S, gh, ah(0.045, 0.026, 0.006), v(0.011, 0.034, 0.009), Rh, k=0.008)
    ell('handBack' + S, 'hand' + S, gh, ah(0.055, 0.0, -0.004), v(0.038, 0.045, 0.011), Rh, k=0.008)
    ell('carpus' + S, 'hand' + S, gh, ah(0.012), v(0.027, 0.016, 0.0155), Rh, k=0.008)
    cone('wristStub' + S, 'farm' + S, gh, ah(-0.05), ah(0.0), 0.022, 0.021, k=0.01)
    for f, r0 in (('index', 0.0089), ('middle', 0.0092), ('ring', 0.0087), ('pinky', 0.0077)):
        a1, b1, b2 = H(f'{f}1{S}'), T(f'{f}1{S}'), T(f'{f}2{S}')
        L = np.linalg.norm(b2 - a1); d = nrm(b2 - a1)
        mid = a1 + d * L * 0.46; tip2 = a1 + d * L * 0.74
        ell(f'knuckle_{f}{S}', 'hand' + S, gh, a1 - hn * 0.006 - d * 0.004, v(0.0098, 0.009, 0.0085), k=0.006)
        cone(f'{f}P{S}', f'{f}1{S}', gh, a1 - d * 0.006, mid, r0, r0 * 0.88, k=0.005)
        cone(f'{f}M{S}', f'{f}2{S}', gh, mid, tip2, r0 * 0.88, r0 * 0.8, k=0.005)
        cone(f'{f}D{S}', f'{f}2{S}', gh, tip2, b2 - d * 0.006, r0 * 0.8, r0 * 0.68, k=0.005)
        ell(f'pad_{f}{S}', f'{f}2{S}', gh, b2 - d * 0.011 + hn * 0.0025, v(0.0068, 0.009, 0.0058), k=0.004)
    t0, t1, t2 = H('thumb1' + S), T('thumb1' + S), T('thumb2' + S)
    cone('thumbM' + S, 'thumb1' + S, gh, t0 - (t1 - t0) * 0.2, t1, 0.0135, 0.0115, k=0.008)
    cone('thumbP' + S, 'thumb2' + S, gh, t1, t2 - nrm(t2 - t1) * 0.005, 0.0112, 0.0092, k=0.005)

# ================================================================== LEGS
for s, S in ((1, 'R'), (-1, 'L')):
    g = 'leg' + S
    hp, kn, an = H('thigh' + S), H('shin' + S), H('foot' + S)
    tu, su = nrm(kn - hp), nrm(an - kn)
    lat = nrm(v(s, 0, 0) - tu * (v(s, 0, 0) @ tu)); fr = nrm(v(0, 0, -1) - tu * (v(0, 0, -1) @ tu))
    Rt = np.stack([lat, tu, fr], 1)
    atg = lambda t, f=0.0, l=0.0, hp=hp, tu=tu, fr=fr, lat=lat: hp + tu * t + fr * f + lat * l
    cone('femur' + S, 'thigh' + S, g, atg(-0.02, 0, 0.008), atg(0.4), 0.066, 0.048, k=0.03)
    ell('rectusFem' + S, 'thigh' + S, g, atg(0.19, 0.03, 0.0), v(0.03, 0.15, 0.026), Rt, k=0.016)
    ell('vastusLat' + S, 'thigh' + S, g, atg(0.2, 0.004, 0.034), v(0.032, 0.16, 0.034), Rt, k=0.016)
    ell('vastusMed' + S, 'thigh' + S, g, atg(0.33, 0.016, -0.03), v(0.028, 0.06, 0.026), Rt, k=0.014)     # the teardrop
    ell('adductors' + S, 'thigh' + S, g, atg(0.1, 0.0, -0.04), v(0.034, 0.1, 0.038), Rt, k=0.02)
    ell('hamstrings' + S, 'thigh' + S, g, atg(0.2, -0.034, 0.0), v(0.04, 0.16, 0.03), Rt, k=0.016)
    ell('condyles' + S, 'shin' + S, g, kn + v(0, 0.01, 0.0), v(0.05, 0.035, 0.044), k=0.014)
    ell('patella' + S, 'shin' + S, g, kn + fr * 0.042 + tu * -0.012, v(0.021, 0.025, 0.01), k=0.008)
    cone('patTendon' + S, 'shin' + S, g, kn + fr * 0.036 + su * 0.02, kn + fr * 0.034 + su * 0.06, 0.009, 0.008, k=0.008)
    lat2 = nrm(v(s, 0, 0) - su * (v(s, 0, 0) @ su)); fr2 = nrm(v(0, 0, -1) - su * (v(0, 0, -1) @ su))
    Rs = np.stack([lat2, su, fr2], 1)
    ats = lambda t, f=0.0, l=0.0, kn=kn, su=su, fr=fr2, lat=lat2: kn + su * t + fr * f + lat * l
    cone('tibia' + S, 'shin' + S, g, ats(0.03, 0.006), ats(0.4), 0.036, 0.024, k=0.02)
    cone('shinRidge' + S, 'shin' + S, g, ats(0.07, 0.022, -0.004), ats(0.33, 0.016, -0.006), 0.006, 0.005, k=0.01)
    ell('gastroMed' + S, 'shin' + S, g, ats(0.12, -0.03, -0.016), v(0.026, 0.085, 0.028), Rs, k=0.014)    # inner head lower and bigger
    ell('gastroLat' + S, 'shin' + S, g, ats(0.105, -0.028, 0.018), v(0.022, 0.07, 0.024), Rs, k=0.014)
    ell('soleus' + S, 'shin' + S, g, ats(0.22, -0.018, 0.0), v(0.034, 0.1, 0.022), Rs, k=0.016)
    cone('achilles' + S, 'shin' + S, g, ats(0.3, -0.026), ats(0.41, -0.032), 0.01, 0.008, k=0.01)
    ell('malleolusMed' + S, 'foot' + S, g, an + lat2 * -0.022 + su * -0.004 + fr2 * 0.004, v(0.009, 0.012, 0.01), k=0.008)
    ell('malleolusLat' + S, 'foot' + S, g, an + lat2 * 0.023 + su * 0.008 + fr2 * -0.004, v(0.009, 0.012, 0.01), k=0.008)


def smin(a, b, k):
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


BIG = 0.08


def group_vol(groups, xs, y, zs, skip=(), kmin=0.0, adds_only=False):
    """SDF of the union of the groups' masses on one y-slab, each mass evaluated only inside its own box.
    kmin > 0 blends everything softer (cloth bridging the small forms); adds_only drops the carving."""
    d = np.full((len(xs), len(zs)), BIG, np.float64)
    ms = [m for m in MASSES if m.group in groups and m.name not in skip]
    for op in (('add', 'post') if adds_only else ('add', 'sub', 'post')):
        for m in ms:
            if m.op != op:
                continue
            k = max(m.k, kmin); pad = k - m.k
            if not (m.lo[1] - pad <= y <= m.hi[1] + pad):
                continue
            i0, i1 = np.searchsorted(xs, m.lo[0] - pad), np.searchsorted(xs, m.hi[0] + pad)
            j0, j1 = np.searchsorted(zs, m.lo[2] - pad), np.searchsorted(zs, m.hi[2] + pad)
            if i1 <= i0 or j1 <= j0:
                continue
            Xs, Zs = np.meshgrid(xs[i0:i1], zs[j0:j1], indexing='ij')
            P = np.stack([Xs, np.full_like(Xs, y), Zs], -1)
            x = m.sd(P)
            sub = d[i0:i1, j0:j1]
            d[i0:i1, j0:j1] = smax(sub, -x, k) if op == 'sub' else smin(sub, x, k)
    return d


def group_pts(groups, P, skip=()):
    """Same SDF at arbitrary points (for clothing tests and weights)."""
    d = np.full(P.shape[:-1], BIG)
    for op in ('add', 'sub', 'post'):
        for m in MASSES:
            if m.group in groups and m.op == op and m.name not in skip:
                x = m.sd(P)
                d = smax(d, -x, m.k) if op == 'sub' else smin(d, x, m.k)
    return d


def fold_noise(P, freq, seed):
    r = np.random.default_rng(seed); out = 0
    for i in range(3):
        k = r.normal(size=3); k /= np.linalg.norm(k)
        out = out + np.sin((P @ k) * freq * (1 + 0.37 * i) + r.uniform(0, 6))
    return out / 3


# ------------------------------------------------------------------ meshing
def mesh_slabs(slab_fn, lo, hi, step, name):
    """slab_fn(xs, y, zs) -> (nx, nz) SDF.  Skipped (None) when ONLY= names other pieces."""
    if not want(name):
        return None
    t0 = time.time()
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    n = np.ceil((hi - lo) / step).astype(int) + 1
    xs, ys, zs = [lo[i] + np.arange(n[i]) * step for i in range(3)]
    vol = np.empty((n[0], n[1], n[2]), np.float32)
    for j, y in enumerate(ys):
        vol[:, j, :] = slab_fn(xs, y, zs)
    verts, faces, _, _ = measure.marching_cubes(vol, 0.0, spacing=(step, step, step))
    verts += lo
    m = clean_smooth(trimesh.Trimesh(verts, faces, process=True), step, 5)
    print(f'  {name}: {len(m.faces)} tris raw, grid {tuple(n)}, {time.time() - t0:.1f}s', flush=True)
    return m


def grid_pts(xs, y, zs):
    Xs, Zs = np.meshgrid(xs, zs, indexing='ij')
    return np.stack([Xs, np.full_like(Xs, y), Zs], -1)


def clean_smooth(m, step, iters):
    m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
    parts = [p for p in m.split(only_watertight=False) if len(p.faces) >= 200]
    m = trimesh.util.concatenate(parts) if len(parts) > 1 else parts[0]
    v0 = m.vertices.copy()
    trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=iters)
    bad = np.linalg.norm(m.vertices - v0, axis=1) > 2 * step
    if bad.any():
        vv = m.vertices.copy(); vv[bad] = v0[bad]; m.vertices = vv
    return m


def decimate(m, target, step):
    if m is None:
        return None
    if len(m.faces) <= target:
        return m
    p, f = fast_simplification.simplify(m.vertices.astype(np.float32), m.faces.astype(np.int64), 1 - target / len(m.faces))
    return clean_smooth(trimesh.Trimesh(p, f, process=True), step, 1)


def keep_faces(m, keep_vert):
    if m is None:
        return None
    return m.submesh([np.where(keep_vert[m.faces].all(1))[0]], append=True)


# ------------------------------------------------------------------ skin weights
def weights(V, groups=None, extra=None):
    ms = [m for m in MASSES if m.op != 'sub' and (groups is None or m.group in groups)]
    D = np.stack([m.sd(V) for m in ms], 1)
    dmin = D.min(1, keepdims=True)
    W = np.exp(-(D - dmin) / 0.01)
    bw = np.zeros((len(V), len(BONES)))
    for j, m in enumerate(ms):
        bw[:, BONES.index(m.bone)] += W[:, j]
    if extra is not None:
        bw = extra(V, bw)
    idx = np.argsort(-bw, 1)[:, :4]
    w = np.take_along_axis(bw, idx, 1)
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    w[w < 0.01] = 0
    w = w / np.maximum(w.sum(1, keepdims=True), 1e-9)
    return idx.astype(np.uint16), w.astype(np.float32)


def jaw_extra(V, bw):
    """Below the lip line and in front of the ears the face rides on the jaw, with a soft edge."""
    hi, ja = BONES.index('head'), BONES.index('jaw')
    y, z = V[:, 1], V[:, 2]
    k = np.clip((MOUTH_Y + 0.0006 - y) / 0.0035, 0, 1) ** 0.7 * np.clip((0.025 - z) / 0.03, 0, 1) * np.clip((y - (HC[1] - 0.14)) / 0.02, 0, 1)
    tot = bw[:, hi] + bw[:, ja]
    bw[:, ja] = tot * k; bw[:, hi] = tot * (1 - k)
    return bw


def brow_extra(V, bw):
    """The brow and the forehead skin just above/below it follow the brow bone, fading out over ~2 cm."""
    hi = BONES.index('head')
    for S in 'RL':
        bi = BONES.index('brow' + S)
        c = H('brow' + S)
        d = np.linalg.norm((V - c) / v(0.024, 0.016, 0.03), axis=1)
        k = np.clip(1.15 - d, 0, 1) ** 1.5 * np.clip((HC[2] - 0.05 - V[:, 2]) / 0.015, 0, 1)
        tot = bw[:, hi] + bw[:, bi]
        bw[:, bi] = tot * k; bw[:, hi] = tot * (1 - k)
    return bw


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def face_colors(V):
    """Per-vertex colour multipliers for the broad tones: a faint beard shadow, cheek/nose/ear flush, nostril and ear-bowl
    shadow.  Fine detail (brows, lashes, lips) is painted per pixel in the shader (web/guy3d.js) from the rest position."""
    C = np.ones((len(V), 3))
    def paint(mask, col):
        nonlocal C
        C = C * (1 - mask[:, None]) + np.asarray(col)[None] * mask[:, None]
    x, y, z = V[:, 0], V[:, 1], V[:, 2]
    # beard shadow: jaw, chin and upper lip, faded toward the cheeks
    lips_d = np.min(np.stack([m.sd(V) for m in MASSES if m.name.startswith(('lipUpper', 'lipLower', 'lipTubercle'))], 1), 1)
    beard = smoothstep(HC[1] - 0.035, HC[1] - 0.055, y) * smoothstep(-0.045, -0.06, z - HC[2] - 0.0 + np.abs(x) * 0.25)
    beard *= smoothstep(0.003, 0.007, lips_d) * smoothstep(HC[1] - 0.16, HC[1] - 0.12, y)
    up_lip = smoothstep(HC[1] - 0.046, HC[1] - 0.052, y) * smoothstep(0.003, 0.006, lips_d) * smoothstep(0.03, 0.02, np.abs(x)) * (z < HC[2] - 0.085)
    paint(np.clip(beard + up_lip, 0, 1) * 0.35, (0.72, 0.72, 0.78))
    # flush: cheeks, nose tip, ears
    for c, r, a in ((HC + v(0.042, -0.025, -0.07), 0.018, 0.25), (HC + v(-0.042, -0.025, -0.07), 0.018, 0.25), (HC + v(0, -0.033, -0.115), 0.012, 0.2)):
        paint(a * np.exp(-((V - c) ** 2).sum(1) / (r * r)), (1.0, 0.82, 0.8))
    for S, s in (('R', 1), ('L', -1)):
        paint(0.3 * np.exp(-((V - (HC + v(0.08 * s, -0.012, 0.022))) ** 2).sum(1) / 0.02 ** 2), (1.0, 0.8, 0.78))
    # nostrils, mouth slit, ear bowl: occlusion darkening
    for m in MASSES:
        if m.name.startswith(('nostril', 'concha', 'mouthCorner')):
            paint(0.6 * smoothstep(0.002, -0.0005, m.sd(V)), (0.45, 0.3, 0.3))
    return np.clip(C * 255, 0, 255).astype(np.uint8)


def spine_extra(V, bw):
    names = ['hips', 'spine1', 'spine2', 'chest']
    ys = [HIP[1] + 0.0, HIP[1] + 0.12, HIP[1] + 0.25, HIP[1] + 0.40]
    idx = [BONES.index(n) for n in names]
    tot = bw[:, idx].sum(1)
    y = np.clip(V[:, 1], ys[0], ys[-1])
    gg = np.stack([np.exp(-((y - yy) / 0.075) ** 2) for yy in ys], 1)
    gg /= gg.sum(1, keepdims=True)
    for j, b in enumerate(idx):
        bw[:, b] = tot * gg[:, j]
    return bw


# ------------------------------------------------------------------ build
def shoe_upper_sd(P, an):
    """The shoe's upper (no laces): body, toe box, and a low collar that the jeans hem covers."""
    body = Mass('u', 'x', 'x', 'ell', (an + v(0, -0.05, -0.05), v(0.048, 0.046, 0.128), None)).sd(P)
    toe = Mass('t', 'x', 'x', 'ell', (an + v(0, -0.07, -0.135), v(0.043, 0.028, 0.05), None)).sd(P)
    collar = Mass('c', 'x', 'x', 'cone', (an + v(0, -0.02, 0.008), an + v(0, 0.018, 0.006), 0.045, 0.042)).sd(P)
    return smin(smin(body, toe, 0.02), collar, 0.025)


JEANS_HEM = 0.115


def jeans_core(xs, y, zs):
    """The jeans' main volume.  Fabric bridges small forms (kmin), the waist sits snug (it hides under the shirt), and
    from mid-shin down the leg widens into a hem that always clears the shoe collar by 6 mm."""
    P = grid_pts(xs, y, zs)
    legs = smin(group_vol({'legR'}, xs, y, zs, kmin=0.03, adds_only=True), group_vol({'legL'}, xs, y, zs, kmin=0.03, adds_only=True), 0.02)
    hips = group_vol({'torso'}, xs, y, zs, kmin=0.03, adds_only=True)
    d = smin(hips - 0.001 + 0.004 * np.clip((y - (HIP[1] - 0.03)) / 0.03, 0, 1), legs - 0.012 - 0.004 * np.clip((0.4 - y) / 0.3, 0, 1), 0.035)
    if y < 0.24:
        Xs, Zs = np.meshgrid(xs, zs, indexing='ij')
        for S in 'RL':
            an = H('foot' + S)
            boot = np.sqrt((Xs - an[0]) ** 2 + (Zs - an[2] - 0.006) ** 2) - (0.051 + 0.004 * np.clip((0.16 - y) / 0.05, 0, 1))
            boot = boot + 0.06 * np.clip((y - 0.17) / 0.07, 0, 1)                   # fades out up the shin
            d = smin(d, boot, 0.02)
            d = np.minimum(d, shoe_upper_sd(P, an) - 0.006)
    return d


def ankle_blend(V, S):
    """0 = rides the foot, 1 = rides the shin.  Shoe collar and jeans hem use the same curve so they move together."""
    return np.clip((V[:, 1] - (H('foot' + S)[1] - 0.01)) / 0.05, 0, 1)


def cloth_extra(V, bw):
    """Clothes: spine smoothing plus, near each ankle, the same foot/shin blend the shoe uses."""
    bw = spine_extra(V, bw)
    for S in 'RL':
        an = H('foot' + S)
        near = (np.abs(V[:, 0] - an[0]) < 0.09) & (V[:, 1] < an[1] + 0.06)
        if not near.any():
            continue
        fi, si_, ti = BONES.index('foot' + S), BONES.index('shin' + S), BONES.index('thigh' + S)
        ab = ankle_blend(V, S)
        tot = bw[:, fi] + bw[:, si_] + bw[:, ti]
        bw[near, fi] = (tot * (1 - ab))[near]; bw[near, si_] = (tot * ab)[near]; bw[near, ti] = 0
    return bw


def neck_extra(V, bw):
    """Neck skin hands over to the chest gradually above the collarbones, so turning the head never folds the neck
    skin through the collarbones or into the shirt collar."""
    ci, ni = BONES.index('chest'), BONES.index('neck')
    tot = bw[:, ci] + bw[:, ni]
    k = np.clip((V[:, 1] - (HIP[1] + 0.5)) / 0.07, 0, 1)
    k = k * k * (3 - 2 * k)
    bw[:, ni] = tot * k; bw[:, ci] = tot * (1 - k)
    return bw


ONLY = set(filter(None, os.environ.get('ONLY', '').split(',')))


def want(n):
    return not ONLY or any(n.startswith(o) for o in ONLY)


CLOTH_GROUPS = {'torso', 'armR', 'armL', 'legR', 'legL'}           # every clothing layer takes weights from the same body


def main():
    pieces = {}
    t0 = time.time()
    # head + neck: skull and face, then carved socket/mouth opening; eyelids are part of the skin
    def head_slab(xs, y, zs):
        d = smin(group_vol({'head'}, xs, y, zs), group_vol({'torso'}, xs, y, zs, skip=set()), 0.02)
        P = grid_pts(xs, y, zs)
        mouth = Mass('m', 'head', 'x', 'ell', (v(0, MOUTH_Y, MOUTH_Z - 0.012), v(0.0235, 0.0009, 0.03), None)).sd(P)
        d = smax(d, -mouth, 0.002)
        return d
    m = mesh_slabs(head_slab, (-0.105, 1.37, -0.135), (0.105, 1.77, 0.12), 0.001, 'head')
    m = keep_faces(m, m.vertices[:, 1] > 1.385) if m is not None else None
    pieces['skin_head'] = (decimate(m, 64000, 0.001), {'head', 'torso'}, lambda V, bw: brow_extra(V, jaw_extra(V, neck_extra(V, spine_extra(V, bw)))))
    # hair: a cap over the skull with a real hairline (temples recede, sideburns, nape), parted tufts
    skull = [m for m in MASSES if m.name in ('cranium', 'parietal', 'forehead')]
    TH = np.array([0, 0.4, 0.62, 0.9, 1.2, 1.4, 1.55, 1.95, 2.25, np.pi])
    LY = np.array([0.086, 0.083, 0.07, 0.06, 0.042, -0.006, 0.027, 0.027, -0.03, -0.074])

    def hair_slab(xs, y, zs):
        """A shell over the skull: thick on top, thin at the sides, thinning out to nothing at a real hairline
        (temples recede, sideburns, clears the ears, down to the nape); combed strands as shallow grooves."""
        P = grid_pts(xs, y, zs)
        sk = np.full(P.shape[:-1], BIG)
        for m in skull:
            sk = smin(sk, m.sd(P), m.k)
        q = P - (HC + v(0, 0.02, 0.01))
        th = np.abs(np.arctan2(q[..., 0], -q[..., 2]))
        line = HC[1] + np.interp(th, TH, LY)
        up = np.clip(q[..., 1] / 0.09, 0, 1)
        thick = (0.0055 + 0.0075 * up) * np.clip((y - line) / 0.016, 0.12, 1.0)
        az = np.arctan2(q[..., 0], q[..., 1] + 0.12)                                 # strands combed back and down
        thick *= 1 + 0.1 * np.sin(az * 90 + 0.8 * np.sin(q[..., 2] * 60)) + 0.05 * np.sin(az * 37)
        d = sk - thick
        d = np.maximum(d, line - y)
        d = np.maximum(d, -group_pts({'head'}, P, skip={m.name for m in MASSES if m.name.startswith(('helix', 'antihelix', 'earPlate', 'earLobe', 'concha', 'tragus'))}))
        return d
    m = mesh_slabs(hair_slab, (-0.1, 1.6, -0.115), (0.1, 1.77, 0.12), 0.0015, 'hair')
    pieces['hair'] = (decimate(m, 16000, 0.0015), {'head'}, None)
    # arms (skin below the sleeve) and hands
    for s, S in ((1, 'R'), (-1, 'L')):
        sh, el = H('uarm' + S), H('farm' + S)
        au = nrm(el - sh); cut = sh + au * 0.11
        def arm_slab(xs, y, zs, S=S, cut=cut, au=au):
            d = group_vol({'arm' + S}, xs, y, zs)
            return np.maximum(d, -((grid_pts(xs, y, zs) - cut) @ au))
        lo = np.minimum(sh, H('hand' + S)) - 0.07; hi = np.maximum(sh, H('hand' + S)) + 0.07
        m = mesh_slabs(arm_slab, lo, hi, 0.0022, 'arm' + S)
        pieces['skin_arm' + S] = (decimate(m, 14000, 0.0022), {'arm' + S}, None)
        hb = [b for b in BONES if b.endswith(S) and (b.startswith(('index', 'middle', 'ring', 'pinky', 'thumb', 'hand')))]
        pts = np.array([H(b) for b in hb] + [T(b) for b in hb] + [H('hand' + S) - HAND[S]['u'] * 0.06])
        m = mesh_slabs(lambda xs, y, zs, S=S: group_vol({'hand' + S}, xs, y, zs), pts.min(0) - 0.025, pts.max(0) + 0.025, 0.0011, 'hand' + S)
        pieces['skin_hand' + S] = (decimate(m, 14000, 0.0011), {'hand' + S, 'arm' + S}, None)
    # shirt: drapes over the torso (fabric bridges small forms), folds at the armpit and waist, hems and seams
    def shirt_slab(xs, y, zs):
        P = grid_pts(xs, y, zs)
        small = {'neck', 'adamsApple', 'scmR', 'scmL', 'abs', 'iliacR', 'iliacL', 'trapMid'} | {f'{n}{S}' for n in ('serratus0', 'serratus1', 'serratus2', 'scapula', 'erector', 'oblique', 'lat') for S in 'RL'}
        body = group_vol({'torso'}, xs, y, zs, skip=small, kmin=0.05, adds_only=True)
        exact = group_vol({'torso'}, xs, y, zs, skip={'neck', 'adamsApple', 'scmR', 'scmL'}, adds_only=True)
        d = smin(body - 0.011, exact - 0.007, 0.012)                                  # drapes smooth, but never inside the body
        # below the chest the cloth hangs straight down from the pecs and shoulder blades instead of following the waist
        Xs, Zs = np.meshgrid(xs, zs, indexing='ij')
        hang = np.clip((HIP[1] + 0.42 + 0.06 * np.clip(Zs / 0.06, 0, 1) - y) / 0.16, 0, 1)     # hangs from the shoulder blades at the back
        lo_ = np.clip((HIP[1] + 0.12 - y) / 0.16, 0, 1)
        a = 0.147 + 0.026 * lo_; b = 0.108 + 0.012 * lo_
        tube = (np.sqrt((Xs / a) ** 2 + ((Zs - 0.008) / b) ** 2) - 1.0) * 0.11
        d = np.where(hang > 0, smin(d, tube + (1 - hang) * 0.04, 0.065), d)
        for s, S in ((1, 'R'), (-1, 'L')):
            sh, el = H('uarm' + S), H('farm' + S)
            au = nrm(el - sh); cut = sh + au * 0.15
            arm = group_vol({'arm' + S}, xs, y, zs) - 0.012
            arm = np.maximum(arm, (P - cut) @ au)
            hem = np.abs((P - cut) @ au + 0.006) - 0.006
            d = smin(d, arm, 0.035)
            d = smin(d, np.maximum(arm - 0.0025, hem), 0.003)                       # sleeve hem band
        d -= 0.0016 * fold_noise(P, 120, 3) * np.clip((HIP[1] + 0.2 - y) / 0.2, 0, 1)   # soft folds bunching at the waist
        if y < HIP[1] + 0.08:                                                          # the hem always clears the jeans
            ramp = 0.03 * np.clip((y - (HIP[1] + 0.0)) / 0.08, 0, 1)                    # fades in smoothly toward the hem
            d = smin(d, smax(jeans_core(xs, y, zs) - 0.013 + ramp, (HIP[1] - 0.045) - y, 0.004), 0.03)
        d = np.maximum(d, (HIP[1] - 0.045) - y)
        outer = d
        # crew neck: an oval hole (lower in front) cut through a thin cloth shell, edged with a ribbed band
        Xs, Zs = np.meshgrid(xs, zs, indexing='ij')
        rz = np.where(Zs < 0.012, 0.071, 0.06)
        cyl = (np.sqrt((Xs / 0.074) ** 2 + ((Zs - 0.012) / rz) ** 2) - 1.0) * 0.066
        neckY = HIP[1] + 0.492 + 0.22 * (Zs - 0.012) + 0.7 * np.maximum(cyl, 0)            # the neckline: lower in front
        hole = np.minimum(np.maximum(cyl, HIP[1] + 0.462 - y), neckY - y)
        band = np.maximum(np.abs(hole + 0.0045) - 0.0045, outer - 0.0028)
        d = smin(np.maximum(d, -hole), band, 0.002)
        hemB = np.maximum(outer - 0.002, np.abs(y - (HIP[1] - 0.038)) - 0.007)          # bottom hem band
        d = smin(d, hemB, 0.002)
        return np.maximum(d, -(outer + 0.0055)) if y > HIP[1] + 0.38 else d            # hollow near the neck opening: 5 mm of cloth
    m = mesh_slabs(shirt_slab, (-0.34, 0.86, -0.17), (0.34, 1.5, 0.17), 0.0025, 'shirt')
    pieces['shirt'] = (decimate(m, 22000, 0.0025), CLOTH_GROUPS, cloth_extra)
    # jeans: waistband, belt loops, back pockets, outseams, knee and ankle folds, cuffs
    def jeans_slab(xs, y, zs):
        P = grid_pts(xs, y, zs)
        d = jeans_core(xs, y, zs)
        for s in (1, -1):
            kn = H('shin' + ('R' if s == 1 else 'L'))
            near = np.exp(-((P - (kn + v(0, 0, 0.03))) ** 2).sum(-1) / 0.004)
            d -= 0.003 * np.sin(P[..., 1] * 260 + s) * near                            # folds behind the knee
            d -= 0.002 * np.sin(P[..., 1] * 220) * np.clip((0.2 - y) / 0.08, 0, 1)     # stacking at the ankle
            seam = Mass('s', 'x', 'x', 'cone', (v(0.155 * s, HIP[1] + 0.03, 0.0), kn + v(0.055 * s, 0, 0.0), 0.0022, 0.0022)).sd(P)
            d = smin(d, np.maximum(seam, d - 0.0018), 0.002)
            pk = Mass('p', 'x', 'x', 'ell', (HIP + v(0.07 * s, -0.045, 0.118), v(0.05, 0.055, 0.01), None)).sd(P)
            d = smin(d, np.maximum(pk, d - 0.0022), 0.002)                          # back pockets
        d = np.maximum(d, y - (HIP[1] + 0.04))
        wb = np.maximum(d - 0.0035, np.abs(y - (HIP[1] + 0.025)) - 0.016)                # waistband
        for ang in (-0.9, -0.3, 0.3, 0.9, 3.14):
            loop = Mass('l', 'x', 'x', 'ell', (HIP + v(math.sin(ang) * 0.155, 0.02, -math.cos(ang) * 0.11), v(0.006, 0.022, 0.004), None)).sd(P)
            wb = smin(wb, np.maximum(loop, -(d - 0.0045)), 0.002)
        d = smin(d, wb, 0.003)
        cuff = np.maximum(d - 0.0025, np.abs(y - (JEANS_HEM + 0.01)) - 0.01)
        d = smin(d, cuff, 0.003)
        return np.maximum(d, JEANS_HEM - y)
    m = mesh_slabs(jeans_slab, (-0.24, 0.1, -0.16), (0.24, 1.0, 0.16), 0.0026, 'jeans')
    pieces['jeans'] = (decimate(m, 22000, 0.0026), CLOTH_GROUPS, cloth_extra)
    # shoes: upper with a toe box and collar, laces, two-tone sole
    for s, S in ((1, 'R'), (-1, 'L')):
        an = H('foot' + S)
        def upper_slab(xs, y, zs, an=an):
            P = grid_pts(xs, y, zs)
            d = shoe_upper_sd(P, an)
            for j in range(4):                                                         # lace rows
                lace = Mass('x', 'x', 'x', 'cone', (an + v(-0.018, -0.0 - 0.012 * j, -0.06 - 0.02 * j), an + v(0.018, -0.0 - 0.012 * j, -0.06 - 0.02 * j), 0.003, 0.003)).sd(P)
                d = smin(d, lace, 0.002)
            return np.maximum(d, (an[1] - 0.088) - y)
        m = mesh_slabs(upper_slab, an + v(-0.08, -0.11, -0.21), an + v(0.08, 0.06, 0.1), 0.0022, 'shoe' + S)
        pieces['shoe' + S] = (decimate(m, 7000, 0.0022), None, None)
        def sole_slab(xs, y, zs, an=an):
            P = grid_pts(xs, y, zs)
            d = Mass('s', 'x', 'x', 'ell', (an + v(0, -0.09, -0.05), v(0.053, 0.02, 0.138), None)).sd(P)
            return np.maximum(np.maximum(d, -y), y - (an[1] - 0.074))
        m = mesh_slabs(sole_slab, an + v(-0.07, -0.12, -0.2), an + v(0.07, -0.06, 0.1), 0.002, 'sole' + S)
        pieces['sole' + S] = (decimate(m, 3000, 0.002), None, None)
    # ---- export
    manifest = dict(bones=[dict(name=n, parent=B[n]['parent'], head=B[n]['head'].tolist(), tail=B[n]['tail'].tolist()) for n in BONES],
                    eyes={S: EYE[S].tolist() for S in 'RL'}, eyeR=EYE_R, mouthY=float(MOUTH_Y), mouthZ=MOUTH_Z, headC=HC.tolist(),
                    hands={S: {k: HAND[S][k].tolist() for k in 'unw'} for S in 'RL'},
                    lips=[[m.prm[0].tolist(), m.prm[1].tolist()] for m in MASSES if m.name.startswith(('lipUpper', 'lipLower', 'lipTubercle'))],
                    nails={f'{f}{S}': (T(f'{f}2{S}') - nrm(T(f'{f}2{S}') - H(f'{f}1{S}')) * 0.009 - HAND[S]['n'] * 0.0062).tolist()
                           for S in 'RL' for f in ('index', 'middle', 'ring', 'pinky')},
                    meshes=[])
    blob = bytearray()
    for name, (m, groups, extra) in pieces.items():
        if m is None:
            continue
        V = np.asarray(m.vertices, np.float64)
        if name.startswith(('shoe', 'sole')):
            S = name[-1]
            si = np.zeros((len(V), 4), np.uint16); sw = np.zeros((len(V), 4), np.float32)
            ab = ankle_blend(V, S)
            si[:, 0] = BONES.index('foot' + S); si[:, 1] = BONES.index('shin' + S); sw[:, 0] = 1 - ab; sw[:, 1] = ab
        elif name == 'hair':
            si = np.full((len(V), 4), BONES.index('head'), np.uint16); sw = np.zeros((len(V), 4), np.float32); sw[:, 0] = 1
        else:
            si, sw = weights(V, groups, extra)
        F = np.asarray(m.faces, np.uint32)
        ent = dict(name=name, nv=len(V), nf=len(F))
        arrs = [('pos', V.astype(np.float32)), ('idx', F), ('si', si), ('sw', sw)]
        if name == 'skin_head':
            arrs.append(('col', np.concatenate([face_colors(V), np.full((len(V), 1), 255, np.uint8)], 1)))
        for key, arr in arrs:
            while len(blob) % 4:
                blob.append(0)
            ent[key] = len(blob); blob += arr.tobytes()
        manifest['meshes'].append(ent)
        print(f'{name}: {len(V)} verts {len(F)} tris', flush=True)
    open(os.path.join(OUT, 'guy.bin'), 'wb').write(bytes(blob))
    json.dump(manifest, open(os.path.join(OUT, 'guy.json'), 'w'))
    print(f'done in {time.time() - t0:.0f}s, {len(blob) / 1e6:.1f} MB, {len(MASSES)} masses')


if __name__ == '__main__':
    main()
