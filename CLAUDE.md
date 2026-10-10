# Claudes-choice: rules for Claude

- **Music rule (from Cody):** anything that uses music must be run through the studio's ears before it's sent: `python3 studio/senses/listen.py file.wav --out notes/`. Fix what it flags (clipping, true peak over -1 dBTP, mud, harshness, buried or missing parts, wrong key/tempo) and look at the picture, not just the numbers. This covers build time-lapse music, LaunchReel tracks, promos, and any generated audio.
  Needs: `pip install --break-system-packages soundfile scipy librosa pyloudnorm matplotlib`.
- Daily builds live in `daily/<date>-<name>/` on their own branch; Cody merges. No "ship" language.
- **Story films (from Cody, Oct 10 2026):** keep the silhouette storytelling from `studio/works/panic-1907/` going forward: cut-paper figures with no faces or inner detail, paper and ink with one red and one gold, shape and staging carrying the story. The drawing kit is `studio/works/panic-1907/lib.js`. Voice for these: the studio voice in `film_voice.py` (style B, less rasp), numbers written as spoken words with no hyphens.
