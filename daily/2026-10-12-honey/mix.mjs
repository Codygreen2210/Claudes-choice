// Honey: put the soundtrack together.
//
// Reuses LaunchReel's mixer, so the music ducks under the narrator by the same
// sidechain path the reel tool already uses and was tested on.
//
//   node mix.mjs   ->  mix.wav
import path from 'node:path'
import url from 'node:url'
import { mix } from '../2026-09-30-launchreel/lib/mix.mjs'

const HERE = path.dirname(url.fileURLToPath(import.meta.url))
const p = (f) => path.join(HERE, f)

const SECONDS = 64.70

await mix({
  music: p('score.wav'),
  voice: p('narration.wav'),
  voiceAt: 0,
  voiceVol: 1.0,
  seconds: SECONDS,
  out: p('mix.wav'),
})

console.log(`mix.wav  ${SECONDS}s  (score ducked under the narration)`)
