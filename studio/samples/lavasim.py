"""Lava-lake crust simulation (ours).  Crust thickness h in [0,1] on a 512^2 grid over 80 m.
Convection cells (moving up-wellings/down-wellings + curl noise) carry rigid-ish plates (semi-Lagrangian
advection); spreading zones stretch and tear the crust (glowing seams); crust re-cools; fountains punch holes.
Writes N frames as uint8 (255 = thick cold crust) to web/lava.bin, frames sampled in *action time*."""
import sys, math
import numpy as np
import cv2

R = 512
L = 80.0                   # metres across
DX = L / R
FPS = 30
N = 150
SUB = 4                    # sim steps per frame
rng = np.random.default_rng(21)

y, x = np.mgrid[0:R, 0:R].astype(np.float32)
X, Y = (x + 0.5) * DX - L / 2, (y + 0.5) * DX - L / 2


def vnoise(cell, seed):
    r = np.random.default_rng(seed)
    g = r.random((int(R / cell) + 3, int(R / cell) + 3)).astype(np.float32)
    return cv2.resize(g, (g.shape[1] * cell, g.shape[0] * cell), interpolation=cv2.INTER_CUBIC)[:R, :R]


def voronoi_edge(n_cells, seed):
    """Distance (m) from each point to the nearest plate seam of a warped Voronoi diagram."""
    r = np.random.default_rng(seed)
    pts = r.uniform(-L / 2 - 5, L / 2 + 5, (n_cells, 2)).astype(np.float32)
    wx = (vnoise(40, seed + 1) - 0.5) * 2.2; wy = (vnoise(40, seed + 2) - 0.5) * 2.2
    XX, YY = X + wx, Y + wy
    d1 = np.full((R, R), 1e9, np.float32); d2 = np.full((R, R), 1e9, np.float32)
    for px, py in pts:
        d = np.sqrt((XX - px) ** 2 + (YY - py) ** 2)
        m = d < d1
        d2 = np.where(m, d1, np.minimum(d2, d)); d1 = np.where(m, d, d1)
    return (d2 - d1) * 0.5


class Cells:
    def __init__(self):
        self.src = []
        for i in range(9):
            self.src.append(dict(p=rng.uniform(-30, 30, 2), v=rng.normal(0, 0.15, 2), a=rng.choice([1.0, 1.0, -0.8]) * rng.uniform(0.6, 1.2), s=rng.uniform(5, 10), ang=rng.uniform(0, math.pi)))

    def vel(self, t):
        u = np.zeros((R, R), np.float32); w = np.zeros((R, R), np.float32)
        for c in self.src:
            p = c['p'] + c['v'] * t
            dx, dy = X - float(p[0]), Y - float(p[1])            # python floats keep the maths in float32
            ca, sa = math.cos(c['ang']), math.sin(c['ang'])
            along, across = dx * ca + dy * sa, -dx * sa + dy * ca
            ia, ib = 1.0 / (c['s'] * 2.2) ** 2, 1.0 / (c['s'] * 0.5) ** 2
            g = np.exp(-(along * along * ia + across * across * ib))
            # potential flow from a Gaussian bump: outward for up-wellings, inward for sinks
            k = float(c['a'] / c['s'] * 1.6)
            g *= k
            u += dx * g
            w += dy * g
        # curl noise: swirls (constant in time: built once)
        if not hasattr(self, 'curl'):
            psi = (vnoise(96, 7) - 0.5) * 18 + (vnoise(48, 8) - 0.5) * 6
            gy, gx = np.gradient(psi, DX)
            self.curl = ((gy * 0.2).astype(np.float32), (gx * 0.2).astype(np.float32))
        u += self.curl[0]; w -= self.curl[1]
        return u, w


def advect(f, u, w, dt):
    mx = (x - u * dt / DX).astype(np.float32)
    my = (y - w * dt / DX).astype(np.float32)
    return cv2.remap(f, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def main(out='web/lava.bin', action_times=None):
    E1 = voronoi_edge(160, 3)                    # big plates
    E2 = voronoi_edge(1100, 4)                   # fine contraction cracks
    cells = Cells()
    Mx, My = x.copy(), y.copy()                  # where the crust now at each pixel came from
    Sx = np.zeros((R, R), np.float32)            # accumulated stretching (opens the seams)
    sub = 2
    dt = 1 / (FPS * sub)
    T = -1.5
    fountains = []
    frames = []
    tgt = list(action_times if action_times is not None else [i / FPS for i in range(N)])
    k = 0
    def snap():
        e1 = cv2.remap(E1, Mx, My, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        e2 = cv2.remap(E2, Mx, My, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        w1 = 0.08 + Sx * 1.6                     # seam half-width grows with stretching
        h = np.clip((e1 - w1) / 0.25, 0, 1) ** 0.8
        h *= 0.55 + 0.45 * np.clip((e2 - 0.03) / 0.06, 0, 1)
        for f in fountains:
            age = T - f[1]
            if 0 <= age < 1.6:
                rr = f[2] * (0.5 + 0.6 * age)
                m = np.exp(-((X - f[0][0]) ** 2 + (Y - f[0][1]) ** 2) / (rr * rr))
                h *= 1 - 0.95 * m * (1 - age / 1.6) ** 0.7
        return np.clip(h * 255, 0, 255).astype(np.uint8)
    while k < len(tgt):
        u, w = cells.vel(T)
        mx = (x - u * dt / DX).astype(np.float32); my = (y - w * dt / DX).astype(np.float32)
        Mx = cv2.remap(Mx, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        My = cv2.remap(My, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        Sx = cv2.remap(Sx, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        div = np.gradient(u, DX, axis=1) + np.gradient(w, DX, axis=0)
        Sx += np.clip(div, 0, None) * dt * 0.9
        Sx *= math.exp(-0.25 * dt)               # rifts skin over again
        if rng.random() < 1.4 * dt:
            fountains.append([rng.uniform(-25, 25, 2), T, rng.uniform(0.5, 1.3)])
        fountains = [f for f in fountains if T - f[1] < 1.7]
        T += dt
        while k < len(tgt) and T >= tgt[k]:
            frames.append(snap()); k += 1
    arr = np.stack(frames)
    arr.tofile(out)
    cv2.imwrite('lava_sim_preview.png', np.hstack([arr[0], arr[len(arr) // 2], arr[-1]]))
    print('frames', len(frames), arr.shape, 'mean crust', arr.mean() / 255)


if __name__ == '__main__':
    import json
    at = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else None
    main(action_times=at)
