#!/usr/bin/env python3
"""Acceptance test for the spec-casc-diff patch (Narasimhan et al. Eq. 5:
defer iff max q < max p - alpha). Run by patches/apply.sh. Same shape as
test_spec_casc_opt.py; the kernel check is imported from it unchanged
because the kernel hunk is byte-identical."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

from test_spec_casc_opt import test_kernel_obeys_defer_mask  # same kernel hunk

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-diff-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"
READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({"alpha": m._SPEC_CASC_DIFF_ALPHA, "path": m._SPEC_CASC_DIFF_ALPHA_FILE}))
"""


def read_back_in_subprocess() -> dict[str, object]:
    import json

    proc = subprocess.run([sys.executable, "-c", READ_BACK, MODULE], capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"import failed:\n{proc.stderr[-3000:]}")
    for line in proc.stdout.splitlines():
        if line.startswith("JSON:"):
            return json.loads(line[5:])
    raise AssertionError(f"no result from subprocess:\n{proc.stdout[-2000:]}")


def test_alpha_plumbing() -> None:
    saved = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("-0.1\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == -0.1 and got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> -0.1")
        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (always defer -> strict spec-dec)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def test_defer_formula() -> None:
    """CPU-only: defer iff max q < max p - alpha, hand-picked rows."""
    import torch

    draft_probs = torch.tensor([[0.70, 0.10, 0.10, 0.10], [0.40, 0.20, 0.20, 0.20]])   # max q: 0.70, 0.40
    target_probs = torch.tensor([[0.10, 0.70, 0.10, 0.10], [0.25, 0.25, 0.25, 0.25]])  # max p: 0.70, 0.25
    draft_max = draft_probs.max(dim=-1).values
    target_max = target_probs.max(dim=-1).values
    for alpha, expected in (
        (float("-inf"), [True, True]),
        (-0.2, [True, True]),    # thresholds 0.90, 0.45: 0.70 < 0.90 T; 0.40 < 0.45 T
        (-0.1, [True, False]),   # thresholds 0.80, 0.35: 0.70 < 0.80 T; 0.40 < 0.35 F
        (0.0, [False, False]),   # 0.70 < 0.70 F; 0.40 < 0.25 F
        (0.5, [False, False]),
    ):
        got = (draft_max < (target_max - alpha)).tolist()
        assert got == expected, (alpha, got, expected)
        print(f"  ok  alpha={alpha}: defer={got}")
    # the TV-scaled rule (opt) and this constant-margin rule differ at the same alpha
    tv = (target_probs - draft_probs).clamp_min(0.0).sum(dim=-1)
    opt = (draft_max < (target_max - (-0.2) * tv)).tolist()
    diff = (draft_max < (target_max + 0.2)).tolist()
    assert opt != diff, "at alpha=-0.2 diff must be stricter than opt on the low-TV row"
    print(f"  ok  alpha=-0.2: opt={opt} vs diff={diff} (diff stricter where TV < 1)")


def main() -> int:
    failures = 0
    for test in (test_alpha_plumbing, test_defer_formula, test_kernel_obeys_defer_mask):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-diff patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
