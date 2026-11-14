# handchk.py: per frame, the left hand's skin against the stopwatch (shots 1-2): CLIP = skin inside the watch case,
# FLOAT = the watch's back sits more than 4 mm off the palm. Also a self-test: push the watch 3 mm into the palm, it must CLIP.
#   python3 handchk.py OUT 0 0 --frames 69-200   (CLOSE=dir also renders close-ups from 4 sides)
import sys, os
fr_arg = sys.argv[sys.argv.index('--frames') + 1]; del sys.argv[sys.argv.index('--frames'):sys.argv.index('--frames') + 2]
__file__ = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'sunz.py'); exec(open(__file__).read())
frames = []
for part in fr_arg.split(','):
    a_, b_ = (part.split('-') + [part])[:2]; frames += list(range(int(a_), int(b_) + 1))
hand_idx = np.where(_hd > 0.3)[0]
def check(f, push=0.0):
    frame(f)
    if SWATCH.hide_render or SW[0].hide_render: return None
    if push: SWATCH.location = SWATCH.location - SWATCH.rotation_quaternion.to_matrix().col[2] * push; bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); oe = BODY.evaluated_get(dg); me = oe.to_mesh()
    # the subsurf changes vertex order: test every evaluated vertex within 8 cm of the watch
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3); oe.to_mesh_clear()
    W = np.array(BODY.matrix_world); co = co @ W[:3, :3].T + W[:3, 3]
    M = np.array(SWATCH.matrix_world.inverted()); lc = co @ M[:3, :3].T + M[:3, 3]
    near = np.linalg.norm(lc, axis=1) < 0.08; lc = lc[near]
    r = np.hypot(lc[:, 0], lc[:, 1]); inside = (r < SW_R - 0.0005) & (np.abs(lc[:, 2]) < SW_T / 2)
    under = lc[(r < SW_R * 0.7) & (lc[:, 2] < 0)]; gap = (-SW_T / 2 - under[:, 2].max()) if len(under) else 9.9
    return int(inside.sum()), (float(inside.sum() and (SW_T / 2 - np.abs(lc[inside, 2])).max())), gap
bad = 0
for f in frames:
    r = check(f)
    if r is None: continue
    n, depth, gap = r; tag = 'CLIP' if depth > 0.0005 else ('FLOAT' if gap > 0.004 else 'ok')
    if tag != 'ok': bad += 1
    print(f'frame {f}: {tag} inside={n} depth={depth*1000:.1f}mm gap={gap*1000:.1f}mm', flush=True)
st = check(frames[0], push=0.003 + 0.004)
print('self-test (watch pushed into the palm):', 'fires' if st and st[0] > 0 else 'DID NOT FIRE', st)
print('handchk:', 'clean' if bad == 0 else f'{bad} bad frames')
# close-ups of the grip from four sides (plus the shot's own view) for the first frame listed
import os
od = os.environ.get('CLOSE', '')
if od:
    os.makedirs(od, exist_ok=True); f = frames[len(frames) // 2]; frame(f); CAM.animation_data_clear(); CAM.data.animation_data_clear()
    S.render.use_motion_blur = False; S.render.resolution_x, S.render.resolution_y = 540, 960
    S.render.filepath = f'{od}/grip_{f}_shot.png'; bpy.ops.render.render(write_still=True)
    c0 = SWATCH.matrix_world.translation.copy(); zax = SWATCH.matrix_world.to_3x3().col[2]; yax = SWATCH.matrix_world.to_3x3().col[1]; xax = zax.cross(yax)
    for nm, d_ in (('front', zax), ('side', xax * 0.8 + zax * 0.4), ('top', yax * 0.8 + zax * 0.3), ('back', -xax * 0.8 + zax * 0.2)):
        look(c0 + d_.normalized() * 0.16, c0, lens=50, fstop=16); S.render.filepath = f'{od}/grip_{f}_{nm}.png'; bpy.ops.render.render(write_still=True)
    print('close-ups in', od)
