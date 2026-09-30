// Reads and checks a demo script. Errors name the step and say how to fix it.
const ACTIONS = ['click', 'hover', 'type', 'scroll', 'zoom', 'wait'];
export function checkScript(s) {
  const errs = [];
  if (!s || typeof s !== 'object') return ['The script should be a JSON object like {"url": "...", "steps": [...]}.'];
  try { const u = new URL(s.url); if (!/^https?:|^file:/.test(u.protocol)) errs.push('"url" must start with http://, https:// or file://.'); }
  catch { errs.push('"url" is missing or not a full address (e.g. "http://localhost:3000").'); }
  if (!Array.isArray(s.steps) || !s.steps.length) errs.push('"steps" should be a list with at least one step.');
  (s.steps || []).forEach((st, i) => {
    const n = `Step ${i + 1}`;
    if (!st || typeof st !== 'object') { errs.push(`${n}: should be an object like {"click": "Sign up"}.`); return; }
    const acts = ACTIONS.filter((a) => a in st);
    if (acts.length > 1) errs.push(`${n}: has ${acts.join(' and ')}; use one action per step.`);
    if (!acts.length && !('caption' in st)) errs.push(`${n}: needs one of ${ACTIONS.join(', ')} (or just a "caption").`);
    if ('type' in st && !(Array.isArray(st.type) && st.type.length === 2 && typeof st.type[1] === 'string')) errs.push(`${n}: "type" should be ["field", "text to type"].`);
    if ('scroll' in st && !Number.isFinite(Number(st.scroll))) errs.push(`${n}: "scroll" should be a number of pixels, like 600.`);
    for (const k of ['click', 'hover', 'zoom']) if (k in st && (typeof st[k] !== 'string' || !st[k].trim())) errs.push(`${n}: "${k}" should be the button text or a CSS selector.`);
    if ('caption' in st && typeof st.caption !== 'string') errs.push(`${n}: "caption" should be text.`);
    if (typeof st.caption === 'string' && st.caption.length > 70) errs.push(`${n}: caption is ${st.caption.length} characters; keep it under 70 so it fits on a phone.`);
  });
  if (s.format && !['landscape', 'vertical', 'square'].includes(s.format)) errs.push('"format" should be landscape, vertical or square.');
  return errs;
}
