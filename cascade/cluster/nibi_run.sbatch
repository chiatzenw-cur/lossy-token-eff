#!/bin/bash
#SBATCH --account=def-hongyanz_gpu
#SBATCH --job-name=casc
#SBATCH --gpus-per-node=h100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=%x-%j.out
#
# Generic one-GPU job: set up the environment exactly like nibi_campaign.sbatch
# and run an arbitrary command string from the repo root. cascade/run.sh
# submits through this when --target nibi is given.
#
#   sbatch cascade/cluster/nibi_run.sbatch "python3 scripts/campaign_run.py --dataset gsm8k --methods spec_casc_tok_lt --full-cases 30"
#   sbatch --time=4:00:00 cascade/cluster/nibi_run.sbatch "bash patches/apply.sh spec-casc-tok-lt"
set -euo pipefail

COMMAND="${1:?command string to run from the repo root}"
PROJECT_DIR="${PROJECT_DIR:-$HOME/projects/def-hongyanz/$USER}"
REPO_DIR="${REPO_DIR:-$PROJECT_DIR/lossy-token-eff}"
MODULES="${MODULES:-StdEnv/2023 python/3.12 cuda/12.9}"

# shellcheck disable=SC2086
module load $MODULES
# the python module's PYTHONPATH would shadow the venvs' packages (see setup_nibi.sh)
unset PYTHONPATH
cd "$REPO_DIR"

export HF_HOME="${HF_HOME:-$PROJECT_DIR/hf}"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export CUDA_HOME="${CUDA_HOME:-${EBROOTCUDA:-/usr/local/cuda}}"
# Persistent scratch, not $SLURM_TMPDIR: vLLM's torch.compile / CUDA-graph
# artefacts for GPT-OSS-20B take minutes to build and are keyed by config, so
# reusing them across jobs saves that on every fresh server start.
export VLLM_CACHE_ROOT="${VLLM_CACHE_ROOT:-$SCRATCH/vllm_cache}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-$SCRATCH/triton_cache}"
export TORCHINDUCTOR_CACHE_DIR="${TORCHINDUCTOR_CACHE_DIR:-$SCRATCH/inductor_cache}"
mkdir -p "$VLLM_CACHE_ROOT" "$TRITON_CACHE_DIR" "$TORCHINDUCTOR_CACHE_DIR"
# cascade/run.sh reads PORT so two jobs on one node never share a vLLM port
export PORT=$((30000 + SLURM_JOB_ID % 20000))

echo "=== job $SLURM_JOB_ID on $(hostname) port=$PORT ==="
echo "=== $COMMAND ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
bash -c "$COMMAND"
status=$?
echo "=== exit $status $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
exit $status
