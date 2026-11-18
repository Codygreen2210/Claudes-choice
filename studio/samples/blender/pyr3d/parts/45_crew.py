# ---------------------------------------------------------------- eight haulers in a V ahead of the sled (four rows of two), each on his own rope over
# the inner shoulder; the water man beside the sled, who climbs onto its front deck with the jar
TIE = {1: Vector((0.46, 0.98, 0.42)), -1: Vector((-0.46, 0.98, 0.42))}
HAUL = []
for k in range(4):
    for s_ in (1, -1):
        tone = (0.36 + 0.06 * h1(k * 2 + s_), 0.20 + 0.04 * h1(k * 3 + s_), 0.12 + 0.03 * h1(k + s_))
        m_ = Man(f'haul{k}{"r" if s_ > 0 else "l"}', tone)
        m_.row, m_.side = k, s_; m_.off = Vector((s_ * (0.50 + 0.46 * k), 2.35 + 1.05 * k, 0.0))
        m_.rope = Rope(f'rope{k}{s_}', 30, 0.016); m_.seed = k * 2.3 + s_ * 1.1; HAUL.append(m_)
WATERMAN = Man('waterman', (0.34, 0.19, 0.11))
