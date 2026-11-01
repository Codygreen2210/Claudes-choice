T=$(cd "$(dirname "$0")" && pwd) && cd "$T/../../web" && {
cat <<'EOF'
// "You just slammed your leg into the coffee table, and by tomorrow it's purple." - a 3D Short: why you bruise so easily.
//   bruise.html?w=1080&h=1920            (times from bruise/times.json; one shot per narration line)
// Beats: 0 his shin hits the table; next day it's purple (hook) | 1 in the skin: the hit breaks tiny vessels, blood leaks | 2 the trapped blood: red, then blue and purple
//        3 days on his shin: green, yellow, gone | 4 why so easily? | 5 older skin: thinner, less padding | 6 aspirin, blood thinners; see a doctor | 7 reading his phone (loops)
EOF
sed -n '6,84p' grease.js | sed 's#/grease/times.json#/bruise/times.json#'
sed -n '85,187p' grease.js
echo '// ================================================================== WHY YOU BRUISE'
cat $T/set.js $T/story.js $T/tail.js; } > bruise.js
