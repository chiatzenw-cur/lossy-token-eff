#!/bin/bash
#SBATCH --account=def-hongyanz_gpu
#SBATCH --job-name=casc
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=%x-%j.out
#
# One campaign_run.py invocation on one GPU, exactly as on the old box.
#
#   sbatch cascade/cluster/nibi_campaign.sbatch <dataset> "<method> [method ...]" [full_cases] [calib_cases]
#   sbatch cascade/cluster/nibi_campaign.sbatch gsm8k spec_casc_tok_lt 30 3
#   sbatch cascade/cluster/nibi_campaign.sbatch aime24 "spec_casc_tok_lt spec_casc_tok" 30 3
#
# Override the account/GPU with sbatch flags if the group runs elsewhere:
#   sbatch --account=aip-hongyanz --gpus-per-node=h100:1 ...   (Killarney/Vulcan: check `sinfo` for the gres name)
set -euo pipefail

DATASET="${1:?dataset (e.g. gsm8k)}"
METHODS="${2:?method name(s), space separated}"
FULL_CASES="${3:-12}"
CALIB_CASES="${4:-3}"

PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/def-hongyanz/$USER}"
REPO_DIR="${REPO_DIR:-$PROJECT_DIR/lossy-token-eff}"
MODULES="${MODULES:-StdEnv/2023 python/3.12 cuda/12.9}"

case "$DATASET" in
  *_qwen3)
    echo "refusing: Qwen3 datasets need the consolidated V2 sampler, which is not in this repo (cascade/DIRECTIONS.md D8)" >&2
    exit 2 ;;
esac

# shellcheck disable=SC2086
module load $MODULES
# the python module's PYTHONPATH would shadow the venvs' packages (see setup_nibi.sh)
unset PYTHONPATH
cd "$REPO_DIR"

export HF_HOME="${HF_HOME:-$PROJECT_DIR/hf}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
# remote/run_server_vllm.sh defaults CUDA_HOME to /usr/local/cuda; the cuda
# module exports EBROOTCUDA (and usually CUDA_HOME) instead.
export CUDA_HOME="${CUDA_HOME:-${EBROOTCUDA:-/usr/local/cuda}}"
# compile caches on node-local disk: fast and never counted against quota
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-$SCRATCH/triton_cache}"
export TORCHINDUCTOR_CACHE_DIR="${TORCHINDUCTOR_CACHE_DIR:-$SCRATCH/inductor_cache}"
mkdir -p "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR"
# two jobs sharing a node must not share a vLLM port
PORT=$((30000 + SLURM_JOB_ID % 20000))

echo "=== job $SLURM_JOB_ID on $(hostname) dataset=$DATASET methods=$METHODS full=$FULL_CASES calib=$CALIB_CASES port=$PORT ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

# shellcheck disable=SC2086
python3 scripts/campaign_run.py \
  --dataset "$DATASET" \
  --methods $METHODS \
  --full-cases "$FULL_CASES" \
  --calib-cases "$CALIB_CASES" \
  --port "$PORT"
status=$?
echo "campaign_run.py exited $status"

.venv-report/bin/python scripts/campaign_report.py --dataset "$DATASET" || echo "campaign_report.py failed (runs are intact; re-run it by hand)"
python3 cascade/analysis/speed_ignoring_accuracy.py || true
echo "=== done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
exit $status
