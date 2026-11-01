T=$(cd "$(dirname "$0")" && pwd) && cd "$T/../../web" && {
cat <<'EOF'
// "You just finished your fourth energy drink, and your heart is pounding." - a 3D Short: what too much caffeine does, and how long it stays.
//   energy.html?w=1080&h=1920            (times from energy/times.json; one shot per narration line)
// Beats: 0 he chugs the 4th can; x-ray: his heart pounding (hook) | 1 the can up close: up to 300 mg | 2 a tube fills can by can past the 400 mg limit
//        3 inside the brain: caffeine sits in the "tired" receptors, the signal bounces off | 4 racing heart, then his shaking hand
//        5 an electric storm in his brain (1,200 mg fast) | 6 five hours go by: the tube drains to half | 7 he grabs the next can (loops)
EOF
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/energy/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== ENERGY DRINKS'
cat $T/set.js $T/story.js $T/tail.js; } > energy.js
