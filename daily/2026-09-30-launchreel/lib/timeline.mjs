// Turns captured steps into a timeline, and answers "what does the frame look like at time t".
// Pure and dependency-free: the same file runs in Node (tests) and inside the render page.

export const ease = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const lerp = (a, b, k) => a + (b - a) * k;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// events: from capture. view: {w, h} of the captured viewport in CSS px.
// states: {id: {height}} page heights, so the camera never pans past the page.
// follow: how far the camera leans in on the thing being clicked (1 = off).
export function buildTimeline(events, { view, states, title = true, outro = true, pace = 1, follow = 1.4 }) {
  const P = (s) => s * pace;
  const keys = []; // {t, state, cam:{x,y,z}, cur:{x,y,show}, press, caption, card}
  const marks = []; // when each event starts, for the editor's timeline strip
  let t = 0;
  let state = events.find((e) => e.state)?.state ?? null;
  const pageH = (id) => states[id]?.height ?? view.h;
  // Camera: x, y = top-left of the visible area in page px; z = zoom.
  let cam = { x: 0, y: 0, z: 1 };
  let cur = { x: view.w * 0.62, y: view.h * 0.7, show: false };
  let caption = '';
  let card = null;
  const fit = (c, id = state) => {
    const z = c.z;
    return { x: clamp(c.x, 0, Math.max(0, view.w - view.w / z)), y: clamp(c.y, 0, Math.max(0, pageH(id) - view.h / z)), z };
  };
  const push = (extra = {}) => keys.push({ t, state, cam: { ...cam }, cur: { ...cur }, press: 0, caption, card, ...extra });
  const hold = (s) => { t += s; push(); };
  // Move the camera so a page-space box is on screen (only if it isn't already).
  const reveal = (box, dur = P(0.8)) => {
    const vis = { top: cam.y, bottom: cam.y + view.h / cam.z };
    if (box.y >= vis.top + 8 && box.y + box.h <= vis.bottom - 8) return;
    cam = fit({ x: cam.x, y: box.y + box.h / 2 - view.h / cam.z / 2, z: cam.z });
    t += dur; push();
  };
  const moveTo = (p) => {
    const d = Math.hypot(p.x - cur.x, p.y - cur.y);
    const dur = cur.show ? clamp(d / 900, 0.45, 1.0) : 0.35;
    cur = { x: p.x, y: p.y, show: true };
    t += P(dur); push();
  };
  const center = (b) => ({ x: b.x + b.w / 2, y: b.y + Math.min(b.h / 2, 20) });
  // Lean in on a target and glide the cursor there in the same move.
  const approach = (box) => {
    const p = center(box);
    if (follow > 1) {
      const z = Math.max(1, Math.min(follow, (view.w * 0.9) / Math.max(box.w, 1)));
      cam = fit({ x: p.x - view.w / z / 2, y: p.y - view.h / z / 2, z });
    } else reveal(box, 0);
    const d = Math.hypot(p.x - cur.x, p.y - cur.y);
    const dur = Math.max(cur.show ? clamp(d / 900, 0.5, 1.0) : 0.5, follow > 1 ? 0.7 : 0);
    cur = { x: p.x, y: p.y, show: true };
    t += P(dur); push();
  };
  const unzoom = (dur = 0.6) => { if (cam.z !== 1) { cam = fit({ x: 0, y: cam.y, z: 1 }); t += P(dur); push(); } };

  if (title) { card = 'title'; push(); t += 2.2; push(); card = null; t += 0.5; push(); } else push();

  let zoomed = false;
  for (const [ei, e] of events.entries()) {
    marks.push({ event: ei, t });
    if (zoomed && e.kind !== 'zoom') { cam = fit({ ...cam, z: 1, x: 0 }); t += P(0.6); push(); zoomed = false; }
    if ('caption' in e && e.caption !== undefined) { caption = e.caption; push(); }
    if (e.state && e.state !== state && e.kind !== 'type') { state = e.state; cam = fit(cam); push(); }
    switch (e.kind) {
      case 'start': cam = fit({ x: 0, y: e.scrollY ?? 0, z: 1 }); push(); hold(P(0.8)); break;
      case 'click': {
        approach(e.box);
        t += 0.12; push({ press: 1 });
        t += 0.12; push({ press: 0 });
        const scrolled = e.afterScrollY != null && e.beforeScrollY != null && Math.abs(e.afterScrollY - e.beforeScrollY) > 4;
        if (e.after && e.after !== state) {
          state = e.after;
          if (e.afterScrollY != null && Math.abs(e.afterScrollY - cam.y) > 4) cam = fit({ ...cam, y: e.afterScrollY }); else cam = fit(cam);
          t += 0.3; push();
        }
        if (scrolled) { cam = fit({ x: 0, y: e.afterScrollY, z: 1 }); t += P(0.8); push(); } // the click scrolled the page: follow it
        hold(P(e.hold ?? 1.0));
        break;
      }
      case 'hover': approach(e.box); if (e.after) { state = e.after; t += 0.25; push(); } hold(P(e.hold ?? 0.8)); break;
      case 'type': {
        approach(e.box);
        t += 0.12; push({ press: 1 }); t += 0.12; push({ press: 0 });
        const per = clamp(1.4 / Math.max(1, e.frames.length), 0.06, 0.16);
        for (const s of e.frames) { state = s; t += per; push(); }
        hold(P(e.hold ?? 0.7));
        break;
      }
      case 'scroll': {
        cam = fit({ x: 0, y: cam.y + e.by, z: 1 });
        cur = { ...cur, show: cur.show };
        t += P(clamp(Math.abs(e.by) / 700, 0.7, 1.8)); push();
        hold(P(e.hold ?? 0.5));
        break;
      }
      case 'zoom': {
        unzoom(0.4);
        const b = e.box, pad = 28;
        const z = clamp(Math.min(view.w / (b.w + pad * 2), view.h / (b.h + pad * 2)), 1, e.max ?? 2.2);
        cam = fit({ x: b.x + b.w / 2 - view.w / z / 2, y: b.y + b.h / 2 - view.h / z / 2, z });
        t += P(0.9); push();
        hold(P(e.hold ?? 1.6));
        zoomed = true;
        break;
      }
      case 'wait': unzoom(); hold(P((e.ms ?? 800) / 1000)); break;
    }
  }
  unzoom();
  if (outro) { caption = ''; t += 0.3; push(); card = 'outro'; t += 0.5; push(); t += 2.4; push(); }
  marks.push({ event: events.length, t }); // end marker (outro start)
  return { keys, duration: t, marks };
}

// The frame at time t: camera, cursor, which screenshot(s) to show and how much to blend.
export function frameAt(tl, t) {
  const k = tl.keys;
  let i = 0;
  while (i < k.length - 1 && k[i + 1].t <= t) i++;
  const a = k[i], b = k[Math.min(i + 1, k.length - 1)];
  const span = b.t - a.t;
  const u = span > 0 ? ease((t - a.t) / span) : 1;
  const cam = { x: lerp(a.cam.x, b.cam.x, u), y: lerp(a.cam.y, b.cam.y, u), z: lerp(a.cam.z, b.cam.z, u) };
  const cur = { x: lerp(a.cur.x, b.cur.x, u), y: lerp(a.cur.y, b.cur.y, u), show: a.cur.show || b.cur.show, alpha: a.cur.show && b.cur.show ? 1 : b.cur.show ? u : 1 - u };
  // A state change blends over 0.25s after the key where it happened.
  let from = a.state, to = a.state, mix = 1;
  if (i > 0 && k[i - 1].state !== a.state) {
    const since = t - a.t;
    if (since < 0.25) { from = k[i - 1].state; mix = ease(since / 0.25); }
  }
  // Press: a quick dip and ripple around the keys marked press.
  let press = 0;
  for (const kk of k) if (kk.press && Math.abs(t - kk.t) < 0.35) press = Math.max(press, 1 - Math.abs(t - kk.t) / 0.35);
  // Caption and card fade in over 0.25s from the key where they changed.
  const since = (field) => { let j = i; while (j > 0 && k[j - 1][field] === a[field]) j--; return t - k[j].t; };
  const capIn = a.caption ? clamp(since('caption') / 0.25, 0, 1) : 0;
  const cardIn = a.card ? clamp(since('card') / 0.35, 0, 1) : 0;
  const cardOut = !a.card && i > 0 && k[i - 1].card ? 1 - clamp((t - a.t) / 0.5, 0, 1) : 0;
  const capT = a.caption ? since('caption') : 0; // seconds since this caption appeared, for text animations
  return { cam, cur, from, to, mix, press, caption: a.caption, capIn, capT, card: a.card || (cardOut ? k[i - 1].card : null), cardAlpha: a.card ? cardIn : cardOut };
}
