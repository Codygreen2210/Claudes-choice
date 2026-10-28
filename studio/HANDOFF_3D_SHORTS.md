# Handoff: hektiqminds 3D Shorts (paste this into the new chat)

You are picking up work from another Claude session. Read this whole file first, then read `studio/SHORTS_HANDOFF.md` and `studio/RIGGING.md` in the repo.

## 1. The owner and the rules (follow these exactly)

- Faceless YouTube Shorts channel, "Zack D Films" style (how-it-works / survival / body facts, 3D guy, x-ray cutaways, captions, loops). Posting is through Metricool, brand "hektiqminds" (blogId 7119923, timezone America/Chicago).
- Replies: short, plain, blue-collar. No jargon dumps.
- **Ask before big or expensive choices.**
- **Never delete anything in connected apps.**
- **Spend no Runway or ElevenLabs credits.** Voice, sound and picture all come from our own code ("our own advancements").
- YouTube-safe content; every fact checked against real sources, with sources listed.
- Fix flaws in the system itself and log each lesson in `studio/SHORTS_HANDOFF.md` (Lessons log, newest first).
- **Don't make low-res previews. Render the full video and check it yourself before sending.**
- The owner judges motion hard: no clipping, hands must really hold things, joints must move like a human's ("if a human can't bend like that, neither should the rig").

## 2. Where everything is

- Repo: `github.com/Codygreen2210/Claudes-choice`
  - Branch **`studio/animate`**: all committed work (latest `199db0a`, moldy bread with the human-limit arm rig).
  - Branch **`studio/face-wip`** (`75057a5`): the newer mid-20s face and hair. The avalanche and moldy-bread Shorts were rendered with this face. **Not yet reviewed by the owner.** To render with the same guy as those Shorts, use this branch's `character.py`, `mh_head.py`, `assets/mh_head_mesh.npz` and `guy3d.js`.
  - **Never commit** these uncommitted files: `studio/toon/shorts/lava.py`, `voice/say.json`, `senses/mix.listen.*`, and the lava hunks in `body_sound.py`. They belong to a paused lava v4. Stage only your own changes; use `git hash-object -w` + `git update-index --cacheinfo` when a file mixes both.
- Old session layout (rebuild this in the new session):
  - `~/vt/samples` = working copy of `studio/samples`.
  - `~/vt/kit` = the sound kit (STUDIO_ROOT).
  - `~/vt/v` = the voice model and `beer_ref.wav`.
  - Work dirs: `~/vt/n<GEN>/<name>`.
  - `studio/setup_shorts.sh` and SHORTS_HANDOFF section 5 describe setup.
  - The exact rigs used in the recent Shorts are committed (force-added past .gitignore) on `studio/animate`: `samples/web/char/guy.bin`, `guy.json` (the guy) and `dog.json` (the golden retriever). Use these as-is so every video has the same guy; don't rebuild them unless the owner asks for a new look.
- Finished videos (in the old session only, not in the repo): `avalanche.mp4`, `moldy-bread.mp4`, `quicksand.mp4`, plus earlier 2D ones. Ask the owner to re-upload them if needed.

## 3. The 3D pipeline (short version; details in SHORTS_HANDOFF 6b)

**The character**
- `samples/char/character.py` sculpts the guy in code: SDF masses, lofted body segments fitted to real male measurements, clothes layered so nothing clips. It builds `web/char/guy.bin` + `guy.json`; the build takes about 75 s: `python3 character.py ../web/char`.
- `ONLY=shirt` builds one piece quickly; `merge_piece.py` swaps it into a full build.
- `measure.py` checks body girths against real adult-male averages (all within 5%).

**The rig and loader**
- `web/guy3d.js` loads the guy with dual-quaternion skinning, twist bones, face morphs, leg IK, hair cards, and sleeve/glove material options.

**A Short is**
- One scene file (`web/quick.js` quicksand, `web/av.js` avalanche, `web/mold.js` moldy bread) plus `web/<x>.html`.
- Its data folder `web/<x>/` holds `times.json`, `lines.json`, and `finish.json` (hook word, yellow/red labels).

**Steps for a new Short**
1. Write `lines.json`. Make the voice: `python3 studio/voice/narrate_short.py ~/vt/v ~/vt/v/beer_ref.wav $d --lines $d/lines.json` (local, free).
2. Copy `times.json` and `lines.json` into `web/<x>/`. Build the scene with one shot per narration line; beat 9 must loop into beat 0.
3. Debug stills: `PAGE=<x>.html node web/avpose.mjs out.png t [poseOverride] [camera]`, or `PAGE=<x>.html QS="&ao=0" node web/qstills.mjs prefix t1,t2,...`.
4. Hand and arm check: `node web/wristscan.mjs <x>.html` reports per beat how far each hold had to compromise. A high cost means fix the scene, never the limits.
5. Sound: add an `elif name == '<x>':` section in `studio/toon/shorts/body_sound.py`, plus key/reveal entries. Then run `STUDIO_ROOT=~/vt/kit python3 body_sound.py <x> times.json narration.wav mix.wav`, then `senses/listen.py mix.wav > ears.txt`.
6. Final render (about 45 min, chunked, auto-retry): `PAGE=<x>.html TD=web/<x> CFG=web/<x>/finish.json bash studio/samples/qs_render.sh $d`. Then run `python3 studio/toon/shorts/check.py $d` (voice spread ≤ 2.5 dB, loop seam < 15). Look at a frame tile of the whole video before sending.
7. Add the Short to `studio/toon/series.json`, commit to `studio/animate`, and send the mp4 with a title and description.

**Traps**
- Never `pkill -f <pattern>` when the pattern is in your own command (it kills your shell); kill by PID.
- JS rejects `-(x) ** 2`; write `-((x) ** 2)`.
- `G.untwist()` is not idempotent; use `untwistSafe()` (in mold.js).

## 4. Status of each piece of work

**Done**
- **Anatomy pass:** body lofted to real girths, muscles as relief, face landmarks. See `studio/ANATOMY.md`.
- **Quicksand Short:** finished.
- **Avalanche Short:** finished (`avalanche.mp4`). Facts checked:
  - Utah and Shasta avalanche centers: 80 mph, 9 in 10 victims trigger the slide, swim, hand up, air pocket, sets like concrete, 93% survive if dug out within 15 min, spit trick is a myth.
  - Haegeli et al., CMAJ 2011: survival vs burial time.
  - Title given: "How to Survive an Avalanche 🏂❄️". Not scheduled yet.
- **Moldy bread Short:** `moldy-bread.mp4` rendered from commit `199db0a`. Facts:
  - USDA FSIS: mold threads go deep into bread, throw bread out instead of cutting the mold off, don't sniff it.
  - Cornell / Penn State food scientists via NBC: stomach acid breaks mold down, healthy people are usually fine, mycotoxins, allergy and weak-immune risk.
  - Title given: "What Happens If You Eat Moldy Bread 🍞🦠".

**Fixed (render running at handoff time): arm flailing**
- `armSolve` now warm-starts from the previous frame with a continuity cost; the full multi-seed search runs only when a hold starts.
- A frame that doesn't follow the last one replays its beat from the start, so chunked renders match a straight render.
- Beat 9 eases the arm into the loop's first-frame pose (loop seam 0.1°).
- Check: `node web/armjerk.mjs mold.html` shows the biggest per-frame joint jump per beat (all ≤ 9°/frame).
- If the session ended before delivery: re-render with qs_render.sh, check it, and send it.
- Arm limits in use (keep them): shoulder forward raise -50..170, side raise -25..170, upper-arm roll ±60; elbow hinge 0..145; forearm roll ±80; wrist bend -65..70, side bend ±25; no elbow or forearm inside the trunk; elbows not above the shoulder.
- Grips: the hand is solved first, then the prop is placed in the hand (`holdProp` / `propFromHand`).
- When he holds food up to eat, the back of the hand (knuckles) faces the camera: grip `SLICE_GRIPS[5]`.

**Still open from the owner**
- Small leftovers he was told about:
  - A seam where the wrist mesh meets the hand mesh, visible in close-ups.
  - A dark gap at the armpit when the arm is raised (shirt mesh).
  - The x-ray "ghost" body looks slightly boxy.
- Offered, not answered: schedule the avalanche and moldy-bread Shorts on Metricool. Ask for days and times first.
- He also asked earlier for the face and hair to look like a real man in his mid 20s. That work is on `studio/face-wip`; show it to him before merging.
- Lava v4 is paused. Don't touch its files.
