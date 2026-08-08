#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok patch. Run by patches/apply_spec_casc_tok.sh.

Checks, in order:

1. alpha reaches the module (same env-sanitisation failure mode as every
   other patch in this repo),
2. the discontinuity this method actually has: alpha=0 does NOT equal p,
   alpha=-inf DOES -- the one place in this repo where "0 is the safe
   missing-config default" would be a silent correctness bug, not a
   convention. Checked directly against the Eq. 15 formula, no GPU needed.
3. the composed pi_rej tensor built in plain PyTorch is a valid probability
   distribution (rows sum to 1) across a range of alpha, mirroring this
   repo's cactus patch's H_x check.
4. the *kernel* matches the same formula for the drafted token's own
   acceptance probability, driven directly (no model, no server).
5. residual sampling actually uses pi_rej, not raw p -- the same class of bug
   this repo's cactus patch had to fix once (recorded in that patch's own
   module comment), checked here by construction rather than by trusting the
   accept-kernel test alone.

(4) needs a GPU and is skipped without one; the rest do not.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "path": m._SPEC_CASC_TOK_ALPHA_FILE,
}))
"""


def read_back_in_subprocess() -> dict[str, object]:
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
        ALPHA_FILE.write_text("0.3\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.3, got
        assert got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.3")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (the ACTUAL strict point, not 0.0)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def _pi_rej(p, q, alpha):
    """Reference implementation of Eq. 15, independent of the patch's own code."""
    import torch

    top1 = p.max(dim=-1, keepdim=True).values
    in_top_set = p >= (1.0 - alpha) * top1
    eta = 1.0 - (q * in_top_set).sum(dim=-1, keepdim=True)
    return eta * p + torch.where(in_top_set, q, torch.zeros_like(q))


def test_alpha_zero_is_not_strict_but_neg_inf_is() -> None:
    """The discontinuity this method has that no other patch in this repo
    does: alpha=0 gives A = {argmax p} only, so pi_rej != p in general.
    alpha=-inf empties A entirely, giving pi_rej == p exactly."""
    import torch

    torch.manual_seed(0)
    p = torch.softmax(torch.randn(5, 32), dim=-1)
    q = torch.softmax(torch.randn(5, 32), dim=-1)

    pi_at_zero = _pi_rej(p, q, 0.0)
    assert not torch.allclose(pi_at_zero, p), (
        "alpha=0 should NOT equal p in general -- if this fires, either the "
        "test distributions are degenerate or the formula regressed"
    )
    print("  ok  alpha=0: pi_rej != p (confirms the discontinuity is real, not a typo)")

    pi_at_neg_inf = _pi_rej(p, q, float("-inf"))
    assert torch.allclose(pi_at_neg_inf, p, atol=1e-6), (
        f"alpha=-inf should equal p exactly; max diff = {(pi_at_neg_inf - p).abs().max().item()}"
    )
    print("  ok  alpha=-inf: pi_rej == p exactly (the actual strict point)")


def test_pi_rej_is_valid_distribution() -> None:
    import torch

    torch.manual_seed(1)
    p = torch.softmax(torch.randn(6, 16), dim=-1)
    q = torch.softmax(torch.randn(6, 16), dim=-1)
    for alpha in (float("-inf"), 0.0, 0.3, 1.0, 5.0):
        pi_rej = _pi_rej(p, q, alpha)
        row_sums = pi_rej.sum(dim=-1)
        assert torch.allclose(row_sums, torch.ones_like(row_sums), atol=1e-5), (
            f"alpha={alpha}: rows sum to {row_sums.tolist()}, not 1"
        )
        assert (pi_rej >= -1e-6).all(), f"alpha={alpha}: pi_rej has negative entries"
        print(f"  ok  alpha={alpha}: pi_rej sums to 1.0 and is non-negative (rows: {row_sums.tolist()})")


def test_recovery_uses_pi_rej_not_raw_p() -> None:
    """GPU: repeated recovery draws must reflect pi_rej's residual mass, not
    raw p's -- the same class of bug this repo's cactus patch had to fix once
    (an earlier version fed the accept kernel the relaxed target but left
    recovery/residual sampling on unmodified p; see that patch's own module
    comment). Constructed so index 2 has ZERO residual under raw p (so it
    could NEVER be recovered if this patch regressed to using target_probs
    instead of pi_rej) but positive residual under pi_rej at alpha=0.8 -- so
    seeing index 2 recovered at all, across repeated trials, is proof pi_rej
    is actually driving recovery."""
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; recovery test not run")
        return
    from types import SimpleNamespace

    from vllm.v1.sample.rejection_sampler import sample_recovered_tokens

    device = "cuda"
    p = torch.tensor([[0.60, 0.25, 0.15, 0.00]], device=device)
    q = torch.tensor([[0.50, 0.05, 0.20, 0.25]], device=device)
    draft_token_ids = torch.tensor([0], dtype=torch.int32, device=device)
    cu_num_draft_tokens = torch.tensor([1], dtype=torch.int32, device=device)
    meta = SimpleNamespace(generators={})

    # Sanity: raw p's residual at index 2 is exactly 0 (0.15 - 0.20 clipped),
    # so under the bug this test is designed to catch, index 2 is IMPOSSIBLE.
    raw_residual = (p - q).clamp_min(0.0)
    assert raw_residual[0, 2].item() == 0.0, raw_residual.tolist()

    pi_rej = _pi_rej(p, q, 0.8)
    pi_residual = (pi_rej - q).clamp_min(0.0)
    assert pi_residual[0, 2].item() > 0.0, (
        f"test construction bug: expected positive residual at index 2 under pi_rej, got {pi_residual.tolist()}"
    )

    def recovered(target_probs: torch.Tensor) -> int:
        out = sample_recovered_tokens(
            1, [1], cu_num_draft_tokens, draft_token_ids, q.contiguous(), target_probs.contiguous(), meta, device,
        )
        return int(out[0].item())

    saw_index_2 = False
    outcomes: set[int] = set()
    for _ in range(200):
        got = recovered(pi_rej)
        outcomes.add(got)
        if got == 2:
            saw_index_2 = True
            break
    assert saw_index_2, (
        f"index 2 never recovered across 200 trials (outcomes seen: {outcomes}) -- "
        f"recovery is likely still using raw p instead of pi_rej"
    )
    print(f"  ok  index 2 recovered under pi_rej (outcomes seen: {outcomes}) -- "
          f"impossible if recovery still used raw target_probs")

    control_outcomes = {recovered(p) for _ in range(50)}
    assert 2 not in control_outcomes, (
        f"control failed: raw p produced index 2 ({control_outcomes}) -- test construction is broken"
    )
    print(f"  ok  (control) raw p never produces index 2 across 50 trials (outcomes: {control_outcomes})")


def test_kernel_matches_formula() -> None:
    """Drive the V1 verify kernel directly: no model, no server, no sampler.

    Builds eta/top1 the same way rejection_sample() does (full-vocab
    reduction in plain PyTorch), then checks the kernel's accept decision
    for the DRAFTED token against the independent _pi_rej reference above.
    """
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; kernel test not run")
        return
    from vllm.v1.sample.rejection_sampler import rejection_random_sample_kernel

    device = "cuda"
    torch.manual_seed(2)
    vocab, draft_tok, recovered_tok, bonus_tok = 16, 3, 5, 7
    uniform = torch.linspace(0.05, 0.95, 19, device=device, dtype=torch.float32)
    n = uniform.numel()

    def run(alpha: float) -> tuple[torch.Tensor, torch.Tensor]:
        target_probs = torch.softmax(torch.randn(n, vocab, device=device), dim=-1)
        draft_probs = torch.softmax(torch.randn(n, vocab, device=device), dim=-1)
        pi_rej = _pi_rej(target_probs, draft_probs, alpha)
        expected_prob = pi_rej[:, draft_tok]
        q_at_draft = draft_probs[:, draft_tok]
        expected_accept = uniform.cpu() <= (expected_prob / q_at_draft).cpu()

        top1 = target_probs.max(dim=-1).values.contiguous()
        in_top_set_x = target_probs >= (1.0 - alpha) * target_probs.max(dim=-1, keepdim=True).values
        eta = (1.0 - (draft_probs * in_top_set_x).sum(dim=-1)).contiguous()

        out = torch.full((n, 2), -1, dtype=torch.int32, device=device)
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
            eta,
            top1,
            alpha,
            NO_DRAFT_PROBS=False,
            SYNTHETIC_MODE=False,
        )
        accepted = (out[:, 0] == draft_tok).cpu()
        return accepted, expected_accept

    for alpha in (float("-inf"), 0.0, 0.3, 2.0):
        accepted, expected = run(alpha)
        assert torch.equal(accepted, expected), (
            f"alpha={alpha}\n got      {accepted.tolist()}\n expected {expected.tolist()}"
        )
        print(f"  ok  kernel accept decision matches pi_rej(x)/q(x) >= u   alpha={alpha}")


def main() -> int:
    failures = 0
    for test in (
        test_alpha_plumbing,
        test_alpha_zero_is_not_strict_but_neg_inf_is,
        test_pi_rej_is_valid_distribution,
        test_recovery_uses_pi_rej_not_raw_p,
        test_kernel_matches_formula,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
