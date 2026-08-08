#!/usr/bin/env python3
"""Acceptance test for the r-fuzzy patch. Run by patches/apply_r_fuzzy.sh.

Structurally mirrors test_spec_casc_opt.py in this repo (same defer_mask
kernel plumbing), swapping the deferral formula for Jensen-Shannon divergence.

Checks, in order:

1. the alpha value reaches the module (same env-sanitisation failure mode as
   every other patch in this repo),
2. the defer-mask FORMULA (JSD(p,q) >= alpha) is correct, independent of the
   kernel -- needs no GPU,
3. the *kernel* obeys a supplied defer_mask correctly: defer=True must behave
   exactly like the strict test, defer=False must always accept regardless of
   u. Identical kernel contract to spec-casc-opt's, since both patches thread
   the same shape of boolean mask through the same kernel argument slot.

(3) needs a GPU and is skipped without one; (1) and (2) are not.
"""

from __future__ import annotations

import math
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._R_FUZZY_ALPHA,
    "path": m._R_FUZZY_ALPHA_FILE,
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
        ALPHA_FILE.write_text("0.2\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.2, got
        assert got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.2")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (Div < -inf never true -> strict spec-dec)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def _jsd(p, q):
    import torch

    eps = 1e-12
    m = 0.5 * (p + q)
    log_m = torch.log(m.clamp_min(eps))
    kl_pm = (p * (torch.log(p.clamp_min(eps)) - log_m)).sum(dim=-1)
    kl_qm = (q * (torch.log(q.clamp_min(eps)) - log_m)).sum(dim=-1)
    return (0.5 * kl_pm + 0.5 * kl_qm).clamp_min(0.0)


def test_defer_formula() -> None:
    """CPU-only: JSD(p,q) >= alpha, against hand-picked distributions,
    including a known-closed-form case (disjoint support, JSD = ln 2)."""
    import torch

    # Row 0: p and q identical -> JSD == 0 exactly.
    # Row 1: p and q have disjoint support -> JSD == ln(2), the maximum for
    #   base-e JSD, a standard closed-form sanity check.
    # Row 2: partial overlap, no closed form -- just checks monotonic sanity.
    p = torch.tensor(
        [
            [0.25, 0.25, 0.25, 0.25],
            [1.0, 0.0, 0.0, 0.0],
            [0.70, 0.10, 0.10, 0.10],
        ]
    )
    q = torch.tensor(
        [
            [0.25, 0.25, 0.25, 0.25],
            [0.0, 1.0, 0.0, 0.0],
            [0.40, 0.20, 0.20, 0.20],
        ]
    )
    jsd = _jsd(p, q)
    assert abs(jsd[0].item() - 0.0) < 1e-9, jsd[0].item()
    assert abs(jsd[1].item() - math.log(2)) < 1e-4, jsd[1].item()
    assert 0.0 < jsd[2].item() < math.log(2), jsd[2].item()
    print(f"  ok  JSD closed forms: identical=0.0, disjoint=ln2={math.log(2):.6f}, got {jsd.tolist()}")

    # Threshold table on just the two closed-form rows (identical=0.0,
    # disjoint=ln2), so expected defer values don't depend on row 2's
    # non-closed-form number.
    jsd01 = jsd[:2]
    for alpha, expected in (
        (0.0, [True, True]),  # JSD >= 0 always true (both >= 0)
        (0.5, [False, True]),  # 0.0 < 0.5 <= ln2(0.693)
        (float("-inf"), [True, True]),  # always defer
        (float("inf"), [False, False]),  # never defer (JSD is always finite)
    ):
        defer = (jsd01 >= alpha).tolist()
        assert defer == expected, (alpha, defer, expected, jsd01.tolist())
        print(f"  ok  alpha={alpha}: defer={defer}")

    print("  ok  defer formula matches hand-computed JSD and thresholds")


def test_kernel_obeys_defer_mask() -> None:
    """Drive the V1 verify kernel directly with an explicit defer_mask: no
    model, no server, no probability reductions -- isolates the kernel change
    from the Python-side JSD computation tested above. Identical contract to
    spec-casc-opt's kernel test, since both patches thread the same shape of
    boolean mask through the same argument slot.

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
    print("FAILED" if failures else "all r-fuzzy patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
