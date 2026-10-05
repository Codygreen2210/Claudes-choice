# How a cheetah runs (teaching video, clay look)

`how-a-cheetah-runs.mp4`: 1920x1080, 24 fps, 2:18. Cody's brief: narrated, shows how the running works by revealing the muscle structure, energetic like a nature show. Sent to him for approval; not posted.

## What it claims, and where each claim comes from
- 58 mph (93 km/h) clocked on a wild cheetah with a tracking collar; grip and turning mattered more than top speed; 367 runs by 5 cheetahs; average run 173 m; about four times the power of the fastest human sprinter: Wilson et al. 2013, Nature (via ScienceDaily's summary).
- 0 to 45 mph in about 2.5 seconds; stride about 7 m; spine works as a spring for the back legs; semi-retractable claws; tail as a rudder: Smithsonian's National Zoo.
- Stride rate rises with speed (2.4 to 3.2 a second measured): Hudson et al. 2012.
- They do not stop hunts because they overheat: Hetem et al. 2013 (via National Geographic).
- From general cat anatomy, not looked up for this video: two airborne moments per stride (stretched and tucked), shoulder blades not fixed by a collarbone, the biggest muscles high on the back legs and along the spine. Worth a second check before it goes up.
- "Longer than a big pickup truck": 7 m against roughly 5.8 m; the truck is drawn to that scale.

## How it is made
- `script.json` -> `voice.py <kokoro folder>` -> `voice.wav`, `cues.js` (the voice sets the clock).
- `clock.js`: strides per second at every moment, keyed to the cues. `film.html` draws from it; `events.cjs` writes the footfalls for the sound.
- The cheetah is a rig in `film.html`: a bending spine, legs solved from where the feet must be (feet stay planted while down), a tail that lags. Bones and muscles are drawn inside the same pose.
- `clay.js`: the clay and yarn drawing kit, lifted out of the Marble Tune story film for reuse.
- `sound.py` -> `score.wav` (passes `listen.py` after fixes: it was bottom-heavy and dark, then thin and crowded). `mix.py` -> `final.wav`: -15.5 LUFS, true peak -2.3 dBTP; flag left: flat dynamics, from steady narration.
- `look.py`: no flags beyond the fade from black.

## Honest limits
- The anatomy is simplified clay, not a medical drawing: muscle shapes are blobs in the right places, not individual named muscles.
- The run cycle is built from rules, not traced from footage. At full speed it reads well; in slow motion the back legs look a little stiff.
- The voice model cannot do real excitement; the energy is in the words.

## Ending (Cody's change, Oct 4)
The sign-off no longer says "I'm Claude... a person checks this". It ends on a call to subscribe: animal facts, history's greatest battles, the world's craziest financial collapses. The end card keeps one small line, "animated and narrated with AI", so viewers are still told; Cody can drop it. The last 8 seconds were re-rendered and spliced onto the first render.
