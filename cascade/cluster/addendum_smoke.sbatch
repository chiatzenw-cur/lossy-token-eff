#!/bin/bash
#SBATCH --account=def-hongyanz_gpu
#SBATCH --job-name=add-smoke
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=%x-%j.out
#
# Addendum step 0.1 (campaign/addendum/PROGRESS.md): one GPT-OSS gsm8k case
# through scripts/persistent_arm_replay.py at `strict`, request seed 7, into a
# throwaway run root under $SCRATCH that this job deletes once it has printed
# the run record and the timings.
#
#   REPO_DIR=... sbatch --exclude=g[15-28] cascade/cluster/addendum_smoke.sbatch
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/def-hongyanz/$USER}"
REPO_DIR="${REPO_DIR:-$PROJECT_DIR/lossy-token-eff}"
MODULES="${MODULES:-StdEnv/2023 python/3.12 cuda/12.9}"
# shellcheck disable=SC2086
module load $MODULES
unset PYTHONPATH
cd "$REPO_DIR"

export HF_HOME="${HF_HOME:-$PROJECT_DIR/hf}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_HOME="${CUDA_HOME:-${EBROOTCUDA:-/usr/local/cuda}}"
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-$SCRATCH/triton_cache}"
export TORCHINDUCTOR_CACHE_DIR="${TORCHINDUCTOR_CACHE_DIR:-$SCRATCH/inductor_cache}"
mkdir -p "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR"
PORT=$((30000 + SLURM_JOB_ID % 20000))
SMOKE="$SCRATCH/lossy-addendum/smoke-$SLURM_JOB_ID"
mkdir -p "$SMOKE"

echo "=== smoke job $SLURM_JOB_ID on $(hostname) repo=$REPO_DIR port=$PORT $(date -u +%FT%TZ) ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

# Time from launch until the server answers /health (patch switch + server start).
(
  s=$(date +%s.%N)
  until curl -sf "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; do sleep 1; done
  e=$(date +%s.%N)
  echo "SMOKE server_healthy_after_s=$(python3 -c "print(round($e - $s, 1))")"
) &
watcher=$!

t0=$(date +%s.%N)
status=0
.venv-vllm/bin/python scripts/persistent_arm_replay.py \
  --arms strict --cases case_001 --seeds 7 \
  --prompt-root prompts/gsm8k --runs-root "$SMOKE/runs" --log-root "$SMOKE/logs" \
  --max-new-tokens 2048 --port "$PORT" --no-trace-proposals || status=$?
t1=$(date +%s.%N)
kill "$watcher" 2>/dev/null || true
echo "SMOKE persistent_arm_replay_exit=$status total_s=$(python3 -c "print(round($t1 - $t0, 1))")"

run_json="$SMOKE/runs/gsm8k/strict/strict/case_001/seed_7/run.json"
if [[ -f "$run_json" ]]; then
  echo "SMOKE run.json:"; cat "$run_json"
  echo "SMOKE config.json acceptance + vllm fields:"
  python3 - "$SMOKE/runs/gsm8k/strict/strict/case_001/seed_7/config.json" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))
for k in ("seed", "temperature", "top_p", "max_new_tokens", "server_request_ordinal", "model", "draft_model", "vllm"):
    print(k, "=", json.dumps(c.get(k))[:400])
PY
else
  echo "SMOKE FAILED: no run.json"; status=1
fi
echo "SMOKE server log tail:"; tail -n 5 "$SMOKE"/logs/*.log 2>/dev/null || true
rm -rf "$SMOKE"
echo "SMOKE scratch run root removed: $SMOKE"
echo "=== done $(date -u +%FT%TZ) ==="
exit $status
