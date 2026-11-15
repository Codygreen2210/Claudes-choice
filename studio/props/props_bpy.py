"""Prop studio inside Blender (scene scripts). Uses props fetched with studio/props/props.py.
    sys.path.insert(0, '<repo>/studio/props'); import props_bpy as P
    P.hdri('ph:kloofendal_48d_partly_cloudy_puresky', strength=1.0, rot_deg=-70)     # sky + light + reflections
    chair = P.place('ph:wooden_stool_02', loc=(0, 0, 0), rot_deg=30, height=0.45)     # glTF prop, scaled to a real height (m)
    m = P.material('acg:Asphalt012', scale=2.0); obj.data.materials.append(m)       # photo PBR material (Poly Haven set or ambientCG)
    P.farm_files(['ph:wooden_stool_02', ...])  -> {cache file: repo path} for a Short's farm.sh
Looks for files in <scene dir>/assets/<id>/ first (what the farm gets), then the local cache /root/vt/assets/<id>/."""
import os, glob, math
import bpy
from mathutils import Vector
CACHE = os.environ.get('PROPS_CACHE', '/root/vt/assets')
_HERE = [None]
def set_scene_dir(d): _HERE[0] = d
def _dir(pid):
    aid = pid.split(':', 1)[-1]
    for root in ([os.path.join(_HERE[0], 'assets')] if _HERE[0] else []) + [CACHE]:
        p = os.path.join(root, aid)
        if os.path.isdir(p): return p
    raise FileNotFoundError(f'{pid} not fetched: python3 studio/props/props.py get {pid}')
def _one(d, *pats):
    for pt in pats:
        f = sorted(glob.glob(os.path.join(d, '**', pt), recursive=True))
        if f: return f[0]
    return None

def hdri(pid, strength=1.0, rot_deg=0.0, world=None):
    """the sky: lights the scene, shows in reflections and behind everything"""
    S = bpy.context.scene; W = world or S.world or bpy.data.worlds.new('world'); S.world = W; W.use_nodes = True; nt = W.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND'); env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(_one(_dir(pid), '*.hdr', '*.exr')); mp = nt.nodes.new('ShaderNodeMapping'); tc = nt.nodes.new('ShaderNodeTexCoord')
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(rot_deg))
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], env.inputs['Vector']); nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength; return env

def place(pid, loc=(0, 0, 0), rot_deg=0.0, height=None, scale=1.0, name=None, parent=None):
    """import a glTF prop once per call; returns an empty that holds its parts. height (m) rescales it to that real height;
    the prop is set down so its lowest point sits at loc.z and it is centred on loc in x/y."""
    f = _one(_dir(pid), '*.gltf', '*.glb', '*.fbx', '*.obj')
    if f is None: raise FileNotFoundError(f'no model file for {pid}')
    before = set(bpy.data.objects)
    if f.endswith(('.gltf', '.glb')): bpy.ops.import_scene.gltf(filepath=f)
    elif f.endswith('.fbx'): bpy.ops.import_scene.fbx(filepath=f)
    else: bpy.ops.wm.obj_import(filepath=f)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name or pid.split(':', 1)[-1], None); bpy.context.scene.collection.objects.link(root)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in new if o.type == 'MESH' for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    for o in new:
        if o.parent is None: mw = o.matrix_world.copy(); o.parent = root; o.matrix_world = mw
    s = (height / max(1e-6, hi.z - lo.z)) if height else scale
    for o in root.children: o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    root.scale = (s, s, s); root.location = loc; root.rotation_euler = (0, 0, math.radians(rot_deg))
    if parent: root.parent = parent
    root['size'] = tuple((hi - lo) * s); return root

def material(pid, scale=1.0, name=None, disp=0.0):
    """a photo PBR material from a texture set (colour, roughness, normal, AO/ARM, metal, optional displacement)"""
    d = _dir(pid); m = bpy.data.materials.new(name or pid.split(':', 1)[-1]); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs['UV'], mp.inputs['Vector'])
    def tex(pats, nc):
        f = _one(d, *pats)
        if not f: return None
        n = nt.nodes.new('ShaderNodeTexImage'); n.image = bpy.data.images.load(f); n.image.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
        nt.links.new(mp.outputs[0], n.inputs['Vector']); return n
    c = tex(['*_diff_*.*', '*_Color.*', '*_col_*.*', '*diffuse*.*'], False)
    if c: nt.links.new(c.outputs['Color'], b.inputs['Base Color'])
    r = tex(['*_rough_*.*', '*_Roughness.*'], True)
    if r: nt.links.new(r.outputs['Color'], b.inputs['Roughness'])
    mt = tex(['*_metal_*.*', '*_Metalness.*'], True)
    if mt: nt.links.new(mt.outputs['Color'], b.inputs['Metallic'])
    nmi = tex(['*_nor_gl_*.*', '*_NormalGL.*'], True)
    if nmi: nn = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(nmi.outputs['Color'], nn.inputs['Color']); nt.links.new(nn.outputs['Normal'], b.inputs['Normal'])
    if disp:
        dm = tex(['*_disp_*.*', '*_Displacement.*'], True)
        if dm:
            dn = nt.nodes.new('ShaderNodeDisplacement'); dn.inputs['Scale'].default_value = disp; nt.links.new(dm.outputs['Color'], dn.inputs['Height'])
            nt.links.new(dn.outputs[0], nt.nodes['Material Output'].inputs['Displacement']); m.displacement_method = 'BOTH'
    return m

def farm_files(ids, scene_rel):
    """{cache file: repo path under <scene_rel>/assets/<id>/} for every file of these props (feed it to git update-index)"""
    out = {}
    for pid in ids:
        aid = pid.split(':', 1)[-1]; d = os.path.join(CACHE, aid)
        for r, _, fs in os.walk(d):
            for f in fs: p = os.path.join(r, f); out[p] = os.path.join(scene_rel, 'assets', aid, os.path.relpath(p, d))
    return out
