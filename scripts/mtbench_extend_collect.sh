#!/usr/bin/env bash
# Extend mtbench data collection from 12 to 30 cases (18 new: case_013..030,
# added via extend_borrowed_prompts.py) at the campaign's already-SELECTED
# target alphas (campaign/results/mtbench{,_qwen3}.csv) -- not a fresh
# calibration grid. User request 2026-08-25 "add another 18 sets of
# prompts" / "collect data on all mtbench prompts, selected parameters,
# qwen3 and gpt-oss 20b, all methods". Only case_013..030 are requested
# here (fresh_server_replay.py's own skip-if-done keeps case_001..012
# untouched). One fresh server per (method, alpha, case) -- 28 arms
# (13 alphas + strict, per model family) x 18 cases = 504 runs, est.
# ~106s/run average (real empirical mean from this dataset's own prior
# runs) ~= ~15h total.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

NEW_CASES="$(printf 'case_%03d ' $(seq 13 30))"
MIN_FREE_GB="${MIN_FREE_GB:-2}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

# Clear any partial/error run left in case_013..030 from a prior killed
# attempt -- same rationale as campaign_run.py's clean_partial_runs()
# (skip-if-done only checks run.json EXISTS, not its status).
.venv-vllm/bin/python3 - <<'PYEOF'
import sys
sys.path.insert(0, "scripts")
from campaign_run import clean_partial_runs
import pathlib
for dataset in ("mtbench", "mtbench_qwen3"):
    n = clean_partial_runs(pathlib.Path("runs"), dataset)
    print(f"clean_partial_runs({dataset}): removed {n}")
PYEOF

run_arm() {
  local family="$1" method="$2" alpha="$3"
  shift 3
  local flag="--${method//_/-}-alpha"
  local prompt_root runs_root log_root
  if [[ "$family" == "gptoss" ]]; then
    prompt_root="prompts/mtbench"
    log_root="logs/campaign_mtbench_extend"
    "$PY_BIN" scripts/fresh_server_replay.py \
      --arms "$method" $flag "$alpha" \
      --cases $NEW_CASES \
      --prompt-root "$prompt_root" --runs-root runs --log-root "$log_root" \
      --max-new-tokens 4096 --port 30000
  else
    prompt_root="prompts/mtbench_qwen3"
    log_root="logs/campaign_mtbench_qwen3_extend"
    "$PY_BIN" scripts/fresh_server_replay.py \
      --arms "$method" $flag "$alpha" \
      --cases $NEW_CASES \
      --prompt-root "$prompt_root" --runs-root runs --log-root "$log_root" \
      --max-new-tokens 4096 --port 30000 \
      --model-path Qwen/Qwen3-8B \
      --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
      --served-model-name qwen3-8b \
      --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  fi
  echo "  -> $family $method alpha=$alpha exited $?"
}

run_strict() {
  local family="$1"
  if [[ "$family" == "gptoss" ]]; then
    "$PY_BIN" scripts/fresh_server_replay.py \
      --arms strict \
      --cases $NEW_CASES \
      --prompt-root prompts/mtbench --runs-root runs --log-root logs/campaign_mtbench_extend \
      --max-new-tokens 4096 --port 30000
  else
    "$PY_BIN" scripts/fresh_server_replay.py \
      --arms strict \
      --cases $NEW_CASES \
      --prompt-root prompts/mtbench_qwen3 --runs-root runs --log-root logs/campaign_mtbench_qwen3_extend \
      --max-new-tokens 4096 --port 30000 \
      --model-path Qwen/Qwen3-8B \
      --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
      --served-model-name qwen3-8b \
      --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  fi
  echo "  -> $family strict exited $?"
}

PY_BIN=".venv-vllm/bin/python3"

# method -> selected alphas, one array per family (from campaign/results/*.csv)
declare -A GPTOSS_ALPHAS=(
  [mentored_dec]="0.15 0.55 0.75"
  [cactus]="0.03 0.18 0.35"
  [spec_casc_opt]="-0.3 0.05"
  [r_fuzzy]="0.08 0.15 0.25"
  [spec_casc_tok]="0.8 0.15"
)
declare -A QWEN3_ALPHAS=(
  [mentored_dec]="0.75 0.15"
  [cactus]="0.03 0.08 0.35"
  [spec_casc_opt]="-0.02 -0.3 0.05"
  [r_fuzzy]="0.15 0.25 0.03"
  [spec_casc_tok]="0.8 0.15"
)
METHOD_ORDER=(mentored_dec cactus spec_casc_opt r_fuzzy spec_casc_tok)

echo "=== mtbench_extend_collect.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

for family in gptoss qwen3; do
  free="$(free_gb)"
  echo ""
  echo "### family=$family starting $(date -u +%Y-%m-%dT%H:%M:%SZ), free=${free}G ###"
  if [[ "$free" -lt "$MIN_FREE_GB" ]]; then
    echo "STOPPING: only ${free}G free (< ${MIN_FREE_GB}G floor) before family=$family." >&2
    break
  fi

  run_strict "$family"

  if [[ "$family" == "gptoss" ]]; then
    declare -n ALPHAS=GPTOSS_ALPHAS
  else
    declare -n ALPHAS=QWEN3_ALPHAS
  fi
  for method in "${METHOD_ORDER[@]}"; do
    for alpha in ${ALPHAS[$method]}; do
      free="$(free_gb)"
      if [[ "$free" -lt "$MIN_FREE_GB" ]]; then
        echo "STOPPING mid-family: only ${free}G free before $family/$method/alpha=$alpha." >&2
        break 3
      fi
      echo ""
      echo "## $family / $method / alpha=$alpha started $(date -u +%Y-%m-%dT%H:%M:%SZ) ##"
      run_arm "$family" "$method" "$alpha"
      echo "## $family / $method / alpha=$alpha finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ##"
    done
  done
  unset -n ALPHAS
  echo "### family=$family finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ###"
done

echo ""
echo "=== mtbench_extend_collect.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
