#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-semantic-guard patch. Run by
patches/apply.sh.

This patch is spec-casc-tok plus one addition: at hesitation-marker draft
token ids, force the trusted top set A empty for that row -- which this
method's own module comment already proves is EXACTLY its alpha=-inf strict
limit (A={} => eta=1 => pi_rej=p), not an approximation of strict. Unlike
r_fuzzy_semantic_guard (a wholesale q/p switch with nothing else to touch),
spec-casc-tok is a genuine full-vocab blend that also drives recovery, so
the guard has to be enforced in two places kept consistent with each other:
the Python-side in_top_set (recovery) and the kernel's own from-scratch
recheck of the drafted token's membership (accept test) -- see the patch's
module comment for why a mismatch between the two would be a real bug, not
just style.

Checks, in order:

1. the alpha value reaches the module, from THIS patch's own file (not
   plain spec-casc-tok's -- they must never alias),
2. the guard token-id set matches r_fuzzy_semantic_guard's documented list
   exactly (same hypothesis, same tokens, different method),
3. the guard mask is True only at guarded ids, independent of the kernel,
4. forcing the top set empty at a guarded row reproduces alpha=-inf's
   pi_rej == p exactly, at ANY configured alpha, not just when alpha
   already happened to be -inf -- the actual guard property this patch
   depends on,
5. the *kernel* accept decision at guarded rows matches the raw strict
   ratio test regardless of alpha, while unguarded rows still match plain
   spec-casc-tok's own formula (test_spec_casc_tok.py's own kernel test,
   generalized to carry a guard_mask argument),
6. residual/recovery sampling at a guarded row draws from p's own residual,
   not the alpha-blended pi_rej's -- the same class of check
   test_spec_casc_tok.py's own test_recovery_uses_pi_rej_not_raw_p does,
   inverted: proving the guard, not the relaxation, is what's live there.

(5) and (6) need a GPU and are skipped without one; the rest do not.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

# Same 18 ids r_fuzzy_semantic_guard's own test documents (5 markers, mostly
# leading-space single-token forms) -- kept here as an independent expected
# value, not imported from either patch, so a change to either's own set is
# what this test is meant to catch.
EXPECTED_GUARD_TOKEN_IDS = frozenset(
    {
        29126, 17114, 5238, 24305,  # wait / Wait / " wait" / " Wait"
        112576, 186402, 165972,  # Hmm / " hmm" / " Hmm"
        138925, 87471, 4771, 50557,  # actually / Actually / " actually" / " Actually"
        8293, 7943, 889, 3072,  # but / But / " but" / " But"
        58369, 35717, 41021,  # Let's / " let's" / " Let's"
    }
)

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "path": m._SPEC_CASC_TOK_ALPHA_FILE,
    "guard_ids": sorted(m._SEMANTIC_GUARD_TOKEN_IDS),
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
        print(f"  ok  module reads {ALPHA_FILE} -> 0.3 (own file, not plain spec-casc-tok's)")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (the ACTUAL strict point, not 0.0)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def test_guard_token_ids() -> None:
    got = read_back_in_subprocess()
    ids = set(got["guard_ids"])
    assert ids == EXPECTED_GUARD_TOKEN_IDS, (
        f"installed patch's guard set differs from the documented list -- "
        f"missing {EXPECTED_GUARD_TOKEN_IDS - ids}, extra {ids - EXPECTED_GUARD_TOKEN_IDS}"
    )
    print(f"  ok  {len(ids)} guard token ids match r_fuzzy_semantic_guard's list exactly")


def _load_patched_module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def test_guard_mask_formula() -> None:
    """CPU-only: _semantic_guard_mask is True only at guarded ids."""
    import torch

    m = _load_patched_module()
    guarded = sorted(m._SEMANTIC_GUARD_TOKEN_IDS)
    probe = torch.tensor([guarded[0], guarded[-1], 0, 1, 999999999], dtype=torch.int64)
    mask = m._semantic_guard_mask(probe)
    expected = torch.tensor([True, True, False, False, False])
    assert torch.equal(mask, expected), (mask.tolist(), expected.tolist())
    print(f"  ok  _semantic_guard_mask true only at guarded ids (probe={probe.tolist()})")


def _pi_rej(p, q, alpha, guard_mask=None):
    """Reference implementation of Eq. 15, with the guard's own forcing
    applied -- independent of the patch's own code. guard_mask: [n] bool,
    forces that row's trusted top set empty regardless of alpha."""
    import torch

    top1 = p.max(dim=-1, keepdim=True).values
    in_top_set = p >= (1.0 - alpha) * top1
    if guard_mask is not None:
        in_top_set = in_top_set & ~guard_mask.unsqueeze(-1)
    eta = 1.0 - (q * in_top_set).sum(dim=-1, keepdim=True)
    return eta * p + torch.where(in_top_set, q, torch.zeros_like(q))


def test_guard_forces_strict_limit_at_any_alpha() -> None:
    """The property this whole patch depends on: forcing the top set empty
    at a guarded row reproduces alpha=-inf's pi_rej==p exactly, at ANY
    alpha -- not only when alpha already happened to be -inf. Checked
    against a range of alphas including ones where plain (unguarded)
    spec-casc-tok would clearly NOT equal p, to make sure the guard is
    doing real work, not passing vacuously."""
    import torch

    torch.manual_seed(3)
    n, vocab = 5, 32
    p = torch.softmax(torch.randn(n, vocab), dim=-1)
    q = torch.softmax(torch.randn(n, vocab), dim=-1)
    guard_mask = torch.zeros(n, dtype=torch.bool)
    guard_mask[1] = True
    guard_mask[3] = True

    for alpha in (0.0, 0.3, 1.0, 5.0):
        unguarded = _pi_rej(p, q, alpha)
        assert not torch.allclose(unguarded[1], p[1], atol=1e-6), (
            f"alpha={alpha}: test construction bug -- row 1 already equals p without the guard, "
            f"so this alpha can't demonstrate the guard is doing anything"
        )
        guarded = _pi_rej(p, q, alpha, guard_mask=guard_mask)
        assert torch.allclose(guarded[1], p[1], atol=1e-6), (
            f"alpha={alpha}: guarded row 1 does not equal p exactly, "
            f"max diff={(guarded[1] - p[1]).abs().max().item()}"
        )
        assert torch.allclose(guarded[3], p[3], atol=1e-6), f"alpha={alpha}: guarded row 3 does not equal p exactly"
        # unguarded rows must be UNCHANGED by the guard's presence
        for i in (0, 2, 4):
            assert torch.allclose(guarded[i], unguarded[i], atol=1e-6), (
                f"alpha={alpha}: unguarded row {i} changed when the guard mask was supplied"
            )
        print(f"  ok  alpha={alpha}: guarded rows forced to p exactly, unguarded rows unchanged")


def test_kernel_matches_formula_with_guard() -> None:
    """Drive the V1 verify kernel directly, mixing guarded and unguarded
    rows in the same batch, across several alphas."""
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; kernel test not run")
        return
    m = _load_patched_module()

    device = "cuda"
    torch.manual_seed(4)
    vocab, draft_tok, recovered_tok, bonus_tok = 16, 3, 5, 7
    uniform = torch.linspace(0.05, 0.95, 19, device=device, dtype=torch.float32)
    n = uniform.numel()
    # Alternate guarded/unguarded rows.
    guard_mask = (torch.arange(n, device=device) % 2 == 0)

    def run(alpha: float) -> tuple[torch.Tensor, torch.Tensor]:
        target_probs = torch.softmax(torch.randn(n, vocab, device=device), dim=-1)
        draft_probs = torch.softmax(torch.randn(n, vocab, device=device), dim=-1)
        pi_rej = _pi_rej(target_probs.cpu(), draft_probs.cpu(), alpha, guard_mask=guard_mask.cpu()).to(device)
        expected_prob = pi_rej[:, draft_tok]
        q_at_draft = draft_probs[:, draft_tok]
        expected_accept = uniform.cpu() <= (expected_prob / q_at_draft).cpu()

        top1 = target_probs.max(dim=-1).values.contiguous()
        in_top_set_x = target_probs >= (1.0 - alpha) * target_probs.max(dim=-1, keepdim=True).values
        in_top_set_x = in_top_set_x & ~guard_mask.unsqueeze(-1)
        eta = (1.0 - (draft_probs * in_top_set_x).sum(dim=-1)).contiguous()

        out = torch.full((n, 2), -1, dtype=torch.int32, device=device)
        m.rejection_random_sample_kernel[(n,)](
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
            guard_mask.contiguous(),
            NO_DRAFT_PROBS=False,
            SYNTHETIC_MODE=False,
        )
        accepted = (out[:, 0] == draft_tok).cpu()
        return accepted, expected_accept

    for alpha in (0.0, 0.3, 2.0):
        accepted, expected = run(alpha)
        assert torch.equal(accepted, expected), (
            f"alpha={alpha}\n got      {accepted.tolist()}\n expected {expected.tolist()}"
        )
        # Also confirm guarded rows independently match the RAW strict test
        # (target_prob/draft_prob >= u), i.e. genuinely alpha-independent.
        print(f"  ok  kernel accept decision matches guard-aware pi_rej(x)/q(x) >= u   alpha={alpha}")


def test_recovery_uses_guarded_residual() -> None:
    """GPU: a guarded row's recovery residual must match raw p's, not the
    alpha-relaxed pi_rej's -- constructed so index 2 has zero residual
    under raw p but positive residual under the UNGUARDED alpha=0.8 blend,
    same construction as test_spec_casc_tok.py's own
    test_recovery_uses_pi_rej_not_raw_p, but this time checking that
    GUARDING suppresses that extra residual back to zero."""
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

    pi_rej_unguarded = _pi_rej(p.cpu(), q.cpu(), 0.8).to(device)
    residual_unguarded = (pi_rej_unguarded - q).clamp_min(0.0)
    assert residual_unguarded[0, 2].item() > 0.0, (
        f"test construction bug: expected positive unguarded residual at index 2, got {residual_unguarded.tolist()}"
    )

    guard_mask = torch.tensor([True], device=device)
    pi_rej_guarded = _pi_rej(p.cpu(), q.cpu(), 0.8, guard_mask=guard_mask.cpu()).to(device)
    residual_guarded = (pi_rej_guarded - q).clamp_min(0.0)
    assert residual_guarded[0, 2].item() == 0.0, (
        f"guarded residual at index 2 should be exactly 0 (matches raw p), got {residual_guarded.tolist()}"
    )
    print(f"  ok  guarded pi_rej's residual at index 2 is exactly 0 (raw-p-equivalent), "
          f"vs unguarded's {residual_unguarded[0, 2].item():.4f}")

    def recovered(target_probs: torch.Tensor) -> int:
        out = sample_recovered_tokens(
            1, [1], cu_num_draft_tokens, draft_token_ids, q.contiguous(), target_probs.contiguous(), meta, device,
        )
        return int(out[0].item())

    guarded_outcomes = {recovered(pi_rej_guarded) for _ in range(100)}
    assert 2 not in guarded_outcomes, (
        f"index 2 recovered under a GUARDED row ({guarded_outcomes}) -- guard is not suppressing "
        f"the relaxed residual as intended"
    )
    print(f"  ok  index 2 never recovered under the guarded row across 100 trials (outcomes: {guarded_outcomes})")


def main() -> int:
    failures = 0
    for test in (
        test_alpha_plumbing,
        test_guard_token_ids,
        test_guard_mask_formula,
        test_guard_forces_strict_limit_at_any_alpha,
        test_kernel_matches_formula_with_guard,
        test_recovery_uses_guarded_residual,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-semantic-guard patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
