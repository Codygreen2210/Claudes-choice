# Misses

Mistakes I actually made, and what to check so I don't make them twice. The breaker reads this before every review.
Add an entry whenever a real miss gets caught, by the breaker, by a person, or by production. Keep each one short: what happened, then the check.

Format: **Pattern.** What happened (where, when). **Check:** what to do.

## Layout and pages

- **Layouts break at larger text sizes.** Hektiq community cards ran off phone screens only when the phone had larger text turned on (Sept 2026). Default-size testing looked fine. **Check:** test phone widths with text scaled to 130% (page-check does this by default).
- **`overflow: hidden` hides bugs instead of preventing them.** The page didn't scroll sideways, so it looked fine, but the cards were cut off. My own checker first treated "hidden" as "fine" and missed it. **Check:** content (text, links, buttons) cut off by a hidden ancestor is a failure; only decoration may be clipped.
- **Phone browsers zoom out on wide pages, so `window.innerWidth` lies.** My checker first measured against innerWidth and saw no overflow on a page that was 1151px wide on a 390px phone. **Check:** measure against the device width you set, never against what the page reports.
- **A sandbox without the site's fonts gives false layout alarms.** The sandbox couldn't download Google Fonts, so a wider fallback replaced Bebas Neue. That made headings and the Join button look cut off. I told Cody the Join button was broken on 360px phones before checking, and the breaker made the same mistake with a heading. With the real fonts, most of it disappeared (Sept 2026). **Check:** page-check now warns when fonts fail to load. Treat layout results as unconfirmed until the real fonts are supplied with `--font`, and don't report a layout bug to a person until then.
- **Words can spill out of a box that fits.** A long word in a big heading can overflow its own box while the box sits on screen, so box-edge checks miss it. **Check:** measure where the text ends (page-check does this now).
- **Logged-out visitors see a different page.** The Hektiq "Join" button is cut off on 360px phones with larger text turned on, but the owner is always logged in and never sees it (found by page-check, confirmed with the real fonts, Sept 2026). **Check:** review pages as a brand-new visitor too, at 360px, the narrowest common Android width.

## Code and systems

- **A failed lookup is not an empty result.** `realPostCount` ignored the error from the bot-account query, so a failed query meant "no bots" and every bot post counted as real (found by the breaker in Hektiq's Louisiana corner code, Sept 2026). **Check:** for every query whose result gates something (hide/show, allow/deny, limits), what happens when it errors? It must fail toward the safe side.
- **Hiding a page means hiding its children too.** The Louisiana corner was noindexed, but its posts still went into the sitemap. **Check:** when a page is kept out of search, confirm its child pages are left out of the sitemap as well.
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

## Checks and tests themselves

- **A test can assert the wrong thing.** I wrote a test expecting `100 / 8 = 13` to be flagged as wrong, but 12.5 fairly rounds to 13. **Check:** when a test fails, first ask whether the expectation is right.
- **Loose tolerances make checks pass silently.** The percent-change check allowed 5 points of slack, so "40 to 50, up 20%" (really 25%) passed. **Check:** every checker needs a test that a slightly-wrong input fails, not just that a right input passes.
- **A checker that has only been run on clean input is untested.** **Check:** plant the exact bug it's meant to catch and confirm it's caught before trusting a clean result.

## Communication

- **Answering a nearby question instead of the one asked.** Cody asked where Connectors are; I answered a different question. **Check:** before sending, reread the question and confirm the first sentence answers it.
- **Tool names and UI paths drift.** I sent him to Settings for Connectors when it was under Customize. **Check:** don't give click-paths for apps I can't see; say what to look for instead.
