// events: run the episode's machine start to finish and write every bounce to video/events.json for the sound.
require('../sim.js'); require('./timeline.js')
const fs = require('fs'), Sim = globalThis.Sim, TL = globalThis.TL
require('./layout.js'); TL.setLayout(globalThis.LAYOUT)
const c = TL.at(Sim, TL.DUR)
fs.writeFileSync(__dirname + '/events.json', JSON.stringify(c.hits.map(h => ({ t: +h.t.toFixed(4), midi: h.midi, vel: +h.vel.toFixed(3), x: Math.round(h.x), id: h.id }))))
const by = {}; c.hits.forEach(h => by[h.id] = (by[h.id] || 0) + 1)
console.log(c.hits.length, 'bounces', JSON.stringify(by))
const off = c.hits.map(h => Math.abs(h.t * 8 - Math.round(h.t * 8)) / 8 * 1000)
console.log('worst distance from the 16th grid (ms):', Math.max(...off).toFixed(1), ' over 15 ms:', off.filter(o => o > 15).length)
console.log('first:', c.hits[0].t, 'last:', c.hits[c.hits.length - 1].t)
