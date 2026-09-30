#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-lt patch. Run by patches/apply.sh.

Same three-part shape as test_spec_casc_opt.py, because the patch has the
same shape (a per-token defer mask computed in PyTorch, fed to spec-casc-opt's
kernel hunk unchanged):

1. the alpha value reaches the module through its own /tmp file, and a
   missing file falls back to -inf (every position defers -> strict),
2. the mask FORMULA: defer iff p(x) < (1-alpha) * max_w p(w), i.e. the drafted
   token is outside the verifier's trusted top set -- CPU only, hand-picked
   rows, including the alpha=0-is-not-strict trap this method shares with
   spec-casc-tok,
3. the kernel obeys a supplied defer_mask (defer=True == strict test,
   defer=False == always accept) -- byte-identical kernel to spec-casc-opt's,
   re-run here anyway so this method's install is verified on its own.

(3) needs a GPU and is skipped without one; (1) and (2) are not.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-lt-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_LT_ALPHA,
    "path": m._SPEC_CASC_TOK_LT_ALPHA_FILE,
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
        ALPHA_FILE.write_text("0.3\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.3, got
        assert got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.3")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (empty trusted set -> strict spec-dec)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def test_defer_formula() -> None:
    """CPU-only: defer iff p(x) < (1-alpha)*max_w p(w), exactly as the patch
    computes it (gather the drafted token's verifier probability, compare to
    the row's top-1), against hand-picked rows."""
    import torch

    target_probs = torch.tensor(
        [
            [0.70, 0.10, 0.10, 0.10],  # top1 0.70, drafted token 0 -> p(x)=0.70 (the argmax)
            [0.70, 0.10, 0.10, 0.10],  # top1 0.70, drafted token 1 -> p(x)=0.10
            [0.25, 0.25, 0.25, 0.25],  # flat,      drafted token 2 -> p(x)=0.25 (tied argmax)
        ]
    )
    draft_token_ids = torch.tensor([0, 1, 2], dtype=torch.int32)

    def mask(alpha: float) -> list[bool]:
        top1 = target_probs.max(dim=-1).values
        drafted_p = target_probs.gather(1, draft_token_ids.to(torch.int64).unsqueeze(1)).squeeze(1)
        return (drafted_p < (1.0 - alpha) * top1).tolist()

    # Row 1 enters the set iff 0.10 >= (1-alpha)*0.70  <=>  alpha >= 6/7.
    for alpha, expected in (
        (float("-inf"), [True, True, True]),  # empty set: every position defers (strict)
        (0.0, [False, True, False]),  # only the argmax is trusted -- NOT strict
        (0.5, [False, True, False]),
        (0.9, [False, False, False]),
        (1.0, [False, False, False]),  # threshold 0: whole vocabulary trusted
    ):
        got = mask(alpha)
        assert got == expected, (alpha, got, expected)
        print(f"  ok  alpha={alpha}: defer={got}")

    assert mask(0.0) != mask(float("-inf")), "alpha=0 must NOT coincide with the strict point"
    print("  ok  alpha=0 is a real relaxation (argmax draft always kept); strict point is -inf")


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
    print("FAILED" if failures else "all spec-casc-tok-lt patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
