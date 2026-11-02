T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF'
// "You just got lost in the woods with no food and no water." - a 3D Short: how long you can last without water, then without food.
//   starve.html?w=1080&h=1920            (times from starve/times.json; one shot per narration line)
// Beats: 0 he shakes his empty bottle: one drop (hook) | 1 three days and nights race past; he wilts | 2 x-ray: the kidneys fail, it all dims
//        3 the stream: he fills the bottle and drinks | 4 x-ray: the liver's sugar runs out, the fat burns | 5 x-ray: then the muscle
//        6 a tally carved on a tree: weeks, up to about two months | 7 lost, looking around (loops)
EOF
sed -n '6,49p' grease.js | sed 's#/grease/times.json#/starve/times.json#'
sed -n '84p' grease.js
sed -n '85,187p' grease.js
echo '// ================================================================== SURVIVING WITHOUT FOOD AND WATER'
cat $T/set.js $T/story.js $T/tail.js; } > starve.js
