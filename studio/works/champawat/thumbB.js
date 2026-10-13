// thumbB.js: the Style B thumbnail: one frame of the film, darkened at the side, two lines of cream text, the key word in red.
(function () {
  const { W, H, text, vgrad, hgrad } = PK, cv = document.getElementById('cv'), c = cv.getContext('2d')
  window.__nolabels = true; window.__seek = () => {
    const S = window.TIMING.scenes[7]; c.setTransform(1, 0, 0, 1, 0, 0); window.SCENES[7](c, 293.2, S.q, S); c.setTransform(1, 0, 0, 1, 0, 0)
    c.fillStyle = hgrad(c, 0, W, 'rgba(10,8,6,0.0)', 'rgba(10,8,6,0.15)', 'rgba(10,8,6,0.0)'); c.fillRect(0, 0, W, H)
    c.fillStyle = vgrad(c, 560, 1080, 'rgba(10,8,6,0)', 'rgba(10,8,6,0.85)'); c.fillRect(0, 560, W, 520)
    text(c, 'RIGHT ABOVE', 1380, 760, 140, '#f3e7d0', { weight: 900, stroke: 18, strokeCol: '#140f0b' })
    text(c, 'HIM', 1380, 920, 170, 1 ? '#d8483a' : '#f3e7d0', { weight: 900, stroke: 18, strokeCol: '#140f0b' })
  }
})()
