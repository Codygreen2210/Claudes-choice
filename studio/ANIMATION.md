# Animation: what I studied, what the studio can do now, and what is still missing

Cody's brief (Oct 4, 2026): build an animation studio "on par with Pixar", study animation and storytelling, start with character animation.

## The honest size of this
A Pixar film is hundreds of people for four to six years, with 3D lighting, cloth, hair and crowds. This studio is 2D shapes drawn by code, made in an evening by one model that cannot watch its own work. It will not be on par. What it can do is take the same craft rules those animators work by and build them in, one at a time, and measure each. That is the plan below.

## What I studied
The twelve principles from Thomas and Johnston's *The Illusion of Life* (1981), read against the three videos made this week. Where each stood before tonight:

| Principle | Before | Now |
|---|---|---|
| Squash and stretch | none on characters | `Actor.squash`: stretch along the path, volume kept; crouch squashes on landing |
| Anticipation | none | `antic` on any beat: a pull the other way first |
| Staging | by eye | unchanged (`see.py` helps on stills) |
| Pose to pose | positions keyed, no poses | `actor.js`: named poses on beats |
| Follow-through, overlap | everything moved together | per-part lags (eyes lead, arms trail, never the same lag twice) and a spring settle |
| Moving hold | host breathed a little | `alive` drift per part |
| Slow in, slow out | yes (easing) | yes; the settle curve also starts gently |
| Arcs | cheetah feet only | hops travel a thrown arc |
| Secondary action | mouth flap only | brows, eye widening, blinks before a look |
| Timing | one speed for everything | `dur` per beat; nothing chooses it for me yet |
| Exaggeration | none | crouch and stretch amounts are mine to push |
| Solid drawing, appeal | flat blob with eyes | the Lump puppet has arms, feet, brows; still very simple |

## The first tool (built tonight)
- `motion/actor.js`: pose-to-pose performance engine. Tested in `tests/actor.test.mjs` (7 tests: pull-back direction, overshoot, lead and trail order, plain mode, no teleporting, hop arc, volume kept).
- `motion/puppet.js`: Lump, the clay host, as a rig actor.js can perform.
- `motion/clay.js`: the clay and yarn drawing kit, moved here from the cheetah film.
- `works/acting-test/`: the same eight poses played twice, plain and acted, side by side (`acting-test.mp4`).

What the motion critic (`senses/motion.py`) said:
- First run: it called the acted moves **jolts**. It was right: my settle curve reached full speed in under three frames. I gave the curve a slow start; the jolts are gone.
- The hop leaves and lands as hits. Those are marked as intended accents, the way the critic expects.
- It does **not** score the acted side higher than the plain side. Eased moves already pass it. Anticipation, overlap and squash are things it cannot see yet, so the difference is judged by eye for now. Teaching the critic to see them is on the list.

## What is missing, in the order I would build it
1. **Voice and script** (Cody asked for this too): how narration is planned for the ear: beats, emphasis, breath, where the picture should carry it instead of words. Then pitch and pause shaping on the voice.
2. **Story planning**: a step every episode passes before any drawing: who wants what, what goes wrong, what changes; a beat sheet and thumbnail boards.
3. **Acting from the voice**: drive brows, eyes and gestures from the script's emphasis, not just a mouth flap.
4. **Critic for acting**: measure anticipation, overlap between parts of one body, and squash, so "better" is a number.
5. **Limbs with weight**: walk and run cycles with planted feet for two-legged characters (the cheetah rig is a start).
6. **Light and depth**: layered sets, cast shadows that move, depth of field.

Source: [Twelve basic principles of animation](https://en.wikipedia.org/wiki/Twelve_basic_principles_of_animation), summarising Thomas and Johnston.
