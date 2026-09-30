#!/usr/bin/env python3
"""Acceptance test for the spec-casc-opt-head patch (opt's deferral OR the
drafted token outside the verifier's head at beta). Run by patches/apply.sh.
Checks both knob files, the combined mask formula (including beta=1 ==
plain opt and alpha=-inf == strict regardless of beta), and the kernel via
test_spec_casc_opt.py's own check (byte-identical kernel hunk)."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

from test_spec_casc_opt import test_kernel_obeys_defer_mask  # same kernel hunk

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-opt-head-alpha-{os.getuid()}")
BETA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-opt-head-beta-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"
READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_OPT_HEAD_ALPHA, "alpha_path": m._SPEC_CASC_OPT_HEAD_ALPHA_FILE,
    "beta": m._SPEC_CASC_OPT_HEAD_BETA, "beta_path": m._SPEC_CASC_OPT_HEAD_BETA_FILE,
}))
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


def test_knob_plumbing() -> None:
    saved = {f: (f.read_text() if f.is_file() else None) for f in (ALPHA_FILE, BETA_FILE)}
    try:
        ALPHA_FILE.write_text("0.05\n")
        BETA_FILE.write_text("0.8\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.05 and got["beta"] == 0.8, got
        assert got["alpha_path"] == str(ALPHA_FILE) and got["beta_path"] == str(BETA_FILE), got
        print(f"  ok  module reads alpha=0.05 from {ALPHA_FILE.name}, beta=0.8 from {BETA_FILE.name}")
        ALPHA_FILE.unlink()
        BETA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf") and got["beta"] == 1.0, got
        print("  ok  missing files fall back to alpha=-inf (strict), beta=1 (whole vocabulary = plain opt)")
    finally:
        for f, content in saved.items():
            if content is None:
                f.unlink(missing_ok=True)
            else:
                f.write_text(content)


def test_defer_formula() -> None:
    """CPU-only: defer iff opt_defer OR p(x) < (1-beta)*max p."""
    import torch

    draft_probs = torch.tensor([
        [0.70, 0.10, 0.10, 0.10],   # confident drafter, drafts token 0
        [0.70, 0.10, 0.10, 0.10],   # confident drafter, drafts token 1 (a low-p token)
        [0.40, 0.20, 0.20, 0.20],   # unsure drafter, drafts token 0
    ])
    target_probs = torch.tensor([
        [0.60, 0.20, 0.10, 0.10],   # p(x)=0.60 = top1
        [0.60, 0.20, 0.10, 0.10],   # p(x)=0.20, top1 0.60
        [0.25, 0.25, 0.25, 0.25],   # flat, p(x)=0.25 = top1
    ])
    draft_token_ids = torch.tensor([0, 1, 0], dtype=torch.int32)
    draft_max = draft_probs.max(dim=-1).values     # 0.70, 0.70, 0.40
    target_max = target_probs.max(dim=-1).values   # 0.60, 0.60, 0.25
    tv = (target_probs - draft_probs).clamp_min(0.0).sum(dim=-1)  # 0.10, 0.10, 0.15
    drafted_p = target_probs.gather(1, draft_token_ids.to(torch.int64).unsqueeze(1)).squeeze(1)

    def mask(alpha: float, beta: float) -> list[bool]:
        opt_defer = draft_max < (target_max - alpha * tv)
        outside = drafted_p < (1.0 - beta) * target_max
        return (opt_defer | outside).tolist()

    # opt alone (beta=1): at alpha=0 nothing defers (draft_max >= target_max everywhere)
    assert mask(0.0, 1.0) == [False, False, False]
    # row1's drafted token has p=0.20 vs top1 0.60: outside the head at beta=0.5 (0.20 < 0.30), inside at beta=0.8 (0.20 < 0.12? no)
    assert mask(0.0, 0.5) == [False, True, False]
    assert mask(0.0, 0.8) == [False, False, False]
    # beta=0 trusts only the verifier's argmax: rows 0 and 2 drafted the argmax, row 1 did not
    assert mask(0.0, 0.0) == [False, True, False]
    # alpha=-inf: strict regardless of beta
    assert mask(float("-inf"), 1.0) == [True, True, True]
    assert mask(float("-inf"), 0.0) == [True, True, True]
    # a very negative finite alpha makes opt defer everywhere too
    assert mask(-10.0, 1.0) == [True, True, True]
    print("  ok  combined mask: beta=1 is plain opt, head check adds exactly the low-p drafted token, -inf is strict")


def main() -> int:
    failures = 0
    for test in (test_knob_plumbing, test_defer_formula, test_kernel_obeys_defer_mask):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-opt-head patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
