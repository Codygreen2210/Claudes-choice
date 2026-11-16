"""Race events from the baked physics + camera (cam.npz, dumped from marble.py): who leads, lead changes, finish order,
hits (marble on marble, marble on track), airborne spans, distance and pan to the camera. Shared by the sound and the overlay
so the leaderboard and the sounds land on the same frames.   from race import Race; R = Race('/root/vt/n50/marble/cam.npz')"""
import numpy as np
FPS = 30
NAMES = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'CYAN', 'BLUE', 'PURPLE', 'PINK']
COLS = [(255, 40, 30), (255, 130, 0), (255, 220, 30), (40, 240, 70), (0, 225, 255), (40, 90, 255), (170, 60, 255), (255, 60, 170)]
MR = 0.05

class Race:
    def __init__(self, path):
        d = np.load(path, allow_pickle=True)
        self.cpos, self.ctgt, self.pos, self.prog = d['cpos'], d['ctgt'], d['pos'], d['prog']
        self.piece = d['piece']; self.pnames = list(d['names']); self.fin = d['fin']; self.N = self.pos.shape[0]
        self.T = self.N / FPS; self.t_win = float(d['t_win']); self.t_last = float(d['t_last']); self.hoop = d['hoop']; self.kicks = d['kicks']
        p = self.pos; v = np.gradient(p, axis=0) * FPS; self.vel = v; self.speed = np.linalg.norm(v, axis=2)
        acc = np.gradient(v, axis=0) * FPS
        ff = np.array([0, 0, -9.81])[None, None, :] - 0.357 * v
        free = np.linalg.norm(acc - ff, axis=2) < 2.5
        air = free.copy()
        for k in range(1, 3): air &= np.roll(free, k, 0) | np.roll(free, -k, 0)
        self.air = air
        # finish order + places over time (by progress; finished marbles keep their finishing place)
        self.order_final = list(np.argsort(self.fin))
        rank = np.zeros((self.N, 8), int)
        for f in range(self.N):
            done = [i for i in self.order_final if self.fin[i] <= f]
            rest = [i for i in np.argsort(-self.prog[f]) if i not in done]
            for r, i in enumerate(done + rest): rank[f, i] = r
        self.rank = rank
        lead = [int(np.where(rank[f] == 0)[0][0]) for f in range(self.N)]
        self.lead_changes = []; cur = lead[0]
        for f in range(1, self.N):
            if lead[f] != cur and all(x == lead[f] for x in lead[f:f + 24]): self.lead_changes.append((f, lead[f])); cur = lead[f]
        self.lead = lead
        # hits: marble-marble (closing speed) and marble-track (sudden change in velocity, not explained by gravity)
        self.hits = []                                      # (frame, kind, strength, i, j)
        for i in range(8):
            for j in range(i + 1, 8):
                dd = np.linalg.norm(p[:, i] - p[:, j], axis=1); touch = dd < 2 * MR + 0.006
                rel = np.einsum('fk,fk->f', v[:, i] - v[:, j], (p[:, j] - p[:, i]) / np.maximum(dd, 1e-6)[:, None])
                for f in np.where(touch[1:] & ~touch[:-1])[0] + 1:
                    s = float(max(rel[f - 1], rel[max(f - 2, 0)], 0))
                    if s > 0.06: self.hits.append((f, 'mm', s, i, j))
        dv = np.linalg.norm(v[1:] - v[:-1] - ff[:-1] / FPS, axis=2)
        for i in range(8):
            x = dv[:, i]
            for f in range(1, len(x) - 1):
                if x[f] > 0.32 and x[f] >= x[f - 1] and x[f] >= x[f + 1]:
                    if any(h[0] in (f, f + 1) and h[1] == 'mm' and i in (h[3], h[4]) for h in self.hits[-40:]): continue
                    self.hits.append((f + 1, 'wall', float(x[f]), i, -1))
        self.hits.sort()
        # launches / landings for the three big jumps
        self.jumps = []
        for k, kp in enumerate(self.kicks):
            for i in range(8):
                near = np.where(np.linalg.norm(p[:, i] - kp, axis=1) < 0.25)[0]
                if not len(near): continue
                f0 = near[-1]; a = np.where(~self.air[f0:f0 + 45, i])[0]
                f1 = f0 + (a[a > 3][0] if len(a[a > 3]) else 20)
                self.jumps.append((k, i, int(f0), int(f1)))
    def cam_basis(self, f):
        c = self.cpos[f]; fw = self.ctgt[f] - c; fw /= np.linalg.norm(fw) + 1e-9
        rt = np.cross(fw, [0, 0, 1.0]); rt /= np.linalg.norm(rt) + 1e-9; return c, fw, rt
    def near(self, f, pt):
        """gain (0..1) and pan (-1..1) of a point for the camera at frame f"""
        f = int(np.clip(f, 0, self.N - 1)); c, fw, rt = self.cam_basis(f); d = pt - c; dist = np.linalg.norm(d)
        g = 1.0 / (1.0 + max(dist - 0.6, 0) / 1.4) ** 1.6; pan = float(np.clip(np.dot(d, rt) / (dist + 1e-6) * 1.4, -0.85, 0.85))
        return float(g), pan
