#!/usr/bin/env bash
# spec_casc_tok (baseline, alpha=0.3) vs spec_casc_tok_hsr_guard on
# GPT-OSS-20B for mtbench -- the one dataset the original GPT-OSS-20B
# semantic-guard investigation (analysis/semantic_guard/README.md) never
# covered (that investigation was aime24-only). User request 2026-08-25
# "rollout mtbench in campaigns" / "on selected parameter sets do full
# mtbench collect". Uses the investigation's own CORRECTED calibration
# (window=600, budget=25, percentile=99.9, actuator_k=8 -- see README.md
# "the new defaults are window=600, budget=25, percentile=99.9,
# actuator_k=8"), not the original budget=3 setting. GPT-OSS defaults
# (model/draft-model/served-name, no rope scaling) need no overrides,
# unlike the Qwen3 rollout scripts this mirrors
# (hsr_guard_all_qwen3.sh / hsr_guard_c_rollout.sh).
#
# No pre-existing spec_casc_tok/alpha0.3 baseline for mtbench (the main
# campaign's own calibration grid for spec_casc_tok on mtbench is
# 0.15/0.35/0.55/0.8, not 0.3) -- so both arms run fresh here.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

MIN_FREE_GB="${MIN_FREE_GB:-3}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

free="$(free_gb)"
echo "=== hsr_guard_mtbench_gptoss.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ), free=${free}G ==="
if [[ "$free" -lt "$MIN_FREE_GB" ]]; then
  echo "STOPPING: only ${free}G free (< ${MIN_FREE_GB}G floor) -- not starting." >&2
  exit 1
fi

.venv-vllm/bin/python3 scripts/fresh_server_replay.py \
  --arms spec_casc_tok spec_casc_tok_hsr_guard \
  --spec-casc-tok-alpha 0.3 \
  --spec-casc-tok-hsr-guard-alpha 0.3 \
  --spec-casc-tok-hsr-guard-window 600 \
  --spec-casc-tok-hsr-guard-budget 25 \
  --spec-casc-tok-hsr-guard-percentile 99.9 \
  --spec-casc-tok-hsr-guard-actuator-k 8 \
  --cases $(printf 'case_%03d ' $(seq 1 12)) \
  --prompt-root prompts/mtbench \
  --runs-root runs \
  --log-root logs/hsr_guard_mtbench_gptoss \
  --max-new-tokens 4096 \
  --port 30000
run_status=$?
echo "fresh_server_replay.py --prompt-root prompts/mtbench exited $run_status"
echo "=== hsr_guard_mtbench_gptoss.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
