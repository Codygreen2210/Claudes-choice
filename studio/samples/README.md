# Style samples (lava slip, 5 s): three levels above the house 2D style

All of it is our own code: no outside AI services.

| Level | Picture | Sound | Build (5 s) |
|---|---|---|---|
| 1 hand-drawn | `l1/` jointed 2D skeleton, cel shading, boiling ink, painted backdrops, look-up tunnel shot | real foley, crater echo built from the pit size, ducking, wind tied to fall speed | ~80 s |
| 2 real 3D | `web/main.js?level=2` three.js crater, lava shader, 3D guy, lava light, 3 cameras | binaural placement (ITD, head shadow, pinna notch, distance, doppler) from exported camera paths | ~145 s |
| 3 cinematic | `web/main.js?level=3` + `lavasim.py` crust sim, slow-mo boot close-up, DOF, bloom, haze, GPU motion blur | original score, procedural rock/lava, slow-mo audio, multiband glue | ~325 s |

    cd web && npm install          # three + playwright-core (once)
    bash build_all.sh all          # or 1 / 2 / 3

3D character: `char/character.py` sculpts the guy in code (signed-distance masses: skull, jaw, cheeks, nose, ears, lips,
deltoids, biceps, calves, shirt, jeans, shoes, hair), meshes it (marching cubes, cleaned, smoothed, reduced to ~115k tris),
builds a 41-bone skeleton (3-bone spine, collarbones, fingers, jaw) and smooth skin weights from the same masses.
`web/guy3d.js` loads it with a face rig (jaw, blink, brows, eyes) and is driven by the limit-safe rig in `main.js`
(bone aim from the FK hinge axes, shoulder-blade shrug past 80 deg, spine curl, finger curl). Look at it alone:
`node web/charstills.mjs out front,q34,side,face`.

Renderer: headless Chromium on Mesa **llvmpipe** (`--use-gl=angle --use-angle=gl-egl`), ~3x faster than SwiftShader here.
Set `GL=swiftshader` to compare. Frames stream as raw RGBA from the page to `finish.py` (grade + captions + one encode).
`voice.wav` = first line of the lava narration (Kokoro).
