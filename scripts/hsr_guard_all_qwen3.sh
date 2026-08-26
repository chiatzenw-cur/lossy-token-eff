#!/usr/bin/env bash
# spec_casc_tok vs spec_casc_tok_hsr_guard, both alpha=0.3, across all 6
# qwen3 datasets -- user request 2026-08-23 "collect data on all
# benchmarks", following up on the gsm8k_qwen3 comparison (24/24 ok,
# bit-identical baseline-vs-guard -- guard never fired, consistent with
# gsm8k's short completions not giving the recurrence signal enough
# runway; see campaign/JOURNAL.md). Same per-dataset token budgets as the
# main 6-dataset campaign (campaign_run.py's own TOKEN_BUDGETS). gsm8k
# skipped here -- already collected.
set -uo pipefail  # NOT -e: one dataset failing must not stop the others

cd "$(dirname "${BASH_SOURCE[0]}")/.."

declare -A BUDGETS=(
  [aime24_qwen3]=32768
  [humaneval_qwen3]=9000
  [livecodebench_qwen3]=12000
  [mtbench_qwen3]=4096
  [longbench_v2_qwen3]=8192
)
ORDER=(mtbench_qwen3 humaneval_qwen3 longbench_v2_qwen3 livecodebench_qwen3 aime24_qwen3)  # fast ones first

MIN_FREE_GB="${MIN_FREE_GB:-3}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

echo "=== hsr_guard_all_qwen3.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
for dataset in "${ORDER[@]}"; do
  free="$(free_gb)"
  echo ""
  echo "free space check before $dataset: ${free}G"
  if [[ "$free" -lt "$MIN_FREE_GB" ]]; then
    echo "STOPPING: only ${free}G free (< ${MIN_FREE_GB}G floor) before dataset=$dataset -- not attempting it." >&2
    break
  fi

  budget="${BUDGETS[$dataset]}"
  echo "########## dataset=$dataset started $(date -u +%Y-%m-%dT%H:%M:%SZ) (max_new_tokens=$budget) ##########"
  .venv-vllm/bin/python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok spec_casc_tok_hsr_guard \
    --spec-casc-tok-alpha 0.3 \
    --spec-casc-tok-hsr-guard-alpha 0.3 \
    --cases $(printf 'case_%03d ' $(seq 1 12)) \
    --prompt-root "prompts/$dataset" \
    --runs-root runs \
    --log-root "logs/hsr_guard_qwen3" \
    --max-new-tokens "$budget" \
    --port 30000 \
    --model-path Qwen/Qwen3-8B \
    --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
    --served-model-name qwen3-8b \
    --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  run_status=$?
  echo "fresh_server_replay.py --prompt-root prompts/$dataset exited $run_status"
  echo "########## dataset=$dataset finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
done

echo ""
echo "=== hsr_guard_all_qwen3.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
