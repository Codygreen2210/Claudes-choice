// Draws every frame in a headless browser page (the "studio") and streams them into ffmpeg,
// then adds the music. Frames are drawn at exact times, so the video is smooth and repeatable.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { spawn } from 'node:child_process';
import { FORMATS } from './capture.mjs';
import { buildTimeline } from './timeline.mjs';
import { makeMusic } from './music.mjs';
import { sfxWav } from './sfx.mjs';
import { mix } from './mix.mjs';
import { checkAudio } from './ears.mjs';
import { CAPTION_STYLES, fontCss, styleCss, CAPTION_ANIM } from './styles.mjs';

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// "rgb(29, 107, 79)" or "#1d6b4f" -> [r,g,b]
export function parseColor(c) {
  if (!c) return null;
  let m = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(c.trim());
  if (m) { let h = m[1]; if (h.length === 3) h = [...h].map((x) => x + x).join(''); return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)); }
  m = c.match(/\d+(\.\d+)?/g);
  return m && m.length >= 3 ? m.slice(0, 3).map(Number) : null;
}
// A backdrop that suits the app: its accent, darkened and shifted for depth.
export function palette(accent) {
  const [r, g, b] = parseColor(accent) || [79, 70, 229];
  const mix = (k, t) => [r, g, b].map((v) => Math.round(v * (1 - k) + t * k));
  const rgb = (a) => `rgb(${a.join(',')})`;
  return { a: rgb(mix(0.55, 12)), b: rgb(mix(0.25, 20)), c: rgb([r, g, b]), glow: `rgba(${r},${g},${b},0.35)` };
}

export function studioHtml({ fmt, meta, script, states, tlSource, imgBase = '', fontBase }) {
  const [W, H] = FORMATS[fmt].stage;
  const [vw, vh] = FORMATS[fmt].view;
  const phone = FORMATS[fmt].frame === 'phone';
  // Size the window/phone to the stage.
  const scale = phone ? Math.min((W * 0.74) / vw, (H * 0.8) / vh) : Math.min((W * 0.84) / vw, (H * (fmt === 'square' ? 0.66 : 0.8)) / (vh + 44));
  const winW = vw * scale, winH = vh * scale;
  const pal = palette(script.accent || meta.accent || meta.theme);
  const title = script.title || meta.title || meta.host;
  const tag = script.tagline || '';
  const cta = script.cta || meta.host;
  const big = phone || fmt === 'square';
  const styleName = CAPTION_STYLES[script.captionStyle] ? script.captionStyle : 'clean';
  const st = CAPTION_STYLES[styleName];
  return `<!doctype html><html><head><meta charset="utf-8">${fontCss([st.font, 'Inter'], { base: fontBase })}<style>
  *{box-sizing:border-box;margin:0}
  html,body{width:${W}px;height:${H}px;overflow:hidden;background:${pal.a}}
  body{font-family:"Inter","Segoe UI","Helvetica Neue",Arial,sans-serif;-webkit-font-smoothing:antialiased}
  #bg{position:absolute;inset:0;background:radial-gradient(120% 90% at 20% 0%,${pal.b} 0%,${pal.a} 55%,#07080c 100%)}
  #glow{position:absolute;width:${W * 0.9}px;height:${W * 0.9}px;border-radius:50%;background:radial-gradient(circle,${pal.glow},transparent 65%);left:${W * 0.05}px;top:${H * 0.5 - W * 0.45}px;filter:blur(20px)}
  #win{position:absolute;left:${(W - winW) / 2}px;top:${phone ? Math.max(H * 0.13, (H - winH) / 2 + H * 0.045) : (H - winH - (big ? 0 : 44)) / 2 + (big ? 30 : 10)}px;width:${winW}px;
    ${phone ? `border-radius:${58 * scale / 2.2}px;box-shadow:0 0 0 ${14 * scale / 2}px #0b0c10,0 0 0 ${16 * scale / 2}px #2a2d36,0 40px 120px rgba(0,0,0,.55)` : 'border-radius:14px;box-shadow:0 30px 90px rgba(0,0,0,.5),0 0 0 1px rgba(255,255,255,.08)'};overflow:hidden;background:#fff;z-index:1;isolation:isolate}
  #bar{height:44px;background:#eceef2;display:${phone ? 'none' : 'flex'};align-items:center;gap:8px;padding:0 16px;border-bottom:1px solid #d9dce3}
  #bar i{width:12px;height:12px;border-radius:50%;display:block}
  #url{margin-left:18px;flex:1;max-width:520px;height:28px;border-radius:8px;background:#fff;color:#51565f;font-size:14px;display:flex;align-items:center;padding:0 12px;gap:6px}
  #vp{position:relative;width:${winW}px;height:${winH}px;overflow:hidden;background:#fff}
  #vp img{position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform,opacity}
  #cur{position:absolute;left:0;top:0;width:${big ? 44 : 30}px;height:${big ? 44 : 30}px;pointer-events:none;filter:drop-shadow(0 3px 6px rgba(0,0,0,.35))}
  #rip{position:absolute;border-radius:50%;border:3px solid ${pal.c};background:${pal.glow};pointer-events:none}
  #cap{position:absolute;z-index:5;left:50%;transform:translateX(-50%);${phone ? `top:${H * 0.035}px` : `bottom:${big ? H * 0.06 : 34}px`};max-width:${W * 0.86}px;white-space:normal}
  ${styleCss(styleName, { big, accent: pal.c, glow: pal.glow })}
  #card{position:absolute;z-index:10;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:${big ? 28 : 20}px;text-align:center;padding:0 8%;background:radial-gradient(120% 90% at 50% 30%,${pal.b},${pal.a} 60%,#07080c)}
  #card h1{color:#fff;font-size:${big ? 104 : 92}px;letter-spacing:-.02em;line-height:1.02;font-weight:800}
  #card p{color:rgba(255,255,255,.82);font-size:${big ? 46 : 38}px;max-width:26ch;line-height:1.3}
  #card .cta{margin-top:10px;color:#0b0c10;background:#fff;font-weight:700;font-size:${big ? 44 : 34}px;padding:16px 34px;border-radius:999px}
  </style></head><body>
  <div id="bg"></div><div id="glow"></div>
  <div id="win"><div id="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><div id="url"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#51565f" stroke-width="2.5"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>${esc(meta.host || 'localhost')}</div></div>
    <div id="vp">${Object.entries(states).map(([id]) => `<img id="${id}" src="${imgBase}${id}.png" style="opacity:0">`).join('')}
    <div id="rip" style="opacity:0"></div>
    <svg id="cur" viewBox="0 0 24 24" style="opacity:0">${phone ? '<circle cx="12" cy="12" r="9" fill="rgba(255,255,255,.55)" stroke="#111" stroke-width="1.5"/>' : '<path d="M4 2l15 10.5-6.6 1.2 3.9 7.3-2.8 1.5-3.9-7.3L4 19.5z" fill="#fff" stroke="#111" stroke-width="1.4" stroke-linejoin="round"/>'}</svg></div></div>
  <div id="cap" style="opacity:0"></div>
  <div id="card" style="opacity:0"><h1 id="ct"></h1><p id="cp"></p><div class="cta" id="cc" hidden></div>${script._licensed ? '' : '<div id="wm" style="position:absolute;bottom:5%;color:rgba(255,255,255,.6);font-size:' + (big ? 30 : 24) + 'px">Made with LaunchReel</div>'}</div>
  <script>
  ${tlSource}
  ${CAPTION_ANIM}
  const ST=${JSON.stringify(st)}, ACC=${JSON.stringify(pal.c)};
  const VW=${vw}, VH=${vh}, S=${scale}, PH=${phone};
  const T={title:${JSON.stringify(title)},tag:${JSON.stringify(tag)},cta:${JSON.stringify(cta)}};
  let lastCap=null, lastCard=null;
  window.draw=(t)=>{
    const f=frameAt(window.TL,t);
    const z=f.cam.z*S;
    for(const img of document.querySelectorAll('#vp img')){
      const o = img.id===f.to ? (f.from!==f.to? f.mix:1) : img.id===f.from && f.from!==f.to ? 1 : 0; // old state stays under while the new one fades in
      img.style.opacity=o; img.style.zIndex = img.id===f.to?2:1;
      if(o>0){ img.style.width=VW+'px'; img.style.transform='translate('+(-f.cam.x*z)+'px,'+(-f.cam.y*z)+'px) scale('+z+')'; }
    }
    const cx=(f.cur.x-f.cam.x)*z, cy=(f.cur.y-f.cam.y)*z;
    const cur=document.getElementById('cur');
    cur.style.opacity=f.cur.show?f.cur.alpha:0;
    const cs=1-0.18*f.press;
    cur.style.transform='translate('+(cx-(PH?cur.clientWidth/2:4))+'px,'+(cy-(PH?cur.clientHeight/2:3))+'px) scale('+cs+')';
    const rip=document.getElementById('rip');
    if(f.press>0){const r=(1-f.press)*46+14; rip.style.opacity=f.press; rip.style.width=rip.style.height=r*2+'px'; rip.style.transform='translate('+(cx-r)+'px,'+(cy-r)+'px)';} else rip.style.opacity=0;
    const cap=document.getElementById('cap');
    if(f.caption){ animCaption(cap, ST, f.caption, f.capIn, f.capT, ACC); } else cap.style.opacity=0;
    const card=document.getElementById('card');
    if(f.card!==lastCard){ lastCard=f.card;
      document.getElementById('ct').textContent=f.card==='outro'?T.title:T.title;
      document.getElementById('cp').textContent=f.card==='outro'?'Try it yourself':T.tag;
      const cc=document.getElementById('cc'); cc.hidden=f.card!=='outro'; cc.textContent=T.cta; }
    card.style.opacity=f.card?f.cardAlpha:0;
  };
  window.ready=Promise.all([...[...document.images].map(i=>i.decode().catch(()=>{})), document.fonts.ready.then(()=>Promise.all([...document.fonts].map(f=>f.load().catch(()=>{}))))]);
  </script></body></html>`;
}

// The timeline for a capture, with the script's timing options. Export and editor share this.
export function timelineFor({ script, cap, fmt }) {
  const [vw, vh] = FORMATS[fmt].view;
  const heights = Object.fromEntries(Object.entries(cap.states).map(([k, v]) => [k, { height: v.height }]));
  return buildTimeline(cap.events, { view: { w: vw, h: vh }, states: heights, pace: script.pace ?? 1, follow: script.follow === false ? 1 : Math.min(Number(script.follow) || 1.4, FORMATS[fmt].frame === 'phone' ? 1.15 : 3), title: script.intro !== false, outro: script.outro !== false });
}

// Render the video. Needs ffmpeg on the PATH.
export async function render({ script, cap, fmt, dir, out, chromium, fps = 30, log = () => {} }) {
  const tl = timelineFor({ script, cap, fmt });
  const tlSource = readFileSync(new URL('./timeline.mjs', import.meta.url), 'utf8').replace(/^export /gm, '');
  writeFileSync(join(dir, 'studio.html'), studioHtml({ fmt, meta: cap.meta, script, states: cap.states, tlSource }));
  const audio = await soundtrack({ script, tl, dir });
  // The studio's ears check every soundtrack before it goes in the video (Cody's music rule).
  // Notes and the picture land next to the video: <out>.ears/
  const ears = script.ears === false ? { skipped: 'turned off in the script' } : await checkAudio(audio, { out: out.replace(/\.mp4$/i, '') + '.ears', log });

  const [W, H] = FORMATS[fmt].stage;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.goto('file://' + join(dir, 'studio.html'));
  await page.evaluate(() => window.ready);
  await page.evaluate((tl) => { window.TL = tl; }, tl);
  writeFileSync(join(dir, 'timeline.json'), JSON.stringify(tl));
  const frames = Math.ceil(tl.duration * fps);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-i', audio,
    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out]);
  let err = '';
  ff.stderr.on('data', (d) => (err += d));
  const done = new Promise((res, rej) => { ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg failed: ' + err.slice(-400))))); ff.on('error', () => rej(new Error('ffmpeg is not installed. Get it from ffmpeg.org, then try again.'))); });
  try {
    for (let i = 0; i < frames; i++) {
      await page.evaluate((t) => window.draw(t), i / fps);
      const jpg = await page.screenshot({ type: 'jpeg', quality: 90 });
      if (!ff.stdin.write(jpg)) await new Promise((r) => ff.stdin.once('drain', r));
      if (i % fps === 0) log(`frame ${i}/${frames}`);
    }
  } finally {
    ff.stdin.end();
    await browser.close();
  }
  await done;
  return { duration: tl.duration, frames, timeline: tl, ears };
}

// Music + sound effects + optional voiceover (music ducks under the voice). Used by export and the editor preview.
export async function soundtrack({ script, tl, dir, name = 'soundtrack.wav' }) {
  const seconds = tl.duration + 0.5;
  const m = script.music || {};
  const music = join(dir, 'music.wav');
  writeFileSync(music, makeMusic({ seconds, seed: m.seed ?? hashSeed(script.url), key: m.key ?? 'F', genre: m.genre ?? m.mood ?? 'lofi', bpm: m.bpm, volume: m.off ? 0.0001 : m.volume ?? 0.5, parts: m.parts || {} }));
  const fx = script.sfx || {};
  let sfx = null;
  if (fx.on !== false && tl.cues?.length) { sfx = join(dir, 'sfx.wav'); writeFileSync(sfx, sfxWav(tl.cues, seconds, { volume: fx.volume ?? 0.7, off: fx.off || [] })); }
  const v = script.voice;
  const voice = v && v.file && existsSync(v.file) ? v.file : null;
  if (!sfx && !voice) return music;
  const out = join(dir, name);
  await mix({ music, sfx, voice, voiceAt: v?.at ?? 0, voiceVol: v?.volume ?? 1, seconds, out });
  return out;
}

export function hashSeed(s) { let h = 2166136261; for (const c of String(s)) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; }
