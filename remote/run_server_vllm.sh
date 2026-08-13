#!/usr/bin/env bash
# Start one vLLM server mode for lossy-token-eff.
#
# Ported from the sibling lossy-spec-decode-repetition repo's
# remote/run_server_vllm.sh, generalised from 3 relaxed rules to 5
# (mentored-dec, cactus, spec-casc-opt, r-fuzzy, spec-casc-tok) and renamed
# from "lenience" to "mentored-dec" throughout (see patches/README.md).
set -euo pipefail

MODE="${1:-}"
if [[ "$MODE" != "baseline" && "$MODE" != "strict" && "$MODE" != "lossy" ]]; then
  echo "usage: $0 baseline|strict|lossy" >&2
  exit 2
fi

PYTHON="${PYTHON:-python3}"
python_bin_dir="$(cd "$(dirname "$PYTHON")" && pwd)"
CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
export CUDA_HOME
export PATH="$python_bin_dir:$CUDA_HOME/bin:$PATH"

MODEL_PATH="${MODEL_PATH:-openai/gpt-oss-20b}"
DRAFT_MODEL_PATH="${DRAFT_MODEL_PATH:-nebius/EAGLE3-gpt-oss-20b}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-30000}"
SEED="${SEED:-0}"
NUM_SPEC="${NUM_SPEC:-6}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-65536}"
GPU_UTIL="${GPU_UTIL:-0.85}"

# Lossy knob. One of: mentored_dec, cactus, spec_casc_opt, r_fuzzy,
# spec_casc_tok, r_fuzzy_semantic_guard, synthetic. The first six need the
# matching patch applied (bash patches/apply.sh <method>); synthetic needs no
# patch at all -- it's vLLM's stock rejection_sample_method that accepts at a
# prescribed rate irrespective of p and q.
LOSSY_RULE="${LOSSY_RULE:-synthetic}"
MENTORED_DEC_ALPHA="${MENTORED_DEC_ALPHA:-0.37}"   # Xia et al. Table 2 alpha; lam = 1-alpha
CACTUS_ALPHA="${CACTUS_ALPHA:-0.25}"                # mid-range of the paper's {0.1,0.25,1,10}
SPEC_CASC_ALPHA="${SPEC_CASC_ALPHA:-0.05}"          # matches the paper's own repetition-loop example (Fig. 5)
R_FUZZY_ALPHA="${R_FUZZY_ALPHA:-0.3}"                # Jensen-Shannon divergence threshold
SPEC_CASC_TOK_ALPHA="${SPEC_CASC_TOK_ALPHA:-0.3}"    # NOT the strict point -- see patches/README.md
SPEC_CASC_TOK_ANTILOOP_ALPHA="${SPEC_CASC_TOK_ANTILOOP_ALPHA:-0.3}"  # spec-casc-tok's own alpha; repetition breaker always on
R_FUZZY_GUARD_ALPHA="${R_FUZZY_GUARD_ALPHA:-0.3}"    # r-fuzzy's own alpha; guard override is always on, no separate knob
R_FUZZY_GUARD_V2_ALPHA="${R_FUZZY_GUARD_V2_ALPHA:-0.3}"  # same idea, wider token set -- see patches/README.md
R_FUZZY_WENTROPY_GUARD_ALPHA="${R_FUZZY_WENTROPY_GUARD_ALPHA:-0.3}"  # r-fuzzy's own alpha; entropy-window override always on
SPEC_CASC_TOK_GUARD_ALPHA="${SPEC_CASC_TOK_GUARD_ALPHA:-0.3}"  # spec-casc-tok's own alpha; guard override is always on, no separate knob
SPEC_CASC_TOK_GUARD_V2_ALPHA="${SPEC_CASC_TOK_GUARD_V2_ALPHA:-0.3}"  # spec-casc-tok's own alpha; wider-marker-set guard override always on
SPEC_CASC_TOK_GUARD_AND_ALPHA="${SPEC_CASC_TOK_GUARD_AND_ALPHA:-0.3}"  # spec-casc-tok's own alpha; AND-combination is always on, no separate knob
SPEC_CASC_TOK_FUTURE_GUARD_ALPHA="${SPEC_CASC_TOK_FUTURE_GUARD_ALPHA:-0.3}"  # spec-casc-tok's own alpha
SPEC_CASC_TOK_FUTURE_GUARD_K="${SPEC_CASC_TOK_FUTURE_GUARD_K:-8}"            # strict-window length after an accepted marker
SPEC_CASC_TOK_FUTURE_GUARD_AND_ALPHA="${SPEC_CASC_TOK_FUTURE_GUARD_AND_ALPHA:-0.3}"  # spec-casc-tok's own alpha
SPEC_CASC_TOK_FUTURE_GUARD_AND_K="${SPEC_CASC_TOK_FUTURE_GUARD_AND_K:-8}"            # AND-combined window length after an accepted marker
SPEC_CASC_TOK_FORCE_COMMIT_ALPHA="${SPEC_CASC_TOK_FORCE_COMMIT_ALPHA:-0.3}"  # spec-casc-tok's own alpha; force-commit is always on
SPEC_CASC_TOK_FORCE_COMMIT_THRESHOLD="${SPEC_CASC_TOK_FORCE_COMMIT_THRESHOLD:-28000}"  # tokens before forcing final-channel-open
SPEC_CASC_TOK_SELF_CHECK_ALPHA="${SPEC_CASC_TOK_SELF_CHECK_ALPHA:-0.3}"  # spec-casc-tok's own alpha; periodic self-check always on
SPEC_CASC_TOK_SELF_CHECK_INTERVAL="${SPEC_CASC_TOK_SELF_CHECK_INTERVAL:-3000}"  # tokens between self-checks
SPEC_CASC_TOK_SELF_CHECK_FINAL_THRESHOLD="${SPEC_CASC_TOK_SELF_CHECK_FINAL_THRESHOLD:-28000}"  # "yes" past this forces final instead of pivoting
SPEC_CASC_TOK_FREE_JUDGMENT_ALPHA="${SPEC_CASC_TOK_FREE_JUDGMENT_ALPHA:-0.3}"  # spec-casc-tok's own alpha; free-judgment observation always on
# Fixed to match vllm-0.26.0-free-judgment-model-runner.patch's own
# _FREE_JUDGMENT_CRITERION_PATTERN length -- NOT independently configurable
# here (both python-side halves hardcode the same 23-token pattern; the
# server side only needs its LENGTH, to compute num_speculative_tokens).
FREE_JUDGMENT_CRITERION_LEN=23
SPEC_CASC_TOK_FREE_JUDGMENT_TRACE_PATH="${SPEC_CASC_TOK_FREE_JUDGMENT_TRACE_PATH:-}"  # empty = disabled (no-op observation)
# REJECT-AND-RESAMPLE (redesigned 2026-08-13, replaces the earlier
# fast/slow-EMA pivot mechanism entirely -- see HASHES.txt's own
# "REDESIGN 2026-08-13" entry for the full story). Offline replay against
# the same 6-case rollout traces showed NO transform of the per-round
# p_yes/p_no reading (raw magnitude, boolean p_yes>p_no, windowed SMA,
# hedge-confident) separates "needs it" from "doesn't" -- the one case
# that genuinely needed help had the smallest signal of all six, at every
# reading. So this design stopped trying to discriminate perfectly and
# instead made a false positive cheap: per round, score = p_yes - p_no
# (no EMA, no trend, nothing persisted); crossing THRESHOLD bans only the
# single last real drafted token (same ban-and-renormalize mechanism as
# the criterion token itself), and rejection sampling's own
# residual-resample draws a fresh, genuinely target-favored alternative
# there -- not a forced, unrelated phrase. A false positive now costs one
# resampled token, not a derailing paragraph, so this can safely default
# ON (unlike the old pivot mechanism's unreachable-by-default 1.0).
# Default 0.08 is picked from real-trace resample-rate calibration (the
# cleanest baseline case never exceeds ~1-3% resample rate at this
# threshold; it is NOT a proof of separation -- there isn't one, see
# above). See analysis/semantic_guard/README.md.
SPEC_CASC_TOK_FREE_JUDGMENT_REJECT_THRESHOLD="${SPEC_CASC_TOK_FREE_JUDGMENT_REJECT_THRESHOLD:-0.08}"
SYNTH_LEN="${SYNTH_LEN:-3.0}"

# Every knob file is written in EVERY mode, including baseline and strict, to
# each method's own neutral/strict value -- if one is left over from an
# earlier lossy run, a strict server started afterwards must not silently
# pick it up. This mirrors the sibling repo's discipline exactly (that repo's
# comment: "written in EVERY mode ... if it is left over from an earlier
# lossy run, a strict server started afterwards silently picks up the stale
# factor and the control arm is not a control arm").
#
# Repo-scoped (lossy-token-eff-, not the sibling repo's lossy-spec-decode-
# prefix) so a server from either repo cannot pick up the other's stale knob
# value if both ever run on this box at once.
mentored_dec_file="/tmp/lossy-token-eff-mentored-dec-alpha-$(id -u)"
cactus_file="/tmp/lossy-token-eff-cactus-alpha-$(id -u)"
spec_casc_opt_file="/tmp/lossy-token-eff-spec-casc-alpha-$(id -u)"
r_fuzzy_file="/tmp/lossy-token-eff-r-fuzzy-alpha-$(id -u)"
spec_casc_tok_file="/tmp/lossy-token-eff-spec-casc-tok-alpha-$(id -u)"
spec_casc_tok_antiloop_file="/tmp/lossy-token-eff-spec-casc-tok-antiloop-alpha-$(id -u)"
r_fuzzy_guard_file="/tmp/lossy-token-eff-r-fuzzy-semantic-guard-alpha-$(id -u)"
r_fuzzy_guard_v2_file="/tmp/lossy-token-eff-r-fuzzy-semantic-guard-v2-alpha-$(id -u)"
r_fuzzy_wentropy_guard_file="/tmp/lossy-token-eff-r-fuzzy-window-entropy-guard-alpha-$(id -u)"
spec_casc_tok_guard_file="/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-alpha-$(id -u)"
spec_casc_tok_guard_v2_file="/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-v2-alpha-$(id -u)"
spec_casc_tok_guard_and_file="/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-and-alpha-$(id -u)"
spec_casc_tok_future_guard_file="/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-alpha-$(id -u)"
spec_casc_tok_future_guard_k_file="/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-k-$(id -u)"
spec_casc_tok_future_guard_and_file="/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-and-alpha-$(id -u)"
spec_casc_tok_future_guard_and_k_file="/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-and-k-$(id -u)"
spec_casc_tok_force_commit_file="/tmp/lossy-token-eff-spec-casc-tok-force-commit-alpha-$(id -u)"
spec_casc_tok_force_commit_threshold_file="/tmp/lossy-token-eff-spec-casc-tok-force-commit-threshold-$(id -u)"
spec_casc_tok_self_check_file="/tmp/lossy-token-eff-spec-casc-tok-self-check-alpha-$(id -u)"
spec_casc_tok_self_check_interval_file="/tmp/lossy-token-eff-spec-casc-tok-self-check-interval-$(id -u)"
spec_casc_tok_self_check_final_threshold_file="/tmp/lossy-token-eff-spec-casc-tok-self-check-final-threshold-$(id -u)"
spec_casc_tok_free_judgment_file="/tmp/lossy-token-eff-spec-casc-tok-free-judgment-alpha-$(id -u)"
# Shared by design between both python-side halves (gpu_model_runner.py's
# overwrite and rejection_sampler.py's read/ban) -- see the patches' own
# module comments for why this ONE knob is intentionally not duplicated
# per-file the way every other method's alpha file is.
free_judgment_real_draft_len_file="/tmp/lossy-token-eff-free-judgment-real-draft-len-$(id -u)"
free_judgment_trace_path_file="/tmp/lossy-token-eff-free-judgment-trace-path-$(id -u)"
free_judgment_reject_threshold_file="/tmp/lossy-token-eff-free-judgment-reject-threshold-$(id -u)"

neutralise_all_knobs() {
  # Each method's own "no relaxation" value -- NOT uniformly 0.0. See
  # patches/README.md for why spec-casc-tok in particular needs -inf, not 0.
  printf '%s\n' "0.0"    > "$mentored_dec_file"
  printf '%s\n' "0.0"    > "$cactus_file"
  printf '%s\n' "-inf"   > "$spec_casc_opt_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_file"
  printf '%s\n' "-inf"   > "$spec_casc_tok_file"
  printf '%s\n' "-inf"   > "$spec_casc_tok_antiloop_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_guard_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_guard_v2_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_wentropy_guard_file"
  printf '%s\n' "-inf"   > "$spec_casc_tok_guard_file"
  printf '%s\n' "-inf"   > "$spec_casc_tok_guard_v2_file"
  printf '%s\n' "-inf"   > "$spec_casc_tok_guard_and_file"
  printf '%s\n' "-inf"   > "$spec_casc_tok_future_guard_file"
  printf '%s\n' "0"      > "$spec_casc_tok_future_guard_k_file"  # moot once alpha=-inf, written for cleanliness
  printf '%s\n' "-inf"   > "$spec_casc_tok_future_guard_and_file"
  printf '%s\n' "0"      > "$spec_casc_tok_future_guard_and_k_file"  # moot once alpha=-inf, written for cleanliness
  printf '%s\n' "-inf"   > "$spec_casc_tok_force_commit_file"
  printf '%s\n' "28000"  > "$spec_casc_tok_force_commit_threshold_file"  # moot once alpha=-inf, written for cleanliness
  printf '%s\n' "-inf"   > "$spec_casc_tok_self_check_file"
  printf '%s\n' "3000"   > "$spec_casc_tok_self_check_interval_file"  # moot once alpha=-inf, written for cleanliness
  printf '%s\n' "28000"  > "$spec_casc_tok_self_check_final_threshold_file"  # moot once alpha=-inf, written for cleanliness
  printf '%s\n' "-inf"   > "$spec_casc_tok_free_judgment_file"
  printf '%s\n' "0"      > "$free_judgment_real_draft_len_file"  # 0 = disabled -- CRITICAL: also disables gpu_model_runner.py's overwrite for every other mode, not just this one
  printf '%s\n' ""       > "$free_judgment_trace_path_file"
  printf '%s\n' "0.08"   > "$free_judgment_reject_threshold_file"  # moot once real_draft_len=0, written for cleanliness
}

common_args=(
  --model "$MODEL_PATH"
  --served-model-name gpt-oss-20b
  --host "$HOST"
  --port "$PORT"
  --seed "$SEED"
  --max-model-len "$MAX_MODEL_LEN"
  --gpu-memory-utilization "$GPU_UTIL"
  # Paper setup: single generation job, no TP/PP/DP/FSDP.
  --tensor-parallel-size 1
  --pipeline-parallel-size 1
  # REQUIRED, not optional. With prefix caching on, a request that reuses
  # cached prompt KV takes a different numeric path than one that recomputes
  # it, so the same prompt+seed diverges depending on what ran before it. The
  # sibling repo measured this on case_001: three server instances gave 1686
  # / 1505 / 1640 tokens, and a warm request differed from the cold first
  # request on the same server, while two warm requests were bit-identical.
  # Same failure mode SGLang's radix cache caused there too.
  --no-enable-prefix-caching
)

# draft_sample_method=probabilistic makes the drafter sample stochastically
# and caches its logits, so verification uses a real q. The default is
# greedy, which the nebius model card notes underestimates acceptance at
# temperature > 0.
DRAFT_SAMPLE_METHOD="${DRAFT_SAMPLE_METHOD:-probabilistic}"

# Off by default: only P-EAGLE-style parallel-drafting draft models (e.g.
# amazon/GPT-OSS-20B-P-EAGLE) need this; the default nebius/EAGLE3 drafter is
# autoregressive (one token per forward pass) and does not set this field.
PARALLEL_DRAFTING="${PARALLEL_DRAFTING:-false}"

spec_json() {
  local method="$1"
  local extra="$2"
  printf '{"method":"eagle3","model":"%s","num_speculative_tokens":%s,"rejection_sample_method":"%s","draft_sample_method":"%s","parallel_drafting":%s%s}' \
    "$DRAFT_MODEL_PATH" "$NUM_SPEC" "$method" "$DRAFT_SAMPLE_METHOD" "$PARALLEL_DRAFTING" "$extra"
}

probe_patched() {
  # $1: python attribute name that only exists once the matching patch is
  # applied. Refuses to start rather than silently falling back to strict --
  # the sibling repo's own worst failure mode (a mislabelled null result).
  local attr="$1"
  local result
  result="$("$PYTHON" - "$attr" <<'PY'
import sys
try:
    import vllm.v1.sample.rejection_sampler as v1
    print("yes" if hasattr(v1, sys.argv[1]) else "no")
except Exception:
    print("no")
PY
)"
  [[ "$result" == "yes" ]]
}

case "$MODE" in
  baseline)
    neutralise_all_knobs
    echo "mode=baseline model=$MODEL_PATH port=$PORT seed=$SEED"
    exec "$PYTHON" -m vllm.entrypoints.openai.api_server "${common_args[@]}"
    ;;
  strict)
    # `standard` is probabilistic rejection sampling, min(1, p/q): lossless
    # with respect to the target distribution. Paired with draft_sample,
    # this is the control arm every lossy rule is compared against.
    neutralise_all_knobs
    cfg="$(spec_json standard '')"
    echo "mode=strict draft=$DRAFT_MODEL_PATH k=$NUM_SPEC rule=standard draft_sample=$DRAFT_SAMPLE_METHOD port=$PORT seed=$SEED"
    exec "$PYTHON" -m vllm.entrypoints.openai.api_server "${common_args[@]}" --speculative-config "$cfg"
    ;;
  lossy)
    if [[ "$LOSSY_RULE" == "synthetic" ]]; then
      neutralise_all_knobs
      cfg="$(spec_json synthetic ",\"synthetic_acceptance_length\":$SYNTH_LEN")"
      echo "mode=lossy rule=synthetic draft=$DRAFT_MODEL_PATH k=$NUM_SPEC accept_len=$SYNTH_LEN port=$PORT seed=$SEED"
      exec "$PYTHON" -m vllm.entrypoints.openai.api_server "${common_args[@]}" --speculative-config "$cfg"
    fi

    neutralise_all_knobs
    case "$LOSSY_RULE" in
      mentored_dec)
        printf '%s\n' "$MENTORED_DEC_ALPHA" > "$mentored_dec_file"
        probe_patched "_MENTORED_DEC_ALPHA" || {
          echo "LOSSY_RULE=mentored_dec needs the patch: bash patches/apply.sh mentored_dec" >&2
          exit 5
        }
        echo "mode=lossy rule=mentored_dec alpha=$MENTORED_DEC_ALPHA (via $mentored_dec_file) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      cactus)
        printf '%s\n' "$CACTUS_ALPHA" > "$cactus_file"
        probe_patched "_CACTUS_ALPHA" || {
          echo "LOSSY_RULE=cactus needs the patch: bash patches/apply.sh cactus" >&2
          exit 5
        }
        echo "mode=lossy rule=cactus alpha=$CACTUS_ALPHA (via $cactus_file) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_opt)
        printf '%s\n' "$SPEC_CASC_ALPHA" > "$spec_casc_opt_file"
        probe_patched "_SPEC_CASC_ALPHA" || {
          echo "LOSSY_RULE=spec_casc_opt needs the patch: bash patches/apply.sh spec_casc_opt" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_opt alpha=$SPEC_CASC_ALPHA (via $spec_casc_opt_file) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      r_fuzzy)
        printf '%s\n' "$R_FUZZY_ALPHA" > "$r_fuzzy_file"
        probe_patched "_R_FUZZY_ALPHA" || {
          echo "LOSSY_RULE=r_fuzzy needs the patch: bash patches/apply.sh r_fuzzy" >&2
          exit 5
        }
        echo "mode=lossy rule=r_fuzzy alpha=$R_FUZZY_ALPHA (via $r_fuzzy_file) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok)
        printf '%s\n' "$SPEC_CASC_TOK_ALPHA" > "$spec_casc_tok_file"
        probe_patched "_SPEC_CASC_TOK_ALPHA" || {
          echo "LOSSY_RULE=spec_casc_tok needs the patch: bash patches/apply.sh spec_casc_tok" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok alpha=$SPEC_CASC_TOK_ALPHA (via $spec_casc_tok_file) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_antiloop)
        printf '%s\n' "$SPEC_CASC_TOK_ANTILOOP_ALPHA" > "$spec_casc_tok_antiloop_file"
        # _ANTILOOP_HISTORY, not _SPEC_CASC_TOK_ALPHA: the latter is defined
        # by every spec-casc-tok-family patch, so it wouldn't disambiguate
        # this variant from plain spec-casc-tok or any guard; the
        # persistent history dict is genuinely unique to this patch.
        probe_patched "_ANTILOOP_HISTORY" || {
          echo "LOSSY_RULE=spec_casc_tok_antiloop needs the patch: bash patches/apply.sh spec-casc-tok-antiloop" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_antiloop alpha=$SPEC_CASC_TOK_ANTILOOP_ALPHA (via $spec_casc_tok_antiloop_file, reactive repetition breaker always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      r_fuzzy_semantic_guard)
        printf '%s\n' "$R_FUZZY_GUARD_ALPHA" > "$r_fuzzy_guard_file"
        # _SEMANTIC_GUARD_TOKEN_IDS, not _R_FUZZY_ALPHA: both r-fuzzy patches
        # define the latter, so probing it wouldn't catch plain r-fuzzy
        # being installed instead of this variant.
        probe_patched "_SEMANTIC_GUARD_TOKEN_IDS" || {
          echo "LOSSY_RULE=r_fuzzy_semantic_guard needs the patch: bash patches/apply.sh r-fuzzy-semantic-guard" >&2
          exit 5
        }
        echo "mode=lossy rule=r_fuzzy_semantic_guard alpha=$R_FUZZY_GUARD_ALPHA (via $r_fuzzy_guard_file, hesitation-marker override always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      r_fuzzy_semantic_guard_v2)
        printf '%s\n' "$R_FUZZY_GUARD_V2_ALPHA" > "$r_fuzzy_guard_v2_file"
        # _SEMANTIC_GUARD_TOKEN_IDS also exists in v1's module -- disambiguate
        # by the guard-set SIZE (v2's is 35 ids, v1's is 18), the one thing
        # that differs at the module-attribute level between the two.
        result="$("$PYTHON" - <<'PY'
import vllm.v1.sample.rejection_sampler as v1
print(len(getattr(v1, "_SEMANTIC_GUARD_TOKEN_IDS", ())))
PY
)"
        if [[ "$result" != "35" ]]; then
          echo "LOSSY_RULE=r_fuzzy_semantic_guard_v2 needs the v2 patch (got guard_token_ids=$result, want 35): bash patches/apply.sh r-fuzzy-semantic-guard-v2" >&2
          exit 5
        fi
        echo "mode=lossy rule=r_fuzzy_semantic_guard_v2 alpha=$R_FUZZY_GUARD_V2_ALPHA (via $r_fuzzy_guard_v2_file, wider hesitation/connective override always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      r_fuzzy_window_entropy_guard)
        printf '%s\n' "$R_FUZZY_WENTROPY_GUARD_ALPHA" > "$r_fuzzy_wentropy_guard_file"
        # _window_entropy_target_history only exists in this variant's module.
        probe_patched "_window_entropy_target_history" || {
          echo "LOSSY_RULE=r_fuzzy_window_entropy_guard needs the patch: bash patches/apply.sh r-fuzzy-window-entropy-guard" >&2
          exit 5
        }
        echo "mode=lossy rule=r_fuzzy_window_entropy_guard alpha=$R_FUZZY_WENTROPY_GUARD_ALPHA (via $r_fuzzy_wentropy_guard_file, rolling-32 entropy override always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_semantic_guard)
        printf '%s\n' "$SPEC_CASC_TOK_GUARD_ALPHA" > "$spec_casc_tok_guard_file"
        # _SEMANTIC_GUARD_TOKEN_IDS, not _SPEC_CASC_TOK_ALPHA: plain
        # spec_casc_tok also defines the latter, so probing it wouldn't catch
        # plain spec_casc_tok being installed instead of this variant.
        probe_patched "_SEMANTIC_GUARD_TOKEN_IDS" || {
          echo "LOSSY_RULE=spec_casc_tok_semantic_guard needs the patch: bash patches/apply.sh spec-casc-tok-semantic-guard" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_semantic_guard alpha=$SPEC_CASC_TOK_GUARD_ALPHA (via $spec_casc_tok_guard_file, hesitation-marker override always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_semantic_guard_v2)
        printf '%s\n' "$SPEC_CASC_TOK_GUARD_V2_ALPHA" > "$spec_casc_tok_guard_v2_file"
        # _SPEC_CASC_TOK_GUARD_V2_ALPHA_FILE, not _SEMANTIC_GUARD_TOKEN_IDS:
        # v2 shares that name with plain spec-casc-tok-semantic-guard (same
        # variable, different token set), so probing it wouldn't disambiguate
        # which one is actually installed -- this variant's own alpha-file-
        # path constant is unique instead.
        probe_patched "_SPEC_CASC_TOK_GUARD_V2_ALPHA_FILE" || {
          echo "LOSSY_RULE=spec_casc_tok_semantic_guard_v2 needs the patch: bash patches/apply.sh spec-casc-tok-semantic-guard-v2" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_semantic_guard_v2 alpha=$SPEC_CASC_TOK_GUARD_V2_ALPHA (via $spec_casc_tok_guard_v2_file, wider-marker-set override always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_semantic_guard_and)
        printf '%s\n' "$SPEC_CASC_TOK_GUARD_AND_ALPHA" > "$spec_casc_tok_guard_and_file"
        # _SPEC_CASC_TOK_GUARD_AND_ALPHA_FILE, not _SEMANTIC_GUARD_TOKEN_IDS:
        # both spec-casc-tok-semantic-guard variants (override and AND)
        # define the latter with the same 18 ids, so probing it wouldn't
        # disambiguate which one is actually installed.
        probe_patched "_SPEC_CASC_TOK_GUARD_AND_ALPHA_FILE" || {
          echo "LOSSY_RULE=spec_casc_tok_semantic_guard_and needs the patch: bash patches/apply.sh spec-casc-tok-semantic-guard-and" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_semantic_guard_and alpha=$SPEC_CASC_TOK_GUARD_AND_ALPHA (via $spec_casc_tok_guard_and_file, AND-combined hesitation-marker guard always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_semantic_guard_future_guard)
        printf '%s\n' "$SPEC_CASC_TOK_FUTURE_GUARD_ALPHA" > "$spec_casc_tok_future_guard_file"
        printf '%s\n' "$SPEC_CASC_TOK_FUTURE_GUARD_K" > "$spec_casc_tok_future_guard_k_file"
        # _FUTURE_GUARD_STATE, not _SEMANTIC_GUARD_TOKEN_IDS: this is the one
        # attribute genuinely unique to this variant (the other two guards
        # share the 18-id set's name, and this one has its own wider set
        # anyway, but _FUTURE_GUARD_STATE is the clearest, most direct probe
        # for "is this specifically the future-guard variant installed").
        probe_patched "_FUTURE_GUARD_STATE" || {
          echo "LOSSY_RULE=spec_casc_tok_semantic_guard_future_guard needs the patch: bash patches/apply.sh spec-casc-tok-semantic-guard-future-guard" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_semantic_guard_future_guard alpha=$SPEC_CASC_TOK_FUTURE_GUARD_ALPHA k=$SPEC_CASC_TOK_FUTURE_GUARD_K (via $spec_casc_tok_future_guard_file, $spec_casc_tok_future_guard_k_file) draft=$DRAFT_MODEL_PATH k_spec=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_semantic_guard_future_guard_and)
        printf '%s\n' "$SPEC_CASC_TOK_FUTURE_GUARD_AND_ALPHA" > "$spec_casc_tok_future_guard_and_file"
        printf '%s\n' "$SPEC_CASC_TOK_FUTURE_GUARD_AND_K" > "$spec_casc_tok_future_guard_and_k_file"
        # _SPEC_CASC_TOK_GUARD_FUTURE_AND_ALPHA_FILE, not _FUTURE_GUARD_STATE:
        # both future-guard variants (raw-strict and AND) share the
        # _FUTURE_GUARD_STATE name (same window-carryover mechanism, only the
        # in-window accept test differs), so probing it wouldn't
        # disambiguate which one is actually installed -- this variant's own
        # alpha-file-path constant is unique instead.
        probe_patched "_SPEC_CASC_TOK_GUARD_FUTURE_AND_ALPHA_FILE" || {
          echo "LOSSY_RULE=spec_casc_tok_semantic_guard_future_guard_and needs the patch: bash patches/apply.sh spec-casc-tok-semantic-guard-future-guard-and" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_semantic_guard_future_guard_and alpha=$SPEC_CASC_TOK_FUTURE_GUARD_AND_ALPHA k=$SPEC_CASC_TOK_FUTURE_GUARD_AND_K (via $spec_casc_tok_future_guard_and_file, $spec_casc_tok_future_guard_and_k_file) draft=$DRAFT_MODEL_PATH k_spec=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_force_commit)
        printf '%s\n' "$SPEC_CASC_TOK_FORCE_COMMIT_ALPHA" > "$spec_casc_tok_force_commit_file"
        printf '%s\n' "$SPEC_CASC_TOK_FORCE_COMMIT_THRESHOLD" > "$spec_casc_tok_force_commit_threshold_file"
        # _FORCE_COMMIT_STATE, not _SPEC_CASC_TOK_ALPHA: the latter is
        # defined by every spec-casc-tok-family patch, so it wouldn't
        # disambiguate this variant from plain spec-casc-tok, antiloop, or
        # any guard; the persistent force-commit state dict is genuinely
        # unique to this patch.
        probe_patched "_FORCE_COMMIT_STATE" || {
          echo "LOSSY_RULE=spec_casc_tok_force_commit needs the patch: bash patches/apply.sh spec-casc-tok-force-commit" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_force_commit alpha=$SPEC_CASC_TOK_FORCE_COMMIT_ALPHA threshold=$SPEC_CASC_TOK_FORCE_COMMIT_THRESHOLD (via $spec_casc_tok_force_commit_file, $spec_casc_tok_force_commit_threshold_file, reactive budget-exhaustion breaker always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_self_check)
        printf '%s\n' "$SPEC_CASC_TOK_SELF_CHECK_ALPHA" > "$spec_casc_tok_self_check_file"
        printf '%s\n' "$SPEC_CASC_TOK_SELF_CHECK_INTERVAL" > "$spec_casc_tok_self_check_interval_file"
        printf '%s\n' "$SPEC_CASC_TOK_SELF_CHECK_FINAL_THRESHOLD" > "$spec_casc_tok_self_check_final_threshold_file"
        # _SELF_CHECK_STATE, not _SPEC_CASC_TOK_ALPHA: the latter is defined
        # by every spec-casc-tok-family patch, so it wouldn't disambiguate
        # this variant from plain spec-casc-tok, antiloop, force-commit, or
        # any guard; the persistent self-check state dict is genuinely
        # unique to this patch.
        probe_patched "_SELF_CHECK_STATE" || {
          echo "LOSSY_RULE=spec_casc_tok_self_check needs the patch: bash patches/apply.sh spec-casc-tok-self-check" >&2
          exit 5
        }
        echo "mode=lossy rule=spec_casc_tok_self_check alpha=$SPEC_CASC_TOK_SELF_CHECK_ALPHA interval=$SPEC_CASC_TOK_SELF_CHECK_INTERVAL final_threshold=$SPEC_CASC_TOK_SELF_CHECK_FINAL_THRESHOLD (via $spec_casc_tok_self_check_file, $spec_casc_tok_self_check_interval_file, $spec_casc_tok_self_check_final_threshold_file, periodic self-assessment always on) draft=$DRAFT_MODEL_PATH k=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      spec_casc_tok_free_judgment)
        printf '%s\n' "$SPEC_CASC_TOK_FREE_JUDGMENT_ALPHA" > "$spec_casc_tok_free_judgment_file"
        printf '%s\n' "$NUM_SPEC" > "$free_judgment_real_draft_len_file"
        printf '%s\n' "$SPEC_CASC_TOK_FREE_JUDGMENT_TRACE_PATH" > "$free_judgment_trace_path_file"
        printf '%s\n' "$SPEC_CASC_TOK_FREE_JUDGMENT_REJECT_THRESHOLD" > "$free_judgment_reject_threshold_file"
        # _FREE_JUDGMENT_STATE, not _SPEC_CASC_TOK_ALPHA: the latter is
        # defined by every spec-casc-tok-family patch, so it wouldn't
        # disambiguate this variant from plain spec-casc-tok or any other
        # sibling; the free-judgment state dict is genuinely unique.
        probe_patched "_FREE_JUDGMENT_STATE" || {
          echo "LOSSY_RULE=spec_casc_tok_free_judgment needs the patch: bash patches/apply.sh spec-casc-tok-free-judgment" >&2
          exit 5
        }
        # CRITICAL: bump num_speculative_tokens up by the criterion's own
        # length so every downstream fixed-size structure (draft_token_ids_cpu,
        # the CUDA graph uniform-decode specialization) sizes itself for the
        # true per-round width from the start -- see
        # vllm-0.26.0-free-judgment-model-runner.patch's own module comment
        # for why padding the OUTPUT of a smaller propose() call afterward
        # does not work instead. NUM_SPEC itself (the "real" draft length
        # written to free_judgment_real_draft_len_file above) is captured
        # BEFORE this reassignment.
        NUM_SPEC=$((NUM_SPEC + FREE_JUDGMENT_CRITERION_LEN))
        echo "mode=lossy rule=spec_casc_tok_free_judgment alpha=$SPEC_CASC_TOK_FREE_JUDGMENT_ALPHA real_draft_len=$(($NUM_SPEC - FREE_JUDGMENT_CRITERION_LEN)) criterion_len=$FREE_JUDGMENT_CRITERION_LEN trace=${SPEC_CASC_TOK_FREE_JUDGMENT_TRACE_PATH:-<disabled>} reject_threshold=$SPEC_CASC_TOK_FREE_JUDGMENT_REJECT_THRESHOLD (via $spec_casc_tok_free_judgment_file, $free_judgment_real_draft_len_file, $free_judgment_trace_path_file, $free_judgment_reject_threshold_file -- reject-and-resample: per-round score=p_yes-p_no crossing threshold bans only the last real drafted token, rejection sampling resamples a fresh alternative there) draft=$DRAFT_MODEL_PATH k_total=$NUM_SPEC port=$PORT seed=$SEED"
        ;;
      *)
        echo "unknown LOSSY_RULE=$LOSSY_RULE (want: mentored_dec|cactus|spec_casc_opt|r_fuzzy|spec_casc_tok|spec_casc_tok_antiloop|r_fuzzy_semantic_guard|r_fuzzy_semantic_guard_v2|r_fuzzy_window_entropy_guard|spec_casc_tok_semantic_guard|spec_casc_tok_semantic_guard_v2|spec_casc_tok_semantic_guard_and|spec_casc_tok_semantic_guard_future_guard|spec_casc_tok_semantic_guard_future_guard_and|spec_casc_tok_force_commit|spec_casc_tok_self_check|spec_casc_tok_free_judgment|synthetic)" >&2
        exit 2
        ;;
    esac
    cfg="$(spec_json standard '')"
    exec "$PYTHON" -m vllm.entrypoints.openai.api_server "${common_args[@]}" --speculative-config "$cfg"
    ;;
esac
