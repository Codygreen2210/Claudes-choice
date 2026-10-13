# Sound effects catalog

Everything in `studio/sfx/foley.py`, built from scratch. Rewritten by `audition.py`; do not edit by hand.

Use: `fx = F.Track(dur)` then `fx.hit(name, t)`, `fx.bed(name, t0, t1)`, `fx.seq(name, t0, t1)`.

## animals

| sound | kind | what it is |
|---|---|---|
| `bark` | hit | a dog bark |
| `cow` | hit | a cow lowing (recorded, CC0) |
| `growl` | hit | a big cat growl |
| `hoof` | hit | one hoof on dirt: a recorded heavy impact, slowed, with a little grit |
| `hoof_synth` | hit | one hoof on dirt |
| `hooves` | seq | a horse at a canter: three-beat hooves on dirt |
| `howl` | hit | a sled dog or wolf howl |
| `paws` | seq | a dog team running on packed snow: paws, harness bells |
| `pawstep` | hit | one paw on packed snow |
| `roar` | hit | a lion roar: rising, open, then the grunts |

## crowds

| sound | kind | what it is |
|---|---|---|
| `cheer` | bed | a crowd cheering: rising roar with whistles |
| `murmur` | bed | a crowd talking: a street, a room, a line of people |
| `panic` | bed | panic: a crowd shouting, raised and ragged |

## machines

| sound | kind | what it is |
|---|---|---|
| `beep` | hit | a pure tone blip, for morse |
| `clock` | seq | a clock ticking once a second |
| `cockpit` | bed | in the cockpit of a piston plane: a radial engine's exhaust beat, the propeller thrum, air rushing past |
| `dive_run` | hit | a dive bomber's dive: engine winding up, air roaring over the open dive brakes, a breathy shriek |
| `drone_far` | bed | piston planes droning far off: low, soft, mostly propeller |
| `engines` | bed | piston aircraft engines droning overhead |
| `flyby` | hit | a piston plane flying past: rising in, Doppler drop, fading off |
| `formation` | bed | a formation of piston planes nearby: several radial engines a little out of step, beating against each other |
| `morse` | seq | morse code tones on a wireless set |
| `ship_horn` | hit | a ship's steam horn, low and long |
| `telegraph` | hit | a telegraph key click |
| `tick` | hit | a clock tick (alternate tick and tock with hi=False) |
| `train` | bed | a steam train under way: chuffs on a beat, rail clatter |
| `typekey` | hit | one typewriter key: a recorded mechanical key slowed down, with the type bar thunk |
| `typekey_synth` | hit | one typewriter key strike |
| `typing` | seq | typing: uneven keys with a carriage bell at the end |
| `whistle` | hit | a steam whistle, two tones |

## nature

| sound | kind | what it is |
|---|---|---|
| `blizzard` | bed | a blizzard: recorded wind with gusts of driven snow hiss on top |
| `blizzard_synth` | bed | a blizzard: gusting wind with a hiss of snow and a high whistle in the gusts |
| `crickets` | bed | night insects and a little wind |
| `fire` | bed | a fire burning: recorded fireplace (CC0) |
| `fire_synth` | bed | a fire burning: low roar with pops |
| `hull` | bed | water lapping against a hull, rigging creaks (field recording, CC0) |
| `ice_crack` | hit | ice cracking: a recorded crack sped up and bright, a groan and a zing along the sheet |
| `ice_crack_synth` | hit | ice cracking: a sharp report and a groan under it |
| `rain` | bed | steady rain: recorded rain loops with a soft synthetic wash to hide the seams |
| `rain_synth` | bed | steady rain on a roof or field |
| `storm` | bed | a thunderstorm: rain, wind and distant thunder (field recording, CC0) |
| `thunder` | hit | thunder: a recorded strike with a long synthetic roll after it |
| `thunder_synth` | hit | thunder: a crack and a long roll |
| `waves` | bed | sea swell: slow waves, foam on the crests |
| `wind` | bed | open wind: field recording (felix.blume, CC0) |
| `wind_synth` | bed | open wind across flat ground |

## people

| sound | kind | what it is |
|---|---|---|
| `column` | seq | a column of soldiers marching in step |
| `drum_line` | seq | a line of village drummers along a ridge: many drums, each a little off the beat, near and far |
| `hand_drum` | hit | a hand drum (dhol): a deep open stroke with the skin ringing, a dry slap on the other head |
| `punch` | hit | a punch or body blow (recorded) |
| `punch_synth` | hit | a punch or body blow |
| `step` | hit | one footstep: surface = snow, wood, dirt or stone (recorded) |
| `step_synth` | hit | one footstep: surface = snow, wood, dirt or stone |
| `walk` | seq | someone walking: surface = snow, wood, dirt or stone |

## rooms

| sound | kind | what it is |
|---|---|---|
| `book` | hit | a hardcover book set down or tapped (recorded) |
| `cell_door` | hit | a jail cell door: recorded iron slam, chain rattle, the lock |
| `cell_door_synth` | hit | a jail cell door: iron clank and rattle |
| `chain` | hit | a chain rattling (recorded) |
| `ching` | hit | a cash register: key clack, then the bell |
| `clack` | hit | a wooden knock or latch: dry, short |
| `clink` | hit | a small metal ring: coin, spur, bell on a sled |
| `coin_drop` | hit | coins handled or dropped (recorded) |
| `coins` | seq | coins spilling or being counted (recorded) |
| `coins_synth` | seq | coins spilling or being counted |
| `creak` | hit | a wooden creak: floorboard, mast, rope under load (recorded) |
| `creak_synth` | hit | a wooden creak: floorboard, mast, rope under load |
| `door_slam` | hit | a heavy door slamming shut in a stone room (recorded, with room) |
| `door_slam_synth` | hit | a heavy door slamming shut in a stone room |
| `gavel` | hit | a judge's gavel: two recorded wood knocks |
| `gavel_synth` | hit | a judge's gavel: two hard knocks |
| `handbell` | hit | a small bell struck once (recorded) |
| `heart` | seq | a heartbeat that speeds up |
| `heartbeat` | hit | a heartbeat: lub-dub |
| `keys` | hit | a ring of keys or a lock turning (recorded) |
| `page` | hit | a page turn or newspaper snap (recorded) |
| `page_synth` | hit | a page turn or newspaper snap |
| `scratch` | hit | a pen scratching across paper (recorded) |
| `scratch_synth` | hit | a pen scratching a line |
| `thud` | hit | a dull thud: a body, a sack, a heavy book on a table (recorded) |
| `thud_synth` | hit | a dull thud: a body, a sack, a heavy book on a table |
| `toll` | hit | a church or town bell toll |

## transitions

| sound | kind | what it is |
|---|---|---|
| `boom` | hit | a deep boom to land a title or a turn in the story |
| `riser` | hit | a rising swell into a hit |
| `swish` | hit | an air swish for a cut or a thrown object |

## war

| sound | kind | what it is |
|---|---|---|
| `arrow` | hit | one arrow passing: a thin whistle and an air rip, Doppler falling |
| `arrow_hit` | hit | an arrow striking wood or a shield: a recorded knock pitched up, a short shaft buzz |
| `arrow_storm` | seq | a storm of arrows: hundreds passing overhead, some striking home |
| `barrage` | seq | distant artillery: booms spread out, far and dull |
| `cannon` | hit | a cannon: recorded blast, a sub thump under it, and a long roll off the land |
| `cannon_synth` | hit | a cannon: hard crack, a deep body and a long rolling tail |
| `clash` | hit | a sword or bayonet clash |
| `dive` | hit | a falling bomb or dive: rising scream, propeller rasp underneath |
| `explosion` | hit | a big explosion: recorded blast pitched down for size, sub, falling debris |
| `explosion_synth` | hit | a big explosion: blast, low thud, falling debris |
| `flak` | hit | an anti-aircraft burst high up: short pop with a puff |
| `march` | seq | a snare march with a roll every other bar |
| `melee` | seq | a battle line at close quarters: shields, spear and sword strikes, blows, all ragged |
| `musket` | hit | a musket or rifle shot: recorded crack with a slap back off the trees |
| `musket_synth` | hit | a musket or rifle shot at middle distance |
| `shield_hit` | hit | a bronze shield taking a blow: recorded metal hit slowed for size, a wooden core knock, the low thump of the body behind it |
| `snare` | hit | a field snare stroke |
| `splash` | hit | something heavy hitting water: a recorded splash with a low whump |
| `splash_synth` | hit | a bomb or shell hitting water: whump and spray |
| `volley` | seq | a ragged musket volley along a line |
| `war_horn` | hit | a war horn: a long low brass call with a rough edge, out across open ground |
| `whip` | hit | a whip crack: a recorded slap made sharp, with the swish before it |
