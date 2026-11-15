#!/bin/bash
# Watch a viral video and break it down.   bash studio/senses/watch.sh OUTDIR LINK_OR_FILE [LINK_OR_FILE ...]
# Links and files go to the Watch room workflow (GitHub runner: downloads links, transcribes everything), then each video gets
# studio/senses/watch.py: OUTDIR/vNN/report.txt, watch.png (timeline), sheet.png (1 frame a second), hook.png (first 3 s).
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
URL=https://github.com/Codygreen2210/Claudes-choice.git
outdir=$1; shift; mkdir -p "$outdir"
id=$(date +%Y%m%d-%H%M%S)
urls=$(mktemp); idx=$(mktemp -u); export GIT_INDEX_FILE=$idx
git read-tree HEAD
for a in "$@"; do
  if [ -f "$a" ]; then git update-index --add --cacheinfo 100644,$(git hash-object -w "$a"),watch/job/files/$(basename "$a" | tr ' ' '_')
  else echo "$a" >> $urls; fi
done
[ -s $urls ] && git update-index --add --cacheinfo 100644,$(git hash-object -w $urls),watch/job/urls.txt
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $urls
c=$(git commit-tree $tree -p HEAD -m "watch job $id")
git push -q $URL $c:refs/heads/watch/in-$id 2>&1 | grep -v '^remote' || true
echo "job $id started"
# wait for the run, then collect
for i in $(seq 1 30); do rid=$(gh run list -R Codygreen2210/Claudes-choice -L 10 --json databaseId,displayTitle --jq ".[] | select(.displayTitle==\"watch job $id\") | .databaseId" | head -1); [ -n "$rid" ] && break; sleep 10; done
[ -z "$rid" ] && { echo "run never started"; exit 1; }
gh run watch $rid -R Codygreen2210/Claudes-choice --exit-status > /dev/null 2>&1 || echo "run $rid did not finish clean (collecting what is there)"
git fetch -q --depth 1 $URL refs/heads/watch/out-$id && git archive FETCH_HEAD | tar -x -C "$outdir"
cat "$outdir/log.txt"
for d in "$outdir"/v*/; do
  [ -f "$d/video.mp4" ] && python3 studio/senses/watch.py "$d/video.mp4" --out "$d" > /dev/null && echo "breakdown: $d/report.txt"
done
