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
  cactus|spec-casc-opt|mentored-dec|r-fuzzy|spec-casc-tok|r-fuzzy-semantic-guard|r-fuzzy-semantic-guard-v2|r-fuzzy-window-entropy-guard|spec-casc-tok-semantic-guard) ;;
  *)
    echo "usage: $0 <cactus|spec-casc-opt|mentored-dec|r-fuzzy|spec-casc-tok|r-fuzzy-semantic-guard|r-fuzzy-semantic-guard-v2|r-fuzzy-window-entropy-guard|spec-casc-tok-semantic-guard>" >&2
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
  mkdir -p "$(dirname "$work/vllm/$V2_REL")"
  cp "$V2" "$work/vllm/$V2_REL"
  patch -p1 -d "$work" < "$here/vllm-0.26.0-$METHOD.patch"
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
  if [[ "$METHOD" == "mentored-dec" ]]; then
    cp --remove-destination "$work/vllm/$V2_REL" "$V2"
  fi
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

# Every method except mentored-dec needs no V2 change; confirm V2 is still
# either pristine or (for mentored-dec) correctly patched.
v2_hash="$(hash_of "$V2")"
v2_label="$(label_for_hash x "$v2_hash")"
if [[ "$METHOD" == "mentored-dec" ]]; then
  if [[ "$v2_label" != "mentored-dec" ]]; then
    echo "V2 file ($V2_REL) does not match the recorded mentored-dec hash -- half-patched install" >&2
    exit 1
  fi
elif [[ "$v2_label" != "upstream" ]]; then
  echo "V2 file ($V2_REL) is not pristine (label: ${v2_label:-unknown}) -- $METHOD does not touch it, so this is unexpected" >&2
  exit 1
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
remote/run_server_vllm.sh writes all eight for every mode (baseline/strict/lossy)
so a stale value from a previous run cannot silently leak into a control arm.
EOF
