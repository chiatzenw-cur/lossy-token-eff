#!/usr/bin/env bash
# Install and self-test each cascade patch in turn on this machine (run it
# on a GPU node so the Triton kernel tests execute), reversing whichever
# patch is currently installed first. patches/apply.sh refuses to switch
# patches on its own -- by design, a human should notice -- and the campaign
# runners (fresh_server_replay.py ensure_patch_applied) do the reversal
# themselves; this is that same reversal, for E0.
#
#   bash cascade/cluster/patch_cycle_test.sh
#   LABELS="spec-casc-opt-head" bash cascade/cluster/patch_cycle_test.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
PY="${PYTHON:-.venv-vllm/bin/python}"
read -r -a LABELS <<< "${LABELS:-spec-casc-tok-lt spec-casc-opt-ent spec-casc-diff spec-casc-chow spec-casc-opt-head}"

sp=$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')
f="$sp/vllm/v1/sample/rejection_sampler.py"
label_of() { awk -v h="$(sha256sum "$f" | cut -d' ' -f1)" '$1==h {print $2}' patches/HASHES.txt; }

for m in "${LABELS[@]}"; do
  cur=$(label_of)
  if [[ -z "$cur" ]]; then
    echo "installed $f matches no state in patches/HASHES.txt -- reinstall vLLM 0.26.0" >&2
    exit 1
  fi
  if [[ "$cur" != "upstream" && "$cur" != "$m" ]]; then
    p="patches/vllm-0.26.0-$cur.patch"
    [[ "$cur" == "mentored-dec" ]] && p="patches/vllm-0.26.0-mentored-dec-v1only.patch"
    echo "reversing $cur before applying $m"
    patch -p1 -R -d "$sp" < "$p"
  fi
  echo "=== $m ==="
  bash patches/apply.sh "$m"
done
echo "all ${#LABELS[@]} patches installed and self-tested; currently installed: $(label_of)"
