# Scout A report: what is on top of phone charts, 2025 to 2026

**Trend**
1. Money and installs are shrinking, puzzle is the exception: H1 2026 IAP $40B (-2%), downloads 24B (-12%), puzzle revenue nearly +20% ([PocketGamer.biz](https://www.pocketgamer.biz/mobile-gaming-iap-dipped-2-as-ad-spend-climbed-in-h1-2026/)).
2. Hybrid casual is the only segment with +20% IAP in 2025, and plain casual D7 retention has fallen since 2022 ([Sensor Tower](https://gamedevreports.substack.com/p/sensor-tower-state-of-gaming-2026)).
3. New puzzle loops win installs: block +2,900% to $183M, sort $280M, screw $206M; Screwdom D30 about 17% ([Naavik](https://naavik.co/digest/how-niche-subgenres-are-reshaping-the-mobile-puzzle-market/)).
4. Q2 2025: Color Block Jam $42M on 21.8M installs, All in Hole $22.3M on 3.4M ([AppMagic](https://gamedevreports.substack.com/p/appmagic-top-10-hybrid-casual-games)).
5. Block Blast: 70M daily players, drag shapes, endless score ([PocketGamer.biz](https://www.pocketgamer.biz/block-blast-reaches-70m-daily-active-users-and-300m-monthly-active-users-worldwide)). H1 2026: sort revenue tripled, 2,000+ block releases ([Gamigion](https://www.gamigion.com/mobile-casual-games-report-h1-2026-analysis/)).

## Idea 1: Bolt Rush (screw puzzle as a 3-minute run)
1. Tap screws on stacked plates to move them into a 4-slot color tray; tap only.
2. First 30 s: board of 3 plates, 12 screws. Clear it in 20 s; the next board is bigger and the tray is already half full. "One more" is the first board where you nearly jam the tray and recover.
3. Reason to play: planning order so the tray never jams; each board adds one color. Score is boards cleared in 3 minutes; beat your best and a friend's link score.
4. Tomorrow: the same seeded 3-minute run for everyone (compare scores via link). Next week: new plate shapes unlock by best score.
5. Borrows Screwdom ($27.1M Q2 2025, D30 17%). Twist: a scored timed run with identical seeds instead of endless levels with paid continues.
6. Yes. Levels come from a generator plus a solver that checks solvability and measures slack; hard parts are tuning difficulty and plate art (flat shapes, no 3D).
7. Finding: Show HN and a challenge link. 30 days: low 50, likely 300, high 3,000 (a lottery; portals pay about 1.20 euros per 1,000 plays).

## Idea 2: Hungry Hole (hole game with hunger)
1. Drag a hole across a top-down board; it swallows things smaller than it and grows.
2. First 30 s: you eat crumbs, then cans, then a car; the board gets crowded and a clock starts. "One more": you fail by 2 items.
3. Reason: route planning, eating small items fast to get big enough before a hunger meter drains. Beat your own ghost path.
4. Tomorrow: daily layout with ghost of your best run. Next week: new boards.
5. Borrows All in Hole ($22.3M Q2 2025) and Attack Hole (60M+ downloads). Twist: hunger meter makes every second tense; no level quotas.
6. Yes. 2D canvas, circle math, generated item scatter; hard part is feel and balance.
7. Same as idea 1; likely 200 players in 30 days.
