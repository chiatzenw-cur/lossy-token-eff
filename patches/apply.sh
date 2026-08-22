#!/usr/bin/env bash
# Apply (or verify) one relaxed-spec-dec patch against an installed vLLM 0.26.0.
#
#   bash patches/apply.sh <method>
#   method in: cactus, spec-casc-opt, mentored-dec, r-fuzzy, spec-casc-tok
#
# Idempotent: re-running with the same method on an already-patched install
# verifies and exits 0. Refuses to guess if the target file is in neither the
# pristine nor the requested-method's own patched state -- including when a
# DIFFERENT method's patch is currently installed (they all touch the same
# file and are mutually exclusive; only one can be live at a time).
#
# Single dispatcher for all five methods, unlike the sibling repo's one
# apply*.sh-per-method layout: hashes come from HASHES.txt (one manifest,
# not five scripts each hardcoding all the others' hashes to cross-detect
# wrong-arm installs) and the method-to-file/test mapping is a single table
# below. Functionally equivalent safety properties, less duplicated bash.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-$(cd "$here/.." && pwd)/.venv-vllm}"
PYTHON="${PYTHON:-$VENV/bin/python}"
HASHES="$here/HASHES.txt"

METHOD="${1:-}"
case "$METHOD" in
  cactus|spec-casc-opt|mentored-dec|r-fuzzy|spec-casc-tok|spec-casc-tok-antiloop|spec-casc-tok-force-commit|spec-casc-tok-self-check|spec-casc-tok-free-judgment|spec-casc-tok-rv|spec-casc-tok-judge-nudge|r-fuzzy-semantic-guard|r-fuzzy-semantic-guard-v2|r-fuzzy-window-entropy-guard|spec-casc-tok-semantic-guard|spec-casc-tok-semantic-guard-v2|spec-casc-tok-semantic-guard-and|spec-casc-tok-semantic-guard-future-guard|spec-casc-tok-semantic-guard-future-guard-and|spec-casc-tok-hsr-guard) ;;
  *)
    echo "usage: $0 <cactus|spec-casc-opt|mentored-dec|r-fuzzy|spec-casc-tok|spec-casc-tok-antiloop|spec-casc-tok-force-commit|spec-casc-tok-self-check|spec-casc-tok-free-judgment|spec-casc-tok-rv|spec-casc-tok-judge-nudge|r-fuzzy-semantic-guard|r-fuzzy-semantic-guard-v2|r-fuzzy-window-entropy-guard|spec-casc-tok-semantic-guard|spec-casc-tok-semantic-guard-v2|spec-casc-tok-semantic-guard-and|spec-casc-tok-semantic-guard-future-guard|spec-casc-tok-semantic-guard-future-guard-and|spec-casc-tok-hsr-guard>" >&2
    exit 2
    ;;
esac

EXPECT_VERSION="0.26.0"
version="$("$PYTHON" -c 'import vllm; print(vllm.__version__)' 2>/dev/null | cut -d+ -f1 || true)"
if [[ "$version" != "$EXPECT_VERSION" ]]; then
  echo "patches target vLLM $EXPECT_VERSION, found ${version:-none} (python: $PYTHON)" >&2
  echo "the hunks are line-addressed against 0.26.0; re-derive them by hand for another version" >&2
  exit 1
fi
pkg="$("$PYTHON" -c 'import pathlib, vllm; print(pathlib.Path(vllm.__file__).parent)')"
sp="$(dirname "$pkg")"

hash_of() { sha256sum "$1" | cut -d' ' -f1; }
label_for_hash() {  # $1: file basename key in HASHES.txt ("rejection_sampler.py" or "utils"), $2: hash
  awk -v h="$2" '$1==h {print $2; found=1} END{if(!found) print ""}' "$HASHES"
}

V1_REL="v1/sample/rejection_sampler.py"
V2_REL="v1/worker/gpu/spec_decode/rejection_sampler_utils.py"
TRACE_REL="v1/sample/relaxation_trace.py"
V1="$pkg/$V1_REL"
V2="$pkg/$V2_REL"
TRACE_DST="$pkg/$TRACE_REL"

v1_hash="$(hash_of "$V1")"
v1_label="$(label_for_hash x "$v1_hash")"

if [[ "$v1_label" == "$METHOD" ]]; then
  echo "$METHOD already applied to $V1 (sha256 matches)"
elif [[ "$v1_label" == "upstream" ]]; then
  echo "applying $METHOD to pristine $V1_REL"
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT
  mkdir -p "$work/vllm"
  cp "$V1" "$work/vllm/$V1_REL" 2>/dev/null || { mkdir -p "$(dirname "$work/vllm/$V1_REL")"; cp "$V1" "$work/vllm/$V1_REL"; }
  # V2 is now permanently in the consolidated "mentored-dec" (or pristine)
  # state regardless of which V1 method is active -- see the V2 pristine-
  # check block below and HASHES.txt's long comment. mentored-dec's own V1
  # hunk is applied from vllm-0.26.0-mentored-dec-v1only.patch (the V1-only
  # first 131 lines of the original two-file patch) rather than the
  # original combined patch: the original's V2 hunk was written against a
  # PRISTINE V2 file and now always fails, because V2 already carries
  # mentored-dec's contribution baked into the consolidated file --
  # re-applying it is both unnecessary and impossible against the changed
  # base. Discovered 2026-08-20 when a real campaign run's automatic
  # cactus->mentored-dec switch started failing this exact way.
  if [[ "$METHOD" == "mentored-dec" ]]; then
    patch_file="$here/vllm-0.26.0-mentored-dec-v1only.patch"
  else
    patch_file="$here/vllm-0.26.0-$METHOD.patch"
  fi
  patch -p1 -d "$work" < "$patch_file"
  new_v1_hash="$(hash_of "$work/vllm/$V1_REL")"
  new_v1_label="$(label_for_hash x "$new_v1_hash")"
  if [[ "$new_v1_label" != "$METHOD" ]]; then
    echo "patched result does not match HASHES.txt's recorded $METHOD hash (got $new_v1_hash) -- refusing to install" >&2
    exit 1
  fi
  # --remove-destination unlinks first. Without it, cp writes THROUGH the
  # hardlink uv keeps into ~/.cache/uv/archive-v0, silently patching the
  # cached wheel for every other venv (including the sibling repo's) built
  # from it.
  cp --remove-destination "$work/vllm/$V1_REL" "$V1"
  echo "installed $METHOD"
elif [[ -n "$v1_label" ]]; then
  echo "$v1_label is currently applied to $V1, not $METHOD" >&2
  echo "reverse it first: patch -p1 -R -d '$sp' < '$here/vllm-0.26.0-$v1_label.patch'" >&2
  echo "or reinstall vLLM 0.26.0 fresh" >&2
  exit 1
else
  echo "$V1 matches no known state (hash $v1_hash) -- reinstall vLLM 0.26.0 fresh" >&2
  exit 1
fi

# UPDATED 2026-08-20: this used to assume only mentored-dec ever touches
# V2 (true for GPT-OSS-20B) -- Qwen3-8B was found to route through V2
# exclusively, so cactus/spec-casc-opt/r-fuzzy/spec-casc-tok were ported
# into V2 too (consolidated into ONE always-present file under the
# "mentored-dec" hash label, not five separate mutually-exclusive V2
# patch files the way V1 still works -- see HASHES.txt's own long comment
# on this for the full story). V2 no longer changes per-method AT ALL,
# including for mentored-dec itself: "mentored-dec" labeled is now the
# correct, expected V2 state for every method, not a mentored-dec-only
# state. Only a truly unrecognized V2 hash is a real problem.
v2_hash="$(hash_of "$V2")"
v2_label="$(label_for_hash x "$v2_hash")"
if [[ "$v2_label" != "mentored-dec" && "$v2_label" != "upstream" ]]; then
  echo "V2 file ($V2_REL) matches neither the consolidated mentored-dec state nor pristine (label: ${v2_label:-unknown}) -- unexpected" >&2
  exit 1
fi

# Three methods ALSO need gpu_model_runner.py patched (the half that
# overwrites the real sequence's own trailing drafted columns -- see each
# method's own model-runner patch for why this can't be done from
# rejection_sampler.py alone). Same pristine-or-already-correct safety
# check as every other file here, just inlined for these methods rather
# than a fully separate installer script (unlike hidden-state-capture,
# these files are NOT meant to compose with arbitrary other methods --
# each only makes sense together with its own rejection_sampler.py half).
GMR_REL="v1/worker/gpu_model_runner.py"
GMR="$pkg/$GMR_REL"
gmr_label_for_method=""
case "$METHOD" in
  spec-casc-tok-free-judgment) gmr_label_for_method="free-judgment-model-runner" ;;
  spec-casc-tok-rv) gmr_label_for_method="rv-model-runner" ;;
  spec-casc-tok-judge-nudge) gmr_label_for_method="jn-model-runner" ;;
  spec-casc-tok-hsr-guard) gmr_label_for_method="hsr-guard-model-runner" ;;
esac
if [[ -n "$gmr_label_for_method" ]]; then
  gmr_patch_file="$here/vllm-0.26.0-$gmr_label_for_method.patch"
  gmr_hash="$(hash_of "$GMR")"
  gmr_label="$(label_for_hash x "$gmr_hash")"
  if [[ "$gmr_label" == "$gmr_label_for_method" ]]; then
    echo "$gmr_label_for_method already applied to $GMR (sha256 matches)"
  elif [[ "$gmr_label" == "upstream" ]]; then
    echo "applying $gmr_label_for_method to pristine $GMR_REL"
    gmr_work="$(mktemp -d)"
    trap 'rm -rf "$gmr_work"' EXIT
    mkdir -p "$(dirname "$gmr_work/vllm/$GMR_REL")"
    cp "$GMR" "$gmr_work/vllm/$GMR_REL"
    patch -p1 -d "$gmr_work" < "$gmr_patch_file"
    new_gmr_hash="$(hash_of "$gmr_work/vllm/$GMR_REL")"
    new_gmr_label="$(label_for_hash x "$new_gmr_hash")"
    if [[ "$new_gmr_label" != "$gmr_label_for_method" ]]; then
      echo "patched result does not match HASHES.txt's recorded $gmr_label_for_method hash (got $new_gmr_hash) -- refusing to install" >&2
      exit 1
    fi
    cp --remove-destination "$gmr_work/vllm/$GMR_REL" "$GMR"
    echo "installed $gmr_label_for_method"
  else
    echo "$GMR matches no known state (hash $gmr_hash) -- reinstall vLLM 0.26.0 fresh, or reverse whatever is there:" >&2
    echo "  patch -p1 -R -d '$sp' < '$gmr_patch_file'  (if it's this patch)" >&2
    echo "  or: patch -p1 -R -d '$sp' < '$here/vllm-0.26.0-hidden-state-capture.patch'  (if that's what's there instead)" >&2
    exit 1
  fi
else
  # Every OTHER method leaves gpu_model_runner.py untouched -- but don't
  # hard-fail if hidden-state-capture happens to be installed alongside
  # (that one IS meant to compose with any method, including this repo's
  # own methods); only warn if it's something else entirely (e.g. stale
  # model-runner state from a previous session).
  gmr_label_other="$(label_for_hash x "$(hash_of "$GMR")")"
  if [[ "$gmr_label_other" != "hidden-state-capture" && "$gmr_label_other" != "upstream" ]]; then
    echo "note: gpu_model_runner.py is patched as '${gmr_label_other:-unknown}', not upstream/hidden-state-capture -- if that's stale model-runner state from free-judgment/rv/judge-nudge, it's harmless here (disabled by its own knob file being unset for any OTHER method), but consider reversing it with the matching vllm-0.26.0-<label>.patch" >&2
  fi
fi

# The trace module (relaxation_trace.py) is a NEW file, not a modification of
# an existing one, so it's installed with a plain cp (nothing to hardlink-
# corrupt: the destination doesn't exist in a pristine install).
if [[ ! -f "$TRACE_DST" ]] || ! cmp -s "$here/relaxation_trace.py" "$TRACE_DST"; then
  cp "$here/relaxation_trace.py" "$TRACE_DST"
  echo "installed $TRACE_DST"
fi

test_file="$here/test_$(echo "$METHOD" | tr '-' '_').py"
if [[ -f "$test_file" ]]; then
  "$PYTHON" "$test_file"
else
  echo "no test file for $METHOD ($test_file not found) -- skipping verification" >&2
fi

cat <<EOF

select alpha by writing it to:
  mentored-dec:    /tmp/lossy-token-eff-mentored-dec-alpha-\$(id -u)   (alpha in [0,1); 0.0 = strict)
  cactus:          /tmp/lossy-token-eff-cactus-alpha-\$(id -u)         (alpha >= 0; 0.0 = strict)
  spec-casc-opt:   /tmp/lossy-token-eff-spec-casc-alpha-\$(id -u)      (any real; -inf = strict)
  r-fuzzy:         /tmp/lossy-token-eff-r-fuzzy-alpha-\$(id -u)        (any real; -inf = strict)
  spec-casc-tok:   /tmp/lossy-token-eff-spec-casc-tok-alpha-\$(id -u)  (any real; -inf = strict, NOT 0.0)
  spec-casc-tok-antiloop: /tmp/lossy-token-eff-spec-casc-tok-antiloop-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
    (spec-casc-tok's own alpha, PLUS a reactive repetition breaker -- zeroes
    a token's probability the moment it would complete a 3rd consecutive
    periodic repeat (period<=12), before spec-casc-tok's own math runs; no
    separate knob, always on. See the patch's module comment and
    analysis/semantic_guard/README.md)
  r-fuzzy-semantic-guard: /tmp/lossy-token-eff-r-fuzzy-semantic-guard-alpha-\$(id -u) (any real; -inf = strict)
    (r-fuzzy's own alpha, PLUS an always-on hesitation-marker override -- see
    the patch's module comment and analysis/semantic_guard/README.md)
  r-fuzzy-semantic-guard-v2: /tmp/lossy-token-eff-r-fuzzy-semantic-guard-v2-alpha-\$(id -u) (any real; -inf = strict)
    (same idea, wider token set -- see the patch's own module comment for
    the explicit caveat about what that widening trades off)
  r-fuzzy-window-entropy-guard: /tmp/lossy-token-eff-r-fuzzy-window-entropy-guard-alpha-\$(id -u) (any real; -inf = strict)
    (distributional sibling of the two above -- gates on a rolling window of
    target+draft entropy instead of token identity; see the patch's own
    module comment for the calibration and analysis/semantic_guard/README.md)
  spec-casc-tok-semantic-guard: /tmp/lossy-token-eff-spec-casc-tok-semantic-guard-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
    (spec-casc-tok's own alpha, PLUS the same always-on hesitation-marker
    override as r-fuzzy-semantic-guard -- forces the trusted top set empty
    at guarded tokens, provably equal to that method's own alpha=-inf limit;
    see the patch's module comment and analysis/semantic_guard/README.md)
  spec-casc-tok-semantic-guard-v2: /tmp/lossy-token-eff-spec-casc-tok-semantic-guard-v2-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
    (identical mechanism to spec-casc-tok-semantic-guard, but the wider
    35-id/14-word marker set instead of the original 18-id/5-word set --
    see the patch's module comment and analysis/semantic_guard/README.md)
  spec-casc-tok-semantic-guard-and: /tmp/lossy-token-eff-spec-casc-tok-semantic-guard-and-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
    (spec-casc-tok's own alpha, PLUS an AND-combination at guarded tokens --
    accept iff BOTH lossless AND spec-casc-tok's own relaxed test would
    accept -- instead of overriding to pure strict; see the patch's module
    comment for the loophole this closes and analysis/semantic_guard/README.md)
  spec-casc-tok-semantic-guard-future-guard: /tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
                                           /tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-k-\$(id -u) (positive int; default 8 if missing)
    (spec-casc-tok's own alpha, PLUS a K-token strict window that arms the
    moment tok accepts a hesitation/discourse-marker token -- wider 35-id
    set, different trigger shape from the other two guards (gates what
    comes AFTER the marker, not the marker itself); see the patch's module
    comment and analysis/semantic_guard/README.md)
  spec-casc-tok-semantic-guard-future-guard-and: /tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-and-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
                                               /tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-and-k-\$(id -u) (positive int; default 8 if missing)
    (same K-token strict-window trigger as spec-casc-tok-semantic-guard-future-guard,
    but AND-combined inside the window instead of pure strict -- accept iff
    BOTH lossless AND tok's own relaxed test would accept; see the patch's
    module comment and analysis/semantic_guard/README.md)
  spec-casc-tok-force-commit: /tmp/lossy-token-eff-spec-casc-tok-force-commit-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
                             /tmp/lossy-token-eff-spec-casc-tok-force-commit-threshold-\$(id -u) (positive int; default 28000 if missing)
    (spec-casc-tok's own alpha, PLUS a reactive budget-exhaustion breaker for
    the "never commits to a final-channel answer" failure shape -- once
    cumulative emitted tokens cross the threshold without a natural
    final-channel-open, force-completes that exact 6-token boundary one
    token per round via one-hot target_probs; permanently a no-op for the
    rest of the sequence once final has opened, natural or forced. See the
    patch's module comment and analysis/semantic_guard/README.md)
  spec-casc-tok-self-check: /tmp/lossy-token-eff-spec-casc-tok-self-check-alpha-\$(id -u) (any real; -inf = strict, NOT 0.0)
                           /tmp/lossy-token-eff-spec-casc-tok-self-check-interval-\$(id -u) (positive int; default 3000 if missing)
                           /tmp/lossy-token-eff-spec-casc-tok-self-check-final-threshold-\$(id -u) (positive int; default 28000 if missing)
    (spec-casc-tok's own alpha, PLUS a periodic self-assessment -- every
    interval tokens, force-injects a fixed "am I going in circles?"
    question, reads back the model's own unconstrained yes/no, and on
    "yes" force-injects a pivot phrase (or force-commit's final-channel
    push if the budget is nearly exhausted). See the patch's module
    comment and analysis/semantic_guard/README.md)
remote/run_server_vllm.sh writes all ten for every mode (baseline/strict/lossy)
so a stale value from a previous run cannot silently leak into a control arm.
EOF
