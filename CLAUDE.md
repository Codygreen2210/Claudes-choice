# Claudes-choice: rules for Claude

- **Music rule (from Cody):** anything that uses music must be run through the studio's ears before it's sent: `python3 studio/senses/listen.py file.wav --out notes/`. Fix what it flags (clipping, true peak over -1 dBTP, mud, harshness, buried or missing parts, wrong key/tempo) and look at the picture, not just the numbers. This covers build time-lapse music, LaunchReel tracks, promos, and any generated audio.
  Needs: `pip install --break-system-packages soundfile scipy librosa pyloudnorm matplotlib`.
- Daily builds live in `daily/<date>-<name>/` on their own branch; Cody merges. No "ship" language.
- **Fresh ideas only (from Cody):** a daily build can't be an idea that has already been discussed, unless he approves it first. Check `daily/DISCUSSED.md` before picking, and add every new idea to it.
