# sneakers painted onto his feet (every face mostly weighted to the foot and toe bones), so nothing can clip through them
SHOE_M = noisy(mat('sneaker', (0.07, 0.07, 0.08), 0.6), 60.0, 0.15); SOLE_M = mat('sole', (0.85, 0.85, 0.82), 0.7)
BODY.data.materials.append(SHOE_M); BODY.data.materials.append(SOLE_M); _shoe_i = len(BODY.data.materials) - 2
_vgn = {g.index: g.name for g in BODY.vertex_groups}
_footw = np.zeros(len(BODY.data.vertices))
for v in BODY.data.vertices:
    _footw[v.index] = sum(g.weight for g in v.groups if _vgn[g.group].startswith(('foot.', 'toe')))
for p_ in BODY.data.polygons:
    w_ = float(np.mean([_footw[i] for i in p_.vertices]))
    if w_ > 0.45:
        zc = sum(BODY.data.vertices[i].co.z for i in p_.vertices) / len(p_.vertices)
        p_.material_index = _shoe_i + 1 if zc < 0.018 else _shoe_i
