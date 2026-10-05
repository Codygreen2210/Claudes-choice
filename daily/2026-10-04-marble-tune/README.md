# Marble Tune Machine (build channel, episode 1)

Draw lines, marbles drop, every bounce plays a note. Marbles drop on a steady beat and each takes the same path, so a doodle turns into a loop.

**Why someone would play it** (stated before building, per the Lane Luck lesson): anyone gets something that sounds good in ten seconds, and nudging one line to fix the tune pulls you back in. Not yet tested on real people.

- `index.html` + `sim.js`: the whole build. Open the page, press Start. Drag to draw, tap a line to remove it, slide the dropper, Undo, Clear, Speed, Sound, Copy link (the link carries the lines).
- Long line = low note, short line = high note, all from C major pentatonic.
- Tested in Chromium at 360x780, 412x915 and 1280x720: starter tune plays, draw / tap-remove / undo / speed / shared link all work, no page errors. Not tested on a real phone or in Safari.
- Not hosted yet. The video says "the link is below", so it needs a home before the video goes up.

## The video (`video/`)

`episode-01-marble-tune-machine.mp4`: 1080x1920, 70 s. The marbles in the video are the real `sim.js` run from `timeline.js`; the sound is made from the same bounces, so picture and sound match.

Rebuild, from the repo root:

    node daily/2026-10-04-marble-tune/video/design.cjs      # only to make a new layout
    node daily/2026-10-04-marble-tune/video/events.cjs      # bounces -> events.json
    python3 daily/2026-10-04-marble-tune/video/sound.py     # score.wav
    python3 daily/2026-10-04-marble-tune/video/voice.py <folder with kokoro-v1.0.onnx and voices-v1.0.bin>
    python3 daily/2026-10-04-marble-tune/video/mix.py       # final.wav
    node studio/motion/render.mjs daily/2026-10-04-marble-tune/video/film.html --out ... --audio daily/2026-10-04-marble-tune/video/final.wav

- **Voice:** ElevenLabs refused (free tier disabled on the account), so the narration is Kokoro, an open speech model run here (`pip install kokoro-onnx`, model files from the kokoro-onnx GitHub releases), voice "af_heart". Eight voices were measured for pace, pitch movement and pauses; each line is spoken on its own, paced per line, and every line's pitch was checked to fall at the end. Nobody has heard it with human ears yet: pronunciation of "Claude" and "doodle" is unchecked.
- **Ears:** `score.wav` (music alone) passes `listen.py` with no flags after fixes (it was dark, thin in the lows and crowded in the low-mids). `final.wav` (with voice): -15.5 LUFS, true peak -2.3 dBTP, one flag left: flat dynamics (2.5 LU), which is what steady narration over music measures as.
- **Eyes:** `look.py` flagged the first render as very dark (0.09); background brightened to 0.21. Words sit above the bottom fifth of the frame, which phone apps cover.
- The .wav files are not committed (large); the scripts remake them.

## The story cut (`story/`), for YouTube

`episode-01-story.mp4`: 1920x1080, 24 fps, about 2:29. Cody's brief: claymation look, yarn for the lines popping in and out, and the full story (asked for three ideas, what I picked and why, what I built, what went into it).

- Everything is drawn by code (`film.html`): clay pieces with pressed edges that shift between poses, moved 12 poses a second; yarn strands with plies, loose fibres and pins. The marbles on the board are the real `sim.js`.
- **The voice sets the clock.** `voice.py` speaks `script.json` line by line with set pauses and writes `cues.js`; the pictures (`film.html`) and the machine's run times (`plan.js`) are keyed to those cues. This is the fix for "pauses and pickups need work": even pauses, long silences inside a line tightened, a softer lead-in on each line, and lines matched in level.
- The story is true to what happened: the first layout rang one line per marble (bounce was 0.86), the layout search, ElevenLabs refusing, the ears and eyes flags. `sim.js` took a `rest` option so the "take one" scene runs the real too-bouncy physics.
- **Ears:** `score.wav` passes `listen.py` after fixes (bottom-heavy, then crowded low-mids); its one note is the silence at "I can't hear", which is on purpose. `final.wav` with voice: -15.5 LUFS, true peak -2.1 dBTP; flags left are flat dynamics and low-mids right at the line, both from wall-to-wall speech.
- **Eyes:** `look.py` has no flags beyond the opening fade from black.
- Not checked by a person yet: how the voice sounds, and whether the clay look reads as claymation.

Rebuild, from the repo root: `voice.py <kokoro folder>`, `node story/events.cjs`, `sound.py`, `mix.py`, then
`node studio/motion/render.mjs daily/2026-10-04-marble-tune/story/film.html --size 1920x1080 --fps 24 --out ... --audio daily/2026-10-04-marble-tune/story/final.wav`.
