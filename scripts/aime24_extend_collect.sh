#!/usr/bin/env bash
# Extend aime24 data collection from 12 to 30 cases (18 new: case_013..030
# -- prompts/aime24 already had all 30 from the original build; only
# prompts/aime24_qwen3 needed rebuilding to match) at the campaign's
# already-SELECTED target alphas (campaign/results/aime24{,_qwen3}.csv),
# same pattern as scripts/mtbench_extend_collect.sh. User request
# 2026-08-26 "roll out aime".
#
# --no-trace-proposals: aime24's own traced proposals.jsonl runs ~10MB/run
# on GPT-OSS (measured directly from the existing 168 selected-alpha runs,
# 1.69GB/168) -- 252 new GPT-OSS runs at that rate would be ~2.5GB against
# only 5.8G free, too risky. (Qwen3's own proposals.jsonl is already
# empty for every run regardless of this flag -- a separate known bug,
# see campaign/JOURNAL.md 2026-08-20 -- so this costs it nothing extra.)
# run.json's summary fields (l_bar, completion length, accuracy) are
# unaffected either way.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

NEW_CASES="$(printf 'case_%03d ' $(seq 13 30))"
MIN_FREE_GB="${MIN_FREE_GB:-2}"
free_gb() { df --output=avail -BG . | tail -1 | tr -dc '0-9'; }

.venv-vllm/bin/python3 - <<'PYEOF'
import sys
sys.path.insert(0, "scripts")
from campaign_run import clean_partial_runs
import pathlib
for dataset in ("aime24", "aime24_qwen3"):
    n = clean_partial_runs(pathlib.Path("runs"), dataset)
    print(f"clean_partial_runs({dataset}): removed {n}")
PYEOF

PY_BIN=".venv-vllm/bin/python3"

run_arm() {
  local family="$1" method="$2" alpha="$3"
  local flag="--${method//_/-}-alpha"
  if [[ "$family" == "gptoss" ]]; then
    "$PY_BIN" scripts/fresh_server_replay.py \
      --arms "$method" $flag "$alpha" \
      --cases $NEW_CASES \
      --prompt-root prompts/aime24 --runs-root runs --log-root logs/campaign_aime24_extend \
      --max-new-tokens 32768 --port 30000 --no-trace-proposals
  else
    "$PY_BIN" scripts/fresh_server_replay.py \
      --arms "$method" $flag "$alpha" \
      --cases $NEW_CASES \
      --prompt-root prompts/aime24_qwen3 --runs-root runs --log-root logs/campaign_aime24_qwen3_extend \
      --max-new-tokens 32768 --port 30000 --no-trace-proposals \
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
      --arms strict --cases $NEW_CASES \
      --prompt-root prompts/aime24 --runs-root runs --log-root logs/campaign_aime24_extend \
      --max-new-tokens 32768 --port 30000 --no-trace-proposals
  else
    "$PY_BIN" scripts/fresh_server_replay.py \
      --arms strict --cases $NEW_CASES \
      --prompt-root prompts/aime24_qwen3 --runs-root runs --log-root logs/campaign_aime24_qwen3_extend \
      --max-new-tokens 32768 --port 30000 --no-trace-proposals \
      --model-path Qwen/Qwen3-8B \
      --draft-model-path RedHatAI/Qwen3-8B-speculator.eagle3 \
      --served-model-name qwen3-8b \
      --rope-scaling-json '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
  fi
  echo "  -> $family strict exited $?"
}

declare -A GPTOSS_ALPHAS=(
  [mentored_dec]="0.35 0.75 0.15"
  [cactus]="0.03 0.08 0.18"
  [spec_casc_opt]="-0.3 0.05"
  [r_fuzzy]="0.08 0.25 0.03"
  [spec_casc_tok]="0.8 0.15"
)
declare -A QWEN3_ALPHAS=(
  [mentored_dec]="0.75 0.15"
  [cactus]="0.03 0.08 0.35"
  [spec_casc_opt]="0.05 -0.3"
  [r_fuzzy]="0.25 0.03"
  [spec_casc_tok]="0.8 0.15"
)
METHOD_ORDER=(mentored_dec cactus spec_casc_opt r_fuzzy spec_casc_tok)

echo "=== aime24_extend_collect.sh starting $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

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
echo "=== aime24_extend_collect.sh done $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
