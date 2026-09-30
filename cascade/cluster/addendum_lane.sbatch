#!/bin/bash
#SBATCH --account=def-hongyanz_gpu
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#
# One addendum lane for up to 12 h on one H100 (campaign/addendum/README.md).
# Runs scripts/addendum_lane.py against <lane root>/work.json; every item is
# skip-if-done, so the next job in the lane's chain
# (--dependency=afterany:<previous>) continues where this one stopped.
#
#   LANE=A REPO_DIR=$HOME/projects/def-hongyanz/$USER/lossy-token-eff \
#     sbatch --job-name=add-A --exclude=g[15-28] \
#            --output=$SCRATCH/lossy-addendum/laneA/slurm/%x-%j.out \
#            cascade/cluster/addendum_lane.sbatch
#
# Lanes must run on disjoint node sets: remote/stop_server.sh kills every
# vllm.entrypoints process of this user on the node, and the patched sampler
# reads node-local /tmp knob files.
set -euo pipefail

LANE="${LANE:?LANE (A, B, ...)}"
PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/def-hongyanz/$USER}"
REPO_DIR="${REPO_DIR:?REPO_DIR (the repo + .venv-vllm copy of this lane)}"
LANE_ROOT="${LANE_ROOT:-$SCRATCH/lossy-addendum/lane$LANE}"
MODULES="${MODULES:-StdEnv/2023 python/3.12 cuda/12.9}"

# shellcheck disable=SC2086
module load $MODULES
# the python module's PYTHONPATH would shadow the venv's packages (setup_nibi.sh)
unset PYTHONPATH
cd "$REPO_DIR"

export HF_HOME="${HF_HOME:-$PROJECT_DIR/hf}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_HOME="${CUDA_HOME:-${EBROOTCUDA:-/usr/local/cuda}}"
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-$SCRATCH/triton_cache}"
export TORCHINDUCTOR_CACHE_DIR="${TORCHINDUCTOR_CACHE_DIR:-$SCRATCH/inductor_cache}"
mkdir -p "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR" "$LANE_ROOT"
# patches/apply.sh: skip the ~2.5 min self-test when the requested patch is
# already installed with a matching sha256 (a switch still runs it)
export APPLY_SKIP_TEST_IF_APPLIED=1
# two jobs on one node must not share a vLLM port
PORT=$((30000 + SLURM_JOB_ID % 20000))

echo "=== lane $LANE job $SLURM_JOB_ID on $(hostname) repo=$REPO_DIR root=$LANE_ROOT port=$PORT $(date -u +%FT%TZ) ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

status=0
python3 scripts/addendum_lane.py --lane "$LANE" --lane-root "$LANE_ROOT" --port "$PORT" \
  --python "$REPO_DIR/.venv-vllm/bin/python" || status=$?
bash remote/stop_server.sh > /dev/null 2>&1 || true
echo "=== lane $LANE job $SLURM_JOB_ID done, exit $status $(date -u +%FT%TZ) ==="
exit $status
