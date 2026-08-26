#!/usr/bin/env bash
# Backfill for scripts/hsr_guard_radical_pilot.sh -- two things went wrong
# in the first real pass (see campaign/JOURNAL.md): (1) candidate A's
# case_001/case_003 silently reused stale pre-bugfix run.json data, and
# case_004 failed on a leftover partial file from an earlier killed run;
# (2) candidate C (window=150) tripped a genuine gap in
# patches/test_spec_casc_tok_hsr_guard.py's own "fair reference" (searched
# unbounded history, never exercised at window < its own synthetic n=300
# before) -- fixed in the test itself, not production code. Case_001 for
# candidate C already got genuine post-fix data before the failure; this
# backfills the other 3.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "=== hsr_guard_radical_backfill.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

echo ""
echo "########## backfill candidate=C_w150b10p99 (case_003 case_004 case_011) started $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
.venv-vllm/bin/python3 scripts/fresh_server_replay.py \
  --arms spec_casc_tok_hsr_guard \
  --spec-casc-tok-alpha 0.3 \
  --spec-casc-tok-hsr-guard-alpha 0.3 \
  --spec-casc-tok-hsr-guard-window 150 \
  --spec-casc-tok-hsr-guard-budget 10 \
  --spec-casc-tok-hsr-guard-percentile 99 \
  --spec-casc-tok-hsr-guard-actuator-k 8 \
  --cases case_003 case_004 case_011 \
  --prompt-root prompts/aime24_qwen3 \
  --runs-root runs \
  --log-root logs/hsr_guard_radical_pilot \
  --max-new-tokens 32768 \
  --port 30000 \
  --model-path Qwen/Qwen3-8B \
  --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
  --served-model-name qwen3-8b \
  --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
echo "candidate=C backfill exited $?"
echo "########## backfill candidate=C_w150b10p99 finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"

echo ""
echo "########## backfill candidate=A_w600b5p99.9 (case_001 case_003 case_004) started $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
.venv-vllm/bin/python3 scripts/fresh_server_replay.py \
  --arms spec_casc_tok_hsr_guard \
  --spec-casc-tok-alpha 0.3 \
  --spec-casc-tok-hsr-guard-alpha 0.3 \
  --spec-casc-tok-hsr-guard-window 600 \
  --spec-casc-tok-hsr-guard-budget 5 \
  --spec-casc-tok-hsr-guard-percentile 99.9 \
  --spec-casc-tok-hsr-guard-actuator-k 8 \
  --cases case_001 case_003 case_004 \
  --prompt-root prompts/aime24_qwen3 \
  --runs-root runs \
  --log-root logs/hsr_guard_radical_pilot \
  --max-new-tokens 32768 \
  --port 30000 \
  --model-path Qwen/Qwen3-8B \
  --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
  --served-model-name qwen3-8b \
  --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
echo "candidate=A backfill exited $?"
echo "########## backfill candidate=A_w600b5p99.9 finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"

echo ""
echo "=== hsr_guard_radical_backfill.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
