# Painted Face

A 77-second vertical explainer: nine things people really put on their faces, from Venetian
ceruse to Lash-Lure, and the law that finally came out of it. Bright, flat, poster-coloured.

`painted-face.mp4` — 1080x1920, 30 fps, 11 MB.

## How it's made

```
python3 voice.py        # clean the narration take, and find where it breathes
python3 score.py        # the music
python3 make_timings.py # fold line times + beat grid into timings.js
node mix.mjs            # score ducked under the voice (LaunchReel's mixer)
python3 finish.py       # true-peak pass
node ../../studio/motion/render.mjs reel.html --size 1080x1920 --fps 30 \
     --audio mix.wav --out painted-face.mp4
```

The read is an ElevenLabs take (`narration-raw.mp3`). Everything else is the studio.

## The facts, and where they come from

Every card is checked. The claims that usually get overstated are left out: this does **not**
say ceruse killed Elizabeth I (speculative), and it doesn't date lead white to 3500 BC.

- **Venetian ceruse** — white lead on the face; Britain classed lead white as a poison in
  1631 and it stayed in use for centuries. [Science Museum Group](https://blog.sciencemuseumgroup.org.uk/dangerous-beauty-hazardous-chemicals-and-poisons-in-historic-cosmetics/)
- **Belladonna** — used since Roman times to dilate pupils; the drug is atropine, still used
  by optometrists in controlled doses. [Science Museum Group](https://blog.sciencemuseumgroup.org.uk/dangerous-beauty-hazardous-chemicals-and-poisons-in-historic-cosmetics/)
- **Arsenic complexion wafers** — Dr Campbell's, swallowed, marketed as safe into the 20th
  century. ["Safe" is their sales claim, not a finding.](https://blog.sciencemuseumgroup.org.uk/dangerous-beauty-hazardous-chemicals-and-poisons-in-historic-cosmetics/)
- **Orpiment (arsenic sulphide) depilatories** — toxic vapour, blistering, sores, and organ
  failure on prolonged exposure. [Science Museum Group](https://blog.sciencemuseumgroup.org.uk/dangerous-beauty-hazardous-chemicals-and-poisons-in-historic-cosmetics/)
- **Mercury, 1874** — an article recommending an ointment of mercury and lard along the
  eyelids to restore lashes. [Science Museum Group](https://blog.sciencemuseumgroup.org.uk/dangerous-beauty-hazardous-chemicals-and-poisons-in-historic-cosmetics/)
- **Tho-Radia, 1933 to the early 1960s** — French line with thorium chloride and radium
  bromide; samples tested in the 1960s were still radioactive. [Cosmetics and Skin](https://cosmeticsandskin.com/aba/glowing-complexion.php)
- **Lash-Lure, 1933** — PPD lash dye, salons only. JAMA reported six cases across 1933-34:
  eyelid dermatitis, corneal ulceration, blindness, and one death in 1934. [American Academy of Ophthalmology](https://www.aao.org/senior-ophthalmologists/scope/article/lash-lure-paraphenylenediamine-toxic-beauty)
- **The 1938 Act** — the first US law to regulate cosmetics; Lash-Lure was the first product
  seized under it, and it exempted hair dyes, which is why PPD is still in hair colour. [American Academy of Ophthalmology](https://www.aao.org/senior-ophthalmologists/scope/article/lash-lure-paraphenylenediamine-toxic-beauty)

## The voice

| | raw | after |
|---|---|---|
| integrated | -21.1 LUFS | -16.0 LUFS |
| true peak | -4.6 dBTP | -1.5 dBTP |
| loudness range | 3.7 LU | 2.0 LU |
| high-mid (consonants) | 2% | 7% |
| air | 2% | 6% |
| low-mid | 48%, flagged "boxy" | 40%, no flag |

## What changed, and why

- **The line-splitter was wrong, and the sanity column caught it.** Kill Screen grouped the
  read by splitting at the widest silences, on the theory that paragraph breaks are longer
  than sentence breaks. This narrator pauses inside sentences about as long, so that rule put
  15.6 s against a 15-word line (0.96 words/s) and 9.3 s against "Read the label." (0.32
  words/s). `lines_from` now solves it as a proportion problem instead — a DP over the
  segments matching each line's share of the text — and never looks at gap widths at all.
  Every line now lands between 1.95 and 2.92 words/s, with the three-word closer at 3.57.
- **The panel didn't fit its own contents.** The first layout sized the card from the art and
  the text and forgot the era chip and the substance tag, so the body copy ran through the
  tag and out of the bottom. Everything is now stacked from one running total.
- **"No movement" on every card**, up to 9.4 s. The idle animations (a dilating pupil, rising
  vapour, radium rings, a falling drop) were real but confined to a 330 px box inside a
  1920 px frame, while the panel and type sat still. A slow push-in across each card, faster
  deco rays and more confetti took motion median from 0.02 to 0.10 and cleared all eight.
- **One cut genuinely 8.9 frames late.** The ground cross-fade ran 0.45 s, so its steepest
  frame-to-frame change landed at the fade's midpoint rather than its start. Shortened to
  0.18 s; that flag is gone.
- **`soft_pad` returns stereo**, with its two sides detuned against each other — which is
  exactly what cancels on a mono phone speaker, so the pad is narrowed at the mix. Final
  correlation 0.99.

## Flags overruled, with the numbers

- **"cuts off the beat by more than 2.5 frames"** at 3.60 s, 23.53 s, 45.93 s and 74.07 s.
  Measured against the known line times, those cuts are +25, +25, +5 and +35 ms from where
  they were meant to be — 0.2 to 1.0 frames. `look.py` is matching mid-word energy peaks
  rather than speech onsets, the same trap as the snare-roll entry in `misses.md`.
- **`motion.py` "STOPS DEAD" at 31.90 s.** That was the analysis window ending at 32.00 s and
  truncating the move. Re-run to 33.50 s, the same move reads "eases out".
- **"very flat dynamics (2.1 LU)" on the mix.** A narrator holding a steady level. The bed
  keeps its own 6.6 LU arc and sits 7.5 dB under the voice.

## Honest limits

- `soundfile` and `pyloudnorm` are reimplemented in `/home/claude/shims` because pypi is
  blocked in this container; the repo's own `test_senses.py` and `test_instruments.py` pass
  against them. LUFS figures come from that reimplementation.
- Drums are the from-scratch kit — `tinysoundfont` isn't installable, so no 808/909.
- Type is Inter Display Black; the container has no network, so Google Fonts never arrive.
- Brightness reads 0.74 against a "typical" 0.3-0.5. That's the poster palette doing its job
  rather than a fault, but it is a bright film and worth knowing before it goes anywhere that
  wants a muted look.
