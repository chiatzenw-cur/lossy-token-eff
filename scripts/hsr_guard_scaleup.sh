#!/usr/bin/env bash
# Scale-up for scripts/hsr_guard_radical_pilot.sh -- the 4-case pilot
# found candidate C (window=150 budget=10 pct=99) genuinely RESCUES
# case_003 (wrong/capped -> correct/stop) and shortens case_011 by 37%
# while staying correct; candidate B (window=300 budget=10 pct=99.9)
# shortens case_011 by 45.5%, also staying correct, tied on accuracy
# elsewhere. Both promising enough (user: "if so work autonomously to
# collect all necessary data") to run at full 12-case scale rather than
# propose anything off 4 cases. Baseline (spec_casc_tok/alpha0.3) already
# exists for all 12 cases from the main campaign sweep -- only the
# remaining 8 guard-arm cases need running per candidate. Priority order:
# C first (the standout -- a genuine rescue), then B (biggest single
# length win), then A (tied on accuracy, lowest priority but still
# collected for a complete picture across all 3 tested configs).
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

REMAINING_CASES="case_002 case_005 case_006 case_007 case_008 case_009 case_010 case_012"

# name:window:budget:pct
CANDIDATES=(
  "C_w150b10p99:150:10:99"
  "B_w300b10p99.9:300:10:99.9"
  "A_w600b5p99.9:600:5:99.9"
)

MIN_FREE_GB="${MIN_FREE_GB:-3}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

echo "=== hsr_guard_scaleup.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
for cand in "${CANDIDATES[@]}"; do
  IFS=':' read -r name window budget pct <<< "$cand"
  free="$(free_gb)"
  echo ""
  echo "free space check before $name: ${free}G"
  if [[ "$free" -lt "$MIN_FREE_GB" ]]; then
    echo "STOPPING: only ${free}G free (< ${MIN_FREE_GB}G floor) before candidate=$name -- not attempting it." >&2
    break
  fi
  echo "########## scaleup candidate=$name (window=$window budget=$budget pct=$pct) started $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
  .venv-vllm/bin/python3 scripts/fresh_server_replay.py \
    --arms spec_casc_tok_hsr_guard \
    --spec-casc-tok-alpha 0.3 \
    --spec-casc-tok-hsr-guard-alpha 0.3 \
    --spec-casc-tok-hsr-guard-window "$window" \
    --spec-casc-tok-hsr-guard-budget "$budget" \
    --spec-casc-tok-hsr-guard-percentile "$pct" \
    --spec-casc-tok-hsr-guard-actuator-k 8 \
    --cases $REMAINING_CASES \
    --prompt-root prompts/aime24_qwen3 \
    --runs-root runs \
    --log-root logs/hsr_guard_scaleup \
    --max-new-tokens 32768 \
    --port 30000 \
    --model-path Qwen/Qwen3-8B \
    --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
    --served-model-name qwen3-8b \
    --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  echo "candidate=$name scaleup exited $?"
  echo "########## scaleup candidate=$name finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
done

echo ""
echo "=== hsr_guard_scaleup.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
