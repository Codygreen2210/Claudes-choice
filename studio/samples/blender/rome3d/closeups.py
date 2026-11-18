# Close-ups of every contact, aimed from the scene's own maths: each hauler's hands on his rope, the water man's hands on the jar,
# feet on the sand/deck, and kilts from the side.   python3 closeups.py OUTDIR FRAME[,FRAME..] [--scale 0.4]
import sys, os
here = os.path.dirname(os.path.abspath(__file__)); out = sys.argv[1]; frames = [int(x) for x in sys.argv[2].split(',')]
sc = sys.argv[sys.argv.index('--scale') + 1] if '--scale' in sys.argv else '0.4'
src = open(os.path.join(here, 'pyr3d.py')).read(); src = src[:src.index("if __name__ == '__main__':")]
sys.argv = ['pyr3d.py', '/tmp/x', '0', '1', '--samples', '10', '--scale', sc]
g = {'__file__': os.path.join(here, 'pyr3d.py'), '__name__': 'chk'}; exec(compile(src, 'pyr3d.py', 'exec'), g)
import bpy
from mathutils import Vector
S = bpy.context.scene; os.makedirs(out, exist_ok=True)
S.render.resolution_x = int(S.render.resolution_x * 1.0); S.render.resolution_y = int(S.render.resolution_x)
for f in frames:
    g['frame'](f); bpy.context.view_layer.update()
    shots = []
    for m_ in g['HAUL'][::3] + [g['WATERMAN']]:
        for s_ in ('R', 'L'):
            p = m_.palm(s_); side = m_.right() * (1 if s_ == 'R' else -1)
            shots.append((f'{m_.root.name}_{s_}', p + side * 0.45 + m_.fwd() * 0.25 + Vector((0, 0, 0.12)), p))
        hip = m_.bone('root'); shots.append((f'{m_.root.name}_kilt', hip + m_.right() * 1.1 - Vector((0, 0, 0.15)), hip - Vector((0, 0, 0.12))))
        ft = (m_.bone('foot.L') + m_.bone('foot.R')) / 2; shots.append((f'{m_.root.name}_feet', ft + m_.right() * 0.7 + m_.fwd() * 0.4 + Vector((0, 0, 0.25)), ft - Vector((0, 0, 0.05))))
    for nm, cp, ct in shots:
        g['look'](cp, ct, 45 if 'kilt' in nm else 55, 16.0)
        S.render.filepath = os.path.join(out, f'{f:05d}_{nm}.png'); bpy.ops.render.render(write_still=True)
    print('frame', f, len(shots), 'shots', flush=True)
