#!/usr/bin/env bash
# Follow-up to scripts/hsr_guard_radical_pilot.sh -- user question
# 2026-08-24: "does it have similarity score guarding? maybe we should
# be more radical with similarity". Candidate C (window=150, budget=10,
# pct=99) was the standout of the window/budget sweep but was only ever
# tested at pct=99/99.9 live; this tests MORE radical (lower) percentile
# thresholds -- i.e. the guard fires on much milder similarity, not just
# extreme spikes -- holding window/budget fixed at C's own values so
# percentile is the one isolated variable. Reuses the SAME 4 aime24_qwen3
# cases as the original pilot (case_001 ordinary, case_003/case_004
# capped, case_011 near-cap) for direct comparability against candidate
# C's already-known per-case results. Baseline already exists.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

CASES="case_001 case_003 case_004 case_011"

# name:window:budget:pct
CANDIDATES=(
  "D_w150b10p95:150:10:95"
  "E_w150b10p90:150:10:90"
)

MIN_FREE_GB="${MIN_FREE_GB:-3}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

echo "=== hsr_guard_pct_pilot.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
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
    --log-root logs/hsr_guard_pct_pilot \
    --max-new-tokens 32768 \
    --port 30000 \
    --model-path Qwen/Qwen3-8B \
    --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
    --served-model-name qwen3-8b \
    --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  echo "candidate=$name exited $?"
  echo "########## candidate=$name finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
done

echo ""
echo "=== hsr_guard_pct_pilot.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
