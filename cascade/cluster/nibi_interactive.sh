#!/usr/bin/env bash
# Interactive GPU shell for debugging (not for sweeps -- interactive
# allocations are short and the scheduler prefers batch jobs).
#
#   bash cascade/cluster/nibi_interactive.sh            # 1 x H100, 8 CPUs, 64G, 2 h
#   HOURS=1 GPU=h100:1 ACCOUNT=aip-hongyanz bash cascade/cluster/nibi_interactive.sh
set -euo pipefail
ACCOUNT="${ACCOUNT:-def-hongyanz_gpu}"
GPU="${GPU:-h100:1}"
HOURS="${HOURS:-2}"
exec salloc --account="$ACCOUNT" --gpus-per-node="$GPU" --cpus-per-task=8 --mem=64G --time="${HOURS}:00:00"
