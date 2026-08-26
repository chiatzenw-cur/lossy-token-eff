#!/usr/bin/env bash
# Radical-parameter pilot for spec_casc_tok_hsr_guard on Qwen3-8B --
# user redirect 2026-08-23: discrimination (stuck vs ordinary) doesn't
# matter, just find a parameter point that measurably shortens
# completion length. GPT-OSS-20B's own calibration (window=600,
# budget=25, pct=99.9) never fires on Qwen3-8B at all -- an offline
# sweep (see campaign/JOURNAL.md) picked 3 much more aggressive
# candidates that fire 30-55% of positions on both a capped/stuck-
# looking case and an ordinary one. This script tests all 3 live,
# baseline-vs-guard, on 4 aime24_qwen3 cases chosen for length variety
# (case_001 ordinary L=6350, case_003/case_004 capped L=32768,
# case_011 near-cap L=32765). Baseline (spec_casc_tok/alpha0.3) already
# exists in runs/aime24_qwen3/ from the earlier full sweep -- only the
# guard arm needs a fresh run per candidate.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

CASES="case_001 case_003 case_004 case_011"

# name:window:budget:pct
CANDIDATES=(
  "A_w600b5p99.9:600:5:99.9"
  "B_w300b10p99.9:300:10:99.9"
  "C_w150b10p99:150:10:99"
)

MIN_FREE_GB="${MIN_FREE_GB:-3}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

echo "=== hsr_guard_radical_pilot.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
for cand in "${CANDIDATES[@]}"; do
  IFS=':' read -r name window budget pct <<< "$cand"
  free="$(free_gb)"
  echo ""
  echo "free space check before $name: ${free}G"
  if [[ "$free" -lt "$MIN_FREE_GB" ]]; then
    echo "STOPPING: only ${free}G free (< ${MIN_FREE_GB}G floor) before candidate=$name -- not attempting it." >&2
    break
  fi
  echo "########## candidate=$name (window=$window budget=$budget pct=$pct) started $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
  .venv-vllm/bin/python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok_hsr_guard \
    --spec-casc-tok-alpha 0.3 \
    --spec-casc-tok-hsr-guard-alpha 0.3 \
    --spec-casc-tok-hsr-guard-window "$window" \
    --spec-casc-tok-hsr-guard-budget "$budget" \
    --spec-casc-tok-hsr-guard-percentile "$pct" \
    --spec-casc-tok-hsr-guard-actuator-k 8 \
    --cases $CASES \
    --prompt-root prompts/aime24_qwen3 \
    --runs-root runs \
    --log-root logs/hsr_guard_radical_pilot \
    --max-new-tokens 32768 \
    --port 30000 \
    --model-path Qwen/Qwen3-8B \
    --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
    --served-model-name qwen3-8b \
    --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  run_status=$?
  echo "fresh_server_replay.py candidate=$name exited $run_status"
  echo "########## candidate=$name finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
done

echo ""
echo "=== hsr_guard_radical_pilot.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
