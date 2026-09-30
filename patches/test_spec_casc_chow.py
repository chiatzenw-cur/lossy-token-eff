#!/usr/bin/env python3
"""Acceptance test for the spec-casc-chow patch (Chow's rule, Narasimhan et
al. Eq. 2: defer iff max q < 1 - alpha). Run by patches/apply.sh. Kernel
check imported from test_spec_casc_opt.py (byte-identical kernel hunk)."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

from test_spec_casc_opt import test_kernel_obeys_defer_mask  # same kernel hunk

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-chow-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"
READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({"alpha": m._SPEC_CASC_CHOW_ALPHA, "path": m._SPEC_CASC_CHOW_ALPHA_FILE}))
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
        ALPHA_FILE.write_text("0.5\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.5 and got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.5")
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
    """CPU-only: defer iff max q < 1 - alpha; the verifier never enters."""
    import torch

    draft_probs = torch.tensor([[0.70, 0.10, 0.10, 0.10], [0.40, 0.20, 0.20, 0.20], [0.97, 0.01, 0.01, 0.01]])
    draft_max = draft_probs.max(dim=-1).values  # 0.70, 0.40, 0.97
    for alpha, expected in (
        (float("-inf"), [True, True, True]),
        (0.0, [True, True, True]),      # threshold 1.0: only a one-hot drafter is trusted
        (0.05, [True, True, False]),    # threshold 0.95
        (0.5, [False, True, False]),    # threshold 0.5
        (0.7, [False, False, False]),   # threshold 0.3
        (1.0, [False, False, False]),   # threshold 0: never defer
    ):
        got = (draft_max < (1.0 - alpha)).tolist()
        assert got == expected, (alpha, got, expected)
        print(f"  ok  alpha={alpha}: defer={got}")


def main() -> int:
    failures = 0
    for test in (test_alpha_plumbing, test_defer_formula, test_kernel_obeys_defer_mask):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-chow patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
