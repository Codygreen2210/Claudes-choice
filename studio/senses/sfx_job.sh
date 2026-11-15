#!/bin/bash
# Run the Sound library workflow.   bash studio/senses/sfx_job.sh OUTDIR "page URL" "get URL" ...   (waits, then unpacks into OUTDIR)
set -e
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
URL=https://github.com/Codygreen2210/Claudes-choice.git; out=$1; shift; mkdir -p "$out"
id=$(date +%Y%m%d-%H%M%S); job=$(mktemp); for l in "$@"; do echo "$l" >> $job; done
idx=$(mktemp -u); export GIT_INDEX_FILE=$idx; git read-tree HEAD
git update-index --add --cacheinfo 100644,$(git hash-object -w $job),sfx/job.txt
tree=$(git write-tree); unset GIT_INDEX_FILE; rm -f $idx $job
c=$(git commit-tree $tree -p HEAD -m "sfx job $id"); git push -q $URL $c:refs/heads/sfx/in-$id 2>&1 | grep -v '^remote' || true
echo "job $id"
for i in $(seq 1 30); do rid=$(gh run list -R Codygreen2210/Claudes-choice -L 10 --json databaseId,displayTitle --jq ".[] | select(.displayTitle==\"sfx job $id\") | .databaseId" | head -1); [ -n "$rid" ] && break; sleep 10; done
gh run watch $rid -R Codygreen2210/Claudes-choice --exit-status > /dev/null 2>&1 || echo "run $rid did not finish clean"
git fetch -q $URL refs/heads/sfx/out-$id && git archive FETCH_HEAD | tar -x -C "$out"; cat "$out/log.txt" | tail -30
