# Honey

A 64.7-second animated film: one drop followed from a flower to a face. The bee drinks the
nectar, carries it home, the hive dries it into honey and caps it, it is poured into the
things you buy, and it ends on skin. Beginning, middle, end.

`honey.mp4` — 1080x1920, 30 fps, 24 MB.

`look.py` reads the whole film as **0 cuts, one 64.70-second shot**. That is the point: the
earlier card-based builds in this repo read as 10 to 14 cuts.

## How it's made

```
python3 voice.py        # clean the narration, and find where she breathes
python3 score.py        # the music
python3 make_timings.py # fold line times + beat grid into timings.js
node mix.mjs            # score ducked under the voice (LaunchReel's mixer)
python3 finish.py       # true-peak pass
node ../../studio/motion/render.mjs reel.html --size 1080x1920 --fps 30 \
     --audio mix.wav --out honey.mp4
```

The read is an ElevenLabs take. Everything else is the studio.

## The story, scene by scene

Each scene is one narrated line, and the scene times come from the take itself, so the
picture turns over on the words rather than on a grid.

| | scene | what moves |
|---|---|---|
| 1 | a flower | she arrives on an arc, decelerating, and the nectar climbs into her |
| 2 | the journey | the field streams past in two parallax layers; the hive slides in |
| 3 | mouth to mouth | the drop is handed along three workers, shrinking as water leaves |
| 4 | fan and cap | wings fan, the cell thickens and darkens, wax seals it across |
| 5 | that is honey | pull back to capped comb; one cell opens on sugar and three waters |
| 6 | why nothing grows | bacteria come at it and shrivel; peroxide comes off the surface |
| 7 | the dressing | a pad falls onto skin and the honey keeps working under it |
| 8 | skin, then hair | water is drawn in and held; then the same on strands, which smooth |
| 9 | what it will not do | sprouts start and come to nothing; two bars of evidence strength |
| 10 | the shelf, and out | it pours into soap, pump, balm and jar; a patch test; she leaves |

## The claims

Checked before scripting. Honey has real evidence behind some of this and none behind the
rest, and the film says so out loud rather than leaving the gap unmentioned.

- **Supported:** wound healing (the best-studied use, and why medical-grade honey is in
  licensed dressings), moisture (it is a humectant and an emollient), antibacterial action
  (very low water activity, mild acidity, and glucose oxidase producing peroxide).
- **Weaker:** acne and eczema — plausible mechanism, thin trial evidence. The film says
  "thinner" and shows it as a half-filled bar.
- **Not supported:** hair growth. The film states plainly that no good study shows it, and
  scene 9 animates the absence — sprouts that start and fail.
- **Caution:** patch test; avoid if bee stings or pollen are a problem for you.

Sources: [GoodRx dermatology review of honey for skin](https://www.goodrx.com/health-topic/dermatology/honey-benefits-for-skin),
[Honey in dermatology and skin care: a review (PubMed 24305429)](https://pubmed.ncbi.nlm.nih.gov/24305429/).

Scripture is King James, which is public domain. An early cut used Sirach 11:3, which is
apocryphal and not in Protestant Bibles; it was swapped for Judges 14:8.

## What the critics changed

- **The first version was slides, and was scrapped.** Ten set pieces with captions is not a
  film. The rebuild has a spine — one drop, one character — and that is what took the cut
  count from 14 to 0.
- **Everything was drawn too small.** The bee was about 8% of the frame height in a mostly
  empty sky. Characters and props were scaled up roughly twice over.
- **"No movement" on four stretches, the worst 10.4 s.** The first fix — a push-in across
  each scene, which had worked on two earlier films — moved the needle almost not at all.
  The reason is that roughly 85% of each frame was flat background, and scaling flat colour
  changes no pixels. The fix that worked was giving the whole frame content: a honeycomb
  lattice that drifts behind everything. Motion median went 0.06 → 0.12, every freeze flag
  cleared, and it lowered the blown-out 0.91 mean lightness at the same time.
- **The bee jolted into motion on frame one.** `motion.py` caught it. Her flight used an
  ease-out, which is right for decelerating into a landing but starts at full speed. Changed
  to ease-in-out so she accelerates from rest off camera: now "eases in, eases out, arcs".

## Flags overruled, with the numbers

- **`motion.py` "STOPS DEAD" on the drop at 5.63 s.** That run ended at 6.00 s and truncated
  the move. The 0–11 s run shows the same two drop passes as "eases in, eases out".
- **"very flat dynamics (2.2 LU)" on the mix.** A narrator at a steady level. The bed keeps
  its own 5.2 LU arc, ducks 5.2 dB under her, and she sits above it.
- **Brightness 0.84 against a "typical" 0.3–0.5.** Deliberate: it is a warm, bright film
  about honey. It was 0.91 and genuinely washed out; the lattice and a deeper ground brought
  it down. Worth knowing if it ever needs to sit next to something muted.

## Honest limits

- `soundfile` and `pyloudnorm` are reimplemented in `/home/claude/shims` (pypi is blocked
  here); the repo's own test suites pass against them. LUFS figures come from that.
- Drums are the from-scratch kit — `tinysoundfont` will not install.
- `listen.py` still calls the score's low-mids crowded. That band is the electric piano,
  which is the piece; the score is carved at 400, 760 and 2200 Hz to make room for her, and
  the measured result is the voice clearly over the bed.
- The animation is flat vector shapes, not drawn frames. It is a long way from the
  hand-drawn `studio/works/` pieces, and the bee is a shape that moves well rather than a
  character with weight.
