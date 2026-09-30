# LaunchReel

A launch video for your side project, made from a short script instead of a screen recording.

You built something. Now you have to post it on r/SideProject, r/vibecoding, X or Product Hunt, and posts with a video do better. But recording one means screen-recording software, a Mac, twenty takes, editing, captions and finding music you're allowed to use. Then you change the UI next week and the video is out of date.

LaunchReel drives your app in a real browser, following a few lines of JSON, and renders a polished video:

- a title card and an end card with your link, in your app's own colour (picked up from your buttons)
- a browser window (or a phone, for TikTok / Shorts / Reels) on a soft backdrop
- a smooth cursor that glides to each button, click ripples, and a camera that leans in on what's being clicked
- typing that plays out letter by letter, and zoom-ins on the part you want people to see
- captions, one per step
- **original background music, generated fresh** (a mellow electric-piano groove, seeded, so no licensing worries)

Change your app, run it again, and you get a new video in about a minute. It runs on Mac, Windows, Linux or in GitHub Actions.

Built Sept 30, 2026, as a daily build. It's a product: it runs on its own, with nobody's time per customer.

## The editor

```
node reel.mjs studio demo.json
```

This opens LaunchReel Studio in your browser at http://localhost:4567. It only listens on your own computer.

- **Steps panel:** your clicks, typing, zooms and pauses as cards. Add, reorder, delete and edit them in the inspector.
- **Live preview:** capture once, then scrub and play instantly. Captions, caption style, title and end cards, pace, camera lean-in and hold times all update right away, because the preview runs the same timeline code as the exporter. Only changing *what* gets clicked needs a new capture (about 10 seconds).
- **Timeline strip:** step blocks, a caption track and the music waveform. Click to seek or pick a step.
- **Text:** 12 caption styles, all with fonts under the Open Font License (free for commercial use):

  | Style | Font | Motion |
  |---|---|---|
  | Clean pill | Inter | slides up |
  | Bold outline | Montserrat 900 | pops in |
  | Word by word | Poppins | highlights each word |
  | Headline block | Anton | wipes in |
  | Neon | Syne | glows |
  | Typewriter | JetBrains Mono | types out |
  | Soft card | Outfit | slides up |
  | Handwritten | Caveat | pops in, tilted |
  | Editorial | DM Serif Display | fades |
  | Lower third | Space Grotesk | wipes in |
  | Bubble | Fredoka | bounces |
  | Marker | Permanent Marker | pops in |

- **Music:** seven original genres: lo-fi, synthwave, house, trap-lite, ambient, upbeat pop and slow blues. You can change the key and tempo, switch drums, bass, chords and melody on or off, and press "New take" for a fresh variation. Every track is synthesised for your video, so there's nothing to license.
- **Sound effects:** a click on every press, key taps while typing, whooshes on zooms and scrolls, a pop when a caption appears, and a low hit on the title and end cards. Each one can be switched on or off, and there's a volume slider. All synthesised, so there's nothing to license.
- **Voiceover:** upload any audio file, or press Record and talk while the video plays. Slide it to where it should start. The music automatically drops under your voice and comes back up in the gaps (sidechain ducking). The preview and the export use the same mix.
- **Write it for me:** describe the video ("30 seconds, show sign-up and checking in a habit, upbeat"). LaunchReel reads what's actually on your page, including things that only appear after sign-up, then Claude writes the steps, captions, style and music. Anything that isn't really on the page, and any risky click (delete, pay, log out), is sent back once to be fixed. If it's still wrong, nothing is changed and you're told why. Then it captures automatically.
- **Formats:** 16:9, 9:16 in a phone frame, and 1:1. **Export** renders the MP4 with the same engine as the command line.

Fonts load from Google Fonts. To work offline, `npm i @fontsource/inter @fontsource/anton ...` and set `LAUNCHREEL_FONTS` to that `node_modules` folder.

## Use it

Needs Node 18+, ffmpeg, and Playwright (`npm install playwright && npx playwright install chromium`).

```json
{
  "url": "http://localhost:3000",
  "title": "Streakly",
  "tagline": "Keep your streak alive.",
  "cta": "streakly.app",
  "steps": [
    { "caption": "Habit tracking without the setup" },
    { "click": "Get started free", "caption": "Sign up in one step" },
    { "type": ["#email", "cody@example.com"] },
    { "click": "Create account", "caption": "Your habits, as dots" },
    { "zoom": "#chart", "caption": "See your best week" }
  ]
}
```

```
node reel.mjs demo.json                  # 1920x1080 for X, Reddit, YouTube
node reel.mjs demo.json --format vertical  # 1080x1920 phone, for TikTok / Shorts / Reels
node reel.mjs demo.json --format all       # landscape, vertical and square
```

Steps: `click`, `hover`, `type: [field, text]`, `scroll: pixels`, `zoom`, `wait: ms`, each with an optional `caption`. Targets are the button's text, or any CSS selector. Options: `pace` (1.2 = slower), `follow` (camera lean-in, `false` to turn off), `theme: "dark"`, `captionStyle` (see the editor), `music: { genre, key, seed, bpm, volume, parts: { drums, bass, chords, lead } }`.

Mistakes in the script are caught before anything runs, with the step number and how to fix it.

## How it works

1. **Capture** (`lib/capture.mjs`): Playwright walks through the steps and takes a full-page snapshot of every screen, where each click landed, and where the page scrolled. It waits until the screen stops moving (animations, smooth scrolls) before each snapshot.
2. **Timeline** (`lib/timeline.mjs`): turns that into camera moves, cursor paths, clicks, captions and cards, with easing. It's a pure function, tested without a browser, and the camera never shows past the page's edges.
3. **Studio** (`lib/render.mjs`): draws each frame at an exact time in a headless browser page and streams them to ffmpeg (H.264 + AAC, ready for every social site).
4. **Music** (`lib/music.mjs`): synthesises an original track to the video's length: chords, walking bass, brushed hat, a little room echo.

## Prompt-to-video: who pays for the AI

- **Your own key:** set `ANTHROPIC_API_KEY` before `node reel.mjs studio`. It costs you a few cents per video, straight from your computer.
- **Pro, hosted:** the seller runs `hosted/api/ai.js` (a Vercel function) with their own key. Buyers set `LAUNCHREEL_AI_URL` plus their Pro key. The service guards against abuse and runaway cost:
  - it only accepts valid Pro keys
  - it enforces a monthly cap per key (default 50), counted atomically in Supabase (`hosted/supabase.sql`, and the table has no public access)
  - it allows 5 requests a minute per IP
  - it keeps inputs small
  - answers are capped at 1,500 tokens, with at most 2 AI calls per video
  - it builds the prompt itself, so it can't be used as a general-purpose AI

  Also set a monthly spend limit in the Anthropic console.

## Free and Pro

The free version adds a small "Made with LaunchReel" line to the end card. A Pro key removes it (`LAUNCHREEL_KEY=...`). Keys are checked offline (Ed25519). The seller makes them with `tools/keygen.mjs`, and the private key is never in this repo.

## Tested

`node --test --test-reporter=dot "test/*.test.mjs"` (21 tests): script checks, camera bounds at every frame, the cursor on the button at the click, captions and cards in order, music (a real WAV, no clipping, same seed gives the same song), license keys (forged and foreign keys rejected), a full end-to-end run from browser to MP4 with sound (checking that the screen really changes after the click), every music genre and caption style, the editor server (including refusing paths outside its folders), sound cues landing exactly on clicks and key taps, the music measurably ducking under a voice and recovering after, AI scripts checked against the real page (made-up buttons and risky clicks refused, one retry with the problems listed), and the hosted AI service (no key, over the cap, too many requests, and oversized input are all refused, and a caller's own "system" text is ignored). The editor itself was driven in Chromium: capture, play, edit a caption, change style, genre and pace, export, then switch to phone size.

It was also run on an app it wasn't built for: `examples/rowproof.json` films the RowProof statement converter in all three formats.

`github-workflow-example.yml` re-films your demo on every push.

MIT license.
