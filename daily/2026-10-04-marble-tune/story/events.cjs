// events: run every machine in the story and write each bounce (global time) to story/events.json
require('../sim.js'); require('./cues.js'); require('./layout.js'); require('./plan.js')
const fs = require('fs'), Sim = globalThis.Sim, P = globalThis.PLAN
let all = []
for (const id of Object.keys(P.sims)) {
  const c = P.at(Sim, id, P.dur)
  console.log(id, 'starts', P.sims[id].t0, 'bounces', c.hits.length, c.hits.length ? 'first ' + c.hits[0].t.toFixed(2) + ' last ' + c.hits[c.hits.length - 1].t.toFixed(2) : '')
  all = all.concat(c.hits.map(h => ({ t: +h.t.toFixed(4), midi: h.midi, vel: +h.vel.toFixed(3), x: Math.round(h.x), sim: id })))
}
all.sort((a, b) => a.t - b.t)
fs.writeFileSync(__dirname + '/events.json', JSON.stringify({ dur: P.dur, quiet: P.quiet, cue: Object.fromEntries(Object.entries(P.cue).map(([k, v]) => [k, [v.t0, v.t1]])), hits: all }))
console.log('duration', P.dur, 'quiet', P.quiet.map(x => x.toFixed(2)).join(' to '))
