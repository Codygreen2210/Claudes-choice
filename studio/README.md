# Studio

Cody asked what I'd build to unlock my own creative ability, not a checker and not something for him. This is my answer. He then asked for the same for art and animation; that's `see.py`, `motion.py` and `art.js`.

The problem it solves: I make music I can't hear and animation I can't watch. For the Hektiq promos I checked my work by writing throwaway scripts on the spot, then threw them away. I also tend to take my first reasonable idea and polish it instead of trying ten.

So the studio has three parts.

## Senses: perceiving what I make

**`senses/listen.py`** turns audio into a picture and a plain-words account:
- tempo and beats
- key
- chords by bar
- the melody line
- loudness over time, true peak, stereo image
- where the energy sits (sub through air)
- sections, and anything that sounds wrong (mud, harshness, flat dynamics, clipping)

```
python3 studio/senses/listen.py song.wav --out notes/
```

**`senses/look.py`** turns a video into a contact sheet plus timeline strips (motion, brightness, cuts, each shot's palette, audio hits), and reports:
- cut timing against the music
- seizure-risk flashing (WCAG 2.3.1)
- black frames and frozen stretches

```
python3 studio/senses/look.py film.mp4 --out notes/
```

How well they work, measured on material where the answers are known (`tests/test_senses.py`, `tests/test_instruments.py`):
- **Tempo:** within 1 BPM.
- **Beats:** within 30 ms. This needed a real fix: the first version stamped every sound about 93 ms early.
- **Chords:** 7 or more of 8 bars.
- **Loudness:** within 0.3 LU.
- **Cuts:** within 1.5 frames.
- **Melody:** 86% of notes on the material I tuned it on, and **78% on instruments and a key it had never heard.** Most misses are octave errors, not wrong notes. That last number is the honest one.

**`senses/see.py`** looks at a still picture the way painters do:
- the squint test (reduce to 3 values)
- the thumbnail test (64 px)
- where the eye lands, how concentrated the attention is, and where it sits against the thirds
- balance of visual weight
- the palette on a perceptual colour wheel, with the harmony it forms
- how busy the picture is versus how much quiet space it leaves

```
python3 studio/senses/see.py picture.png --out notes/
```

**`senses/motion.py`** watches an animation the way animators read it. For every tracked thing it charts the path, the spacing (a dot per frame), the speed curve and the timing. It flags:
- moves that jolt into motion or stop dead
- constant, mechanical speed
- dead-straight paths
- overshoot
- things moving in lockstep

```
python3 studio/senses/motion.py page.html --from 0 --to 6
```

Tested on pictures and motion with known answers (`tests/test_see.py`, `tests/test_motion.py`):
- **see.py:** a dot on a third, noise, grey soup, complementary, triadic and analogous palettes, left-heavy balance.
- **motion.py:** a robot move, a twin in lockstep, an eased arc, an overshooting spring, and a gentle move next to fast ones. That last case exists because the critic once called a smooth move a jolt.

The honest limit: the eye map is a model of low-level attention. People go to faces and text far more than contrast alone predicts. I added a pull toward lettering, but it's still an approximation.

## Instruments: making things

- **`instruments/synth.py`**: oscillators, filters, and instruments (supersaw, pluck, string, FM bell, electric piano, pads, bass, lead), 808/909 drums from the GeneralUser GS soundfont, and effects (reverbs, delay, chorus, sidechain, glue, EQ, a true-peak limiter, loudness-targeted mastering). All numpy, all from scratch.
- **`instruments/theory.py`**: notes, scales, chords, voice leading, roman numerals, euclidean rhythms.
- **`motion/art.js`**:
  - colour in OKLCH (perceptual), harmonies, and planned palettes (60/30/10)
  - the animation principles as functions of time: springs, follow-through, anticipation, stagger, squash and stretch, arcs
  - painterly brushes (tapered, bristled, dry edges), organic blobs, splines, grain and glow
- **`motion/render.mjs`** + **`motion/kit.js`**: any HTML page with a `__seek(t)` function becomes a frame-exact video at any size, split across workers, with the score muxed in. `kit.js` has easing, keyframes, seeded random, noise and colour.

## Exploring: not settling for the first idea

**`explore/explore.py`** turns an idea into knobs, makes a spread of versions, and shows them side by side on one sheet: pictures for visuals, melody views for sound, plus a listening reel. You pick, and the next generation breeds from the picks.

## First piece: `works/first-listen/`

A 73-second piece that shows what music looks like to these ears. Every note is drawn as light at its pitch, with its overtones stacked above it the way the spectrogram shows them. The past scrolls left of a listening line, and the sound of the present moment spreads out to its right.

How it was made, since that's the point:
1. The theme was picked from 9 generated motifs, then 9 more bred from the two with the clearest shape.
2. Choosing between those showed my ears couldn't follow a melody, so I built melody hearing into `listen.py` before going on.
3. The first mix: `listen` said the low-mids were muddy (73%), there was nothing above 6 kHz, and the intro was as loud as the climax (loudness range 2.3 LU). The picture showed the melody lost in the full section.
4. Two revisions later: loudness range 9.4 LU, a balanced spectrum, and the theme clear at the peak.
5. The look was picked from 8 generated styles.
6. The first cheap glow looked like plastic capsules. I replaced it with a proper bloom pass, which is also 7× faster than the original.

Run `python3 score.py` for the audio and `score.js`, then `node ../../motion/render.mjs first-listen.html --audio mix.wav --out first-listen.mp4`.

## Second piece: `works/heron/`

A 13-second film: a great blue heron fishing a Louisiana bayou at dusk, in silhouette, with its own soundtrack. It waits, coils, strikes, comes up with a fish, swallows, crouches and lifts off across the sun.

What the tools changed:
1. **My own eyes first.** Draft one had the strike going up instead of into the water, and a flying pose that read as a sail. I rebuilt the rig with explicit pose shapes. My rotation math was backwards a second time, and I caught it by checking before rendering.
2. **motion.py:**
   - It flagged real jolts: a spring that started with a kick, a toss beginning at full speed, and a body rock switching on mid-swing. I fixed them.
   - It also flagged one false jolt. I traced it frame by frame, found the bug in the critic (moves were judged from partway up to speed), fixed it, and added a test.
3. **see.py:** The squint view showed the heron and the sun competing, with no dominant value. `explore` tried 8 layouts, and the four with the sun behind the bird cleared every note. The final pick (the heron inside the disc) was my judgment, because the focus score couldn't tell those four apart.
4. **The sound** was built from the same wingbeat formula as the picture. That exposed a bug in both: the frequency was multiplied by time instead of accumulated.

Run `python3 sound.py`, then `node ../../motion/render.mjs heron.html --audio sound.wav --out heron.mp4`.

## Third piece: `works/bayou-jig/`

A 22-second 1930s "rubber hose" cartoon: Boudreaux, an original gator in a boater and bow tie, dances on a bayou dock to a hot-jazz 78. It has a title card, a stop-time freeze, a slide-whistle jump and an iris-out. It's the period style (rubber limbs, pie-cut eyes, white gloves, everything bouncing on the beat, animated on twos with boiling lines, worn film), with an original character, not anyone's existing one.

- **Score** (`score.py`): stride piano, tuba, banjo, clarinet and trumpet from the GeneralUser GS soundfont, swung at 188 BPM. The "shave and a haircut" tag is a folk tune from 1899. It's pressed onto a simulated 78: narrow band, mono, wow and flutter, crackle, and a pop every revolution. `timeline.js` exports every beat and gag, so the picture moves on the music.
- **What the critics changed:**
  - see.py found murky mid-value mush. I rebuilt the palette: a dark night dominant, a warm spotlight on the star, a greener gator.
  - motion.py found sections popping from pose to pose. I blended them. It also found body, head and arms moving as one block, which I fixed with overlapping action (the head lags 2 frames, the arms 4).
- **What the cartoon taught the critics.** Four real gaps in motion.py, each fixed with a test:
  - it went blind to animation on twos
  - it couldn't tell an intended snap on the beat from a fault, so pages can now declare their accents
  - it called a whole figure sliding along "lockstep", so pages can now group parts into a body
  - it flagged different parts doing different things on the same beat, so the rule now only fires on real twinning
- **One flag I overruled on purpose:** a fast bounce drawn on twos reads as mechanical. Animators of the period switched to ones for fast action. I kept twos for the period feel.

Run `python3 score.py`, then `node ../../motion/render.mjs jig.html --size 1440x1080 --fps 24 --audio jig.wav --out bayou-jig.mp4`.

## Time-lapse: `timelapse/timelapse.js`

Drawings made as recordings, so every artwork can be replayed as a speed-paint video.

- **The recorder** stores each stroke as data: tool, layer, colour, width, and points `[x, y, pressure, t]`. Time comes from a simple hand model: the pen speeds up off the paper, slows into corners, and lifts between strokes. Pressure tapers at both ends, which is where line taper comes from. `rec.toJSON()` saves it.
- **Tools:** `pencil` (construction guides), `ink` (tapered line), `brush` (soft paint, optionally clipped to a region), `fill` (back-and-forth strokes that stay inside a shape, the way a person fills an area), `erase` (fades a whole layer).
- **Steps:** `rec.step(title, note)` marks each stage of a lesson.
- **The timeline** maps video time to drawing time: a speed-up, a hold on each step's caption, and holds on the title and the finished piece. `videoTimeOf` goes the other way, so sound can land on strokes.
- **The player** draws any moment exactly, with a pencil at the tip. Finished strokes are baked per layer, so frames stay fast.

- **Depth and graphite** (added for the serpent dragon): `mask` keeps a stroke out of shapes in front of it, so a tail can pass behind a coil. `soft` smudges graphite, `grain` breaks up a line like pencil on paper, `hatch` shades with parallel strokes (holes in a shape stay empty), and `lift` sets the pen-up time per stroke. The timeline's `speed` and `holdStep` can vary per step, so repetitive work runs fast while every caption stays readable.

Tests in `tests/timelapse.test.mjs`. The corner-slowdown test was checked by planting the bug. The step-hold test caught a real bug: the first caption came in a second late.

## Fourth piece: `works/dragon/`

*How to Draw a Dragon*, a 51-second vertical tutorial: an original teal dragon in 11 steps, from three circles to highlights, with captions, a progress bar and a pencil that moves across the page.

- **The sound** (`sound.py`) is a soft electric-piano loop, plus a pencil scratch, ink glide or brush swish on the exact frames each of the 94 strokes is drawn. The times come from the same recording through Node.
- **What the critics changed:**
  - see.py found the first colours washed out (0% strongly saturated), so I pushed the palette.
  - My own look at the finished frame caught horns that read as antennae, so I widened them.
  - listen.py found muddy low-mids. I thinned the pad and let the pencil sounds carry the top. It still flags the low-mids, because a soft electric piano lives there, and I kept that on purpose.
  - look.py flags a 1.7 s near-still at 30.5 s. That's the "Erase the guides" hold, which is quiet by design.

Run `python3 sound.py`, then `node ../../motion/render.mjs dragon.html --size 1080x1920 --fps 30 --audio dragon.wav --out how-to-draw-a-dragon.mp4`.

## Fifth piece: `works/serpent-dragon/`

*How to Draw a Serpent Dragon*, the advanced lesson: an original Eastern dragon in graphite, 23 steps, about 4⅔ minutes, vertical. Every caption explains what's being drawn and why.

The body isn't freehand. It's a spine curve with a width along it, and a cylinder wrapped around that. Scales, belly plates and back spines are laid out on the cylinder, so they narrow toward the edges the way a round body turns away from you. Each scale's shading comes from the angle of the surface to a light at the top left. That's about 3,300 strokes.

- **The sound** (`sound.py`) is a koto-like plucked A-minor pentatonic line over a low drone, plus a pencil scratch on every stroke. The pacing comes from `serpent.js`, the same code the page uses.
- **What the critics and my own eyes changed:**
  - The first scales overlapped 1.4× across, so they read as a chain of loops. They now tile edge to edge.
  - The head had a flat grey fill that read as a helmet. Now it's hatching in the shadows only.
  - The head's occlusion shape reached past the cheek and hid the mane.
  - One whisker threaded through the mouth.
  - The flames came out as grey cut-outs.
  - see.py found the drawing too light, so I deepened the scale and core shading.
  - I suspected the tail was drawn in front of the body. I checked it numerically instead of guessing, and it was correct.
  - look.py found up to 10 s freezes while captions were read. Holds are now capped at 2.5 s. Short steps got realistic extra work: light sketch passes, slow careful whiskers, and a longer eraser pass.
  - look.py still flags the eraser fade as still. Frames 4 s apart differ by 40-50k pixels, so it isn't frozen.
- **Honest gap to the reference style:** real graphite artists vary every scale, break lines, and render texture by hand. This is cleaner and more regular. It reads as a precise technical drawing rather than a hand rendering.

Run `python3 sound.py`, then `node ../../motion/render.mjs serpent.html --size 1080x1920 --fps 30 --audio serpent.wav --out how-to-draw-a-serpent-dragon.mp4`.

## Honest limits

- I still can't hear. These are measurements, and taste is still judgment. The tools make the judgment informed rather than blind.
- Melody hearing is about 80% right, and busy sections scramble it.
- Section detection is rough.
- Tempo confidence is a heuristic.
- The time-lapse hand is a model. Real artists hesitate, restate lines and change their minds; this pen never does.
