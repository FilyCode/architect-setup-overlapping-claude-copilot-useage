#!/bin/bash -l
#$ -P liu-scc
#$ -N cc-evals
#$ -l h_rt=06:00:00
#$ -pe omp 1
#$ -j y
#$ -o /projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage/evals/runs/eval.log
# Usage: qsub -v ARM=before,K=5 evals/run_evals.sh
set -uo pipefail
REPO=/projectnb/liu-scc/philipp/architect-setup-overlapping-claude-copilot-useage
OUT=${EVAL_OUT:-$REPO/evals/runs/$ARM}; mkdir -p "$OUT"
echo "=== cc-evals arm=$ARM k=$K started: $(date -Is) commit=$(git -C $REPO rev-parse --short HEAD)"
cd /projectnb/liu-scc/philipp
jq -r '.[].id' $REPO/evals/scenarios.json | grep -E "^(${EVAL_ONLY:-.*})$" | while read -r id; do
  prompt=$(jq -r --arg id "$id" '.[] | select(.id==$id) | .prompt' $REPO/evals/scenarios.json)
  for k in $(seq 1 "$K"); do
    claude -p "$prompt" --output-format stream-json --verbose --permission-mode plan --max-turns 8 \
      < /dev/null > "$OUT/$id-$k.jsonl" 2> "$OUT/$id-$k.err"
    echo "$id-$k exit=$?"
  done
done
echo "=== finished: $(date -Is)"
