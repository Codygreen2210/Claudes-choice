// Prompt-to-video. LaunchReel first lists what's really on your page (buttons, links, fields,
// sections), then asks Claude to write a script using only those. Anything that isn't on the
// page is sent back once to be fixed; if it's still wrong, you get told plainly.
import { checkScript } from './script.mjs';
import { CAPTION_STYLES } from './styles.mjs';
import { GENRES } from './music.mjs';

const LIMITS = { prompt: 600, items: 60 };

// What a viewer could click, type into, or zoom in on.
export async function inventory(url, { chromium, mobile = false }) {
  const b = await chromium.launch();
  try {
    const ctx = await b.newContext({ viewport: mobile ? { width: 390, height: 844 } : { width: 1120, height: 700 }, isMobile: mobile });
    const p = await ctx.newPage();
    await p.goto(url, { waitUntil: 'networkidle', timeout: 30000 }).catch((e) => { if (/ERR_|NS_ERROR/.test(e.message)) throw new Error(`Couldn't open ${url}. Is the app running?`); });
    return await p.evaluate((max) => {
      const vis = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 4 && r.height > 4 && s.visibility !== 'hidden' && s.display !== 'none'; };
      const txt = (el) => (el.innerText || el.value || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 60);
      const uniq = (a) => [...new Set(a.filter(Boolean))].slice(0, max);
      // Hidden things matter too: a dashboard that appears after sign-up is still part of the demo.
      const txtAny = (el) => (el.textContent || el.value || el.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim().slice(0, 60);
      const allClick = [...document.querySelectorAll('button, a[href], [role=button], input[type=submit], summary')];
      const clickables = uniq(allClick.filter(vis).map(txt));
      const laterClickables = uniq(allClick.filter((el) => !vis(el)).map(txtAny)).filter((t) => !clickables.includes(t));
      const fields = [...document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=checkbox]):not([type=radio]), textarea')].slice(0, max).map((el) => {
        const sel = el.id ? '#' + CSS.escape(el.id) : el.name ? `[name="${el.name}"]` : el.placeholder ? `[placeholder="${el.placeholder}"]` : null;
        const label = (el.labels?.[0]?.innerText || el.placeholder || el.name || el.type || '').trim().slice(0, 50);
        return sel && { selector: sel, label, type: el.type || 'text', visibleNow: vis(el) };
      }).filter(Boolean);
      const ids = [...document.querySelectorAll('[id]')].filter((el) => !/^(root|__next|app)$/.test(el.id) && !/^(SCRIPT|STYLE|INPUT|TEXTAREA|BUTTON)$/.test(el.tagName));
      const sections = uniq(ids.filter((el) => vis(el) && el.getBoundingClientRect().height > 60).map((el) => '#' + CSS.escape(el.id)));
      const laterSections = uniq(ids.filter((el) => !vis(el) && (el.textContent || '').trim().length > 10).map((el) => '#' + CSS.escape(el.id))).filter((x) => !sections.includes(x));
      const headings = uniq([...document.querySelectorAll('h1,h2,h3')].filter(vis).map(txt));
      return { title: document.title, description: document.querySelector('meta[name=description]')?.content || '', headings, clickables, laterClickables, fields, sections, laterSections, pageHeight: document.documentElement.scrollHeight };
    }, LIMITS.items);
  } finally { await b.close(); }
}

export function buildPrompt(userPrompt, inv, format = 'landscape') {
  const styles = Object.entries(CAPTION_STYLES).map(([k, v]) => `${k} (${v.label})`).join(', ');
  const genres = Object.entries(GENRES).map(([k, v]) => `${k} (${v.blurb})`).join(', ');
  const system = `You write demo-video scripts for LaunchReel, a tool that films a web app. Reply with ONE JSON object and nothing else.
Shape: {"title": str, "tagline": str (under 70 chars), "cta": str (short), "captionStyle": one of [${Object.keys(CAPTION_STYLES).join(', ')}], "music": {"genre": one of [${Object.keys(GENRES).join(', ')}], "key": "C".."B"}, "pace": 0.8-1.4, "steps": [...]}
Each step has exactly one action or none, plus an optional "caption" (under 60 chars, plain words a viewer understands):
 {"click": "<exact text of a clickable from the list>"} | {"type": ["<field selector from the list>", "<realistic sample text>"]} | {"zoom": "<section selector from the list>"} | {"scroll": <pixels>} | {"hover": "<clickable text>"} | {"caption": "..."} alone for a pause.
Rules: only use clickables, field selectors and sections exactly as listed. Ones that appear later can only be used after the step that reveals them. Start with a caption-only step that says what the app is. 4-9 steps. A field can only be typed into after whatever reveals it (e.g. a sign-up button) is clicked; fields marked hidden need that. Never click things that delete data, pay, log out or send real messages. Captions describe the benefit, not the button. Style guide: ${styles}. Music: ${genres}. Format: ${format}.`;
  const user = `What the video should show: ${String(userPrompt).slice(0, LIMITS.prompt)}

The page (${inv.title}${inv.description ? ' - ' + inv.description : ''}):
Headings: ${JSON.stringify(inv.headings)}
Clickables: ${JSON.stringify(inv.clickables)}
Clickables that appear only after an earlier step (e.g. after sign-up): ${JSON.stringify(inv.laterClickables || [])}
Fields: ${JSON.stringify(inv.fields.map((f) => ({ selector: f.selector, label: f.label, type: f.type, hidden: !f.visibleNow })))}
Sections: ${JSON.stringify(inv.sections)}
Sections that appear only after an earlier step: ${JSON.stringify(inv.laterSections || [])}
Page height: ${inv.pageHeight}px`;
  return { system, user };
}

// Checks a proposed script against the real page. Returns a list of problems (empty = good).
export function checkAgainstPage(script, invIn) {
  const inv = { ...invIn, clickables: [...(invIn.clickables || []), ...(invIn.laterClickables || [])], sections: [...(invIn.sections || []), ...(invIn.laterSections || [])] };
  const errs = [];
  const has = (list, v) => list.some((x) => x.toLowerCase() === String(v).toLowerCase());
  const loose = (list, v) => list.some((x) => x.toLowerCase().includes(String(v).toLowerCase()) && String(v).length >= 2);
  (script.steps || []).forEach((s, i) => {
    const n = `Step ${i + 1}`;
    for (const k of ['click', 'hover']) if (k in s && !(has(inv.clickables, s[k]) || loose(inv.clickables, s[k]) || has(inv.sections, s[k]))) errs.push(`${n}: "${s[k]}" isn't a button or link on the page.`);
    if ('type' in s && Array.isArray(s.type) && !inv.fields.some((f) => f.selector === s.type[0])) errs.push(`${n}: "${s.type[0]}" isn't a field on the page. Use a selector from the Fields list.`);
    if ('zoom' in s && !(has(inv.sections, s.zoom) || inv.fields.some((f) => f.selector === s.zoom) || loose(inv.clickables, s.zoom))) errs.push(`${n}: "${s.zoom}" isn't a section on the page.`);
    if (s.click && /delete|remove|log ?out|sign ?out|pay|purchase|buy now|unsubscribe/i.test(s.click)) errs.push(`${n}: won't click "${s.click}" in a demo.`);
  });
  return errs;
}

export function parseJson(text) {
  const t = String(text).trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '');
  const a = t.indexOf('{'), b = t.lastIndexOf('}');
  if (a < 0 || b < a) throw new Error("The AI didn't return a script.");
  return JSON.parse(t.slice(a, b + 1));
}

// call({system, messages}) -> text. Tries once, then once more with the problems listed.
export async function promptToScript({ prompt, url, inv, call, format }) {
  if (!String(prompt || '').trim()) throw new Error('Describe the video you want first.');
  const { system, user } = buildPrompt(prompt, inv, format);
  const messages = [{ role: 'user', content: user }];
  let lastErrs = [];
  for (let attempt = 0; attempt < 2; attempt++) {
    const text = await call({ system, messages });
    let s;
    try { s = parseJson(text); } catch { lastErrs = ['Reply was not valid JSON.']; messages.push({ role: 'assistant', content: String(text).slice(0, 4000) }, { role: 'user', content: 'That was not valid JSON. Reply with only the JSON object.' }); continue; }
    s.url = url;
    if (!CAPTION_STYLES[s.captionStyle]) s.captionStyle = 'clean';
    if (!s.music || !GENRES[s.music.genre]) s.music = { genre: 'lofi', ...(s.music || {}), ...(GENRES[s.music?.genre] ? {} : { genre: 'lofi' }) };
    const errs = [...checkScript(s), ...checkAgainstPage(s, inv)];
    if (!errs.length) return { script: s, attempts: attempt + 1 };
    lastErrs = errs;
    messages.push({ role: 'assistant', content: JSON.stringify(s) }, { role: 'user', content: 'Fix these problems and reply with the whole corrected JSON only:\n- ' + errs.join('\n- ') });
  }
  throw new Error("The AI's script still had problems, so nothing was changed:\n- " + lastErrs.join('\n- '));
}

// Callers. Your own Anthropic key, straight from your computer:
export function anthropicCaller({ apiKey, model = process.env.LAUNCHREEL_AI_MODEL || 'claude-sonnet-5-5', fetchImpl = fetch }) {
  return async ({ system, messages }) => {
    const r = await fetchImpl('https://api.anthropic.com/v1/messages', {
      method: 'POST', headers: { 'content-type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify({ model, max_tokens: 1500, system, messages }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error('AI request failed: ' + (j.error?.message || r.status));
    return (j.content || []).map((c) => c.text || '').join('');
  };
}
// Or the seller's hosted service (Pro key). It only accepts the description and the page list
// and builds the prompt itself, so it can't be used as a general-purpose AI.
export async function proxyScript({ url, licenseKey, prompt, inv, format, pageUrl, fetchImpl = fetch }) {
  const r = await fetchImpl(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ licenseKey, prompt, inventory: inv, format, url: pageUrl }) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || 'AI service error ' + r.status);
  return j;
}

// Keeps a page list small and plain before it goes anywhere.
export function cleanInventory(inv) {
  const str = (v, n) => String(v ?? '').slice(0, n);
  const arr = (a, n, m) => (Array.isArray(a) ? a.slice(0, n).map((x) => str(x, m)) : []);
  return {
    title: str(inv?.title, 120), description: str(inv?.description, 200),
    headings: arr(inv?.headings, 30, 80), clickables: arr(inv?.clickables, 60, 60), laterClickables: arr(inv?.laterClickables, 40, 60), sections: arr(inv?.sections, 40, 60), laterSections: arr(inv?.laterSections, 30, 60),
    fields: Array.isArray(inv?.fields) ? inv.fields.slice(0, 30).map((f) => ({ selector: str(f?.selector, 80), label: str(f?.label, 50), type: str(f?.type, 20), visibleNow: !!f?.visibleNow })) : [],
    pageHeight: Math.min(100000, Number(inv?.pageHeight) || 0),
  };
}
