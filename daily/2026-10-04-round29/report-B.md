# Report B: why people keep playing

**Trend (2025-26)**
- Match and puzzle retain best: D1 32.7%, D7 14.0%, D30 7.2% (match) vs hypercasual 29.3 / 5.9 / 1.4 ([Mistplay via Segwise](https://segwise.ai/blog/mobile-gaming-app-user-retention-strategies)).
- Block Blast: 870M downloads, 17.3M DAU, but D30 only 1.1% ([Udonis](https://www.blog.udonis.co/statistics/block-blast)). Installs are not staying.
- Smash Fest!: 2.9M downloads in a month, #1 US iOS June 2026, no meta, no passes; retries from near-misses and sound ([Foxdata](https://foxdata.com/en/blogs/how-smash-fest-hit-1-on-the-us-app-store-with-zero-paid-uaand-what-it-means-for-hybrid-casual/)).
- Hypercasual without progression dies; Archero added light meta ([DoF](https://www.deconstructoroffun.com/blog/four-reasons-why-the-hypercasual-gold-rush-is-coming-to-an-end)); about 60% quit when too hard too fast (Segwise).
- Streaks only help real daily loops (8.1% of apps in 2025, down from 14.0%) ([Lazyweb](https://labs.lazyweb.com/research/are-streaks-still-spreading-beyond-duolingo.md)).

**Reasons to play, proven:** (1) a score or board you can beat by skill; (2) near-miss retries with limited tries; (3) physical sound and feel; (4) a light visible goal; (5) one shared daily puzzle.

## Idea 1: Cannon Collapse (own name TBD)
1. Drag back and release to fire at a stacked tower; limited shots; knock every block off the platform.
2. First 30s: tower of crates and glass, three shots; second shot nearly clears it, one block left teetering. "One more go."
3. Reason: aim and angle improve with practice; fewer shots = more stars; chain reactions and per-material sound are satisfying each second.
4. Tomorrow: one shared daily tower, same for everyone, share the shot count. Week: star map of 3-star levels.
5. Borrows Smash Fest (2.9M, #1 US) mechanics; twist: daily shared tower plus a ghost replay of friends' shots.
6. Hard: physics tuning, levels. Use matter.js; levels generated from seeded stack recipes, auto-checked solvable by a bot. Sound by Web Audio.
7. Stranger finds it: portals (CrazyGames), shared daily card. 30 days: low 100, likely 600, high 5,000.

## Idea 2: Grid Run, daily seeded block puzzle
1. Drag three pieces onto a 8x8 grid; same piece sequence for everyone each day.
2. First 30s: board half-full, a three-line clear at hand; combo meter.
3. Reason: score chase against a fixed daily seed, personal best, replayable skill.
4. Tomorrow: new seed and streak; week: best-week total.
5. Borrows Block Blast (17.3M DAU, D30 1.1%); twist: shared seed so scores compare, which Block Blast lacks.
6. Easy: no levels, a seeded random generator. Hard: fairness of pieces.
7. Find: share-grid text like Wordle. 30 days: low 80, likely 400, high 3,000.
