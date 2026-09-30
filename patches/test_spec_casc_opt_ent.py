#!/usr/bin/env python3
"""Acceptance test for the spec-casc-opt-ent patch. Run by patches/apply.sh.

Same three-part shape as test_spec_casc_opt.py (the patch is spec-casc-opt's
with a different per-token defer mask; the kernel hunk is byte-identical):

1. the alpha value reaches the module through its own /tmp file, and a
   missing file falls back to -inf (every position defers -> strict),
2. the mask FORMULA: defer iff H(q) > H(p) + alpha*TV(p,q), including the
   0*inf -> NaN corner at alpha=-inf on a row where p == q, which the patch
   maps to "defer" -- CPU only, hand-computed entropies,
3. the kernel obeys a supplied defer_mask (defer=True == strict test,
   defer=False == always accept) -- re-run here so this install is verified
   on its own.

(3) needs a GPU and is skipped without one; (1) and (2) are not.
"""

from __future__ import annotations

import math
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-opt-ent-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_OPT_ENT_ALPHA,
    "path": m._SPEC_CASC_OPT_ENT_ALPHA_FILE,
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


def test_alpha_plumbing() -> None:
    saved = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("-0.5\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == -0.5, got
        assert got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> -0.5")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (always defer -> strict spec-dec)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def entropy(row: list[float]) -> float:
    return -sum(v * math.log(v) for v in row if v > 0)


def test_defer_formula() -> None:
    """CPU-only: defer iff H(q) > H(p) + alpha*TV(p,q), exactly as the patch
    computes it, against hand-computed rows."""
    import torch

    # No two rows are permutations of each other: exactly-equal entropies
    # would sit on the alpha=0 boundary, where float32 summation order alone
    # could flip the comparison. Every boundary below has a clear margin.
    q_rows = [
        [0.70, 0.10, 0.10, 0.10],  # H(q) = 0.9404; p below has H(p) = 1.0889, TV 0.10
        [0.40, 0.20, 0.20, 0.20],  # H(q) = 1.3322 vs uniform p: H(p) = ln 4 = 1.3863, TV 0.15
        [0.25, 0.25, 0.25, 0.25],  # p == q: TV 0, entropies identical (same tensor values)
    ]
    p_rows = [
        [0.60, 0.20, 0.10, 0.10],
        [0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25],
    ]
    draft_probs = torch.tensor(q_rows)
    target_probs = torch.tensor(p_rows)

    tv = (target_probs - draft_probs).clamp_min(0.0).sum(dim=-1)
    assert torch.allclose(tv, torch.tensor([0.10, 0.15, 0.0]), atol=1e-6), tv.tolist()
    target_ent = -(target_probs * torch.log(target_probs.clamp_min(1e-10))).sum(dim=-1)
    draft_ent = -(draft_probs * torch.log(draft_probs.clamp_min(1e-10))).sum(dim=-1)
    for i, (q, p) in enumerate(zip(q_rows, p_rows)):
        assert abs(draft_ent[i].item() - entropy(q)) < 1e-5, (i, draft_ent[i].item(), entropy(q))
        assert abs(target_ent[i].item() - entropy(p)) < 1e-5, (i, target_ent[i].item(), entropy(p))
    print(f"  ok  entropies match hand computation: H(q)={[round(v, 4) for v in draft_ent.tolist()]}")

    def mask(alpha: float) -> list[bool]:
        threshold = target_ent + alpha * tv
        return ((draft_ent > threshold) | torch.isnan(threshold)).tolist()

    # Row 0: defer iff 0.9404 > 1.0889 + 0.10*alpha  <=> alpha < -1.485.
    # Row 1: defer iff 1.3322 > 1.3863 + 0.15*alpha  <=> alpha < -0.361.
    # Row 2: TV == 0, entropies equal: never defers at finite alpha (p == q, so
    #        accepting is lossless anyway); NaN at +-inf is mapped to defer.
    for alpha, expected in (
        (float("-inf"), [True, True, True]),  # strict point: every position defers
        (-2.0, [True, True, False]),
        (-1.0, [False, True, False]),
        (-0.3, [False, False, False]),
        (0.0, [False, False, False]),
        (1.0, [False, False, False]),
        (float("inf"), [False, False, True]),  # NaN corner on the p == q row -> defer
    ):
        got = mask(alpha)
        assert got == expected, (alpha, got, expected)
        print(f"  ok  alpha={alpha}: defer={got}")


def test_kernel_obeys_defer_mask() -> None:
    """Drive the V1 verify kernel directly with an explicit defer_mask.
    defer=True must reduce to exactly the strict test u <= p/q; defer=False
    must always accept, regardless of u. Needs a GPU."""
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; kernel test not run")
        return
    from vllm.v1.sample.rejection_sampler import rejection_random_sample_kernel

    device = "cuda"
    vocab, draft_tok, recovered_tok, bonus_tok = 8, 3, 5, 7
    uniform = torch.linspace(0.05, 0.95, 19, device=device, dtype=torch.float32)
    n = uniform.numel()

    def run(ratio: float, defer: bool) -> torch.Tensor:
        draft_probs = torch.full((n, vocab), 0.5 / (vocab - 1), device=device)
        draft_probs[:, draft_tok] = 0.5
        target_probs = torch.full((n, vocab), (1.0 - 0.5 * ratio) / (vocab - 1), device=device)
        target_probs[:, draft_tok] = 0.5 * ratio
        out = torch.full((n, 2), -1, dtype=torch.int32, device=device)
        defer_mask = torch.full((n,), defer, dtype=torch.bool, device=device)
        rejection_random_sample_kernel[(n,)](
            out,
            torch.arange(1, n + 1, dtype=torch.int32, device=device),
            torch.full((n,), draft_tok, dtype=torch.int32, device=device),
            draft_probs.contiguous(),
            target_probs.contiguous(),
            torch.full((n,), bonus_tok, dtype=torch.int32, device=device),
            torch.full((n,), recovered_tok, dtype=torch.int32, device=device),
            uniform,
            torch.zeros(n, dtype=torch.bool, device=device),
            1,  # max_spec_len
            vocab,
            None,  # synthetic_conditional_rates
            defer_mask,
            NO_DRAFT_PROBS=False,
            SYNTHETIC_MODE=False,
        )
        return out.cpu()

    for ratio in (0.1, 0.5, 0.9):
        out = run(ratio, defer=True)
        accepted = out[:, 0] == draft_tok
        expected = uniform.cpu() <= ratio
        assert torch.equal(accepted, expected), (
            f"defer=True ratio={ratio}\n got      {accepted.tolist()}\n expected {expected.tolist()}"
        )
        print(f"  ok  defer=True reduces to the strict test (p/q={ratio})")

    for ratio in (0.01, 0.5, 0.99):
        out = run(ratio, defer=False)
        accepted = out[:, 0] == draft_tok
        assert bool(accepted.all()), f"defer=False ratio={ratio}: not all accepted: {accepted.tolist()}"
        assert torch.equal(out[:, 1], torch.full((n,), bonus_tok, dtype=torch.int32)), (
            "defer=False: accepted draft must be followed by the bonus token"
        )
        print(f"  ok  defer=False always accepts, even at p/q={ratio} across all u")


def main() -> int:
    failures = 0
    for test in (test_alpha_plumbing, test_defer_formula, test_kernel_obeys_defer_mask):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-opt-ent patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
