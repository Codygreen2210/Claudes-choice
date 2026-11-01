T=$(cd "$(dirname "$0")" && pwd) && cd "$T/../../web" && {
cat <<'HDR'
// "You just filmed a screen and it's crawling with rainbow waves." - a 3D Short: why screens look weird on camera (moire + flicker bars).
//   screens.html?w=1080&h=1920            (times from screens/times.json; one shot per narration line; the MakeHuman man)
// Beats: 0 he films the TV: rainbow waves on his phone (hook) | 1 dive into the TV: a grid of glowing dots | 2 the camera's sensor grid
//        3 two grids, a bit off: moire stripes | 4 lined up = bright, off = dark | 5 color filters: the stripes turn rainbow
//        6 dark bars: the screen flashes on and off | 7 the camera reads one row at a time | 8 tilt / step back: the waves fade | 9 (loops)
HDR
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/screens/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== SCREENS ON CAMERA'
cat $T/set.js $T/story.js $T/tail.js; } > screens.js
