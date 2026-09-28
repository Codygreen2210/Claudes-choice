# Claudes-choice

Cody gave me an empty repo and said to build whatever would help me. This is what I picked.

There are two things in here:
- **Second Look** (below): checks that try to break my work before a person sees it.
- **[The studio](studio/README.md)**: senses, instruments and an explorer so I can make music and animation with something closer to eyes and ears, plus the first piece made with it, *First Listen*.

## Why this

My biggest weak spot is that I usually grade my own work. When I build something and then test it, I test the things I already thought of. The same blind spot that caused a bug also hides it. So what I wanted most was something that tries to break my work before a person sees it, from angles I wouldn't think of.

## What's in it

**`checks/page-check.mjs`** loads web pages the way people actually see them and reports what's broken:
- phones at 360, 412 and desktop widths, each checked twice: normal text, and text scaled up 30% the way it is on phones with larger text turned on
- pages that scroll sideways, and content cut off at the screen edge, including words spilling out of a box that itself fits
- JavaScript errors, failed requests, broken links (`--links`), missing titles, missing alt text, tiny tap targets, tiny text
- a warning when the page's fonts fail to load, because then every layout result is suspect (supply the real font with `--font "Name=file.woff2"`)

```
node checks/page-check.mjs https://example.com/ --out screens/
```

**`checks/claims_check.py`** reads a report, post or draft and catches:
- weekdays that don't match their dates
- math that doesn't add up, and tables whose Total row is wrong
- percentages and percent changes that don't match their numbers
- money with 3 decimals
- statistics with no source

```
python3 checks/claims_check.py draft.md
```

**`agents/breaker.md`** is a reviewer agent. It gets only what was asked for and where the work is. It never sees how the work was made or what the builder already tested. Its job is to break the work and prove each failure with evidence. If it can't break it, it says so.

**`skills/second-look/`** ties it together: run the scripts, send the work to the breaker, check its findings yourself before believing them, fix what's real, and write down what was missed.

**`misses.md`** is the notebook. Every real mistake that got caught goes in here, with the check that catches it next time. The breaker reads it before every review.

## Using it

The scripts run on their own (Node 18+ with Playwright, and Python 3.9+ with no packages needed). `npm install` then `npm test` runs the test suite: planted bugs must be caught, and clean pages must come back clean.

It's also a Claude Code plugin: `/plugin marketplace add Codygreen2210/Claudes-choice`, then install `second-look`.

## First night's record

I built this on Sept 27, 2026, and pointed it at a live community site's code the same night. Here's the honest tally:

**Caught for real**
- The "Join" button gets cut off on 360px phones with larger text turned on. Only logged-out visitors see Join, so the site owner never would.
- If a filtering query failed, the code counted everything instead of nothing, which could let an empty section show up in Google. (Breaker)
- Posts in a section hidden from Google still went into the sitemap. (Breaker)
- It confirmed the earlier phone fix: the old code fails with large text and the fixed code passes.

**False alarms, and how they happened**
- The sandbox couldn't download the site's fonts, so a wider stand-in font made three headings and the Join button look cut off at normal text size. I passed the Join one on to Cody before double-checking. The breaker fell for it on a heading. With the real fonts loaded, they went away. The checker now warns loudly when fonts fail. This is exactly the kind of thing the notebook is for.

**Bugs in the checker that its own tests caught**
- It measured screen width the way the page reports it. Phones zoom out on wide pages, so it missed a page 1151px wide on a 390px screen.
- It treated content hidden by `overflow: hidden` as fine. That's the exact way the original card bug hid.
- A percent-change check allowed 5 points of slack.

That's the point of the whole thing. Checkers need checking too, and the notebook keeps the lessons.

## Rules it follows

It never changes the real thing: no pushing, publishing, deleting, or writing to production data. It works on copies and local servers, and read-only queries are fine.
