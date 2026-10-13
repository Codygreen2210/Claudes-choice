// thumbB.js: the Style B thumbnail: one frame of the film, darkened at the side, two lines of cream text, the key word in red.
(function () {
  const { W, H, text, vgrad, hgrad } = PK, cv = document.getElementById('cv'), c = cv.getContext('2d')
  window.__nolabels = true; window.__seek = () => {
    const S = window.TIMING.scenes[8]; c.setTransform(1, 0, 0, 1, 0, 0); window.SCENES[8](c, 347.0, S.q, S); c.setTransform(1, 0, 0, 1, 0, 0)
    c.fillStyle = hgrad(c, 0, W, 'rgba(10,8,6,0.0)', 'rgba(10,8,6,0.15)', 'rgba(10,8,6,0.0)'); c.fillRect(0, 0, W, H)
    c.fillStyle = vgrad(c, 560, 1080, 'rgba(10,8,6,0)', 'rgba(10,8,6,0.85)'); c.fillRect(0, 560, W, 520)
    text(c, '3 CARRIERS', W / 2, 800, 150, '#f3e7d0', { weight: 900, stroke: 18, strokeCol: '#140f0b' })
    text(c, '5 MINUTES', W / 2, 960, 170, 1 ? '#d8483a' : '#f3e7d0', { weight: 900, stroke: 18, strokeCol: '#140f0b' })
  }
})()
