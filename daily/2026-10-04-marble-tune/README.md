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
