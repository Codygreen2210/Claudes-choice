# Shorts Studio Handoff

Everything a new Claude profile needs to make Shorts exactly the way this channel makes them: the 2D Zack D Films style, the same look, the same voice, the same checks and the same way of posting.

---

## 0. Paste this into the new profile to start

> Clone `https://github.com/Codygreen2210/Claudes-choice`, check out branch `studio/animate`, and read `studio/SHORTS_HANDOFF.md` top to bottom. Run `bash studio/setup_shorts.sh`. Then follow the handoff's rules and pipeline for every Short I ask for. Keep replies short. Every video comes with a title, a description and tags.

Connect these in the new profile (Settings → Connectors) to get the same reach:
- **Metricool**: scheduling and posting to YouTube. Brand "hektiqminds", blogId `7119923`, timezone `America/Chicago`.
- **Ubersuggest**: picking topics by search volume. The free plan allows 3 reports a day.

---

## 1. What the channel is

- **The 2D Zack D Films.** Animated, faceless, explain-it-in-40-seconds Shorts about the body, science and weird what-ifs.
- **Adults are the audience**, not kids. Gross or edgy topics are fine, but they must be YouTube-safe. Always post with `madeForKids: false`.
- **Growth plan:**
  1. Pick high-search, weak-competition topics (high volume and low SEO difficulty in Ubersuggest).
  2. Predict trends from seasons, holidays and news.
  3. Run a weekly trend scan (section 9).
- **Never rebuild a video once it's posted.** Take the lesson into a new Short instead.

## 2. Script rules (Zack D style)

Write 9 beats plus 1 loop line (10 lines in `lines.json`). That's about 35–45 seconds.

1. **Line 0 is: "You just [did the thing]. Here's what you do."** (owner, 2026-10-26). Second person puts the viewer inside it, and the promise of steps keeps them for the answer. Frame one shows the thing happening. The script then delivers real steps (sourced), in "you", with the why and the twist between them; the last line says the title ("And that's what to do when you ...").
   - Example: "You just filled your gas car with diesel. Here's what you do."
   - (Old rule, retired: a plain statement about "this man", never a question.)
2. **Each line after that is one short cause-and-effect step** that matches exactly one picture.
   - Example: "With his first big gulp, all that salt hits his blood."
3. **Build to a twist or a big-number reveal** around beat 6–7.
   - Example: "…it would still take over two hundred million years."
4. **The last line is a complete sentence that says the title, or very close to it.**
   - Example: "And that's what really happens when you drink the ocean."
   - Never end on a half sentence. The video then loops straight back to line 0.
5. **Use words at a 7th grade reading level or below.** This applies to the script, the on-screen text and the titles.
6. **Facts get checked against real sources** (NOAA, USGS, CDC, NIH, university pages). Do the math in code, not in your head. List the sources when you deliver.

`lines.json` format: a list of `{"text": "...", "after": 0.3}`. You can also add `"speed": 1.05` to a line.

## 2b. Replay checklist (aim: so addictive it's hard to stop replaying)

- **The first second asks a question the video answers at the very end.** Frame one shows the danger mid-action; the hook word names it.
- **Every line opens a new "wait, what?"** No line just restates. Each beat shows one new picture you haven't seen yet.
- **One jaw-drop number or image at beat 6–7**, big on screen, with the chime.
- **Nothing on screen is ever still.** Something moves in every beat: the subject, particles, the camera.
- **The loop is invisible.** The last line says the title, the last frames run straight into frame one, and the loop seam diff is under 15.
- **Shorter beats.** 30–38 s total; no beat over about 5 s.
- **The swipe test (from real numbers, 2026-10-25).** Frame one shows the danger up close and already happening, readable on a phone with the sound off. Pick an everyday person in an everyday place ("this man", "you"), a fear people grew up with (cartoons, movies), and title it "What happens if you…", not "How to…".

## 3. Look rules

- **House look is soft 3D:** 2D shapes shaded to read as 3D (`TOON_LOOK=soft3d`, the default).
- **House touches, all built in:**
  - **House cut is the hybrid** (`kit.CUT = 'hybrid'`): on the 2–3 cuts that go *inside* something (a mouth, an ear, a cell, the blood), the camera dives into that spot and lands in the next scene. Every other cut is a punch: a hard cut that lands with a small zoom hit. Each Short names its dives with `DIVE = {beat_index: (x, y)}`, where (x, y) is the screen pixel to dive into on the beat before (screen = 540 + world x, 960 + world y at zoom 1). The sound matches automatically: a rising rush for a dive, a whoosh and low hit for a punch. Other styles: `TOON_CUT=punch|dive|whip`. The paper page turn is retired;
  - a bell chime on the reveal;
  - slow camera push-ins;
  - a SUBSCRIBE button with a finger tap 2.8 s before the loop.
- **There is no sidekick character.** Blip stays off.
- **Subscribe Easter eggs: dial it back (owner's call, 2026-10-23).** One or two per Short, total, tucked into the background of a room or outdoor shot (a poster, a phone, a magnet). Never in every beat, never inside-the-body shots, never next to the main action. They should be found on a rewatch, not noticed on the first watch. Helpers in `kit.py`: `sub_poster`, `sub_phone`, `sticky`, `sub_button`, `bell_icon`, `thumb_icon`, `neon_sign`, `xray_tag`, `doormat`.
- **Printed text on props uses `label(..., stroke=0)`.** The thick outline is for text floating over the scene. On paper, tags and fabric it turns small words into blobs.
- **An open mouth comes from the face code, not drawn over the face.** Use `face='snore'` (closed eyes, open mouth with top teeth and a tongue). A mouth drawn on top lets the smile line show through and slides when the body breathes.
- **Frame one already has motion happening,** plus one big statement word as the hook, shown full size from the first frame (`hook_text(cv, 'GULP', lt, y=-780, size=190, ...)`). A still or calm opening gets swiped away.
- **Every object must read in under a second.**
  - Example: a straw has to look like a real bendy straw (clear plastic, spiral stripes, an accordion bend, sitting in his lips). Otherwise people see an intestine.
  - Put people and props close to the camera, and keep a clear horizon or background.
- **Layout:**
  - Captions sit at about screen y +390 (from the center). Keep the main subject between -650 and +300.
  - Hook words go at y -780.
  - Labels must not hit the captions or get cut off.
- **Don't animate background colors or vignettes every frame unless they're rounded.** The background cache is capped now, but keep it in mind.

## 3b. Rig rules (no limbs through the body, no spinning in the socket)

Read `studio/RIGGING.md` (study notes, basics to advanced, with sources). The rules are enforced in code:
- **`guy()` runs every arm through `rigsafe.safe_arm`:** human joint limits (shoulder -40..176, elbow +-145, soft
  limits so motion slows into them), the upper arm never through the head, the hand never past the far shoulder, and
  a hand at the face is drawn over the head automatically (no more `front_arm` for that). `raw_arms=True` turns it off
  only for something that isn't a human arm.
- **Pose in local angles; the tumble belongs to the root.** Spin the whole figure with `layer_xform`, never by adding
  a rotation to every joint.
- **Flailing:** use `rigsafe.flail(T, base, amp, hz, seed)` (<= 35 deg, <= 2.5 Hz). Never slow a flail by warping
  its clock (`sin(T*(1-k))` races the phase); fade its amplitude.
- **Pose changes take time:** blend with `rigsafe.blend_pose(a, b, k)` (short way round) over at least ~6-9 frames
  unless there's a cut. One-frame snaps read as pops. Joints faster than 25 deg/frame get flagged.
- **Hands on targets:** `reach()` / `reach_move()` now use the limit-aware IK (`rigsafe.ik_arm`); poses that were
  already legal come out the same.
- **Lag/settle:** `rigsafe.spring_follow(target_fn, T, halflife)` for overlapping action (hair, loose arms).

## 4. Sound rules

- **Narrator** (default, male): Kokoro `am_fenrir:0.65,am_puck:0.35`, speed 1.12, tone-matched to `studio/voice/beer_ref.wav`.
- **Female narrator "A3"** (`--preset female`, `af_heart`, speed 1.24): only when the owner asks for it.
- **Pacing is tight with no dead air.** These are now the defaults:
  - gap after a sentence: 0.12 s;
  - longest pause inside a sentence: 0.13 s;
  - pause between lines: × 0.35;
  - LEAD/TAIL: 0.06/0.10.
- **Each line is spoken in one smooth take** (the narrator no longer splits a line at sentence ends, which made every sentence restart like a fresh breath). `--choppy` brings the old way back.
- **Mispronounced words go in `studio/voice/say.json`** as word → Kokoro phonemes. Captions keep the real spelling.
  - Example: dopamine = `dˈoʊpəmˌiːn`.
  - Check a word with `k.tokenizer.phonemize('word', 'en-us')`.
- **Music sits well under the voice** (`MUSIC_DROP = 10` dB in `kit.py`). Zack's music is barely there.
- **The voice stays steady.**
  - Section shaping moves only the music and sound effects.
  - Every line is leveled to the same loudness.
  - Target: the voice level varies by 2.5 dB or less across lines (`check.py` reports this).
- **Sound effects stay under the voice.**
  - Use small pops, ticks, whooshes and drips around -18 to -24 dB.
  - Nothing should jump out over the narration: no loud heartbeat, gulp or chime.
  - The chime is -19.
- **Every mix runs through the studio's ears** (`studio/senses/listen.py`). Target -14 LUFS with the true peak below -1 dBTP.
  - "Very flat dynamics" is expected now, because the voice stays level on purpose.
  - Fix anything else it flags before delivering.

## 5. Setup (once per machine)

```bash
git clone https://github.com/Codygreen2210/Claudes-choice ~/cc && cd ~/cc && git checkout studio/animate
bash studio/setup_shorts.sh
```

The script installs everything:
- the Python packages (numpy, scipy, pillow, opencv, soundfile, librosa, pyloudnorm, onnxruntime, kokoro-onnx 0.6.1);
- ffmpeg and gcc;
- the Kokoro voice models into `~/vt/v`;
- the voice reference;
- the sound kit (`studio/instruments` + `studio/sfx` from the `studio/ponzi` branch) into `~/vt/kit`.

It also compiles the renderer (`studio/toon/fastk.c`, which builds itself on import).

## 6. Pipeline for one Short

The work dir is `~/vt/n<GEN>/<name>/`. Use a new GEN number per batch.

```bash
d=~/vt/n13/<name>; mkdir -p $d          # 1. write $d/lines.json (section 2)
cd ~/cc
python3 studio/voice/narrate_short.py ~/vt/v ~/vt/v/beer_ref.wav $d --lines $d/lines.json      # 2. voice + times.json
# 3. write studio/toon/shorts/<name>.py  (copy ocean.py as the template: `from body2 import *`, 9 beat functions, BEATS list, run(BEATS))
python3 studio/toon/shorts/<name>.py $d/times.json $d/lines.json $d/sheet.png --sheet           # 4. contact sheet, look at it, fix layout
python3 studio/toon/shorts/<name>.py $d/times.json $d/lines.json $d/still.png --still 0.3        #    frame one up close
# 5. sound: in studio/toon/shorts/body_sound.py add '<name>' to the light_score key dict and the reveal dict,
#    and an `elif name == '<name>':` section before "# ---- house sounds ----" (see the 'ocean' section)
GEN=13 bash studio/toon/shorts/build.sh <name>                                                 # 6. mix -> ears -> picture -> final.mp4
python3 studio/toon/shorts/check.py $d                                                         # 7. ears, voice spread, loop seam, grid.png
python3 studio/toon/shorts/rigcheck.py <name> $d                                              # 8. rig check (~15 s): limits, body, spins, flips
```

**Beat functions** look like `def b3_kidneys(lt, dur, T)`:
- `lt` is the time inside the beat, `dur` is the beat length and `T` is the global time.
- Return a `Canvas(cx, cy, zoom)`.
- `b0_hook` is also drawn at the end, where `lt < 0` is the run-up into the loop, so it must be continuous across lt = 0.

**Helpers:**
- `common.py`: `guy` with faces calm, happy, worried, shock, scream, closed, snore (asleep, mouth open), hold (eyes squeezed, cheeks puffed), puff and pain; `box`, `disc`, `line`, `label`, `hook_text`, `wave_surface`, `bubbles` and `vignette_red`.
- `kit.py`: `meter` (the color must be a `ramp(...)`), `brain`, `arrows`, `sky_bg`, `heart_icon`, and the subscribe Easter eggs (`sub_poster`, `sub_phone`, `sticky`, `sub_button`, `bell_icon`, `thumb_icon`, `neon_sign`, `xray_tag`, `doormat`), `reach(side, x, y)` to put a hand exactly on a spot (nose, mouth) in a still pose, `reach_move(side, k, target)` for a hand that MOVES there (it blends the joint angles; aiming reach() at a moving point makes the elbow flip and the arm go crazy), and `front_arm(...)` to redraw that arm on top, `layer_xform(...)` to tumble/rotate/squash a figure (guy() can't rotate), `whip(a, b, k)` for a camera-whip transition instead of a hard cut (guy() draws arms before the head, so a hand on the face otherwise disappears behind it).
- `body.py`: `badge`, `drop`, `toilet`, `stomach`, `chest`, `cloud`, `germ`, `bed` and `jolt`.
- `body2.py`: `cell`, `vessel`, `tooth`, `fighter`, `virus`, `wall_clock`, `sun`, `moon` and `octopus`.
- `jump.py`: `guy_r`, for tiny people standing around a globe.

**Before delivering, all of these must pass:**
- the contact sheet reads clearly beat by beat;
- frame one has motion and a hook word;
- the ears pass;
- the voice level varies by 2.5 dB or less across lines;
- the loop seam diff is under 15;
- `grid.png` looks clean;
- `rigcheck.py` says clean (no LIMIT, BODY, SPIN or FLIP).

**Then:**
1. Add the Short to `studio/toon/series.json`.
2. Commit to `studio/animate` with plain messages.
3. Copy the final to `~/vt/<slug>.mp4` and send it.

## 6b. 3D Shorts (the sculpted, skinned guy)

The first one is `quicksand` (2026-10-24). Same script, voice, sound, checks and delivery as section 6; only the picture is 3D.

```bash
d=~/vt/n<GEN>/<name>; mkdir -p $d                                    # 1. lines.json, then the voice (same as 2D)
python3 studio/voice/narrate_short.py ~/vt/v ~/vt/v/beer_ref.wav $d --lines $d/lines.json
cd studio/samples/web && npm i && python3 ../char/character.py char  # once: three.js + the guy (~1 min)
cp $d/times.json $d/lines.json qs/                                   # 2. the scene reads its beat times from qs/
#    scene = quick.js (copy it for a new Short): one shot per line, poses in local joint angles (P = {...}),
#    guyAt(t) -> pose/root/face, camAt(t) -> camera; cutaways clip the ground and show a section wall
node qstills.mjs /tmp/s 0.3,5,10 && node qrig.mjs /tmp/rig.json      # 3. stills to look at; per-frame joint angles
#    rig rules: soft limits per joint (LIMITS), every move eased over >= ~0.3 s, flails bounded, <= 25 deg/frame
# 4. sound: a section in toon/shorts/body_sound.py (foley beds/hits via studio.sfx.foley), ears with listen.py
bash studio/samples/qs_render.sh $d                                  #    picture in 180-frame chunks (fresh browser each, auto-retry) + mux -> final.mp4
python3 studio/toon/shorts/check.py $d                              # 5. ears, voice spread, loop seam, grid
```
- `qs_finish.py`: film grade, 2-3 word captions timed by word length inside each line's voice span, the hook word
  (frame one and the last 0.45 s, so the loop seam matches), yellow labels at y 150, the subscribe tap 2.8 s from the end.
- About 1.3 s a frame at 1080x1920 on llvmpipe (35 s Short = ~25 min). Preview at 360x640 runs ~0.3 s a frame.
- Render in chunks (`qs_render.sh`): one long browser session hung silently at frame 568 the first time.
  Never `pkill -f` with a pattern that also appears in your own shell command (it kills the shell running it).
- The loop: the last beat ends on exactly the first frame's pose, face, camera and hook word; anything driven by
  time (ripples, camera shake, flails) is faded to zero at both ends or given a period that divides the length.
- Second 3D Short: `avalanche` (`samples/web/av.js`, times/lines/labels in `web/av/`). Render any 3D scene with
  `PAGE=av.html TD=web/av CFG=web/av/finish.json bash studio/samples/qs_render.sh $d` (CFG holds the hook word and
  the yellow/red labels). `node avpose.mjs` renders debug stills with a pose override and a free camera (fast pose
  tuning). Two guys can share a scene (call `loadGuy` twice); `materials.sleeve` / `materials.glove` turn the arm and
  hand skin into a jacket and gloves; a beanie is a group parented to the head bone (placed in rest world space, then
  moved into the bone's frame). `armIK()` in av.js puts a hand on a point (here: forearm over the face).
- Fourth 3D Short: `elevator` (`samples/web/elev.js`, data in `web/elev/`): a car falling down a cut-away shaft, safety brakes with sparks, a fogged tower, the pit. Arms are posed with human joint angles (`armQuats`).
- Portrait framing: the horizontal field of view is only ~26-30 degrees, so a second person or prop beside the hero
  falls out of frame; stack them in depth instead. Looking toward +z, screen right is -x.

## 7. Delivering a video

Always deliver these, written to be as good as YouTube allows for views:
- **Title:** 7th grade words; the curiosity hook or what-if; it matches the line the video ends on.
- **Description:** a short retelling of the story with the key numbers, then "Subscribe for more …" and 3–5 hashtags.
- **Tags:** 10–15 search phrases people actually type.
- **Sources:** the links behind the facts.

## 8. Posting (Metricool)

1. **Get a public video URL.** Push the mp4 to the repo's `shorts-uploads` branch, using a git worktree on that branch. The URL is then `https://raw.githubusercontent.com/Codygreen2210/Claudes-choice/shorts-uploads/<file>.mp4`. (GitHub releases are blocked from the workspace.)
2. **Schedule it with `createScheduledPost`:**
   - blogId `7119923`;
   - provider `youtube`;
   - `youtubeData` = `{title, type: "short", privacy: "public", tags, category: "EDUCATION", madeForKids: false}`;
   - `publicationDate` in `America/Chicago`;
   - `autoPublish: true`.
3. **To post right away,** schedule it a few minutes ahead, since the date can't be in the past.
4. **Space posts out.** Use separate days, or a morning and an afternoon. Check `getScheduledPosts` first so they don't stack up.

## 9. Weekly trend scan

Set this up as a scheduled task: Mondays at about 8:50 AM Central, with push and email notifications. Prompt:

> Run the Shorts trend scan for the 2D Zack D Films–style channel (repo Codygreen2210/Claudes-choice, read studio/SHORTS_HANDOFF.md). Look 1–3 weeks ahead: holidays, seasons, health news (flu, outbreaks), big science stories, viral body/what-if questions. Check search demand with Ubersuggest (US, volume and SEO difficulty; free plan = 3 reports/day). Return the top 5 Short ideas ranked by (search volume × weak competition × timing), each with a one-line frame-one action, the twist, a working title, and why now. Keep it short.

A "daily run" means: scan → pick the best topic → build the Short → deliver it with a title, description and tags.

## 10. Working style with the owner

- Keep replies short, with the answer first.
- Use plain, blue-collar wording. Don't use "ship" language.
- Ask before big or expensive choices. For small fixes, just do them.
- Never delete anything in a connected app. Point out clutter and let the owner decide.
- If the owner points out a flaw, fix it in the system, so it's fixed for every future Short and not just this one. Note the new rule in this file.

## Lessons log (newest first)

- 2026-10-26 (owner): open like Zack D, in "you": "You just [did X]. Here's what you do." (the owner chose this over "What happens now?"). Script rule 1 changed; the whole script is second person and is built around the steps.
- 2026-10-26 (swallowed gum, 7th 3D Short; picked from Ubersuggest: "what happens if you swallow gum" 18,100/mo US, SD 32): (1) Topic picking now starts from Ubersuggest `match_keywords` on "what happens if you" (one report shows the top questions with volume); the free plan is 3 reports a day. (2) A hand that reaches and comes back to the standing pose: start and end the reach exactly at that pose's palm (compute it once with `handFK` on the pose), and ease back by blending joint angles from where the reach ended, not by solving a moving target; a cold solve on the way back flipped the arm 60 deg at the loop seam. (3) Dark side stages (a close-up of the gum, an endoscope view with a black ring on the camera, a free-floating gut) are cheap NileRed/Zack D style cutaways: a group far from the room, shown one beat at a time.
- 2026-10-25 (bleach + ammonia, 6th 3D Short; the Zack D + NileRed mix the owner asked for): chemistry Shorts show what happens and why not to, never amounts, ratios or steps. NileRed touches that read: a macro of the reaction (dark water with blue streaks of one cleaner, milky tendrils forming, fizz), a ball-and-stick molecule swap on a dark stage, then Zack D x-rays on a dark navy background with everything but him hidden. (1) In a small room the cameras end up behind walls; cut away any wall between the camera and him (`WALLS[].out`). (2) A held prop at the loop seam jumped 20 deg because frame one's solver started cold; warm-start frame one from the solution at the end of beat 9 (`primeSeam`). (3) The thumb check now judges only hanging forearms: with the elbow bent up (a phone at the ear, a hammer curl) the thumb really does point back, which is anatomy, not a bug. (4) Hand holds can also aim the fingers (`u`) as well as the palm (`n`) and little-finger side (`w`); pick two that agree with a real hand (w = n x u for the right hand) or the solver can't satisfy them.
- 2026-10-25 (car into water, 5th 3D Short): (1) The owner caught a fact the first script got wrong: MythBusters confirmed the door DOES open once the car is completely full (pressure evens out). The honest line is "it opens, but by then you're underwater, holding your breath, in the dark"; the experts' plan is belt, window, out, and waiting is the last resort. Check a myth against the best-known test of it (MythBusters results) before calling it busted. (2) Hands that hold things in `sink.js` are solved over real joint limits in the moving car's own space (`solveHand`), warm-started frame to frame; a hold-cost scan (worst cost per beat, over ~30 = the hand misses) found the wheel, handle and window corner out of reach, and the fix was moving those props to where a seated driver can reach (never loosening the limits). (3) The first rendered chunk caught a hook camera that cropped the car (only the hood read); the camera now backs up with the car. (4) A loop over moving water: blend the wave clock to the loop's start in the last second (`uTb`, `uW`) or the seam check fails. (5) Inside a car, cut away the near side like the elevator's open front and shoot from outside it; a camera inside the cabin only ever sees a seat back or a shoulder.
- 2026-10-25 (owner): "bottom" came out wrong: Kokoro reads it with the American soft t (`bˈɑːɾəm`), which this voice mangles. Added `bottom: bˈɑːtəm` (clear t) to `say.json`. Watch for other words with a t or d between vowels (water, better, little, city); check with `k.tokenizer.phonemize(word, 'en-us')` and give them a clear t when they sound off. A say.json fix that keeps the same line length leaves times.json unchanged, so only the sound needs remixing (mux the new mix onto the existing pic.mp4).
- 2026-10-25 (owner): **thumbs were on the wrong side, then (after a wrong fix) the arms looked upside down.** Real cause was in the SCULPT: `character.py` builds the hand's across-knuckle axis `w` (and the forearm's `hw`) with the sign flipped, so the index finger and thumb were made on the BACK of the hand (the comment said "index toward the front"). My first fix twisted the forearm half a turn to bring the thumb forward, which turned the palm and forearm upside down. Fixed at the source: `w`/`hw` now point to the little-finger side (back), so index and thumb are built at the front; the scene adds no twist (`PRO0 = 0`). Check that proves it: arm hanging = thumb forward, palm to the thigh; elbow at 90 = thumb up (`jointjerk.mjs` measures this every frame and flags a turned-around hand). Lesson: when a body part is wrong, find where it's built wrong and fix it there; never cancel it out with a counter-twist in a scene. Roll angles also now mean the same on both arms (roll > 0 = palm turns up).
- 2026-10-25 (elevator, 4th 3D Short): (1) **Real numbers, quicksand vs avalanche.** Quicksand: 5,010 views in 23 h (typical 910-1.2K), 57% stayed past the swipe, 73.5% average viewed, 2.7% likes, 92% from the Shorts feed. Avalanche: 351 views in 14.5 h, only 38% stayed, yet 75.7% average viewed. The people who stayed watched both just as well; the first second lost avalanche (a small snowboarder on a white slope reads as "snow video"; a sport most people never do). Rule added to 2b. (2) **The rig's raw arm Euler angles don't mean what the comments say** (uarm x swings the arm out to the side, not forward). For any posed (not held) arm use human joint angles `armR/armL = [forward raise, side raise, roll, elbow, forearm roll]` through `armQuats` (see `elev.js`), the same model as mold.js's solver; never pose arms with raw uarm/farm Eulers. (3) `node web/jointjerk.mjs page.html` checks any 3D Short: fastest joint per beat (deg/frame), hip pops relative to the car/rig base, and the loop seam. It caught a 12 cm hip jump where two keyed branches handed off. (4) The math check in code caught a wrong label (55 mph - 7 = 48, not 43). Do every on-screen number in code. (5) The headless browser path changed between sessions; all web scripts now find it with `web/browser.mjs` (`CHROME=` overrides), and `setup_shorts.sh` installs the 3D build packages (trimesh, scikit-image, fast-simplification, libigl) and `npm i`. (6) Look at the first rendered chunk (`seg_00000.mp4`) as soon as it lands, before the other ~70 min: here it showed the hook word sitting on top of the snapped cables (the danger was hidden) and limp, gravity-hanging forearms in a float. Keep the frame-one danger below y ~350 px. (7) A scene that moves a whole set (the car) keeps everything in one world and gives the cameras in the set's own space plus its height; a circular mix lets one sound run from the last beat through the loop into the first.
- 2026-10-25 (later): Owner: the arm holding the slice was turned the wrong way and the rig broke on the throw. "If a human can't bend like that, neither should the rig." Every hold in `mold.js` is now solved over a human arm (`armSolve`): shoulder forward raise -50..170, side raise -25..170, upper-arm roll +-60, elbow a hinge 0..145, forearm roll +-80, wrist bend -65..70 and side bend +-25, plus no elbow/forearm inside the trunk and elbows below the shoulder. It searches those joint angles directly (not free IK + clamping), with contact weighted first. Also: a target the arm can't reach shows up as a high cost in `node web/wristscan.mjs mold.html`; fix the scene (move the bin, let him step or turn), never the limits; and a hand can't take an object from under it while it lies on a surface (use a side or top grip, or start the shot with it already in hand).
- 2026-10-25: Owner: in the moldy bread Short nothing the guy touched lined up (hand not holding the knife, stomach acid outside the stomach, wrists bent and turned way past what a real wrist can do). Fixes in `samples/web/mold.js`, use them for every 3D Short with props: (1) props are held by GRIPS (`makeGrip`: prop axes mapped onto the hand's own u/n/w axes plus a palm point), and `holdProp` searches the elbow direction and the wrist roll/flex/side-bend INSIDE real limits (roll +-80, flex +-60, side +-25) for the closest match, slides the wrist so the palm lands exactly, then the prop is placed FROM the hand (`propFromHand`), so contact is exact and the wrist is always natural; (2) `G.untwist()` is not idempotent (a second call throws away the arm twist already split off, the arm swings away): call `untwistSafe()` instead; (3) organs that hold liquid: build the liquid from the same shape shrunk inward and clip it flat at the fill level (plane moves with the body). `node web/wristscan.mjs page.html` reports, per beat, how far each held prop had to turn to fit a natural wrist.
- 2026-10-24: Avalanche Short (second 3D one). Facts checked against avalanche centers (Utah, Shasta) and Haegeli et al. CMAJ 2011; the "spit to find up" trick is listed as a myth by the Shasta Avalanche Center, so the script says so. Traps: JavaScript refuses `-(x) ** 2` (write `-((x) ** 2)`), and `pgrep -f <pattern> | kill` killed my own shell again because the pattern was in my command; kill by exact PID only.
- 2026-10-24 (latest): Owner: make the 3D guy look normal. Measured him against real men (`samples/char/measure.py`, targets in `studio/ANATOMY.md`): limbs were 16-26% too thin, waist/hips 14-18% too small, chest too flat. Rebuilt skeleton-first: the trunk, upper arm, forearm, thigh and shin are now *lofts* (rounded-rectangle sections through measured stations, smooth between them), with muscles laid on top as low relief. Every girth now within 5%. Run `python3 measure.py` after any sculpt change. Traps found: (1) piecewise-linear lofts crease at every station, so interpolate stations smoothly (PCHIP); (2) stacking many soft unions (`k` 3-4 cm) bloats a region by centimetres, so muscle relief uses small `k`; (3) the shirt shows any hard edge of what is under it as a panel, so find creases with a dihedral-angle plot of the mesh and probe the shirt SDF terms along a line; (4) when carving a hollow shell, the cavity SDF is `outer + thickness` (the sign flip carved 5 mm off the outside). `char/merge_piece.py` swaps one piece from a fast `ONLY=shirt` build into a full build (15 s instead of 75 s per try).
- 2026-10-23: The 3D guy is now one sculpted, skinned character (`studio/samples/char/character.py` + `web/guy3d.js`), not capsules: 41 bones, smooth weights from the sculpt's own masses, face rig. Two traps found: skimage marching cubes already winds faces outward (reversing them made every surface inside-out, which looked like goggle eyes and a see-through mouth), and Taubin smoothing explodes on tiny loose fragments (drop pieces under 200 faces and leash vertices to 2 cells). Set the pose first, then the face (a pose reset clears the jaw).
- 2026-10-24 (later): 3D rig and assets to the next level: dual-quaternion skinning, arm twist bones, face expression shapes, planted-foot leg IK, strand hair cards, denim twill + stitching, knit shirt, skin pores + light bleed, detailed iris, baked + screen-space AO. Details in RIGGING.md section 8. Scenes must call `G.untwist()` after posing. `charstills.mjs` views are now separated by `;` (so `at:<bone>:dx,dy,dz` close-ups work).
- 2026-10-24: The 3D guy re-sculpted from anatomy (skull and face landmarks in thirds, real 24 mm eyes with sculpted lids and a blink cap, multi-head deltoids, biceps/triceps/forearm groups, quads/hamstrings/calves, kneecaps, ankle bones, finger segments) and painted per pixel in the shader (brows, lash line, lips) because decimated meshes are too sparse for vertex paint. Clothing clipping (shirt through jeans, shoe through jeans hem, neck vs collar) fixed by layering by construction and shared weights; rules in RIGGING.md section 8, check with `samples/web/clothcheck.sh`.

- 2026-10-23: Owner: limbs kept flying through the body and flailing 360 in the socket. Root causes: arms keyed as raw/world angles with no limits, the old exact IK could answer with a shoulder at -108 deg, a flail slowed by warping its clock (black hole), one-frame pose snaps (scared, ice, lava slip/impact), and the sample rigs adding the body's tumble to every joint and aiming forearms independently (knees bent sideways). Fixed with `rigsafe` (limits, limit-aware IK, short-way blending, bounded flail, springs), automatic face-draw order in `guy()`, local-angle rigs with hinge elbows/knees and capsule push-out in the samples, and `rigcheck.py` / `rigcheck3d` (13 Shorts checked: 9 clean, 4 fixed; lava's two snaps go in with lava v4). Study notes: `studio/RIGGING.md`.

- 2026-10-23: Style samples (Levels 1–3 above the house look) live in `studio/samples/` (README there). 3D renders in headless Chromium on Mesa **llvmpipe** (`--use-gl=angle --use-angle=gl-egl`): ~3x faster than SwiftShader on this 2-core box. In SwiftShader/llvmpipe, extra full-screen passes and texture lookups cost more than shader math, so don't swap math for noise textures or MSAA for FXAA. Motion blur = sub-frames blended on the GPU (never read back per sub-frame), with sub-pixel jitter for free anti-aliasing; turn `renderer.autoClear` off while adding into the accumulation buffer, and set ShaderPass textures after construction (it clones uniforms). `fract(sin(x)*43758)` hashes differ between GPU backends; use the sin-free hash. Stream raw frames from the page by POST, grade + caption in one pass, encode once.

- 2026-10-23: Owner on lava v2: the fall looked like he was being 'slowly lowered', there were no x-rays of the damage, and the ending flipped through cuts. Falls now tumble (layer_xform) with fast-rushing walls, wind and shake; damage gets x-ray shots (skin heating, broken bones, burn depth); end-of-video moves use whip() instead of stacked hard cuts.

- 2026-10-23: Owner: lava narration had 'breaths' and a weird 'movies'. Lines are now one take each (sentences flow); 'movies' is in say.json. The lava Short was rewritten as a height-by-height countdown with real physics numbers (Erta Ale rim 260 ft, lake heat vs height, NOAA heat levels), which also showed the fall is too fast to burn: the landing is the danger.

- 2026-10-23: Owner: dial the subscribe eggs back to 1–2 per Short, and push script and animation quality for replays (see 2b).

- 2026-10-23: The arm 'went crazy' at the loop in the pepper and sneeze Shorts: reach() aimed at a moving hand flipped the elbow between frames. Moving hands now use `reach_move`.

- 2026-10-21: A hand touching the face went through his head because arms are drawn before the head. Redraw it on top with `front_arm`.

- 2026-10-21: Subscribe Easter eggs go in every beat now, not just rooms (neon signs, x-ray tags, gauge plates, hidden bells).

- 2026-10-21: Open mouths are now a face (`snore`) with teeth and a tongue. An ellipse drawn over the face let the smile show and slid when he breathed.
- 2026-10-21: Empty backgrounds are now filled with subscribe Easter eggs (posters, a phone, sticky notes, tags, a doormat). Printed prop text has no outline.

- 2026-10-20: The house cut is the hybrid: dive on the 2–3 cuts that go inside something, punch on the rest. The page turn is retired.
- 2026-10-20: The last line must be a complete sentence with the title. A half-sentence loop line sounds broken.
- 2026-10-20: Pauses and "breaths" were cut, so tight pacing is now the default.
- 2026-10-20: Volume jumps came from section shaping that also moved the voice. Shaping now moves only the music and effects, and every line is leveled.
- 2026-10-20: Music sits 10 dB further under the voice, the Zack style.
- 2026-10-20: Objects must read instantly. A thick curved red-and-white tube read as an intestine; it's a real bendy straw now.
- 2026-10-20: Animated vignettes leaked memory (one full frame per value). The background cache is capped at 24.
- 2026-10-20: Opening narration describes the frame-one action, and the title is said at the end.
