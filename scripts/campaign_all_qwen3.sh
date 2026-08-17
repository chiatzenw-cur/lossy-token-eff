#!/usr/bin/env bash
# Qwen3-8B + drafter counterpart to scripts/campaign_all.sh (2026-08-17,
# user request: "if we have space we would like to try running the
# experiment with qwen 8b and a drafter"). Same driver shape -- calibrate +
# full sweep + report, one dataset at a time, single GPU, inherently serial
# -- over the *_qwen3 dataset names (prompts/<name>_qwen3/, built by
# scripts/build_prompts_qwen3.py from the same underlying problems as the
# GPT-OSS-20B run, re-rendered through Qwen3's own chat template).
#
# Disk is real here, unlike the GPT-OSS run when it started: this box sat
# at 10G free when this was written, and Qwen3's own runs/ tree is unknown
# territory (the GPT-OSS 6-dataset campaign used 3.2G total, but Qwen3-8B's
# hybrid-thinking <think> traces could run considerably longer per case --
# see aime24's own 1.9G vs gsm8k's 69M for how much dataset difficulty alone
# already swings this). So: check free space before EVERY dataset, not just
# once at the top, and stop (not skip) the moment it's actually tight --
# guessing wrong here risks the box, not just this run.
set -uo pipefail  # NOT -e: one dataset failing must not stop the others

cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPORT_PY=".venv-report/bin/python"
MIN_FREE_GB="${MIN_FREE_GB:-3}"

DATASETS=(gsm8k_qwen3 aime24_qwen3 humaneval_qwen3 livecodebench_qwen3 mtbench_qwen3 longbench_v2_qwen3)

free_gb() {
  df --output=avail -BG . | tail -1 | tr -dc '0-9'
}

echo "=== campaign_all_qwen3.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
for dataset in "${DATASETS[@]}"; do
  free="$(free_gb)"
  echo ""
  echo "free space check before $dataset: ${free}G"
  if [[ "$free" -lt "$MIN_FREE_GB" ]]; then
    echo "STOPPING: only ${free}G free (< ${MIN_FREE_GB}G floor) before dataset=$dataset -- not attempting it. Earlier datasets' results are already written and safe." >&2
    break
  fi

  echo "########## dataset=$dataset started $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
  python3 scripts/campaign_run.py --dataset "$dataset"
  run_status=$?
  echo "campaign_run.py --dataset $dataset exited $run_status"

  "$REPORT_PY" scripts/campaign_report.py --dataset "$dataset"
  echo "campaign_report.py --dataset $dataset exited $?"
  echo "########## dataset=$dataset finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
done

echo ""
echo "=== campaign_all_qwen3.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
