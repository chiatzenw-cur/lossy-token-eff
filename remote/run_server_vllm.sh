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
R_FUZZY_GUARD_ALPHA="${R_FUZZY_GUARD_ALPHA:-0.3}"    # r-fuzzy's own alpha; guard override is always on, no separate knob
R_FUZZY_GUARD_V2_ALPHA="${R_FUZZY_GUARD_V2_ALPHA:-0.3}"  # same idea, wider token set -- see patches/README.md
R_FUZZY_WENTROPY_GUARD_ALPHA="${R_FUZZY_WENTROPY_GUARD_ALPHA:-0.3}"  # r-fuzzy's own alpha; entropy-window override always on
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
r_fuzzy_guard_file="/tmp/lossy-token-eff-r-fuzzy-semantic-guard-alpha-$(id -u)"
r_fuzzy_guard_v2_file="/tmp/lossy-token-eff-r-fuzzy-semantic-guard-v2-alpha-$(id -u)"
r_fuzzy_wentropy_guard_file="/tmp/lossy-token-eff-r-fuzzy-window-entropy-guard-alpha-$(id -u)"

neutralise_all_knobs() {
  # Each method's own "no relaxation" value -- NOT uniformly 0.0. See
  # patches/README.md for why spec-casc-tok in particular needs -inf, not 0.
  printf '%s\n' "0.0"    > "$mentored_dec_file"
  printf '%s\n' "0.0"    > "$cactus_file"
  printf '%s\n' "-inf"   > "$spec_casc_opt_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_file"
  printf '%s\n' "-inf"   > "$spec_casc_tok_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_guard_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_guard_v2_file"
  printf '%s\n' "-inf"   > "$r_fuzzy_wentropy_guard_file"
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
      *)
        echo "unknown LOSSY_RULE=$LOSSY_RULE (want: mentored_dec|cactus|spec_casc_opt|r_fuzzy|spec_casc_tok|r_fuzzy_semantic_guard|r_fuzzy_semantic_guard_v2|r_fuzzy_window_entropy_guard|synthetic)" >&2
        exit 2
        ;;
    esac
    cfg="$(spec_json standard '')"
    exec "$PYTHON" -m vllm.entrypoints.openai.api_server "${common_args[@]}" --speculative-config "$cfg"
    ;;
esac
