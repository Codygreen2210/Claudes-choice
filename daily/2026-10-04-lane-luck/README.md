# Lane Luck

Was it bad luck, or was it you? Pick one of five checkout lanes, watch all five run, ten rounds. The card at the end splits the time you lost into luck and your own pick.

Static files, nothing to build, nothing to install to play. No network calls, no tracking, no cookies.

- `index.html`, `style.css`, `app.js`: the page.
- `sim.js`: the model, pure and seeded. `makeGame(seed)`, `scoreRound(round, lane)`, `summarize(results)`.
- `?s=<seed>` fixes the ten rounds and their hidden snags. `&vs=<n>` shows a friend's score to beat.

## Checks

    node --test daily/2026-10-04-lane-luck/test/
    python3 -m http.server 8765 --directory daily/2026-10-04-lane-luck   # then, in another shell:
    node daily/2026-10-04-lane-luck/tools/play-check.mjs http://localhost:8765
    node daily/2026-10-04-lane-luck/tools/make-og.mjs                    # redraws og.png

Balance over 2,000 seeded games: always picking the best lane on paper wins about 7 of 10; picking at random wins about 2 of 10.

After putting it online, set the absolute URL on `og:image` and `og:url` in `index.html`.
