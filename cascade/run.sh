#!/usr/bin/env bash
# Run one experiment from cascade/EXPERIMENTS.md by id.
#
#   bash cascade/run.sh <EXP> [--target box|nibi] [--mode fresh|persistent] [--cases N] [--dry-run]
#
#   E0            smoke: install + self-test every cascade patch, 1-case dry run
#   E1-<dataset>  tok_lt vs tok (mechanism test)            campaign_run, 30 cases
#   E2-<dataset>  opt_ent vs opt (entropy plug-in)          campaign_run, 30 cases
#   E3-<dataset>  timing: baseline / strict / tok(0.8)      fresh servers, 10 cases -> timing_report
#   E4-<dataset>  draft-length sweep N in 3 4 6 8 10        strict + tok(0.8), 20 cases -> timing_report
#   E5-<dataset>  source-paper baselines diff + chow        campaign_run, 30 cases
#   E6-<dataset>  opt_head hybrid, beta in 0.15 0.35        fresh/persistent replay, alpha grid, 30 cases
#   E1F-<dataset> fine low-alpha sweep (0.05..0.25) x 3 seeds, tok_lt + tok + strict, persistent
#   E1P-<dataset> "proper" protocol: tok_lt + tok at 0.15/0.2/0.25 x 3 seeds + strict x 3, persistent,
#                 campaign case counts (longbench_v2: 30); reports to campaign/*/<ds>_proper.*
#   E7            trace analysis on existing runs (no GPU)  cascade/analysis/trace_rank_analysis.py
#   SAMPLE-<ds>   smallest real run: 1 case strict vs tok_lt(0.55), fresh servers, prints run.json
#
# --target box (default): run here, in the foreground, from the repo root.
# --target nibi: submit the same command through cascade/cluster/nibi_run.sbatch.
# --mode fresh (default): one server per measurement (the campaign's clean
#   protocol; ~100 s overhead per run). --mode persistent: one warm server per
#   arm via scripts/persistent_arm_replay.py, ~5x faster, carries the documented
#   request-ordinal confound; only for E1/E2/E5/E6 (uses a fixed alpha grid, no
#   matched-l̄ calibration).
# --dry-run prints the command(s) and exits.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

EXP="${1:?experiment id, see cascade/EXPERIMENTS.md}"; shift
TARGET=box; MODE=fresh; CASES=""; DRY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --cases) CASES="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) echo "unknown flag $1" >&2; exit 2 ;;
  esac
done
PORT="${PORT:-30000}"
# On the cluster the port must be chosen inside the job (nibi_run.sbatch
# exports PORT from the job id so two jobs on one node never collide), so
# leave it as a literal $PORT in the command string for bash -c to expand.
[[ "$TARGET" == "nibi" ]] && PORT='$PORT'
REPORT_PY="${REPORT_PY:-.venv-report/bin/python}"

# ---- helpers ---------------------------------------------------------------
case_list() { local n=$1; local out=""; for i in $(seq 1 "$n"); do out+=$(printf "case_%03d " "$i"); done; echo "$out"; }
grid_for() {  # alpha grid of a method, from scripts/campaign_run.py
  python3 -c "import sys; sys.path.insert(0,'scripts'); import campaign_run as c; print(' '.join(f'{a:g}' for a in c.ALPHA_GRIDS['$1']))"
}
dataset_of() { echo "${EXP#*-}"; }
budget_for() { python3 -c "import sys; sys.path.insert(0,'scripts'); import campaign_run as c; print(c.TOKEN_BUDGETS['$1'])"; }
model_flags_for() {  # --model-path/--draft-model-path/--served-model-name for fresh_server_replay
  python3 - "$1" <<'EOF'
import sys; sys.path.insert(0, "scripts"); import campaign_run as c
m, d, s, r = c.model_family_for(sys.argv[1])
print(f"--model-path {m} --draft-model-path {d} --served-model-name {s}")
EOF
}
run_or_submit() {  # $1: command string, $2: sbatch --time
  local cmd="$1" hours="${2:-12:00:00}"
  if [[ $DRY -eq 1 ]]; then echo "[dry-run] $cmd"; return; fi
  if [[ "$TARGET" == "nibi" ]]; then
    # SBATCH_EXTRA: e.g. "--dependency=afterany:12345" to chain jobs on one GPU
    # shellcheck disable=SC2086
    sbatch --time="$hours" ${SBATCH_EXTRA:-} cascade/cluster/nibi_run.sbatch "$cmd"
  else
    echo "+ $cmd"; bash -c "$cmd"
  fi
}
campaign() {  # $1 dataset, $2 methods (space separated), $3 cases
  local ds="$1" methods="$2" n="$3"
  if [[ "$MODE" == "fresh" ]]; then
    run_or_submit "python3 scripts/campaign_run.py --dataset $ds --methods $methods --full-cases $n --calib-cases 3 --port $PORT && $REPORT_PY scripts/campaign_report.py --dataset $ds && python3 cascade/analysis/speed_ignoring_accuracy.py"
  else
    # Quick look: every grid alpha of every method, no matched-l̄ selection.
    # Report against a calibration file that lists exactly those grid alphas
    # as "chosen", written to *_quick.* outputs so the campaign's own
    # calibration/results/graphs are untouched.
    local quick_cal="campaign/calibration/${ds}_quick.json"
    METHODS_LIST="$methods" DS="$ds" python3 - > "$quick_cal" <<'EOF'
import json, os, sys
sys.path.insert(0, "scripts")
import campaign_run as c
methods = os.environ["METHODS_LIST"].split()
print(json.dumps({"dataset": os.environ["DS"], "note": "quick look: full alpha grids, persistent servers",
                  "chosen_alphas": {m: c.ALPHA_GRIDS[m] for m in methods}}, indent=2))
EOF
    local cmd="" m
    for m in $methods; do
      local a
      for a in $(grid_for "$m"); do
        cmd+="$(persistent_cmd "$ds" "$m" "$a" "$n") && "
      done
    done
    cmd+="$(persistent_cmd "$ds" strict '' "$n")"
    cmd+=" && $REPORT_PY scripts/campaign_report.py --dataset $ds --calibration-json $quick_cal --tables-out campaign/tables/${ds}_quick.csv --results-out campaign/results/${ds}_quick.csv --graph-out campaign/graphs/${ds}_quick.png --accuracy-graph-out campaign/graphs/${ds}_quick_accuracy.png"
    cmd+=" && python3 cascade/analysis/speed_ignoring_accuracy.py && cat campaign/results/${ds}_quick.csv"
    run_or_submit "$cmd"
  fi
}
persistent_cmd() {  # $1 dataset, $2 arm, $3 alpha ('' for strict/baseline), $4 cases, $5 extra flags
  local ds="$1" arm="$2" alpha="$3" n="$4" extra="${5:-}"
  local flag=""; [[ -n "$alpha" ]] && flag="--${arm//_/-}-alpha $alpha"
  echo ".venv-vllm/bin/python scripts/persistent_arm_replay.py --arms $arm $flag $extra --cases $(case_list "$n") --prompt-root prompts/$ds --log-root logs/cascade_$ds --max-new-tokens $(budget_for "$ds") --port $PORT --no-trace-proposals $(model_flags_for "$ds")"
}
fresh_cmd() {  # same, one fresh server per measurement (tracing on by default)
  local ds="$1" arm="$2" alpha="$3" n="$4" extra="${5:-}"
  local flag=""; [[ -n "$alpha" ]] && flag="--${arm//_/-}-alpha $alpha"
  echo ".venv-vllm/bin/python scripts/fresh_server_replay.py --arms $arm $flag $extra --cases $(case_list "$n") --prompt-root prompts/$ds --log-root logs/cascade_$ds --max-new-tokens $(budget_for "$ds") --port $PORT $(model_flags_for "$ds")"
}

# ---- experiments -----------------------------------------------------------
case "$EXP" in
  E0)
    cmd="bash cascade/cluster/patch_cycle_test.sh"
    cmd+=" && python3 scripts/campaign_run.py --dataset gsm8k --methods spec_casc_tok_lt --full-cases 1 --calib-cases 1 --dry-run"
    run_or_submit "$cmd" "1:00:00" ;;
  E1-*) ds=$(dataset_of); campaign "$ds" "spec_casc_tok_lt spec_casc_tok" "${CASES:-30}" ;;
  E2-*) ds=$(dataset_of); campaign "$ds" "spec_casc_opt_ent spec_casc_opt" "${CASES:-30}" ;;
  E3-*)
    ds=$(dataset_of); n="${CASES:-10}"
    cmd="$(fresh_cmd "$ds" baseline '' "$n" --no-trace-proposals) && $(fresh_cmd "$ds" strict '' "$n" --no-trace-proposals) && $(fresh_cmd "$ds" spec_casc_tok 0.8 "$n" --no-trace-proposals)"
    cmd+=" && python3 cascade/analysis/timing_report.py --dataset $ds --runs-root runs --out cascade/results/timing_$ds.md"
    run_or_submit "$cmd" "3:00:00" ;;
  E4-*)
    ds=$(dataset_of); n="${CASES:-20}"; cmd=""; roots=""; specs=""
    for N in 3 4 6 8 10; do
      root="runs_nspec$N"; roots+="$root "; specs+="$N "
      if [[ "$MODE" == "fresh" ]]; then
        cmd+="$(fresh_cmd "$ds" strict '' "$n" "--no-trace-proposals --num-spec $N --runs-root $root") && "
        cmd+="$(fresh_cmd "$ds" spec_casc_tok 0.8 "$n" "--no-trace-proposals --num-spec $N --runs-root $root") && "
      else
        cmd+="$(persistent_cmd "$ds" strict '' "$n" "--num-spec $N --runs-root $root") && "
        cmd+="$(persistent_cmd "$ds" spec_casc_tok 0.8 "$n" "--num-spec $N --runs-root $root") && "
      fi
    done
    cmd+="python3 cascade/analysis/timing_report.py --dataset $ds --runs-root $roots --num-spec $specs --out cascade/results/nspec_$ds.md"
    run_or_submit "$cmd" "8:00:00" ;;
  E5-*) ds=$(dataset_of); campaign "$ds" "spec_casc_diff spec_casc_chow" "${CASES:-30}" ;;
  E1F-*)
    # Fine low-alpha sweep with 3 seeds: where exactly does inflation begin?
    # (E1-aime24 quick look: clean at 0.15, inflating from 0.35.) Persistent
    # servers, one per (arm, seed).
    ds=$(dataset_of); n="${CASES:-30}"; cmd=""
    for m in spec_casc_tok_lt spec_casc_tok; do
      for a in 0.05 0.1 0.15 0.2 0.25; do
        cmd+="$(persistent_cmd "$ds" "$m" "$a" "$n" "--seeds 0 1 2") && "
      done
    done
    cmd+="$(persistent_cmd "$ds" strict '' "$n" "--seeds 0 1 2")"
    cmd+=" && $REPORT_PY scripts/campaign_report.py --dataset $ds --calibration-json campaign/calibration/${ds}_fine.json --tables-out campaign/tables/${ds}_fine.csv --results-out campaign/results/${ds}_fine.csv --graph-out campaign/graphs/${ds}_fine.png --accuracy-graph-out campaign/graphs/${ds}_fine_accuracy.png && python3 cascade/analysis/speed_ignoring_accuracy.py"
    DS="$ds" python3 - > "campaign/calibration/${ds}_fine.json" <<'EOF'
import json, os
print(json.dumps({"dataset": os.environ["DS"], "note": "fine low-alpha sweep, 3 seeds, persistent servers",
                  "chosen_alphas": {m: [0.05, 0.1, 0.15, 0.2, 0.25] for m in ("spec_casc_tok_lt", "spec_casc_tok")}}, indent=2))
EOF
    run_or_submit "$cmd" ;;
  E1P-*)
    # "Proper" protocol, the AIME24 one applied to any benchmark: tok_lt and
    # tok at alpha 0.15/0.20/0.25, seeds 0/1/2, strict x 3 seeds; persistent
    # servers (21 per dataset). Case counts follow the campaign where the
    # generation time allows, else 30 problems (aime24's); time limits from
    # the campaign's measured per-answer times (JOURNAL 2026-09-14).
    ds=$(dataset_of)
    case "$ds" in
      gsm8k)         dn=150; hours="8:00:00" ;;
      humaneval)     dn=150; hours="12:00:00" ;;
      mtbench)       dn=80;  hours="10:00:00" ;;
      livecodebench) dn=90;  hours="20:00:00" ;;
      longbench_v2)  dn=30;  hours="20:00:00" ;;
      *)             dn=30;  hours="12:00:00" ;;
    esac
    n="${CASES:-$dn}"; cmd=""
    for m in spec_casc_tok_lt spec_casc_tok; do
      for a in 0.15 0.2 0.25; do
        cmd+="$(persistent_cmd "$ds" "$m" "$a" "$n" "--seeds 0 1 2") && "
      done
    done
    cmd+="$(persistent_cmd "$ds" strict '' "$n" "--seeds 0 1 2")"
    cmd+=" && $REPORT_PY scripts/campaign_report.py --dataset $ds --calibration-json campaign/calibration/${ds}_proper.json --tables-out campaign/tables/${ds}_proper.csv --results-out campaign/results/${ds}_proper.csv --graph-out campaign/graphs/${ds}_proper.png --accuracy-graph-out campaign/graphs/${ds}_proper_accuracy.png && python3 cascade/analysis/speed_ignoring_accuracy.py && cat campaign/results/${ds}_proper.csv"
    DS="$ds" python3 - > "campaign/calibration/${ds}_proper.json" <<'EOF'
import json, os
print(json.dumps({"dataset": os.environ["DS"], "note": "proper protocol: alpha 0.15/0.2/0.25, 3 seeds, persistent servers",
                  "chosen_alphas": {m: [0.15, 0.2, 0.25] for m in ("spec_casc_tok_lt", "spec_casc_tok")}}, indent=2))
EOF
    run_or_submit "$cmd" "$hours" ;;
  E6-*)
    # Head widths 0.15/0.35 (was 0.5/0.8): the E1-aime24 quick look showed
    # any head wider than ~0.2 x top-1 already inflates on long reasoning.
    ds=$(dataset_of); n="${CASES:-30}"; cmd=""
    for beta in 0.15 0.35; do
      for a in $(grid_for spec_casc_opt); do
        if [[ "$MODE" == "fresh" ]]; then
          cmd+="$(fresh_cmd "$ds" spec_casc_opt_head "$a" "$n" "--no-trace-proposals --spec-casc-opt-head-beta $beta") && "
        else
          cmd+="$(persistent_cmd "$ds" spec_casc_opt_head "$a" "$n" "--spec-casc-opt-head-beta $beta") && "
        fi
      done
    done
    # Report to *_e6.* files: opt_head arms (uncalibrated, beta in the params
    # dir) plus tok_lt/tok at the fine alphas for context (calibrated via the
    # E1F file) plus strict; the campaign's own aime24.* files stay untouched.
    cal="campaign/calibration/${ds}_fine.json"; [[ -f "$cal" ]] || cal="campaign/calibration/${ds}_quick.json"
    cmd+="$REPORT_PY scripts/campaign_report.py --dataset $ds --calibration-json $cal --include-uncalibrated --tables-out campaign/tables/${ds}_e6.csv --results-out campaign/results/${ds}_e6.csv --graph-out campaign/graphs/${ds}_e6.png --accuracy-graph-out campaign/graphs/${ds}_e6_accuracy.png"
    cmd+=" && python3 cascade/analysis/speed_ignoring_accuracy.py && cat campaign/results/${ds}_e6.csv"
    run_or_submit "$cmd" ;;
  E7)
    run_or_submit "python3 cascade/analysis/trace_rank_analysis.py" "0:30:00" ;;
  SAMPLE-*)
    # Smallest real end-to-end run: N cases (default 1) of strict vs
    # spec_casc_tok_lt at alpha 0.55, fresh server each, then print run.json.
    ds=$(dataset_of); n="${CASES:-1}"
    cmd="$(fresh_cmd "$ds" strict '' "$n" --no-trace-proposals) && $(fresh_cmd "$ds" spec_casc_tok_lt 0.55 "$n" --no-trace-proposals)"
    cmd+=" && for f in runs/$ds/strict/strict/case_001/seed_0/run.json runs/$ds/spec_casc_tok_lt/alpha0.55/case_001/seed_0/run.json; do echo \"== \$f\"; python3 -c \"import json,sys; d=json.load(open(sys.argv[1])); print({k: d[k] for k in ('status','output_tokens','draft_rounds','l_bar','finish_reason','wall_time_seconds')})\" \$f; done"
    run_or_submit "$cmd" "1:30:00" ;;
  *) echo "unknown experiment '$EXP' -- see cascade/EXPERIMENTS.md" >&2; exit 2 ;;
esac
