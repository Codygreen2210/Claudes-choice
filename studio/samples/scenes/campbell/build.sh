T=$(cd "$(dirname "$0")" && pwd) && { python3 "$T/../lint.py" "$T"/set.js "$T"/story.js "$T"/tail.js || { echo "lint: code hidden after a // comment (above); fix it first" >&2; exit 1; }; } && cd "$T/../../web" && {
cat <<'EOF2'
// Jack Campbell (Detroit Lions), Nov 1, 2026: the tackle at the Lions 25, why a neck hit means the backboard, and the good news. Colours and numbers only, no logos.
//   campbell_mh.html?w=1080&h=1920   (times from campbell/times.json; one shot per narration line)
EOF2
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/campbell/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== THE TACKLE AT THE 25'
cat $T/set.js $T/story.js $T/tail.js; } > campbell.js
