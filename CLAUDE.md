# Claudes-choice: rules for Claude

- **Music rule (from Cody):** anything that uses music must be run through the studio's ears before it's sent: `python3 studio/senses/listen.py file.wav --out notes/`. Fix what it flags (clipping, true peak over -1 dBTP, mud, harshness, buried or missing parts, wrong key/tempo) and look at the picture, not just the numbers. This covers build time-lapse music, LaunchReel tracks, promos, and any generated audio.
  Needs: `pip install --break-system-packages soundfile scipy librosa pyloudnorm matplotlib`.
- Daily builds live in `daily/<date>-<name>/` on their own branch; Cody merges. No "ship" language.

## Usage rules (measured by `studio/usage/`, see its README)
- Big files: Grep first or Read a range. A hook stops whole-file reads over the cap in `studio/usage/data/config.json`.
- Tests, builds, installs: run through `python3 studio/usage/quiet.py "<command>"` so only failures and the tail come back.
- After each finished step, keep `notes/STATE.md` current in a few lines (decisions, files touched, next step) so a fresh session can pick up from it.
- Subagents only when asked. Tell each one to keep its report short.
- The usage journal commits and pushes its own files (`studio/usage/data/`) on work branches, never on main. Leave those commits alone.
- Idea rounds follow `daily/ROUND.md`: two inventors and one checker, reading `daily/LESSONS.md` (not the whole journal) and reporting in `daily/SCORECARD.md` form. Three agents unless Cody says otherwise.
