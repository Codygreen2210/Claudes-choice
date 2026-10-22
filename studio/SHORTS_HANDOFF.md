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

1. **Line 0 says what's on screen on frame one,** in plain present tense, as a statement. It is never a question.
   - Example: "This man is trying to drink the entire ocean."
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

## 3. Look rules

- **House look is soft 3D:** 2D shapes shaded to read as 3D (`TOON_LOOK=soft3d`, the default).
- **House touches, all built in:**
  - **House cut is the hybrid** (`kit.CUT = 'hybrid'`): on the 2–3 cuts that go *inside* something (a mouth, an ear, a cell, the blood), the camera dives into that spot and lands in the next scene. Every other cut is a punch: a hard cut that lands with a small zoom hit. Each Short names its dives with `DIVE = {beat_index: (x, y)}`, where (x, y) is the screen pixel to dive into on the beat before (screen = 540 + world x, 960 + world y at zoom 1). The sound matches automatically: a rising rush for a dive, a whoosh and low hit for a punch. Other styles: `TOON_CUT=punch|dive|whip`. The paper page turn is retired;
  - a bell chime on the reveal;
  - slow camera push-ins;
  - a SUBSCRIBE button with a finger tap 2.8 s before the loop.
- **There is no sidekick character.** Blip stays off.
- **Fill dead space with subscribe Easter eggs.** Any shot set in a room or on a bed or wall gets 1–3 small props that quietly say LIKE / SUBSCRIBE: a wall poster, a phone with the bell, a sticky note, a mattress tag, a doormat, or text embroidered or knitted into a pillow or blanket. Helpers are in `kit.py`: `sub_poster`, `sub_phone`, `sticky`, `sub_button`, `bell_icon` and `thumb_icon`. Keep them out of the caption band and away from the main subject. **Every beat gets at least one**, including shots inside the body: use a faint `neon_sign` under the captions, an `xray_tag` in the corner of x-rays, a brand plate on a gauge ("LIKE-O-METER"), or a tiny bell or thumbs-up hidden among the floating bits. Rooms can also get a `doormat`.
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

## 4. Sound rules

- **Narrator** (default, male): Kokoro `am_fenrir:0.65,am_puck:0.35`, speed 1.12, tone-matched to `studio/voice/beer_ref.wav`.
- **Female narrator "A3"** (`--preset female`, `af_heart`, speed 1.24): only when the owner asks for it.
- **Pacing is tight with no dead air.** These are now the defaults:
  - gap after a sentence: 0.12 s;
  - longest pause inside a sentence: 0.13 s;
  - pause between lines: × 0.35;
  - LEAD/TAIL: 0.06/0.10.
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
```

**Beat functions** look like `def b3_kidneys(lt, dur, T)`:
- `lt` is the time inside the beat, `dur` is the beat length and `T` is the global time.
- Return a `Canvas(cx, cy, zoom)`.
- `b0_hook` is also drawn at the end, where `lt < 0` is the run-up into the loop, so it must be continuous across lt = 0.

**Helpers:**
- `common.py`: `guy` with faces calm, happy, worried, shock, scream, closed, snore (asleep, mouth open), hold (eyes squeezed, cheeks puffed), puff and pain; `box`, `disc`, `line`, `label`, `hook_text`, `wave_surface`, `bubbles` and `vignette_red`.
- `kit.py`: `meter` (the color must be a `ramp(...)`), `brain`, `arrows`, `sky_bg`, `heart_icon`, and the subscribe Easter eggs (`sub_poster`, `sub_phone`, `sticky`, `sub_button`, `bell_icon`, `thumb_icon`, `neon_sign`, `xray_tag`, `doormat`), and `reach(side, x, y)` to put a hand exactly on a spot (nose, mouth).
- `body.py`: `badge`, `drop`, `toilet`, `stomach`, `chest`, `cloud`, `germ`, `bed` and `jolt`.
- `body2.py`: `cell`, `vessel`, `tooth`, `fighter`, `virus`, `wall_clock`, `sun`, `moon` and `octopus`.
- `jump.py`: `guy_r`, for tiny people standing around a globe.

**Before delivering, all of these must pass:**
- the contact sheet reads clearly beat by beat;
- frame one has motion and a hook word;
- the ears pass;
- the voice level varies by 2.5 dB or less across lines;
- the loop seam diff is under 15;
- `grid.png` looks clean.

**Then:**
1. Add the Short to `studio/toon/series.json`.
2. Commit to `studio/animate` with plain messages.
3. Copy the final to `~/vt/<slug>.mp4` and send it.

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
