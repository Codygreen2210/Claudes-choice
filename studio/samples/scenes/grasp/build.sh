T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF2'
// Grasp test bench: the MakeHuman man holds a bar, a can and a phone (one per beat); contact.js fits and judges each grip.
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/grasp/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== GRASP TEST BENCH'
cat $T/set.js $T/story.js $T/tail.js; } > grasp.js
