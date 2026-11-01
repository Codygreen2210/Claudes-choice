T=$(cd "$(dirname "$0")" && pwd) && cd "$T/../../web" && {
cat <<'EOF'
// "You just got the worst news of your life, and your chest feels like it's being crushed." - a 3D Short: broken heart syndrome (takotsubo).
//   brokenheart.html?w=1080&h=1920            (times from brokenheart/times.json; one shot per narration line)
// Beats: 0 the phone slips, his hand goes to his chest (hook) | 1 x-ray: his heart pounds | 2 x-ray: adrenaline floods it from the adrenal glands
//        3 the big heart: its bottom balloons out like an octopus pot | 4 it can't pump right | 5 call 911 | 6 it goes back to its shape (weeks) | 7 the message (loops)
EOF
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/brokenheart/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== BROKEN HEART SYNDROME'
cat $T/set.js $T/story.js $T/tail.js; } > brokenheart.js
