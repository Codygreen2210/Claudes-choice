// Puts the soundtrack together with ffmpeg: music, effects, and an optional voiceover.
// When there's a voice, the music ducks under it (sidechain compression) and comes back up
// in the gaps. The editor's preview and the export use this same mix.
import { spawn } from 'node:child_process';

export function mixArgs({ music, sfx, voice, voiceAt = 0, voiceVol = 1, seconds, out }) {
  const inputs = ['-i', music];
  if (sfx) inputs.push('-i', sfx);
  if (voice) inputs.push('-i', voice);
  const vi = sfx ? 2 : 1;
  const f = [];
  let bed = '[0:a]';
  if (voice) {
    const delay = Math.max(0, Math.round(voiceAt * 1000));
    f.push(`[${vi}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay=${delay}|${delay},volume=${voiceVol},apad,asplit=2[v][vkey]`);
    f.push(`${bed}[vkey]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350:makeup=1[duck]`);
    bed = '[duck]';
  }
  const parts = [bed, sfx ? '[1:a]' : null, voice ? '[v]' : null].filter(Boolean);
  f.push(`${parts.join('')}amix=inputs=${parts.length}:normalize=0:duration=first,atrim=0:${seconds.toFixed(2)},alimiter=limit=0.95[out]`);
  return [...inputs, '-filter_complex', f.join(';'), '-map', '[out]', '-ar', '44100', '-ac', '2', '-y', '-loglevel', 'error', out];
}

export function mix(opts) {
  return new Promise((ok, bad) => {
    const p = spawn('ffmpeg', mixArgs(opts));
    let err = ''; p.stderr.on('data', (d) => (err += d));
    p.on('error', () => bad(new Error('ffmpeg is not installed. Get it from ffmpeg.org, then try again.')));
    p.on('close', (c) => (c === 0 ? ok(opts.out) : bad(new Error('Mixing the sound failed: ' + err.slice(-300)))));
  });
}

// Any audio file (mp3, m4a, wav, webm from a browser recording...) to a plain WAV.
export function toWav(input, out) {
  return new Promise((ok, bad) => {
    const p = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-i', input, '-vn', '-ar', '44100', '-ac', '2', out]);
    let err = ''; p.stderr.on('data', (d) => (err += d));
    p.on('error', () => bad(new Error('ffmpeg is not installed.')));
    p.on('close', (c) => (c === 0 ? ok(out) : bad(new Error("That file doesn't look like audio ffmpeg can read."))));
  });
}
