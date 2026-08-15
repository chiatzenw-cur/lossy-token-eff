#!/usr/bin/env bash
# Top-level driver for campaign/PLAN.md: run campaign_run.py (calibrate +
# full sweep) then campaign_report.py (tables/results/graph) for each
# dataset in turn. One GPU, fresh-server-per-measurement is a hard
# requirement (remote/ENVIRONMENT.md) -- inherently serial, no parallelism
# across datasets or methods.
#
# Safe to interrupt and re-run: campaign_run.py cleans up any partial run
# directory from a previous interrupted attempt before continuing, and every
# fresh_server_replay.py invocation skips (method, alpha, case) triples that
# already have a run.json. Re-running this script after a crash just
# resumes from wherever it stopped.
set -uo pipefail  # NOT -e: one dataset failing must not stop the others

cd "$(dirname "${BASH_SOURCE[0]}")/.."
REPORT_PY=".venv-report/bin/python"

DATASETS=(gsm8k aime24 humaneval livecodebench mtbench longbench_v2)

echo "=== campaign_all.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
for dataset in "${DATASETS[@]}"; do
  echo ""
  echo "########## dataset=$dataset started $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
  python3 scripts/campaign_run.py --dataset "$dataset"
  run_status=$?
  echo "campaign_run.py --dataset $dataset exited $run_status"

  "$REPORT_PY" scripts/campaign_report.py --dataset "$dataset"
  echo "campaign_report.py --dataset $dataset exited $?"
  echo "########## dataset=$dataset finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##########"
done

echo ""
echo "=== campaign_all.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
