# Kill Screen

A 49.7-second vertical reel: eight retro-gaming facts, cut for Shorts, Reels and TikTok.
Original score, a narrated read, and a picture that cuts on the voice rather than on a grid.

`kill-screen.mp4` — 1080x1920, 30 fps, 37 MB.
`kill-screen-share.mp4` — the same film at crf 24, 14 MB, for sending around.

## How it's made

```
python3 voice.py        # clean up the raw narration, and find where it breathes
python3 score.py        # the music
python3 make_timings.py # fold line times + beat grid into timings.js
node mix.mjs            # score ducked under the voice (LaunchReel's mixer)
python3 finish.py       # true-peak pass, and check the bed isn't buried
node ../../studio/motion/render.mjs reel.html --size 1080x1920 --fps 30 \
     --audio mix.wav --out kill-screen.mp4
```

The voice came from ElevenLabs (the "Liam" read, `narration-raw.mp3`). The studio did the rest.

## The voice

`voice.py` takes the raw take and fixes what `listen.py` found on it:

| | raw | after |
|---|---|---|
| integrated | -24.6 LUFS | -16.0 LUFS |
| true peak | -7.5 dBTP | -1.5 dBTP |
| loudness range | 3.7 LU | 2.6 LU |
| high-mid (consonants) | 7% | 16% |
| air | 1% | 3% |

It also writes `lines.json`: where each of the ten lines starts and ends, measured off the
take itself. The picture reads that file, so every card lands on a word.

## What the critics changed

- **The arp was buried, 13 dB under the bass.** I had high-passed it at 1.1 kHz to keep it
  clear of the voice, but the part plays around A5 (880 Hz) — the filter cut the fundamentals
  out of it and left harmonics. 450 Hz instead, which still clears the voice.
- **`synth.reverb` and `synth.pingpong` are sends, not inserts.** Both return only their wet
  signal, and `plate()` builds two independent random IRs. `mix = reverb(mix, ...)` threw the
  dry signal away, so for three passes the "music" was a decorrelated, band-limited wash.
  That single line was behind the stereo correlation stuck at 0.04 ("may cancel on a phone
  speaker"), the "thin low end" and the low-mid crowding, all at once.
- **The kick is 48% sub.** Raising "the drums" to sharpen the pulse buried the track in low
  end. Kick and transients now sit on separate buses.
- **Very flat dynamics (1.6 LU).** The intro was as loud as the middle. `arc()` gives the bed
  about 8 dB of shape; it reads 4.7 LU on its own.
- **The film was very dark (0.07 mean lightness).** Same failure as First Listen. A lit CRT
  ground — screen glow, a drifting grid — took it to 0.13.
- **Three "no movement" stretches, up to 6.4 s.** The cards were static once they'd landed.
  A slow push-in per card, a rolling sync bar and a bigger beat pulse: motion median went
  from 0.00 to 0.14 and all three freeze flags cleared.
- **`motion.py` caught both text blocks jolting into motion.** The body copy genuinely
  travels, so it got eased properly. The headline stamps in 160 ms behind the card's hit as
  part of the same accent, so that one is declared in `__accents` instead.

## Two flags overruled, with the numbers

- **"cuts off the beat by more than 2.5 frames"** at 3.53 s, 17.87 s, 26.77 s and 30.80 s.
  Checked against the known grid instead of obeyed: every one of those cuts is within
  **0.8 frames** of where it was meant to be (45 ms before its line's first word). `look.py`
  is comparing them to energy peaks that fall mid-word, not to speech onsets — the same trap
  as the snare-roll entry in `misses.md`.
- **"very flat dynamics (2.7 LU)" on the final mix.** That is a narrator holding a steady
  level, which is what a reel wants — every word equally audible. The bed underneath still
  has its own 4.7 LU arc, and ducks 5.1 dB under speech while the voice sits 8.1 dB over it.

## Honest limits

- `soundfile` and `pyloudnorm` aren't installable in this container (pypi is blocked by
  policy), so both are reimplemented in `/home/claude/shims`. The loudness meter is
  BS.1770-4 and was checked for gain linearity (+6.02 LU for +6.02 dB), channel summation
  (+3.01 LU), the K-weighting response (0.70 dB at 1 kHz, +4.04 dB at 10 kHz) and gating
  (20 s of appended silence moves it 0.13 LU). The repo's own `test_senses.py` and
  `test_instruments.py` pass against it, held-out melody included. **LUFS figures here come
  from that reimplementation, not from pyloudnorm.**
- The drums are the from-scratch kit. `tinysoundfont` isn't installable either, so the 808
  and 909 kits were unavailable; the crash and toms are built from noise and a pitch drop.
- Fonts: the container has no network, so Google Fonts never arrive. The type is Inter
  Display Black, pushed hard (wide scaling, hard offset shadows) rather than left as a
  default-looking face.
- `listen.py` still reads the final mix as low-mid crowded. That band is where a voice lives
  and this is a voice-led mix; the score was carved at 420 Hz and 2.1 kHz to make room, and
  the measured result is the voice 8.1 dB over the bed.
