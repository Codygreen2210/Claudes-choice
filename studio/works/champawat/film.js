// paint/film.js: the timeline for a Style B film. Finds each scene's cue words in the narration timing,
// cuts (or dissolves) between scenes, draws captions. Scenes live in window.SCENES[i] = (c, t, q, S) => {}.
(function () {
  const { W, H, prog, text } = PK
  const TM = window.TIMING, cv = document.getElementById('cv'), ctx = cv.getContext('2d')
  const LEAD = 0.45
  const norm = s => s.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim()
  const missing = []
  TM.scenes.forEach((S, i) => { S.i = i; S.vis = i === 0 ? 0 : S.start - LEAD; S.nw = S.words.map(w => norm(w.w)) })
  TM.scenes.forEach((S, i) => { S.out = i < TM.scenes.length - 1 ? TM.scenes[i + 1].vis : TM.total })
  function cueOf(S) {
    return (phrase, nth = 1) => {
      const p = norm(phrase).split(' '); let seen = 0
      for (let i = 0; i + p.length <= S.nw.length; i++) {
        let ok = true; for (let k = 0; k < p.length; k++) if (S.nw[i + k] !== p[k]) { ok = false; break }
        if (ok && ++seen === nth) return S.words[i].s
      }
      const key = S.i + ':' + phrase; if (!missing.includes(key)) missing.push(key)
      return S.start + (S.end - S.start) * 0.5
    }
  }
  TM.scenes.forEach(S => { S.q = cueOf(S); S.q.end = phrase => { const t0 = S.q(phrase), i = S.words.findIndex(w => w.s === t0), n = norm(phrase).split(' ').length; return (S.words[i + n - 1] || S.words[S.words.length - 1]).e } })
  window.__missing = missing

  const caps = []
  TM.scenes.forEach(S => {
    let cur = []
    const flush = () => { if (cur.length) { caps.push({ s: cur[0].s, e: cur[cur.length - 1].e, text: cur.map(w => w.w).join(' ').replace(/(^|\s)"/g, '$1“').replace(/"/g, '”') }); cur = [] } }
    S.words.forEach((w, i) => {
      cur.push(w)
      const len = cur.map(x => x.w).join(' ').length, nxt = S.words[i + 1]
      const gap = nxt ? nxt.s - w.e : 9, stop = /[.?!…]["”]?$/.test(w.w), comma = /[,;:]$/.test(w.w)
      if (stop || gap > 0.45 || (comma && len > 26) || len > 46) flush()
    })
    flush()
  })
  for (let i = 0; i < caps.length; i++) { const n = caps[i + 1]; caps[i].e = Math.min(caps[i].e + 0.35, n ? n.s - 0.04 : 1e9) }
  window.__caps = caps
  function caption(c, t) {
    const k = caps.find(k => t >= k.s - 0.08 && t <= k.e); if (!k) return
    const a = prog(t, k.s - 0.08, k.s + 0.08) * (1 - prog(t, k.e - 0.1, k.e))
    c.setTransform(1, 0, 0, 1, 0, 0)
    c.fillStyle = `rgba(0,0,0,${0.35 * a})`; c.fillStyle = PK.vgrad(c, 930, 1080, 'rgba(0,0,0,0)', `rgba(0,0,0,${0.45 * a})`); c.fillRect(0, 930, W, 150)
    text(c, k.text, W / 2, 1000, 50, '#f3e7d0', { italic: true, alpha: a, shadow: 16 })
  }
  const off = document.createElement('canvas'); off.width = W; off.height = H; const octx = off.getContext('2d')
  const XF = 0.4
  function drawScene(c, i, t) { const S = TM.scenes[i]; c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.filter = 'none'; c.globalCompositeOperation = 'source-over'; window.SCENES[i](c, t, S.q, S); c.restore() }
  window.__seek = t => {
    let i = 0; for (let k = 0; k < TM.scenes.length; k++) if (t >= TM.scenes[k].vis) i = k
    const S = TM.scenes[i]
    drawScene(ctx, i, t)
    if (i > 0 && t < S.vis + XF && !(window.CUTS && window.CUTS.includes(i))) { drawScene(octx, i - 1, t); ctx.save(); ctx.globalAlpha = 1 - prog(t, S.vis, S.vis + XF, 'io'); ctx.drawImage(off, 0, 0); ctx.restore() }
    caption(ctx, t)
    if (t > TM.total - 0.8) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillStyle = `rgba(0,0,0,${prog(t, TM.total - 0.8, TM.total - 0.1)})`; ctx.fillRect(0, 0, W, H) }
  }
  window.__duration = TM.total
  window.__init = async () => { await Promise.all(['700 40px Playfair', '800 40px Playfair', 'italic 600 40px Playfair', 'italic 700 40px Playfair'].map(f => document.fonts.load(f))); if (window.PRELOAD) await window.PRELOAD() }
})()
