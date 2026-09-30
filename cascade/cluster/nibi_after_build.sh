#!/usr/bin/env bash
# Wait for cascade/cluster/setup_nibi.sh (running detached on a login node,
# logging to setup_nibi.log) to finish, then submit E0 and, chained after it,
# the one-case sample run. Run detached on a login node:
#
#   setsid nohup bash cascade/cluster/nibi_after_build.sh > after_build.log 2>&1 < /dev/null &
#
# "Finished" = the log has reached the patch-sanity step (everything is
# installed and downloaded) and has not grown for 2 minutes. The patch
# sanity step itself may fail on a GPU-less login node (import of the
# patched sampler); E0 repeats those tests on a GPU, so that is not a
# blocker. Aborts on pip/download errors.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
LOG=setup_nibi.log
MAX_WAIT_MIN="${MAX_WAIT_MIN:-180}"

log() { echo "$(date -u +%H:%M:%S) $*"; }
log "watching $LOG for completion (max ${MAX_WAIT_MIN} min)"
waited=0
while true; do
  if grep -q -E "No matching distribution|^ERROR:|Traceback \(most recent call last\)" "$LOG" 2>/dev/null; then
    log "build reported an error; not submitting. Last lines:"; tail -15 "$LOG"; exit 1
  fi
  if grep -q -- "--- patch sanity" "$LOG" 2>/dev/null; then
    age=$(( $(date +%s) - $(stat -c %Y "$LOG") ))
    if [[ $age -ge 120 ]]; then
      log "build log reached patch-sanity and has been quiet for ${age}s -> treating as finished"
      break
    fi
  fi
  if [[ $waited -ge $MAX_WAIT_MIN ]]; then
    log "gave up after ${MAX_WAIT_MIN} min; last lines:"; tail -10 "$LOG"; exit 1
  fi
  sleep 60; waited=$((waited + 1))
done

log "import check:"
.venv-vllm/bin/python -c "import torch, vllm; print('torch', torch.__version__, '| vllm', vllm.__version__)" 2>&1 | tail -3
[[ -x .venv-report/bin/python ]] && log "report venv present" || log "WARNING: .venv-report missing"

e0_cmd=$(bash cascade/run.sh E0 --target nibi --dry-run | sed 's/^\[dry-run\] //')
sample_cmd=$(bash cascade/run.sh SAMPLE-gsm8k --target nibi --dry-run | sed 's/^\[dry-run\] //')
log "submitting E0"
e0=$(sbatch --parsable --time=1:00:00 --job-name=E0 cascade/cluster/nibi_run.sbatch "$e0_cmd") || { log "sbatch E0 failed"; exit 1; }
log "E0 job $e0"
log "submitting SAMPLE-gsm8k (afterok:$e0)"
sm=$(sbatch --parsable --time=1:30:00 --job-name=SAMPLE --dependency=afterok:"$e0" cascade/cluster/nibi_run.sbatch "$sample_cmd") || { log "sbatch SAMPLE failed"; exit 1; }
log "SAMPLE job $sm"
squeue -u "$USER" -o "%.10i %.8j %.10T %.10M %.6D %R"
log "done; outputs: E0-$e0.out SAMPLE-$sm.out"
