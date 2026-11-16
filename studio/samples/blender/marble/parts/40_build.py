# ================================================================ build the course
for mo in MARB: mo.visible_shadow = False          # the marble's own light shines out through its glass
LMK = build_course(M)
print('course built:', len(PHYS), 'collision parts,', len(PIECES), 'pieces')
LMK['floor_z'] = min(p_[2] for p_ in SAMPLES_ALL) - 1.2
