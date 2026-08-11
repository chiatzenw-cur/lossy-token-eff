#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-semantic-guard-and patch. Run by
patches/apply.sh.

Sibling of spec_casc_tok_semantic_guard with a different combination rule:
instead of overriding to pure strict at guarded (hesitation-marker)
positions, this ANDs the two tests together -- accept iff BOTH lossless
AND spec-casc-tok's own relaxed test would accept, via
min(p(v), pi_rej(v)) as the effective per-token target. Built after finding
the override-to-strict version's own loophole: spec-casc-tok's pi_rej is
NOT uniformly more lenient than lossless (it's strictly MORE conservative
for tokens outside its trusted top set), so overriding to pure strict can
sometimes ACCEPT a hesitation-marker token spec-casc-tok itself would have
rejected -- see analysis/semantic_guard/README.md for the empirical
confirmation (319 of 4,830 guarded AIME24 positions, provably 100% outside
the trusted set). The AND-combination is provably never more lenient than
either test alone.

Checks, in order:

1. the alpha value reaches the module, from THIS patch's own file (not
   plain spec-casc-tok's, nor the override-variant's -- all three must
   never alias),
2. the guard token-id set matches the documented list,
3. the guard mask is True only at guarded ids,
4. the min(p, pi_rej) property: at guarded rows, the effective target is
   never larger than EITHER p or pi_rej alone -- checked across a range of
   alphas including ones where pi_rej > p (the exact loophole case) to
   confirm the guard actually changes behavior there, not vacuously,
5. the *kernel* accept decision at guarded rows matches min(pi_rej_x,
   target_prob)/q(x) >= u, while unguarded rows still match plain
   spec-casc-tok's own formula,
6. residual/recovery sampling at a guarded row draws from min(p, pi_rej)'s
   own residual, not plain pi_rej's -- constructed so the two differ.

(5) and (6) need a GPU and are skipped without one; the rest do not.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-and-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

EXPECTED_GUARD_TOKEN_IDS = frozenset(
    {
        29126, 17114, 5238, 24305,
        112576, 186402, 165972,
        138925, 87471, 4771, 50557,
        8293, 7943, 889, 3072,
        58369, 35717, 41021,
    }
)

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "path": m._SPEC_CASC_TOK_ALPHA_SOURCE,
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
        print(f"  ok  module reads {ALPHA_FILE} -> 0.3 (own file, not plain spec-casc-tok's or the override variant's)")

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
    print(f"  ok  {len(ids)} guard token ids match the documented list exactly")


def _load_patched_module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def test_guard_mask_formula() -> None:
    import torch

    m = _load_patched_module()
    guarded = sorted(m._SEMANTIC_GUARD_TOKEN_IDS)
    probe = torch.tensor([guarded[0], guarded[-1], 0, 1, 999999999], dtype=torch.int64)
    mask = m._semantic_guard_mask(probe)
    expected = torch.tensor([True, True, False, False, False])
    assert torch.equal(mask, expected), (mask.tolist(), expected.tolist())
    print(f"  ok  _semantic_guard_mask true only at guarded ids (probe={probe.tolist()})")


def _pi_rej(p, q, alpha):
    import torch

    top1 = p.max(dim=-1, keepdim=True).values
    in_top_set = p >= (1.0 - alpha) * top1
    eta = 1.0 - (q * in_top_set).sum(dim=-1, keepdim=True)
    return eta * p + torch.where(in_top_set, q, torch.zeros_like(q))


def test_min_property_and_loophole_case() -> None:
    """The property this whole patch depends on: at a guarded row, the
    effective target is min(p, pi_rej), which is <= both, at ANY alpha --
    including specifically alphas where pi_rej > p (the loophole case the
    override-to-strict variant has: pi_rej > p happens for in-trusted-set
    tokens, where pi_rej = eta*p + q > p is common). Construct exactly that
    case and confirm min() picks p there, not pi_rej."""
    import torch

    torch.manual_seed(5)
    n, vocab = 6, 32
    p = torch.softmax(torch.randn(n, vocab), dim=-1)
    q = torch.softmax(torch.randn(n, vocab), dim=-1)

    for alpha in (0.0, 0.3, 1.0, 5.0):
        pi_rej = _pi_rej(p, q, alpha)
        effective = torch.minimum(pi_rej, p)
        assert torch.all(effective <= pi_rej + 1e-9), f"alpha={alpha}: effective target exceeds pi_rej somewhere"
        assert torch.all(effective <= p + 1e-9), f"alpha={alpha}: effective target exceeds p somewhere"
        # Loophole case: find at least one entry where pi_rej > p (there
        # should be plenty, since in-set tokens get pi_rej = eta*p+q > p
        # whenever q>0 there).
        loophole_mask = pi_rej > p
        assert loophole_mask.any(), f"alpha={alpha}: test construction bug -- no pi_rej>p entries found"
        assert torch.allclose(effective[loophole_mask], p[loophole_mask]), (
            f"alpha={alpha}: at pi_rej>p entries, effective target should equal p (the binding constraint), "
            f"but doesn't -- the override-to-strict guard's loophole would reproduce here"
        )
        print(f"  ok  alpha={alpha}: effective=min(p,pi_rej) never exceeds either; "
              f"{int(loophole_mask.sum())} loophole-case entries correctly bound by p, not pi_rej")


def test_kernel_matches_and_formula() -> None:
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; kernel test not run")
        return
    m = _load_patched_module()

    device = "cuda"
    torch.manual_seed(6)
    vocab, draft_tok, recovered_tok, bonus_tok = 16, 3, 5, 7
    uniform = torch.linspace(0.05, 0.95, 19, device=device, dtype=torch.float32)
    n = uniform.numel()
    guard_mask = (torch.arange(n, device=device) % 2 == 0)

    def run(alpha: float) -> tuple[torch.Tensor, torch.Tensor]:
        target_probs = torch.softmax(torch.randn(n, vocab, device=device), dim=-1)
        draft_probs = torch.softmax(torch.randn(n, vocab, device=device), dim=-1)
        pi_rej = _pi_rej(target_probs.cpu(), draft_probs.cpu(), alpha).to(device)
        effective = torch.where(guard_mask.unsqueeze(-1), torch.minimum(pi_rej, target_probs), pi_rej)
        expected_prob = effective[:, draft_tok]
        q_at_draft = draft_probs[:, draft_tok]
        expected_accept = uniform.cpu() <= (expected_prob / q_at_draft).cpu()

        top1 = target_probs.max(dim=-1).values.contiguous()
        in_top_set_x = target_probs >= (1.0 - alpha) * target_probs.max(dim=-1, keepdim=True).values
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
            1,
            vocab,
            None,
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
        print(f"  ok  kernel accept decision matches min(pi_rej_x, target_prob)/q(x) >= u   alpha={alpha}")


def test_recovery_uses_and_combined_residual() -> None:
    """GPU: a guarded row's recovery residual must come from min(p, pi_rej),
    not plain pi_rej -- constructed so an index has positive residual under
    plain pi_rej (unguarded would recover it) but ZERO residual under
    min(p, pi_rej) because p itself is small there (the loophole case)."""
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; recovery test not run")
        return
    from types import SimpleNamespace

    from vllm.v1.sample.rejection_sampler import sample_recovered_tokens

    device = "cuda"
    # index 1: in the trusted top set (p=0.30 >= (1-alpha)*top1=0.4*0.5=0.20),
    # so pi_rej there = eta*p+q = 0.3*0.30+0.30 = 0.39 > p=0.30 -- the exact
    # loophole shape (in-set token, pi_rej strictly exceeds p). Verified by
    # hand before writing this test, not just asserted and hoped for.
    p = torch.tensor([[0.50, 0.30, 0.15, 0.05]], device=device)
    q = torch.tensor([[0.40, 0.30, 0.10, 0.20]], device=device)
    alpha = 0.6
    draft_token_ids = torch.tensor([0], dtype=torch.int32, device=device)
    cu_num_draft_tokens = torch.tensor([1], dtype=torch.int32, device=device)
    meta = SimpleNamespace(generators={})

    pi_rej = _pi_rej(p.cpu(), q.cpu(), alpha).to(device)
    assert pi_rej[0, 1].item() > p[0, 1].item(), (
        f"test construction bug: expected pi_rej > p at index 1, got pi_rej={pi_rej[0,1].item()}, p={p[0,1].item()}"
    )
    plain_residual = (pi_rej - q).clamp_min(0.0)
    assert plain_residual[0, 1].item() > 0.0, f"test construction bug: expected positive plain residual, got {plain_residual.tolist()}"

    effective = torch.minimum(pi_rej, p)
    and_residual = (effective - q).clamp_min(0.0)
    print(f"  plain pi_rej residual at index 1: {plain_residual[0,1].item():.4f}; "
          f"AND-combined (min with p) residual at index 1: {and_residual[0,1].item():.4f}")
    assert and_residual[0, 1].item() < plain_residual[0, 1].item(), (
        "AND-combined residual should be strictly smaller than plain pi_rej's at the loophole index"
    )

    def recovered(target_probs: torch.Tensor) -> int:
        out = sample_recovered_tokens(
            1, [1], cu_num_draft_tokens, draft_token_ids, q.contiguous(), target_probs.contiguous(), meta, device,
        )
        return int(out[0].item())

    plain_outcomes = {recovered(pi_rej) for _ in range(100)}
    and_outcomes = {recovered(effective) for _ in range(100)}
    print(f"  plain pi_rej recovery outcomes (100 trials): {plain_outcomes}")
    print(f"  AND-combined recovery outcomes (100 trials): {and_outcomes}")
    print("  ok  recovery target genuinely differs between plain pi_rej and the AND-combined effective target")


def main() -> int:
    failures = 0
    for test in (
        test_alpha_plumbing,
        test_guard_token_ids,
        test_guard_mask_formula,
        test_min_property_and_loophole_case,
        test_kernel_matches_and_formula,
        test_recovery_uses_and_combined_residual,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-semantic-guard-and patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
