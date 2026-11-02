T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF'
// "You just cracked open your sixth can of cola today." - a 3D Short: what too much cola does (sugar, insulin, teeth, fat, potassium).
//   cola.html?w=1080&h=1920            (times from cola/times.json; one shot per narration line)
// Beats: 0 the can's just cracked, fizz sprays; he drinks (hook) | 1 ten spoons of sugar pop up next to it | 2 the daily max line: one can is past it
//        3 x-ray: blood sugar shoots up, the pancreas pumps out insulin | 4 a tooth up close: every sip washes acid over it, pits grow
//        5 x-ray: extra sugar stored as fat (the liver yellows) | 6 rare: low potassium, his arm goes weak, the can drops | 7 he grabs the next can (loops)
// The can is a made-up brand (no real logo).
EOF
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/cola/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== TOO MUCH COLA'
cat $T/set.js $T/story.js $T/tail.js; } > cola.js
