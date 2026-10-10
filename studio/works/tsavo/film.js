// film.js: the timeline. Finds each scene's cue words in the narration timing, cuts between scenes, sets captions.
(function () {
  const { clamp, prog } = K, { W, H, C, F, text, tw } = L
  const TM = window.TIMING, cv = document.getElementById('cv'), ctx = cv.getContext('2d')
  const LEAD = 0.45                                  // the picture cuts just ahead of the voice
  const norm = s => s.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim()
  const missing = []
  TM.scenes.forEach((S, i) => {
    S.i = i; S.vis = i === 0 ? 0 : S.start - LEAD
    S.nw = S.words.map(w => norm(w.w))
  })
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
  TM.scenes.forEach(S => {
    S.q = cueOf(S)
    // q.seq('first words', n): the start times of n words in a row, for setting text word by word
    S.q.seq = (phrase, n) => { const t0 = S.q(phrase), i = S.words.findIndex(w => w.s === t0); return Array.from({ length: n }, (_, k) => (S.words[i + k] || S.words[S.words.length - 1]).s) }
  })
  window.__missing = missing

  // captions: short lines, broken where the voice breaks
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
  function caption(c, t, dark) {
    const k = caps.find(k => t >= k.s - 0.08 && t <= k.e); if (!k) return
    const a = prog(t, k.s - 0.08, k.s + 0.08) * (1 - prog(t, k.e - 0.1, k.e))
    const font = F.body(46), w = tw(c, k.text, font) + 64
    c.save(); c.globalAlpha = a * 0.86; c.fillStyle = dark ? '#0b0908' : C.ink; c.beginPath(); c.roundRect(W / 2 - w / 2, 968, w, 72, 6); c.fill(); c.restore()
    text(c, k.text, W / 2, 1020, font, C.paper, { alpha: a })
  }

  const off = document.createElement('canvas'); off.width = W; off.height = H; const octx = off.getContext('2d')
  const XF = 0.4
  function drawScene(c, i, t) { const S = TM.scenes[i]; c.save(); c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; const d = window.SCENES[i](c, t, S.q, S); c.restore(); return d }
  window.__seek = t => {
    let i = 0; for (let k = 0; k < TM.scenes.length; k++) if (t >= TM.scenes[k].vis) i = k
    const S = TM.scenes[i]
    let dark = drawScene(ctx, i, t)
    if (i > 0 && t < S.vis + XF) {                 // dissolve from the scene before
      drawScene(octx, i - 1, t)
      ctx.save(); ctx.globalAlpha = 1 - prog(t, S.vis, S.vis + XF, 'io'); ctx.drawImage(off, 0, 0); ctx.restore()
    }
    caption(ctx, t, dark)
    if (t < 0.6) { ctx.fillStyle = `rgba(0,0,0,${1 - t / 0.6})`; ctx.fillRect(0, 0, W, H) }
    if (t > TM.total - 1) { ctx.fillStyle = `rgba(0,0,0,${prog(t, TM.total - 1, TM.total - 0.1)})`; ctx.fillRect(0, 0, W, H) }
  }
  window.__duration = TM.total
  window.__init = async () => { await Promise.all(['800 40px Playfair', 'italic 600 40px Playfair', '40px Fell', 'italic 40px Fell', '40px FellSC', '40px OldStandard', 'bold 40px OldStandard'].map(f => document.fonts.load(f))) }
})()
