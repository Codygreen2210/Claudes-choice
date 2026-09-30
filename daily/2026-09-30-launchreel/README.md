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

## Free and Pro

The free version adds a small "Made with LaunchReel" line to the end card. A Pro key removes it (`LAUNCHREEL_KEY=...`). Keys are checked offline (Ed25519). The seller makes them with `tools/keygen.mjs`, and the private key is never in this repo.

## Tested

`node --test --test-reporter=dot "test/*.test.mjs"` (14 tests): script checks, camera bounds at every frame, the cursor on the button at the click, captions and cards in order, music (a real WAV, no clipping, same seed gives the same song), license keys (forged and foreign keys rejected), a full end-to-end run from browser to MP4 with sound (checking that the screen really changes after the click), every music genre and caption style, and the editor server (including refusing paths outside its folders). The editor itself was driven in Chromium: capture, play, edit a caption, change style, genre and pace, export, then switch to phone size.

It was also run on an app it wasn't built for: `examples/rowproof.json` films the RowProof statement converter in all three formats.

`github-workflow-example.yml` re-films your demo on every push.

MIT license.
