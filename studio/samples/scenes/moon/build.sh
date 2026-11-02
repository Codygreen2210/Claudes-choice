T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF2'
// "You just watched the Moon vanish. Here's what happens next." - a 3D Short on the MakeHuman man.
//   moon_mh.html?w=1080&h=1920            (times from moon/times.json; one shot per narration line)
// Beats: 0 the dock at night, the moon blinks out (hook) | 1 space: its last light still on the way (1.3 s) | 2 the tide sinks down the pilings
//        3 space: the Sun still pulls a smaller tide | 4 the dark dock, 125x darker | 5 hatchling turtles crawl the wrong way | 6 the reef: corals wait
//        7 space: the tilt swings to 85 degrees | 8 the tipped Earth: one side hardly sees the Sun | 9 back on the dock; the moon comes back (loops)
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/moon/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== THE MOON VANISHES'
cat $T/set.js $T/story.js $T/tail.js; } > moon.js
