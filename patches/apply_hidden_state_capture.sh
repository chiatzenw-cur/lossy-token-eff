#!/usr/bin/env bash
# Apply (or verify) the hidden-state capture patch against an installed
# vLLM 0.26.0. Independent of patches/apply.sh: this touches model_runner.py,
# a file NONE of the mutually-exclusive method patches touch, so it composes
# with whichever method is currently applied via apply.sh rather than
# competing with it. Idempotent, same as apply.sh.
#
#   bash patches/apply_hidden_state_capture.sh
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-$(cd "$here/.." && pwd)/.venv-vllm}"
PYTHON="${PYTHON:-$VENV/bin/python}"
HASHES="$here/HASHES.txt"

EXPECT_VERSION="0.26.0"
version="$("$PYTHON" -c 'import vllm; print(vllm.__version__)' 2>/dev/null | cut -d+ -f1 || true)"
if [[ "$version" != "$EXPECT_VERSION" ]]; then
  echo "patches target vLLM $EXPECT_VERSION, found ${version:-none} (python: $PYTHON)" >&2
  exit 1
fi
pkg="$("$PYTHON" -c 'import pathlib, vllm; print(pathlib.Path(vllm.__file__).parent)')"

hash_of() { sha256sum "$1" | cut -d' ' -f1; }
label_for_hash() {
  awk -v h="$2" '$1==h {print $2; found=1} END{if(!found) print ""}' "$HASHES"
}

REL="v1/worker/gpu_model_runner.py"
DST="$pkg/$REL"
TRACE_REL="v1/worker/hidden_state_trace.py"
TRACE_DST="$pkg/$TRACE_REL"

dst_hash="$(hash_of "$DST")"
dst_label="$(label_for_hash x "$dst_hash")"

if [[ "$dst_label" == "hidden-state-capture" ]]; then
  echo "hidden-state-capture already applied to $DST (sha256 matches)"
elif [[ "$dst_label" == "upstream" ]]; then
  echo "applying hidden-state-capture to pristine $REL"
  work="$(mktemp -d)"
  trap 'rm -rf "$work"' EXIT
  mkdir -p "$(dirname "$work/vllm/$REL")"
  cp "$DST" "$work/vllm/$REL"
  patch -p1 -d "$work" < "$here/vllm-0.26.0-hidden-state-capture.patch"
  new_hash="$(hash_of "$work/vllm/$REL")"
  new_label="$(label_for_hash x "$new_hash")"
  if [[ "$new_label" != "hidden-state-capture" ]]; then
    echo "patched result does not match HASHES.txt's recorded hash (got $new_hash) -- refusing to install" >&2
    exit 1
  fi
  # --remove-destination: see patches/apply.sh's identical comment on why
  # (uv hardlinks into ~/.cache/uv/archive-v0; a bare cp would write through it).
  cp --remove-destination "$work/vllm/$REL" "$DST"
  echo "installed hidden-state-capture"
else
  echo "$DST matches no known state (hash $dst_hash) -- reinstall vLLM 0.26.0 fresh, or check HASHES.txt" >&2
  exit 1
fi

if [[ ! -f "$TRACE_DST" ]] || ! cmp -s "$here/hidden_state_trace.py" "$TRACE_DST"; then
  cp "$here/hidden_state_trace.py" "$TRACE_DST"
  echo "installed $TRACE_DST"
fi

test_file="$here/test_hidden_state_capture.py"
if [[ -f "$test_file" ]]; then
  "$PYTHON" "$test_file"
else
  echo "no test file ($test_file not found) -- skipping verification" >&2
fi

cat <<EOF

enable capture by writing a destination path to:
  /tmp/lossy-token-eff-hidden-state-trace-\$(id -u)
leave the file absent/empty to disable (default) -- negligible overhead
either way, but this is meant to be switched on for short diagnostic runs,
not left on for full sweeps (128-dim projection per token is still real
per-request storage). Composes with any method patches/apply.sh has
installed; does not need re-applying when you switch methods.
EOF
