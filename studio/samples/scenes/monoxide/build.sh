T=$(cd "$(dirname "$0")" && pwd) && cd "$T/../../web" && {
cat <<'EOF'
// "You just started your truck in the garage to warm it up, and the door is shut." - a 3D Short: carbon monoxide.
//   monoxide.html?w=1080&h=1920            (times from monoxide/times.json; one shot per narration line)
// Beats: 0 the truck idles, exhaust pours into the shut garage (hook) | 1 at the pipe: you can't see it or smell it
//        2 inside his blood: CO knocks the oxygen off the red cells | 3 x-ray: brain and heart go dim | 4 headache, dizzy, sick
//        5 confused, weak: he catches himself on the truck, it goes black | 6 door open is still not safe; the alarm: get out | 7 he starts it (loops)
EOF
sed -n '6,49p' grease.js | sed 's#/grease/times.json#/monoxide/times.json#'
sed -n '84p' grease.js
sed -n '85,187p' grease.js
echo '// ================================================================== CARBON MONOXIDE'
cat $T/set.js $T/story.js $T/tail.js; } > monoxide.js
