T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF2'
// Jesus de Miguel (CD Tenerife), Nov 2, 2026: the collision with Andorra's keeper in stoppage time, and what happened after. Stand-in figures, generic kits, no crests.
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/tackle/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== A COLLISION ON THE PITCH'
cat $T/set.js $T/story.js $T/tail.js; } > tackle.js

