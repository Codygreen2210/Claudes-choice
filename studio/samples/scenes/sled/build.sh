T=$(cd "$(dirname "$0")" && pwd) && cd "$T/../../web" && {
cat <<'EOF2'
// "You just got strapped to a rocket sled. Here's what happens next." - a 3D Short on the MakeHuman man (the 1954 Sonic Wind run).
//   sled_mh.html?w=1080&h=1920            (times from sled/times.json; one shot per narration line)
// Beats: 0 ignition (hook) | 1 onboard: nine rockets slam him back | 2 tracking: 632 mph | 3 drone: the desert blurs | 4 SLOW MOTION: the scoop hits the water
//        5 onboard: the 1.4 s stop | 6 REPLAY: 46 G bullet-time | 7 the eye: vessels burst, it goes dark | 8 1954 newsreel, then a car seat belt clicks | 9 back at the start line (loops)
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/sled/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== THE ROCKET SLED'
cat $T/set.js $T/story.js $T/tail.js; } > sled.js
