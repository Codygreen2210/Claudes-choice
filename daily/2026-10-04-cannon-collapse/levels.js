/* Cannon Collapse level data. Add levels by hand here.
   platform: x = centre on a 360-wide screen, w = width, top = height of its top (optional, default 390; smaller = higher).
   blocks:   m = wood | stone | glass | tnt
             x = block centre, measured from the platform centre (minus = towards the cannon)
             y = how far the block's BOTTOM sits above the platform top
             w, h = size
   shots:    'n' = normal ball, 'h' = heavy ball. The player may fire them in any order.
   After changing a level run tools/play-check.mjs: it checks the tower stands, can be cleared, and is not a gift. */
window.LEVELS = [
  { name: 'Stack', shots: ['n', 'n', 'n'], platform: { x: 270, w: 72 }, blocks: [
    { m: 'wood', x: 0, y: 0, w: 40, h: 40 }, { m: 'wood', x: 0, y: 40, w: 40, h: 40 }, { m: 'wood', x: 0, y: 80, w: 40, h: 40 } ] },
  { name: 'Tall and thin', shots: ['n', 'n', 'n'], platform: { x: 270, w: 64 }, blocks: [
    { m: 'wood', x: 0, y: 0, w: 28, h: 36 }, { m: 'wood', x: 0, y: 36, w: 28, h: 36 }, { m: 'wood', x: 0, y: 72, w: 28, h: 36 },
    { m: 'wood', x: 0, y: 108, w: 28, h: 36 }, { m: 'wood', x: 0, y: 144, w: 28, h: 36 } ] },
  { name: 'Wide base', shots: ['n', 'n', 'n'], platform: { x: 270, w: 58 }, blocks: [
    { m: 'wood', x: 0, y: 0, w: 100, h: 14 },
    { m: 'wood', x: 0, y: 14, w: 30, h: 40 }, { m: 'wood', x: 0, y: 54, w: 30, h: 40 }, { m: 'wood', x: 0, y: 94, w: 30, h: 40 } ] },
  { name: 'Stone on legs', shots: ['n', 'n', 'n'], platform: { x: 270, w: 84 }, blocks: [
    { m: 'wood', x: -24, y: 0, w: 16, h: 50 }, { m: 'wood', x: 24, y: 0, w: 16, h: 50 }, { m: 'stone', x: 0, y: 50, w: 76, h: 26 } ] },
  { name: 'Glass in the way', shots: ['n', 'n', 'h'], platform: { x: 266, w: 110 }, blocks: [
    { m: 'glass', x: -42, y: 0, w: 12, h: 90 },
    { m: 'wood', x: 8, y: 0, w: 36, h: 36 }, { m: 'stone', x: 8, y: 36, w: 36, h: 32 }, { m: 'wood', x: 8, y: 68, w: 32, h: 32 } ] },
  { name: 'Bridge', shots: ['n', 'n', 'h'], platform: { x: 266, w: 106 }, blocks: [
    { m: 'wood', x: -42, y: 0, w: 18, h: 60 }, { m: 'wood', x: 42, y: 0, w: 18, h: 60 }, { m: 'wood', x: 0, y: 60, w: 116, h: 12 },
    { m: 'stone', x: 0, y: 72, w: 32, h: 32 }, { m: 'wood', x: 0, y: 0, w: 30, h: 30 } ] },
  { name: 'TNT', shots: ['n', 'n', 'n'], platform: { x: 264, w: 116 }, blocks: [
    { m: 'tnt', x: -42, y: 0, w: 28, h: 28 }, { m: 'stone', x: -9, y: 0, w: 30, h: 40 }, { m: 'stone', x: 41, y: 0, w: 30, h: 40 },
    { m: 'wood', x: 16, y: 40, w: 84, h: 12 }, { m: 'wood', x: 16, y: 52, w: 28, h: 28 } ] },
  { name: 'Glass legs', shots: ['n', 'n', 'h'], platform: { x: 266, w: 116 }, blocks: [
    { m: 'glass', x: -28, y: 0, w: 14, h: 50 }, { m: 'glass', x: 28, y: 0, w: 14, h: 50 }, { m: 'stone', x: 0, y: 50, w: 84, h: 22 },
    { m: 'tnt', x: 0, y: 72, w: 26, h: 26 }, { m: 'wood', x: 0, y: 98, w: 30, h: 30 } ] },
  { name: 'The fort', shots: ['n', 'h', 'n'], platform: { x: 260, w: 146 }, blocks: [
    { m: 'glass', x: -50, y: 0, w: 14, h: 50 }, { m: 'tnt', x: -20, y: 0, w: 28, h: 44 }, { m: 'stone', x: 50, y: 0, w: 28, h: 50 },
    { m: 'wood', x: 0, y: 50, w: 128, h: 12 },
    { m: 'stone', x: 6, y: 62, w: 30, h: 30 }, { m: 'wood', x: 6, y: 92, w: 30, h: 30 }, { m: 'stone', x: 44, y: 62, w: 28, h: 28 } ] },
  { name: 'Two towers', shots: ['n', 'n', 'n', 'h'], platform: { x: 264, w: 116 }, blocks: [
    { m: 'wood', x: -44, y: 0, w: 28, h: 48 }, { m: 'wood', x: -44, y: 48, w: 28, h: 48 },
    { m: 'stone', x: 44, y: 0, w: 32, h: 44 }, { m: 'glass', x: 44, y: 44, w: 28, h: 52 },
    { m: 'wood', x: 0, y: 96, w: 124, h: 12 }, { m: 'wood', x: 0, y: 108, w: 28, h: 28 } ] }
];
