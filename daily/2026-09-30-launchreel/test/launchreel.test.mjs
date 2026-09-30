import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { checkScript } from '../lib/script.mjs';
import { buildTimeline, frameAt } from '../lib/timeline.mjs';
import { makeMusic } from '../lib/music.mjs';
import { parseColor, palette } from '../lib/render.mjs';
import { checkLicense } from '../lib/license.mjs';
import { generateKeyPairSync, sign } from 'node:crypto';

const view = { w: 1120, h: 700 };
const states = { s0: { height: 2400 }, s1: { height: 2400 }, s2: { height: 700 } };
const events = [
  { kind: 'start', state: 's0', scrollY: 0, caption: 'Hello' },
  { kind: 'click', state: 's0', box: { x: 900, y: 1500, w: 120, h: 40 }, after: 's1', afterScrollY: 1200, caption: 'Click the far button' },
  { kind: 'type', state: 's1', box: { x: 100, y: 1300, w: 300, h: 40 }, frames: ['s1', 's2'] },
  { kind: 'scroll', by: 5000 },
  { kind: 'zoom', state: 's2', box: { x: 50, y: 100, w: 200, h: 100 } },
];

test('script checks name the step and the fix', () => {
  assert.deepEqual(checkScript({ url: 'http://localhost:3000', steps: [{ click: 'Sign up' }] }), []);
  const e = checkScript({ url: 'localhost', steps: [{ click: 'a', type: ['#x', 'y'] }, { scroll: 'lots' }, {}, { caption: 'x'.repeat(80) }] });
  assert.match(e.join('\n'), /"url" is missing or not a full address/);
  assert.match(e.join('\n'), /Step 1: has click and type/);
  assert.match(e.join('\n'), /Step 2: "scroll" should be a number/);
  assert.match(e.join('\n'), /Step 3: needs one of/);
  assert.match(e.join('\n'), /Step 4: caption is 80 characters/);
});

test('camera never shows past the edges of the page, at any moment', () => {
  const tl = buildTimeline(events, { view, states });
  for (let t = 0; t <= tl.duration; t += 1 / 30) {
    const f = frameAt(tl, t);
    const h = states[f.to].height;
    assert.ok(f.cam.z >= 1 && f.cam.z <= 2.21, `zoom ${f.cam.z} at ${t}`);
    assert.ok(f.cam.x >= -0.01 && f.cam.x <= view.w - view.w / f.cam.z + 0.01, `x ${f.cam.x} at ${t}`);
    assert.ok(f.cam.y >= -0.01, `y ${f.cam.y} at ${t}`);
    // The pan target is clamped to each state's height; while blending it can't go past the taller one.
    assert.ok(f.cam.y <= Math.max(...Object.values(states).map((s) => s.height)) - view.h / f.cam.z + 0.01, `y ${f.cam.y} at ${t}`);
  }
});

test('the cursor is on the button when the click happens, and the screen changes after', () => {
  const tl = buildTimeline(events, { view, states });
  const pressKey = tl.keys.find((k) => k.press);
  const f = frameAt(tl, pressKey.t);
  assert.ok(Math.abs(f.cur.x - 960) < 1 && Math.abs(f.cur.y - 1520) < 1, `cursor at ${f.cur.x},${f.cur.y}`);
  assert.ok(f.press > 0.9);
  assert.equal(frameAt(tl, pressKey.t - 0.05).to, 's0');
  assert.equal(frameAt(tl, pressKey.t + 0.6).to, 's1');
  // The far-down button had to be brought into view first.
  assert.ok(f.cam.y > 800, 'camera moved down to the button');
});

test('a click that scrolls the page (same screen, new position) is followed by the camera', () => {
  const ev = [{ kind: 'start', state: 's0', scrollY: 0 }, { kind: 'click', state: 's0', box: { x: 100, y: 100, w: 80, h: 30 }, after: 's0', beforeScrollY: 0, afterScrollY: 1400 }];
  const tl = buildTimeline(ev, { view, states, outro: false });
  const end = frameAt(tl, tl.duration);
  assert.equal(end.cam.y, 1400);
  assert.equal(end.cam.z, 1);
});

test('title card first, captions in order, end card last', () => {
  const tl = buildTimeline(events, { view, states });
  assert.equal(frameAt(tl, 1).card, 'title');
  assert.equal(frameAt(tl, 1).cardAlpha, 1);
  const caps = [];
  for (let t = 0; t < tl.duration; t += 0.1) { const c = frameAt(tl, t).caption; if (c && caps.at(-1) !== c) caps.push(c); }
  assert.deepEqual(caps, ['Hello', 'Click the far button']);
  assert.equal(frameAt(tl, tl.duration - 0.5).card, 'outro');
  const plain = buildTimeline(events, { view, states, title: false, outro: false });
  assert.ok(plain.duration < tl.duration - 5);
});

test('follow off means no zoom except on a zoom step; pace stretches the video', () => {
  const tl = buildTimeline(events.slice(0, 3), { view, states, follow: 1 });
  for (let t = 0; t <= tl.duration; t += 0.05) assert.equal(frameAt(tl, t).cam.z, 1);
  const slow = buildTimeline(events, { view, states, pace: 1.5 });
  assert.ok(slow.duration > buildTimeline(events, { view, states }).duration + 2);
});

test('music: real WAV, right length, no clipping, same seed same song', () => {
  const a = makeMusic({ seconds: 6, seed: 3 }), b = makeMusic({ seconds: 6, seed: 3 }), c = makeMusic({ seconds: 6, seed: 4 });
  assert.equal(a.toString('ascii', 0, 4), 'RIFF');
  assert.equal(a.readUInt32LE(24), 44100);
  assert.equal((a.length - 44) / 4, 6 * 44100);
  assert.ok(a.equals(b), 'same seed gives the same song');
  assert.ok(!a.equals(c), 'another seed gives another song');
  let peak = 0, sum = 0;
  for (let i = 44; i < a.length; i += 2) { const v = Math.abs(a.readInt16LE(i)); peak = Math.max(peak, v); sum += v * v; }
  const rms = Math.sqrt(sum / ((a.length - 44) / 2)) / 32767;
  assert.ok(peak <= 0.9 * 32767, 'headroom kept');
  assert.ok(rms > 0.03, 'not silent');
  for (const mood of ['blues', 'bright']) assert.ok(makeMusic({ seconds: 2, mood }).length > 1000);
});

test('backdrop colours come from the app\'s own accent', () => {
  assert.deepEqual(parseColor('rgb(232, 89, 12)'), [232, 89, 12]);
  assert.deepEqual(parseColor('#e8590c'), [232, 89, 12]);
  assert.deepEqual(parseColor('#fff'), [255, 255, 255]);
  assert.equal(parseColor('nonsense'), null);
  assert.equal(palette('#e8590c').c, 'rgb(232,89,12)');
  assert.ok(palette(null).c, 'falls back when the app has no accent');
});

// End to end: real browser, real ffmpeg. Skipped if either is missing.
const hasFF = spawnSync('ffmpeg', ['-version']).status === 0;
let hasPW = true; try { await import('playwright'); } catch { hasPW = false; }
test('end to end: films the sample app into an MP4 with sound', { skip: !(hasFF && hasPW) && 'needs ffmpeg and playwright' }, () => {
  const dir = mkdtempSync(join(tmpdir(), 'reel-test-'));
  const app = new URL('./app/index.html', import.meta.url).href;
  const script = { url: app, intro: false, outro: false, steps: [{ caption: 'Start' }, { click: 'Get started free', caption: 'Sign up' }, { type: ['#email', 'a@b.co'] }] };
  writeFileSync(join(dir, 'd.json'), JSON.stringify(script));
  const out = execFileSync(process.execPath, [new URL('../reel.mjs', import.meta.url).pathname, join(dir, 'd.json'), '--out', join(dir, 'v')], { encoding: 'utf8' });
  assert.match(out, /done:/);
  const mp4 = join(dir, 'v-landscape.mp4');
  assert.ok(existsSync(mp4));
  const probe = execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=codec_type,width,height', '-of', 'csv=p=0', mp4], { encoding: 'utf8' });
  assert.match(probe, /video,1920,1080/);
  assert.match(probe, /audio/);
  // The sign-up box must actually appear: compare a frame before and after the click.
  const grab = (t) => execFileSync('ffmpeg', ['-loglevel', 'error', '-ss', String(t), '-i', mp4, '-frames:v', '1', '-vf', 'scale=64:36', '-f', 'rawvideo', '-pix_fmt', 'gray', '-']);
  const a = grab(0.3), b = grab(3.4);
  let diff = 0; for (let i = 0; i < a.length; i++) diff += Math.abs(a[i] - b[i]);
  assert.ok(diff / a.length > 4, `frames should differ after the click (mean diff ${(diff / a.length).toFixed(1)})`);
});

test('a bad script is refused with the reasons, before any browser starts', () => {
  const dir = mkdtempSync(join(tmpdir(), 'reel-bad-'));
  writeFileSync(join(dir, 'bad.json'), JSON.stringify({ url: 'nope', steps: [] }));
  const r = spawnSync(process.execPath, [new URL('../reel.mjs', import.meta.url).pathname, join(dir, 'bad.json')], { encoding: 'utf8' });
  assert.equal(r.status, 1);
  assert.match(r.stderr, /Fix these/);
  assert.match(r.stderr, /"steps" should be a list/);
});

test('license keys: a signed key passes, a tampered or foreign one fails, no key = free', () => {
  const mine = generateKeyPairSync('ed25519'), other = generateKeyPairSync('ed25519');
  const pub = mine.publicKey.export({ format: 'der', type: 'spki' }).toString('base64');
  const make = (priv, data) => { const p = Buffer.from(JSON.stringify(data)); return p.toString('base64url') + '.' + sign(null, p, priv).toString('base64url'); };
  const key = make(mine.privateKey, { email: 'a@b.co', plan: 'pro' });
  assert.equal(checkLicense(key, pub).email, 'a@b.co');
  const [p, sig] = key.split('.');
  const forged = Buffer.from(JSON.stringify({ email: 'x@y.z', plan: 'pro' })).toString('base64url') + '.' + sig;
  assert.equal(checkLicense(forged, pub), null, 'changed payload');
  assert.equal(checkLicense(make(other.privateKey, { email: 'a@b.co' }), pub), null, 'signed by someone else');
  assert.equal(checkLicense('', pub), null);
  assert.equal(checkLicense('garbage', pub), null);
  assert.equal(checkLicense(key), null, 'no public key set up yet = free version');
});
