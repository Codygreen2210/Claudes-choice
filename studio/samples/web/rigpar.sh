#!/bin/bash
# Rig check on every core at once: bash rigpar.sh page.html [parts]  -> the same report as jointjerk.mjs, about N times faster.
# Slices overlap by one frame so no frame-to-frame jump at a slice edge is missed.
cd "$(dirname "$0")"; pg=$1; P=${2:-$(nproc)}; tmp=$(mktemp -d)
N=$(node -e "const j=require('./'+process.argv[1].replace('.html','').replace('_mh','')+'/times.json'); console.log(Math.round(j.total*30))" "$pg" 2>/dev/null)
[ -z "$N" ] && { echo "set the frame count: can't find times.json for $pg" >&2; exit 1; }
step=$(( (N + P - 1) / P )); pids=()
for ((k = 0; k < P; k++)); do a=$(( k * step - (k > 0 ? 1 : 0) )); b=$(( (k + 1) * step )); ((b > N)) && b=$N
  node jointjerk.mjs "$pg" --from $a --to $b --json $tmp/part$k.json > $tmp/log$k.txt 2>&1 & pids+=($!); done
for p in "${pids[@]}"; do wait $p; done
grep -h "^\[err\]" $tmp/log*.txt | head -3
node jointjerk.mjs --merge $tmp/part*.json; rm -rf $tmp
