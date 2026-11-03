T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF2'
// Two helicopters collide landing at Pheriche, Nepal (Nov 3, 2026); why blade strikes are deadly. Generic AS350-type models, no logos, no people shown hurt.
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/heli/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== A HIMALAYAN HELIPAD'
cat $T/set.js $T/story.js $T/tail.js; } > heli.js

