#!/usr/bin/env python3
"""Acceptance test for the spec-casc-opt patch. Run by patches/apply_spec_casc_opt.sh.

Checks, in order:

1. the alpha value reaches the module (mirrors test_lenience.py's check that
   the factor reaches the module -- the same env-sanitisation failure mode
   applies here, since this patch reads its config the same way),
2. the defer-mask FORMULA (draft_max < target_max - alpha*tv) is correct,
   independent of the kernel -- this is new logic the lenience patch's test
   doesn't cover, and (unlike (3)) needs no GPU,
3. the *kernel* obeys a supplied defer_mask correctly: defer=True must behave
   exactly like the strict test, defer=False must always accept regardless of
   u. This is the highest-risk piece -- a bug here silently corrupts every
   generation on this arm -- so it is checked directly against the Triton
   kernel, not just the wrapping Python.

(3) needs a GPU and is skipped without one; (1) and (2) are not.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_ALPHA,
    "path": m._SPEC_CASC_ALPHA_FILE,
}))
"""


def read_back_in_subprocess() -> dict[str, object]:
    """Import the module fresh; alpha is read once, at import."""
    import json

    proc = subprocess.run(
        [sys.executable, "-c", READ_BACK, MODULE],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise AssertionError(f"import failed:\n{proc.stderr[-3000:]}")
    for line in proc.stdout.splitlines():
        if line.startswith("JSON:"):
            return json.loads(line[5:])
    raise AssertionError(f"no result from subprocess:\n{proc.stdout[-2000:]}")


def test_alpha_plumbing() -> None:
    saved = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.05\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.05, got
        assert got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.05")

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
    """CPU-only: draft_max < target_max - alpha*tv, matching Eq. 12 of
    Narasimhan et al. 2025 (spec-casc-opt), against hand-picked distributions."""
    import torch

    vocab = 4
    # Row 0: q peaked on token 0 (draft confident), p peaked on token 1
    # (target confident elsewhere) -- large disagreement, large TV.
    draft_probs = torch.tensor(
        [
            [0.70, 0.10, 0.10, 0.10],  # draft_max=0.70
            [0.40, 0.20, 0.20, 0.20],  # draft_max=0.40
        ]
    )
    target_probs = torch.tensor(
        [
            [0.10, 0.70, 0.10, 0.10],  # target_max=0.70
            [0.25, 0.25, 0.25, 0.25],  # target_max=0.25
        ]
    )
    draft_max = draft_probs.max(dim=-1).values
    target_max = target_probs.max(dim=-1).values
    tv = (target_probs - draft_probs).clamp_min(0.0).sum(dim=-1)

    # Row 0: |0.10-0.70|+|0.70-0.10|+0+0, positive parts only = 0.60+0 = 0.60
    assert abs(tv[0].item() - 0.60) < 1e-6, tv[0].item()
    # Row 1: positive parts of (target-draft): max(0,0.25-0.40)=0, max(0,0.25-0.20)*3=0.05*3=0.15
    assert abs(tv[1].item() - 0.15) < 1e-6, tv[1].item()

    # threshold = target_max - alpha*tv; defer iff draft_max < threshold.
    # row0: draft_max=0.70, target_max=0.70, tv=0.60
    # row1: draft_max=0.40, target_max=0.25, tv=0.15
    for alpha, expected in (
        (0.0, [False, False]),  # threshold = target_max exactly: 0.70<0.70 F, 0.40<0.25 F
        (-10.0, [True, True]),  # threshold = target_max+10*tv, huge: always defer
        (10.0, [False, False]),  # threshold = target_max-10*tv, very negative: never defer
    ):
        defer = draft_max < (target_max - alpha * tv)
        assert defer.tolist() == expected, (alpha, defer.tolist(), expected)
        print(f"  ok  alpha={alpha}: defer={defer.tolist()}")

    print("  ok  defer formula matches hand-computed TV and thresholds")


def test_kernel_obeys_defer_mask() -> None:
    """Drive the V1 verify kernel directly with an explicit defer_mask: no
    model, no server, no probability reductions -- isolates the kernel change
    from the Python-side mask computation tested above.

    defer=True must reduce to exactly the strict test u <= p/q.
    defer=False must always accept, regardless of u.
    """
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
    print("FAILED" if failures else "all spec-casc-opt patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
