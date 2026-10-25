// Finds the headless Chromium on this machine, so a new session's install path can't break the renders.
// Order: $CHROME, then any /opt/pw-browsers/chromium_headless_shell-*/ build (newest first), then full chromium.
import fs from 'fs';
import path from 'path';

function find() {
  if (process.env.CHROME && fs.existsSync(process.env.CHROME)) return process.env.CHROME;
  const root = '/opt/pw-browsers';
  const dirs = fs.existsSync(root) ? fs.readdirSync(root) : [];
  const ver = (d) => +(d.match(/-(\d+)$/) || [0, 0])[1];
  const cands = [];
  for (const d of dirs.filter((d) => d.startsWith('chromium_headless_shell-')).sort((a, b) => ver(b) - ver(a))) {
    cands.push(path.join(root, d, 'chrome-linux', 'headless_shell'));
    cands.push(path.join(root, d, 'chrome-headless-shell-linux64', 'chrome-headless-shell'));
  }
  for (const d of dirs.filter((d) => /^chromium-\d+$/.test(d)).sort((a, b) => ver(b) - ver(a))) {
    cands.push(path.join(root, d, 'chrome-linux64', 'chrome'));
    cands.push(path.join(root, d, 'chrome-linux', 'chrome'));
  }
  const hit = cands.find((p) => fs.existsSync(p));
  if (!hit) throw new Error('no headless Chromium found; set CHROME=/path/to/chrome');
  return hit;
}

export const CHROME = find();
