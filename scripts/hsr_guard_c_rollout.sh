#!/usr/bin/env bash
# Roll out spec_casc_tok_hsr_guard candidate C (window=150, budget=10,
# pct=99, actuator_k=8 -- the standout from the aime24_qwen3 full-scale
# comparison: 11/12 vs baseline's 10/12, -3.0% total tokens) across the
# 5 remaining Qwen3-8B benchmarks. These were all previously swept at
# the ORIGINAL (GPT-OSS-20B) settings via hsr_guard_all_qwen3.sh BEFORE
# the two actuator bugs were found and fixed -- that "guard never fires"
# result is now known to be a false negative caused by the same bugs
# that made aime24_qwen3 look inert, not a real per-dataset finding. This
# re-tests with the FIXED actuator at the one config that showed genuine
# signal on aime24. Baseline (spec_casc_tok/alpha0.3) already exists for
# all 12 cases on every dataset from the main campaign -- only the guard
# arm needs running.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

declare -A BUDGETS=(
  [gsm8k_qwen3]=2048
  [mtbench_qwen3]=4096
  [humaneval_qwen3]=9000
  [longbench_v2_qwen3]=8192
  [livecodebench_qwen3]=12000
)
ORDER=(gsm8k_qwen3 mtbench_qwen3 longbench_v2_qwen3 humaneval_qwen3 livecodebench_qwen3)

MIN_FREE_GB="${MIN_FREE_GB:-3}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

echo "=== hsr_guard_c_rollout.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
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
    --arms spec_casc_tok_hsr_guard \
    --spec-casc-tok-alpha 0.3 \
    --spec-casc-tok-hsr-guard-alpha 0.3 \
    --spec-casc-tok-hsr-guard-window 150 \
    --spec-casc-tok-hsr-guard-budget 10 \
    --spec-casc-tok-hsr-guard-percentile 99 \
    --spec-casc-tok-hsr-guard-actuator-k 8 \
    --cases $(printf 'case_%03d ' $(seq 1 12)) \
    --prompt-root "prompts/$dataset" \
    --runs-root runs \
    --log-root "logs/hsr_guard_c_rollout" \
    --max-new-tokens "$budget" \
    --port 30000 \
    --model-path Qwen/Qwen3-8B \
    --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
    --served-model-name qwen3-8b \
    --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  echo "dataset=$dataset exited $?"
  echo "########## dataset=$dataset finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
done

echo ""
echo "=== hsr_guard_c_rollout.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
