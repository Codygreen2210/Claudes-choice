// Caption and title styles. Every font here is under the SIL Open Font License (free for
// commercial use, including in videos you sell). Fonts load from Google Fonts at render time,
// or from local @fontsource packages when LAUNCHREEL_FONTS points at a node_modules folder.
import { existsSync } from 'node:fs';
import { join } from 'node:path';

export const FONTS = {
  Inter: [500, 600, 800], Montserrat: [800, 900], Poppins: [600, 800], Anton: [400], 'Bebas Neue': [400],
  Syne: [700, 800], 'JetBrains Mono': [500, 700], Outfit: [600, 800], Caveat: [700], 'DM Serif Display': [400],
  'Space Grotesk': [600, 700], Fredoka: [600, 700], 'Archivo Black': [400], 'Permanent Marker': [400],
};

// anim: fade | pop | slide | typewriter | karaoke | bounce | wipe
export const CAPTION_STYLES = {
  clean: { label: 'Clean pill', font: 'Inter', weight: 600, size: 1, color: '#fff', bg: 'rgba(10,12,18,.72)', radius: 18, anim: 'slide' },
  tiktok: { label: 'Bold outline', font: 'Montserrat', weight: 900, size: 1.15, color: '#fff', stroke: '#000', upper: true, anim: 'pop' },
  karaoke: { label: 'Word by word', font: 'Poppins', weight: 800, size: 1.1, color: '#fff', stroke: '#000', hi: 'accent', anim: 'karaoke' },
  headline: { label: 'Headline block', font: 'Anton', weight: 400, size: 1.3, color: '#111', bg: '#ffd400', radius: 4, upper: true, anim: 'wipe' },
  neon: { label: 'Neon', font: 'Syne', weight: 800, size: 1.1, color: '#fff', glow: 'accent', anim: 'fade' },
  typewriter: { label: 'Typewriter', font: 'JetBrains Mono', weight: 700, size: 0.9, color: '#e8ffe8', bg: 'rgba(0,0,0,.8)', radius: 8, anim: 'typewriter' },
  card: { label: 'Soft card', font: 'Outfit', weight: 600, size: 1, color: '#15171c', bg: '#fff', radius: 22, shadow: true, anim: 'slide' },
  handwritten: { label: 'Handwritten', font: 'Caveat', weight: 700, size: 1.5, color: '#fff', shadowText: true, tilt: -2, anim: 'pop' },
  editorial: { label: 'Editorial', font: 'DM Serif Display', weight: 400, size: 1.15, color: '#fff', italic: true, shadowText: true, anim: 'fade' },
  lower: { label: 'Lower third', font: 'Space Grotesk', weight: 700, size: 0.95, color: '#fff', bg: 'rgba(12,14,20,.86)', radius: 6, bar: 'accent', align: 'left', anim: 'wipe' },
  bubble: { label: 'Bubble', font: 'Fredoka', weight: 700, size: 1.1, color: '#fff', bg: 'accent', radius: 999, anim: 'bounce' },
  marker: { label: 'Marker', font: 'Permanent Marker', weight: 400, size: 1.1, color: '#fff', stroke: '#000', tilt: -1.5, anim: 'pop' },
};

export function fontCss(families, { base } = {}) {
  const list = [...new Set(families)].filter((f) => FONTS[f]);
  const local = process.env.LAUNCHREEL_FONTS;
  if (local) {
    const out = [];
    for (const f of list) {
      const slug = f.toLowerCase().replace(/ /g, '-');
      for (const w of FONTS[f]) {
        for (const style of ['normal', 'italic']) {
          const file = join(local, '@fontsource', slug, 'files', `${slug}-latin-${w}-${style}.woff2`);
          if (existsSync(file)) out.push(`@font-face{font-family:"${f}";font-weight:${w};font-style:${style};src:url("${base ? base + `@fontsource/${slug}/files/${slug}-latin-${w}-${style}.woff2` : 'file://' + file}") format("woff2")}`);
        }
      }
    }
    return `<style>${out.join('\n')}</style>`;
  }
  if (!list.length) return '';
  const q = list.map((f) => `family=${f.replace(/ /g, '+')}:wght@${FONTS[f].join(';')}`).join('&');
  return `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?${q}&display=block">`;
}

// CSS for the caption box and the card title in a given style.
export function styleCss(name, { big, accent, glow }) {
  const s = CAPTION_STYLES[name] || CAPTION_STYLES.clean;
  const col = (c) => (c === 'accent' ? accent : c);
  const px = (big ? 48 : 42) * s.size;
  const stroke = s.stroke ? `-webkit-text-stroke:${Math.max(2, px / 14)}px ${s.stroke};paint-order:stroke fill;` : '';
  const tshadow = s.glow ? `text-shadow:0 0 18px ${col(s.glow)},0 0 42px ${col(s.glow)};` : s.shadowText ? 'text-shadow:0 3px 14px rgba(0,0,0,.6);' : '';
  const box = s.bg ? `background:${col(s.bg)};padding:${big ? '18px 30px' : '12px 26px'};border-radius:${s.radius ?? 18}px;${s.bg.startsWith('rgba') ? 'backdrop-filter:blur(8px);' : ''}` : 'padding:6px 12px;';
  return `#cap{font-family:"${s.font}",Inter,system-ui,sans-serif;font-weight:${s.weight};font-size:${px}px;color:${s.color};${s.italic ? 'font-style:italic;' : ''}${s.upper ? 'text-transform:uppercase;letter-spacing:.01em;' : ''}${stroke}${tshadow}${box}${s.shadow ? 'box-shadow:0 14px 40px rgba(0,0,0,.35);' : ''}${s.bar ? `border-left:8px solid ${col(s.bar)};` : ''}text-align:${s.align || 'center'};line-height:1.18}
  #cap .w{display:inline-block}
  #card h1{font-family:"${s.font}",Inter,system-ui,sans-serif;font-weight:${Math.max(s.weight, FONTS[s.font]?.at(-1) ?? 800)};${s.upper ? 'text-transform:uppercase;' : ''}${s.italic ? 'font-style:italic;' : ''}}`;
}

// Runs inside the studio page each frame: animates the caption from capT (seconds since it appeared).
export const CAPTION_ANIM = `
function animCaption(el, st, text, capIn, capT, accent){
  const ease=(x)=>x<=0?0:x>=1?1:1-Math.pow(1-x,3);
  const back=(x)=>{x=Math.min(1,Math.max(0,x));const c=1.70158;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2);};
  const tilt=st.tilt?' rotate('+st.tilt+'deg)':'';
  let op=capIn, tf='translateX(-50%)', clip='none';
  const a=st.anim;
  if(a==='fade'){ }
  else if(a==='slide'){ tf+=' translateY('+(1-ease(capT/0.3))*24+'px)'; }
  else if(a==='pop'){ const k=back(capT/0.28); tf+=' scale('+(0.6+0.4*k)+')'; op=Math.min(1,capT/0.12)*capIn; }
  else if(a==='bounce'){ const k=back(capT/0.4); tf+=' translateY('+(1-k)*40+'px) scale('+(0.8+0.2*k)+')'; }
  else if(a==='wipe'){ const k=ease(capT/0.35); clip='inset(0 '+(100-k*100)+'% 0 0)'; op=capIn>0?1:0; }
  el.style.transform=tf+tilt; el.style.clipPath=clip; el.style.opacity=op;
  // Per-word effects rebuild the text only when the visible part changes.
  if(a==='typewriter'){ const n=Math.min(text.length, Math.floor(capT*28)); const s=text.slice(0,n)+(n<text.length||Math.floor(capT*2)%2?'▍':''); if(el._s!==s){el.textContent=s; el._s=s;} }
  else if(a==='karaoke'){ const words=text.split(' '); const cur=Math.min(words.length-1, Math.floor(capT/0.32)); const key=cur+'|'+text;
    if(el._s!==key){ el.innerHTML=words.map((w,i)=>'<span class="w" style="color:'+(i===cur?(st.hi==='accent'?accent:st.hi):'inherit')+';transform:scale('+(i===cur?1.08:1)+')">'+w.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</span>').join(' '); el._s=key; } }
  else if(el._s!==text){ el.textContent=text; el._s=text; }
}`;
