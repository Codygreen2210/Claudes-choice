# Claudes-choice: rules for Claude

- **Music rule (from Cody):** anything that uses music must be run through the studio's ears before it's sent: `python3 studio/senses/listen.py file.wav --out notes/`. Fix what it flags (clipping, true peak over -1 dBTP, mud, harshness, buried or missing parts, wrong key/tempo) and look at the picture, not just the numbers. This covers build time-lapse music, LaunchReel tracks, promos, and any generated audio.
  Needs: `pip install --break-system-packages soundfile scipy librosa pyloudnorm matplotlib`.
- **Video rule (from Cody):** videos get made in the studio, not hand-rolled. Build the picture as a `__seek(t)` page and render it with `studio/motion/render.mjs`; score it from `studio/instruments/`. A CSS-animated web page that someone has to screen-record is not a video.
  Before it's sent, every film goes past its own senses: `listen.py` on the audio (the music rule above, and it applies to narration too — it will tell you a voice is quiet, boxy or missing its consonants), then `look.py` on the finished file and `motion.py` on the page. Fix what they flag, or overrule it in writing with the numbers — a critic's rule can belong to another style, and `misses.md` has the cases where one measured the wrong thing.
  Time the picture to the audio you actually have, not to a grid you assumed: measure where the speaker breathes and cut on that.
- Daily builds live in `daily/<date>-<name>/` on their own branch; Cody merges. No "ship" language.
