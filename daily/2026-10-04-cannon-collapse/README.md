# Cannon Collapse (rough version)

A phone browser game: pull back, let go, knock every block off the platform in as few shots as you can.
Plain boxes on purpose. This version exists to answer one question: after a near miss, do you want another go?

## Play
Open `index.html` from any static host (or `python3 -m http.server` in this folder). No build step, no network calls,
no tracking, no cookies, no accounts. Progress (stars, furthest level, sound on/off) sits in localStorage and the game
still works if storage is blocked.

- Drag anywhere to aim, let go to fire. The dotted arc shows only the start of the path.
- After a retry, a faint grey arc shows your last first shot, so the next go is a correction and not a guess.
- Wood is light and slides. Stone is heavy. Glass breaks on a hard hit. TNT blows its neighbours outward.
- From level 5 one shot is a heavy ball (marked H). Tap a ball in the Shots row to choose which goes next.
- Stars: 3 for one shot or two shots to spare, 2 for one to spare, 1 for clearing on the last shot.
- Restart is always one tap (or the R key).

## Files
- `levels.js` level layouts as data; add more by hand (format is at the top of the file)
- `game.js` physics, feel, sound, drawing, and the `window.__cc` test hook
- `vendor/matter.min.js` matter-js 0.20.0 (MIT, licence beside it)
- `sfx/` seven short effects as mp3, plus `listen-report.txt` from `studio/senses/listen.py`
- `tools/make_sfx.py` makes the effects with numpy (`--mp3` to encode)
- `tools/play-check.mjs` loads the game in headless Chromium and checks: no errors or outside requests, towers stand
  still, every level can be cleared, no level from 3 up is a gift, the near miss screen and the Again button work,
  and a real drag aims and fires. `--quick` for fewer samples, `--levels=3,7` for some levels only.

## Tuning knobs (top of `game.js`)
Ball speed range, gravity, material weights and grip, glass and TNT thresholds, blast size, settle timing.
After any change run the play-check; the table shows how often random play clears each level.
