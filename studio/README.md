# Studio

Cody asked what I'd build to unlock my own creative ability, not a checker and not something for him. This is my answer.

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

## Instruments: making things

- **`instruments/synth.py`**: oscillators, filters, and instruments (supersaw, pluck, string, FM bell, electric piano, pads, bass, lead), 808/909 drums from the GeneralUser GS soundfont, and effects (reverbs, delay, chorus, sidechain, glue, EQ, a true-peak limiter, loudness-targeted mastering). All numpy, all from scratch.
- **`instruments/theory.py`**: notes, scales, chords, voice leading, roman numerals, euclidean rhythms.
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

## Honest limits

- I still can't hear. These are measurements, and taste is still judgment. The tools make the judgment informed rather than blind.
- Melody hearing is about 80% right, and busy sections scramble it.
- Section detection is rough.
- Tempo confidence is a heuristic.
