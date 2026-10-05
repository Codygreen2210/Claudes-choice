// probe: print one marble's bounces for a layout. node video/probe.cjs '<json {dropX, lines}>' [H]
require('../sim.js'); const Sim = globalThis.Sim
const lay = JSON.parse(process.argv[2]); const H = Number(process.argv[3] || 1778)
const hits = []
const s = Sim.create({ lines: lay.lines, dropX: lay.dropX, H, interval: 0.5, onHit: e => { if (e.marble === 2) hits.push(e) } })
Sim.advance(s, 12)
console.log(hits.map(e => `${(e.t - 1).toFixed(2)}s L${e.index} ${Sim.noteName(e.midi)} v${e.vel.toFixed(2)} @${Math.round(e.x)},${Math.round(e.y)}`).join('\n'))
console.log('lines:', lay.lines.map(l => Sim.noteName(Sim.midi(l))).join(' '))
