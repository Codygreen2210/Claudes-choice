#!/bin/bash
# Render a 3D Short on the GitHub Actions render farm (.github/workflows/render.yml) instead of this machine.
#   PAGE=bruise.html TD=web/bruise CFG=web/bruise/finish.json bash farm.sh WORKDIR [CHUNK] [GLMODE]
# The scene's files are taken from the working tree (no need to commit them first). Makes branch render/job-<id>
# (HEAD + the scene + render/job.env), pushes it, waits for render/out-<id>, then joins the chunks and adds
# WORKDIR/mix.wav -> WORKDIR/pic.mp4 + final.mp4 (same as qs_render.sh). Logs from each runner land in WORKDIR/farm/.
set -e
cd "$(dirname "$0")"
d=$1; ch=${2:-90}; gl=${3:-}
: "${PAGE:?set PAGE}" "${TD:?set TD}" "${CFG:?set CFG}"
name=${PAGE%.html}; id=$(date +%Y%m%d-%H%M%S)-$name
root=$(git rev-parse --show-toplevel)
job=$(mktemp); printf 'PAGE=%s\nTD=%s\nCFG=%s\nCH=%s\nGLMODE=%s\n' "$PAGE" "$TD" "$CFG" "$ch" "$gl" > $job
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
git add -f web/$PAGE web/$name.js $TD                      # the scene as it is on disk now
git update-index --add --cacheinfo 100644,$(git hash-object -w $job),render/job.env
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $job
c=$(git commit-tree $tree -p HEAD -m "render job $id")
git push -q origin $c:refs/heads/render/job-$id
echo "pushed render/job-$id ($c); waiting for render/out-$id" >&2
t0=$(date +%s)
until git ls-remote --exit-code origin refs/heads/render/out-$id > /dev/null 2>&1; do
  (( $(date +%s) - t0 > 5400 )) && { echo "no result after 90 min" >&2; exit 1; }
  sleep 20
done
echo "result after $(( $(date +%s) - t0 )) s" >&2
mkdir -p $d/farm
git fetch -q --depth 1 origin refs/heads/render/out-$id
git archive FETCH_HEAD | tar -x -C $d/farm
cat $d/farm/log_*.txt | grep "^chunk" | sort -n -k2 >&2 || true
N=$(python3 -c "import json,sys; print(round(json.load(open(sys.argv[1]))['total'] * 30))" $TD/times.json)
want=$(( (N + ch - 1) / ch )); have=$(ls $d/farm/seg_*.mp4 2>/dev/null | wc -l)
[ "$have" = "$want" ] || { echo "only $have of $want chunks came back; see $d/farm/log_*.txt" >&2; exit 1; }
ls $d/farm/seg_*.mp4 | sed "s/^/file '/; s/$/'/" > $d/segs.txt
ffmpeg -y -loglevel error -f concat -safe 0 -i $d/segs.txt -c copy $d/pic.mp4
ffmpeg -y -loglevel error -i $d/pic.mp4 -i $d/mix.wav -c:v copy -c:a aac -b:a 192k -shortest $d/final.mp4
echo "farm $id DONE in $(( $(date +%s) - t0 )) s" >&2
