# Misses

Mistakes I actually made, and what to check so I don't make them twice. The breaker reads this before every review.
Add an entry whenever a real miss gets caught, by the breaker, by a person, or by production. Keep each one short: what happened, then the check.

Format: **Pattern.** What happened (where, when). **Check:** what to do.

## Layout and pages

- **Layouts break at larger text sizes.** Community cards on a live site ran off phone screens only when the phone had larger text turned on (Sept 2026). Default-size testing looked fine. **Check:** test phone widths with text scaled to 130% (page-check does this by default).
- **`overflow: hidden` hides bugs instead of preventing them.** The page didn't scroll sideways, so it looked fine, but the cards were cut off. My own checker first treated "hidden" as "fine" and missed it. **Check:** content (text, links, buttons) cut off by a hidden ancestor is a failure; only decoration may be clipped.
- **Phone browsers zoom out on wide pages, so `window.innerWidth` lies.** My checker first measured against innerWidth and saw no overflow on a page that was 1151px wide on a 390px phone. **Check:** measure against the device width you set, never against what the page reports.
- **A sandbox without the site's fonts gives false layout alarms.** The sandbox couldn't download Google Fonts, so a wider fallback replaced Bebas Neue. That made headings and the Join button look cut off. I told Cody the Join button was broken on 360px phones before checking, and the breaker made the same mistake with a heading. With the real fonts, most of it disappeared (Sept 2026). **Check:** page-check now warns when fonts fail to load. Treat layout results as unconfirmed until the real fonts are supplied with `--font`, and don't report a layout bug to a person until then.
- **Words can spill out of a box that fits.** A long word in a big heading can overflow its own box while the box sits on screen, so box-edge checks miss it. **Check:** measure where the text ends (page-check does this now).
- **Logged-out visitors see a different page.** A site's "Join" button was cut off on 360px phones with larger text turned on, but the owner is always logged in and never sees it (found by page-check, confirmed with the real fonts, Sept 2026). **Check:** review pages as a brand-new visitor too, at 360px, the narrowest common Android width.

## Code and systems

- **A failed lookup is not an empty result.** A count ignored the error from a filtering query, so a failed query meant "nothing to filter" and everything got counted (found by the breaker, Sept 2026). **Check:** for every query whose result gates something (hide/show, allow/deny, limits), what happens when it errors? It must fail toward the safe side.
- **Hiding a page means hiding its children too.** A section was noindexed, but its posts still went into the sitemap. **Check:** when a page is kept out of search, confirm its child pages are left out of the sitemap as well.
- **Time windows collide with jittery schedules.** A daily import counted "the last 24 hours", but Vercel's daily cron fires anywhere inside its hour, so yesterday's run landed in today's window and starved it. **Check:** any "per day" limit tied to a scheduled job: what happens if two runs are 23 hours apart? 25?
- **APIs require fields their docs don't make obvious.** Metricool rejected a post because TikTok needs a title. **Check:** after any API write, read the object back and confirm it exists as intended; don't trust the 200.
- **Platforms treat automated commits differently.** Vercel refused to deploy a commit authored by the bot on main. **Check:** after any push, confirm the deploy actually went READY; don't assume.
- **Killing processes by pattern can kill yourself.** `pkill -f "next dev -p 3100"` matched its own shell. Then I did it AGAIN with `pkill -f "render.mjs"` while this entry already existed (Sept 2026). **Check:** kill by port or PID, not by a pattern that appears in the command line. And reading this file only helps if it happens before acting, not after.
- **Cached answers hide the current state.** A fetch tool served a cached 404 for a URL that was live. **Check:** when a result contradicts what you just did, re-check with a cache-busting variation before believing it.

## Sound and picture (the studio)

- **A frame's time is its middle, not its start.** My ears stamped each STFT frame with its start time, so every beat, chord and hit came out ~93 ms early and the ad's cuts looked "late". **Check:** any windowed analysis: time = start + window/2, and test against material with known event times.
- **Linear light hides change in the dark.** My eyes measured motion in linear luminance and called a slowly scrolling dark film "frozen" and "black". **Check:** measure what people see (gamma-encoded lightness); keep linear light only where a standard requires it (flash safety).
- **The fundamental can be missing.** FM pianos, and notes that land on a held chord tone, have a weak or masked fundamental; my melody tracker kept hearing the octave above. **Check:** name pitch from the harmonic pattern (energy at 1.5x means the note is an octave down), not the loudest line.
- **A score tuned on its own test data is flattering.** Melody hearing read 86% on the motifs I tuned it with, 78% on material it had never heard. **Check:** always keep a held-out test and report that number.
- **Per-element blur is the slow path.** Canvas shadowBlur on every note cost 560 ms a frame; one blurred bloom layer per frame costs ~60. The first cheap replacement (stacked strokes) looked like plastic capsules. **Check:** measure before optimising, and compare the optimised frame against the original by eye.
- **A dark piece is darker on a phone.** First Listen averaged 0.06 lightness; typical video is 0.3 to 0.5. **Check:** look.py's brightness line; night pieces still want ~0.12+.

- **"Forward" gets flipped.** The heron's first strike went up instead of into the water, and later the body tilt lowered the chest instead of raising it. Both times I had the screen's y-down rotation backwards. **Check:** before rendering a rig, compute one point by hand (where does the chest go?) and print it.
- **A critic judged a move from its middle.** motion.py found moves with a threshold set by the fastest thing in the clip, so a gentle move was "found" halfway up to speed and called a jolt. I only caught it by tracing the frames instead of obeying. **Check:** when a critic's verdict surprises you, look at the raw numbers before acting on it.
- **Frequency times time is not a phase.** Slowing the wingbeats with `sin(2π·hz(t)·t)` makes them decelerate far more than intended. **Check:** phase = the running sum of frequency.
- **Competing focal points in a still.** The heron and the sun fought for first look. **Check:** the squint and thumbnail views in see.py; put the darkest dark against the lightest light where you want the eye.

- **Rules from one style misjudge another.** motion.py's ease-in/ease-out rules are naturalistic; rubber-hose animation snaps on the beat on purpose, and hand animation holds drawings on twos. Both read as faults until the critic knew about them. **Check:** before obeying a critic on stylised work, ask whether its rule belongs to this style; give it the style's facts (accents, holds, bodies) rather than silencing it.
- **A hold has a start and an end; ask which one you mean.** Mapping a drawing time back to video time, a pause on a caption matched at its end, so step 1's caption and chime came in a second late (dragon tutorial, Sept 2026). **Check:** any inverse of a function with flat stretches: test that the answer is the first time, not the last.
- **A shape used to hide things hides more than you meant.** The serpent's head outline reached back past the cheek, and since it masked everything behind the head, it swallowed the mane (Sept 2026). **Check:** after adding an occlusion shape, look at what disappeared, not just at what it covers.
- **Tiling needs spacing and size to agree.** Scale arcs 1.4× wider than their row spacing read as a chain of loops instead of scales. **Check:** for any repeated mark, make its size come from the spacing, not a separate number.
- **Reading time is not drawing time.** The serpent tutorial's first cut held a still picture for up to 10 s while long captions were read. look.py flagged eight freezes (Sept 2026). **Check:** cap any hold at a couple of seconds and fill the rest with motion. For short steps, add the real work an artist would do (light sketch passes, a slow careful whisker), not a crawling pen.
- **A slow fade reads as a freeze to a per-frame threshold.** look.py called a 9.6 s eraser fade "no movement" while 40-50k pixels changed every 4 s. **Check:** before acting on a freeze flag, diff frames a few seconds apart.
- **A critic can measure the wrong thing and still sound right.** linework.py's first "repetition" score was driven by the serpent's overall S-curve and by lone lines on empty paper, not by repeating marks. I nearly tuned the drawing against it (Sept 2026). **Check:** when a number won't move no matter what you change, find what's driving it (which frequencies, which region) before changing the work again.
- **A cleanup step can erase the thing being measured.** Roughness was measured after smoothing the line mask. **Check:** measure on raw data, and test each measure with an input where the answer is known.
- **"Random" built from sine waves is a pattern.** The hand's tremor was a sine, so every line wobbled with the same rhythm. **Check:** for anything meant to look human, use noise, not periodic functions.
- **"Left" and "right" of a path depend on which way it points.** I drew the finger plates and highlights on the "left" edge of each finger's tube, which is the palm side for a finger pointing left, and shaded the lit side (Sept 2026). **Check:** decide sides by meaning (the outside of the curl, the side facing the light), never by the tube's left/right.
- **A hard-coded direction breaks on the part that's different.** Talons were set to hook one way, and the thumb curls the other way. **Check:** derive a direction from the thing it follows, then test the odd one out.
- **An effect on a big canvas costs the whole canvas.** Blur filters and clip masks are rasterised over the entire surface. At 2.6× resolution with thousands of strokes, one frame took over 6 minutes. **Check:** work on a scratch canvas that fits the stroke, and skip masks whose bounds don't overlap it.
- **Close hits merge in the ear.** look.py said the title cut was 142 ms late; the snare roll right before the downbeat swallowed the downbeat's own peak. The cut was 14 ms late. **Check:** verify sync claims against the known beat grid.

## Checks and tests themselves

- **A test can assert the wrong thing.** I wrote a test expecting `100 / 8 = 13` to be flagged as wrong, but 12.5 fairly rounds to 13. **Check:** when a test fails, first ask whether the expectation is right.
- **Loose tolerances make checks pass silently.** The percent-change check allowed 5 points of slack, so "40 to 50, up 20%" (really 25%) passed. **Check:** every checker needs a test that a slightly-wrong input fails, not just that a right input passes.
- **A checker that has only been run on clean input is untested.** **Check:** plant the exact bug it's meant to catch and confirm it's caught before trusting a clean result.

## Communication

- **Answering a nearby question instead of the one asked.** Cody asked where Connectors are; I answered a different question. **Check:** before sending, reread the question and confirm the first sentence answers it.
- **Tool names and UI paths drift.** I sent him to Settings for Connectors when it was under Customize. **Check:** don't give click-paths for apps I can't see; say what to look for instead.

### 7. Killed my own shell with pkill, a third time (Sept 30, 2026)
- **Trying to:** stop the Misslog test server before committing.
- **Ask:** "Let's build it completely" (Misslog).
- **Mistake:** `pkill -f "next start -p 3210"` matched my own shell command and killed it, and the README, INDEX line and commit all went down with it. This exact pattern was already in this file twice. I hadn't read it on this branch before acting.
- **Fix:** stopped the server by port (`fuser -k 3210/tcp`) and redid the lost steps. **Check:** never use `pkill -f`. Kill by port or PID only.


## Voice (the Panic of 1907 film, Oct 2026)

- **A hyphen changes the accent.** The local voice says "thirty-nine" with a hard British t and "thirty nine" with the American one; "1907" came out as a plain number. Cody heard both. **Check:** print the phonemes for every number and name in a script before recording, and write numbers the way they are said.
- **Stitching mid-sentence breaks the melody.** The first sample was said in pieces split at every beat and ellipsis; the flow was off. **Check:** never split inside a sentence; change the silence where it already falls.
- **The critic called a fast zoom a flash.** look.py flagged "3 large flashes" at a 1.2 s push-in where brightness moved 3 points out of 255. **Check:** before re-rendering for a flash flag, print the mean brightness per frame.
- **A blocked host is not fixed by asking mid-session.** ElevenLabs audio lives on storage.googleapis.com, which this workspace could not reach, and allowing it did not take effect in the running session. **Check:** test the download of one take before recording the rest.
