
# ================================================================ people: simple rounded figures (seen small), each with hips/shoulders that swing
SKINS = [(0.80, 0.60, 0.46), (0.55, 0.36, 0.24), (0.36, 0.22, 0.14), (0.88, 0.70, 0.56), (0.66, 0.46, 0.32)]
SKIN_M = [mat(f'skin{i}', c, 0.55, sheen=0.2) for i, c in enumerate(SKINS)]
SHIRTS = [(0.15, 0.30, 0.60), (0.70, 0.70, 0.68), (0.55, 0.12, 0.12), (0.20, 0.45, 0.30), (0.85, 0.75, 0.40), (0.30, 0.30, 0.34), (0.60, 0.40, 0.65)]
SHIRT_M = [mat(f'shirt{i}', c, 0.85) for i, c in enumerate(SHIRTS)]
PANTS_M = [mat('pants0', (0.12, 0.13, 0.18), 0.85), mat('pants1', (0.45, 0.40, 0.32), 0.85), mat('pants2', (0.20, 0.20, 0.22), 0.85)]
HAIR_M = [mat('hair0', (0.05, 0.04, 0.03), 0.6), mat('hair1', (0.75, 0.75, 0.74), 0.6), mat('hair2', (0.35, 0.22, 0.12), 0.6)]
VEST_M = mat('lifevest', (1.0, 0.30, 0.02), 0.6)
VEST_STRIPE = mat('reflect', (0.9, 0.9, 0.9), 0.2, 0.6)
POLICE_M = mat('police', (0.05, 0.07, 0.16), 0.8)
CREW_M = mat('crewshirt', (0.92, 0.92, 0.92), 0.8)
BAG_M = [mat('bag0', (0.10, 0.10, 0.12), 0.5), mat('bag1', (0.45, 0.10, 0.10), 0.5), mat('bag2', (0.15, 0.25, 0.45), 0.5)]
PEOPLE = []
def figure(name, seed, kind='guest', parent=None, loc=(0, 0, 0), yaw=0.0, scale=1.0, vest=False, bag=False):
    r_ = random.Random(seed); root = empty(name, parent, loc); root.rotation_mode = 'XYZ'; root.rotation_euler = (0, 0, yaw); root.scale = (scale,) * 3
    skin = SKIN_M[r_.randrange(len(SKIN_M))]
    shirt = POLICE_M if kind == 'police' else CREW_M if kind == 'crew' else SHIRT_M[r_.randrange(len(SHIRT_M))]
    pants = POLICE_M if kind == 'police' else PANTS_M[r_.randrange(len(PANTS_M))]
    body = empty(name + '_body', root, (0, 0, 0.95)); body.rotation_mode = 'XYZ'
    prim('uv_sphere', name + '_torso', shirt, body, loc=(0, 0, 0.33), scale=(0.19, 0.13, 0.33), segments=14, ring_count=10)
    head = prim('uv_sphere', name + '_head', skin, body, loc=(0, 0, 0.80), scale=(0.11, 0.12, 0.13), segments=14, ring_count=10)
    prim('uv_sphere', name + '_hair', HAIR_M[r_.randrange(3)], body, loc=(-0.015, 0, 0.85), scale=(0.115, 0.125, 0.10), segments=12, ring_count=8)
    if kind == 'police': lathe(name + '_cap', [(0.13, 0), (0.13, 0.08), (0.0, 0.1)], 14, POLICE_M, body, loc=(0, 0, 0.88))
    if vest:
        prim('uv_sphere', name + '_vest', VEST_M, body, loc=(0, 0, 0.42), scale=(0.235, 0.18, 0.25), segments=14, ring_count=10)
        box(name + '_vstripe', (0.40, 0.33, 0.04), (0, 0, 0.42), VEST_STRIPE, parent=body)
    limbs = {}
    for side, sy in (('l', 1), ('r', -1)):
        hip = empty(f'{name}_hip{side}', root, (0, 0.09 * sy, 0.95)); hip.rotation_mode = 'XYZ'
        tube(f'{name}_leg{side}', [(0, 0, 0), (0, 0, -0.45), (0, 0, -0.9)], 0.075, pants, hip, seg=8)
        box(f'{name}_shoe{side}', (0.22, 0.09, 0.07), (0.05, 0, -0.92), HAIR_M[0], parent=hip)
        sh = empty(f'{name}_sh{side}', body, (0, 0.21 * sy, 0.58)); sh.rotation_mode = 'XYZ'
        tube(f'{name}_arm{side}', [(0, 0, 0), (0, 0, -0.3), (0.02, 0, -0.6)], 0.055, shirt, sh, seg=8)
        prim('uv_sphere', f'{name}_hand{side}', skin, sh, loc=(0.02, 0, -0.64), scale=(0.05, 0.04, 0.06), segments=8, ring_count=6)
        limbs[side] = (hip, sh)
    if bag:
        box(name + '_bag', (0.38, 0.22, 0.5), (0.05, -0.32, 0.28), BAG_M[r_.randrange(3)], bv=0.04, parent=root)
    p = dict(root=root, body=body, limbs=limbs, seed=seed, kind=kind); PEOPLE.append(p); return p
def pose(p, mode, t, phase=0.0):
    """stand / walk / run / brace / tread (in water) / jump (arms up, legs tucked) / climb"""
    root, body, L_ = p['root'], p['body'], p['limbs']; ph = phase + p['seed'] * 0.37
    sw = 0.0; arm = 0.0; lean = 0.0; spread = 0.0; armup = 0.0; bob = 0.0
    if mode == 'walk': sw = 0.45 * math.sin(2 * math.pi * 1.8 * t + ph); arm = -0.6 * sw; bob = 0.02 * abs(math.sin(2 * math.pi * 1.8 * t + ph))
    elif mode == 'run': sw = 0.85 * math.sin(2 * math.pi * 2.8 * t + ph); arm = -1.0 * sw; lean = 0.25; bob = 0.06 * abs(math.sin(2 * math.pi * 2.8 * t + ph))
    elif mode == 'brace': spread = 0.25; armup = 0.9 + 0.2 * math.sin(3 * t + ph); lean = -0.1
    elif mode == 'climb': sw = 0.5 * math.sin(2 * math.pi * 1.4 * t + ph); armup = 2.2 + 0.4 * math.sin(2 * math.pi * 1.4 * t + ph + 1); lean = 0.35
    elif mode == 'tread': sw = 0.5 * math.sin(2 * math.pi * 1.1 * t + ph); armup = 1.2 + 0.6 * math.sin(2 * math.pi * 1.1 * t + ph); spread = 0.5; bob = 0.06 * math.sin(2 * math.pi * 0.7 * t + ph)
    elif mode == 'jump': sw = 0.6; armup = 2.6; lean = 0.2
    elif mode == 'wave': armup = 2.6 + 0.3 * math.sin(2 * math.pi * 2 * t + ph)
    else: arm = 0.05 * math.sin(1.3 * t + ph)
    body.rotation_euler = (0, lean, 0); body.location.z = 0.95 + bob
    for side, sgn in (('l', 1), ('r', -1)):
        hip, sh = L_[side]
        hip.rotation_euler = (sgn * spread * 0.4, (sw if side == 'l' else -sw) * -1.0 + (0.9 if mode == 'jump' else 0), 0)
        sh.rotation_euler = (-sgn * (spread + 0.15 + (0.25 * armup if mode in ('tread', 'brace') else 0)), (arm if side == 'l' else -arm) - armup * (1 if mode != 'tread' else 0.5), 0)
def place(p, loc, yaw=None, roll=0.0):
    p['root'].location = loc
    if yaw is not None: p['root'].rotation_euler = (roll, 0, yaw)

# ---- the cast
# passengers waiting to get off (on the main-deck dock-side walkway and the gangway, with bags), at rest in the boat's frame
GUESTS = [figure(f'g{i}', 100 + i, parent=RBL, loc=(2 + 1.1 * i + 0.5 * h1(i), RB_CY + 7.2 - 0.4 * h1(i + 50), 1.5), yaw=math.pi + 0.3 * (h1(i + 9) - 0.5), bag=i % 2 == 0) for i in range(12)]
WALKERS = [figure(f'w{i}', 200 + i, loc=(8 + 0.5 * (i % 2), 22 + 1.6 * i, 3.4), yaw=math.pi / 2, bag=True) for i in range(5)]
CREW = figure('crew0', 7, 'crew', RBL, loc=(-6.5, RB_CY + 1.0, 1.5), yaw=0.2)
DINERS = [figure(f'd{i}', 300 + i, parent=RBL, loc=(-22 + 9 * i, RB_CY + 0.4 + 2.0 * (i % 2), 1.5), yaw=0.8 * i) for i in range(4)]
# on the high side with life jackets (deck 2 and 3, dock side), boat frame
HIGH = []
for i in range(26):
    lv = (1, 2)[i % 2]; z0 = LEVELS[lv][0]
    HIGH.append(figure(f'h{i}', 400 + i, parent=RBL, loc=(-30 + 2.3 * i + 0.6 * h1(i), RB_CY + 7.0, z0), yaw=math.pi / 2 + 0.4 * (h1(i + 2) - 0.5), vest=True))
# police running down the wharf (world)
POLICE = [figure(f'p{i}', 500 + i, 'police', loc=(60 + 6 * i, 28 + 2 * (i % 2), 3.4), yaw=math.pi) for i in range(5)]
# people in the river with life jackets, rescuers who jump in (world)
SWIM = [figure(f's{i}', 600 + i, loc=(-26 + 3.6 * i + 2 * h1(i), -6 - 9 * h1(i + 30), -1.1), yaw=h1(i + 60) * 6.28, vest=True) for i in range(14)]
RESC = [figure(f'r{i}', 700 + i, 'police' if i < 2 else 'guest', loc=(-8 + 10 * i, 22, 3.4), yaw=-math.pi / 2, vest=i >= 2) for i in range(4)]
for p in SWIM + RESC: p['root'].hide_render = True
def show_fig(p, on):
    stack = [p['root']]
    while stack:
        o = stack.pop(); o.hide_render = not on; stack.extend(o.children)
