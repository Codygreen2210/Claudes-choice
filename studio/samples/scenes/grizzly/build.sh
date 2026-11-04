T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF2'
// Grizzly attack near Bella Coola, B.C. (Oct 31, 2026): what to do if a grizzly charges. No attack on a person is shown.
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/grizzly/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== A B.C. TRAIL AND A GRIZZLY'
cat $T/set.js $T/story.js $T/tail.js; } > grizzly.js

