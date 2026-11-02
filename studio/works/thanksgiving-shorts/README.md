# Thanksgiving Shorts (Nov 1, 2026)
Two vertical Shorts, photoreal AI clips (free route: Z-Image Turbo stills -> Wan 2.2 i2v on HF ZeroGPU).
- turkey.json / coma.json: narration lines (studio male voice, gap 0.14, after-scale 0.5)
- *-narration.wav + *-times.json: recorded reads and beat timings
- clip-links.txt: finished Wan clips (T1-T4) waiting to be pulled in once *.hf.space is allowed
Status: 4 of 16 shots made; free ZeroGPU quota ran out for the day.
Sources: Britannica (steam ~1,700x volume, oil ~350F), NFPA via Denver7 (Thanksgiving 2023 ~1,446 cooking fires, 388% of daily average), PBS NC (tryptophan myth).

## Nov 1 update: free 3D route
AI clip quota ran out, so both Shorts are built as Cycles 3D scenes (blender/), rendered on the GitHub Actions farm
(post/thanks-farm.yml, pushed with post/push_job.sh to render/thanks-<id>), then finished with post/sound.py (effects + score,
checked with listen.py) and post/compose.py (captions + live readouts).
