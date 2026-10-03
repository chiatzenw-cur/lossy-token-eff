#!/usr/bin/env bash
# Stop a vLLM server and wait for the GPU to actually be released.
#
# `pkill -f vllm.entrypoints` is not enough: vLLM renames its worker process to
# `VLLM::EngineCore`, and that child is what holds the GPU allocation. Killing
# only the API server leaves ~70 GiB pinned, and the next server then dies with
# "Free memory on device ... is less than desired GPU memory utilization".
set -euo pipefail

# PIDs of this user whose command line matches $1 -- inside a Slurm job only those of this job (its
# cgroup path names job_<id>), so two lanes sharing a node never stop each other's server. Outside
# Slurm: every match, as before. (The nvidia-smi steps below only see this job's GPU already.)
own_pids() {
  local p
  for p in $(pgrep -u "$(id -u)" -f "$1" 2>/dev/null || true); do
    if [[ -z "${SLURM_JOB_ID:-}" ]] || grep -qs "/job_${SLURM_JOB_ID}/" "/proc/$p/cgroup"; then
      echo "$p"
    fi
  done
}

pids="$(own_pids vllm.entrypoints)"
# shellcheck disable=SC2086
[[ -n "$pids" ]] && kill -INT $pids 2>/dev/null || true
for _ in $(seq 1 20); do
  pids="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null || true)"
  [[ -z "$pids" ]] && break
  sleep 1
done

# Anything still holding the GPU gets killed by pid, whatever it is called.
pids="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  echo "force-killing GPU holders: $(tr '\n' ' ' <<<"$pids")"
  # shellcheck disable=SC2086
  kill -KILL $pids 2>/dev/null || true
fi
pids="$(own_pids vllm.entrypoints)"
# shellcheck disable=SC2086
[[ -n "$pids" ]] && kill -KILL $pids 2>/dev/null || true

for _ in $(seq 1 60); do
  used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)"
  [[ "$used" -lt 2000 ]] && { echo "gpu released (${used} MiB used)"; exit 0; }
  sleep 1
done
echo "GPU still occupied: $(nvidia-smi --query-gpu=memory.used --format=csv,noheader)" >&2
exit 1
