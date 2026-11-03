T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF2'
// Goliath (Six Flags Over Georgia), Oct 12, 2026: a rider ejected; how airtime and a lap bar work. Generic coaster, no park branding, no gore.
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/coaster/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== A ROLLER COASTER AND ITS LAP BARS'
cat $T/set.js $T/story.js $T/tail.js; } > coaster.js

