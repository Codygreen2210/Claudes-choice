// The studio's ears, hooked into LaunchReel. Every soundtrack gets listened to by
// studio/senses/listen.py (in Claudes-choice) before it goes into a video.
// What it can fix on its own (true peak over -1 dBTP, clipping), it fixes and listens again.
// Everything else it flags goes in the notes next to the video, with the picture.
// If Python or the studio isn't there, LaunchReel still works; it just says the ears were skipped.
import { spawn } from 'node:child_process';
import { existsSync, readFileSync, mkdirSync, renameSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';

const HERE = dirname(new URL(import.meta.url).pathname);

// Where listen.py lives: LAUNCHREEL_EARS, or walk up from here looking for studio/senses/listen.py.
export function findEars() {
  if (process.env.LAUNCHREEL_EARS) return existsSync(process.env.LAUNCHREEL_EARS) ? process.env.LAUNCHREEL_EARS : null;
  let d = HERE;
  for (let i = 0; i < 6; i++) {
    const p = join(d, 'studio', 'senses', 'listen.py');
    if (existsSync(p)) return p;
    const up = resolve(d, '..');
    if (up === d) break;
    d = up;
  }
  return null;
}

function run(cmd, args) {
  return new Promise((ok) => {
    const p = spawn(cmd, args);
    let out = '', err = '';
    p.stdout.on('data', (b) => (out += b));
    p.stderr.on('data', (b) => (err += b));
    p.on('error', (e) => ok({ code: -1, out, err: e.message }));
    p.on('close', (code) => ok({ code, out, err }));
  });
}

// Problems ffmpeg can fix without changing the music: peaks and clipping.
export function fixable(r) {
  const L = r.loudness || {};
  return (L.true_peak_dbtp ?? -99) > -1 || (L.clipped_samples ?? 0) > 0;
}

export async function listen(wav, { out, name = 'soundtrack', picture = true } = {}) {
  const py = findEars();
  if (!py) return { skipped: 'studio ears not found (set LAUNCHREEL_EARS to studio/senses/listen.py)' };
  mkdirSync(out, { recursive: true });
  const args = [py, wav, '--out', out, '--name', name];
  if (!picture) args.push('--no-picture');
  const r = await run(process.env.PYTHON || 'python3', args);
  if (r.code !== 0) return { skipped: 'ears could not run: ' + (r.err.trim().split('\n').pop() || 'python3 missing') };
  // Python writes NaN/Infinity for silent sections; JSON can't hold those, so they become null.
  const report = JSON.parse(readFileSync(join(out, name + '.listen.json'), 'utf8').replace(/:\s*-?(NaN|Infinity)\b/g, ': null'));
  return {
    report,
    warnings: report.warnings || [],
    balance: report.balance_notes || [],
    text: join(out, name + '.listen.txt'),
    picture: picture ? join(out, name + '.listen.png') : null,
  };
}

// Bring the true peak to -1.5 dBTP with a plain gain change. The ears measured the true peak
// (between samples, the way MP3/AAC will see it), so turning down by exactly that much is enough.
async function tame(wav, truePeak) {
  const tmp = wav.replace(/\.wav$/i, '') + '.tamed.wav';
  const db = Math.min(0, -1.5 - truePeak).toFixed(2);
  const r = await run('ffmpeg', ['-y', '-loglevel', 'error', '-i', wav, '-af', `volume=${db}dB`, '-c:a', 'pcm_s16le', tmp]);
  if (r.code !== 0) return false;
  renameSync(tmp, wav);
  return true;
}

// Listen, fix what's safe to fix, listen again. Returns what the ears said about the final audio.
export async function checkAudio(wav, { out, name = 'soundtrack', picture = true, log = () => {} } = {}) {
  let res = await listen(wav, { out, name, picture: false });
  if (res.skipped) { log('ears skipped: ' + res.skipped); return res; }
  const fixed = [];
  if (fixable(res.report) && (await tame(wav, res.report.loudness.true_peak_dbtp))) {
    fixed.push(`peaks pulled down from ${res.report.loudness.true_peak_dbtp.toFixed(1)} dBTP`);
    res = await listen(wav, { out, name, picture });
  } else if (picture) {
    res = await listen(wav, { out, name, picture });
  }
  res.fixed = fixed;
  res.ok = !fixable(res.report);
  const L = res.report.loudness;
  log(`ears: ${res.report.tempo_bpm.toFixed(0)} BPM, ${res.report.key}, ${L.integrated_lufs.toFixed(1)} LUFS, peak ${L.true_peak_dbtp.toFixed(1)} dBTP` +
    (fixed.length ? ` (fixed: ${fixed.join('; ')})` : '') +
    (res.warnings.length ? `\n  listen out for: ${res.warnings.join('; ')}` : ''));
  return res;
}
