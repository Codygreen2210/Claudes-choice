// events: footfall times from the running clock, for the sound.  node events.cjs -> events.json
require('./cues.js'); require('./clock.js')
const fs = require('fs'), K = globalThis.CLOCK, C = globalThis.CUES
const falls = K.footfalls()
fs.writeFileSync(__dirname + '/events.json', JSON.stringify({ dur: C.dur, cue: Object.fromEntries(C.cues.map(c => [c.id, [c.t0, c.t1]])), falls }))
console.log(falls.length, 'footfalls;', falls.filter(f => f.rate < 1.2).length, 'in slow motion')
