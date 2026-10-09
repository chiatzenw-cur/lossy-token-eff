#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-autoguard patch (autoresearch/).

Dispatched by patches/apply.sh for METHOD=spec-casc-tok-autoguard. No GPU
needed -- every check here is plumbing, the frozen wrapper's safety
behaviour, or the closed-form "forcing the trusted top set empty == strict"
identity on tiny CPU tensors. The accept/reject KERNEL itself is byte-
identical to spec-casc-tok-semantic-guard's (this patch only swaps the
source of the mask), so its adversarial real-kernel coverage in
test_spec_casc_tok_semantic_guard.py already applies -- not duplicated here.

Checks, in order:
  1. alpha-file plumbing: the patched module reads its OWN alpha file
     (/tmp/lossy-token-eff-spec-casc-tok-autoguard-alpha-$UID), defaults to
     -inf (this method's strict point) when it is missing/unreadable.
  2. autoguard.py is installed next to the patched module, decide() has the
     documented keyword-only signature, and the shipped default returns an
     all-False mask (=> plain spec_casc_tok, the baseline).
  3. _autoguard_mask (frozen wrapper) degrades safely: a decide() that
     raises, or returns the wrong shape / a non-tensor, yields all-False;
     a warmup-shaped batch (len(num_draft_tokens) > 8) returns all-False
     WITHOUT calling decide() at all.
  4. _autoguard_observe advances round_index, appends only non-negative
     committed ids, and enforces the history cap.
  5. closed form: forcing in_top_set empty for a row (what a True mask
     entry does) makes eta == 1 and pi_rej == p exactly, i.e. that row is
     verified losslessly -- the property the whole design rests on.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import pathlib
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-autoguard-alpha-{os.getuid()}")
RS_MODULE = "vllm.v1.sample.rejection_sampler"
AUTOGUARD_MODULE = "vllm.v1.sample.autoguard"


def _load(name: str):
    spec = importlib.util.find_spec(name)
    if spec is None:
        raise AssertionError(f"{name} not importable -- is the .venv-vllm interpreter being used?")
    return importlib.import_module(name)


def test_alpha_plumbing() -> None:
    saved = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.42\n")
        m = importlib.reload(_load(RS_MODULE))
        assert m._SPEC_CASC_TOK_ALPHA == 0.42, m._SPEC_CASC_TOK_ALPHA
        assert str(ALPHA_FILE) in m._SPEC_CASC_TOK_ALPHA_SOURCE

        ALPHA_FILE.unlink(missing_ok=True)
        m = importlib.reload(m)
        assert m._SPEC_CASC_TOK_ALPHA == float("-inf"), m._SPEC_CASC_TOK_ALPHA
        assert "default" in m._SPEC_CASC_TOK_ALPHA_SOURCE
        print("  ok  reads its own alpha file; missing => -inf (strict point, NOT 0.0)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)
        importlib.reload(_load(RS_MODULE))


def test_autoguard_module_and_default() -> None:
    import inspect
    import torch

    ag = _load(AUTOGUARD_MODULE)
    installed = pathlib.Path(ag.__file__)
    repo_copy = pathlib.Path(__file__).with_name("autoguard.py")
    assert installed.read_bytes() == repo_copy.read_bytes(), (
        f"installed {installed} differs from patches/autoguard.py -- re-run "
        f"`bash patches/apply.sh spec-casc-tok-autoguard` after editing it"
    )
    sig = inspect.signature(ag.decide)
    assert list(sig.parameters) == [
        "round_index", "committed_token_ids", "draft_token_ids", "draft_probs",
        "target_probs", "num_draft_tokens", "vocab_size",
    ], list(sig.parameters)
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in sig.parameters.values())

    n, v = 5, 32
    mask = ag.decide(
        round_index=0,
        committed_token_ids=[],
        draft_token_ids=torch.arange(n),
        draft_probs=torch.full((n, v), 1.0 / v),
        target_probs=torch.full((n, v), 1.0 / v),
        num_draft_tokens=[n],
        vocab_size=v,
    )
    assert mask.shape == (n,) and mask.dtype == torch.bool and not mask.any(), mask
    print("  ok  autoguard.py installed, decide() signature matches contract, default is all-False")


def test_wrapper_degrades_safely() -> None:
    import torch

    m = importlib.reload(_load(RS_MODULE))
    ag = _load(AUTOGUARD_MODULE)
    real = ag.decide
    n, v = 6, 16
    dti = torch.arange(n)
    dp = torch.full((n, v), 1.0 / v)
    tp = torch.full((n, v), 1.0 / v)
    oti = torch.full((1, 7), -1, dtype=torch.long)
    cu = torch.tensor([n])

    def call(nd):
        return m._autoguard_mask(dti, dp, tp, oti, cu, nd)

    try:
        ag.decide = lambda **_: (_ for _ in ()).throw(RuntimeError("boom"))
        assert not call([n]).any(), "a raising decide() must yield all-False"

        ag.decide = lambda **_: torch.zeros(n + 3, dtype=torch.bool)
        assert not call([n]).any(), "a wrong-shape return must yield all-False"

        ag.decide = lambda **_: "not a tensor"
        assert not call([n]).any(), "a non-tensor return must yield all-False"

        calls = []
        ag.decide = lambda **kw: calls.append(1) or torch.ones(n, dtype=torch.bool)
        assert not call([1] * 9).any(), "warmup-shaped batch must yield all-False"
        assert not calls, "decide() must NOT be called for a warmup-shaped batch"

        out = call([n])
        assert out.dtype == torch.bool and out.shape == (n,) and out.all()
        print("  ok  wrapper: raise/wrong-shape/non-tensor => all-False; warmup batch short-circuits; good mask passes through")
    finally:
        ag.decide = real


def test_observe_bookkeeping() -> None:
    import torch

    m = importlib.reload(_load(RS_MODULE))
    m._AUTOGUARD_HISTORY.clear()
    m._AUTOGUARD_STATE["round_index"] = 0

    row = torch.tensor([[10, 11, -1, 12, -1, -1, -1]], dtype=torch.long)
    m._autoguard_observe(row, torch.tensor([3]), [3])
    assert m._AUTOGUARD_STATE["round_index"] == 1
    assert m._AUTOGUARD_HISTORY == [10, 11, 12], m._AUTOGUARD_HISTORY

    m._autoguard_observe(row, torch.tensor([3]), [1] * 9)  # warmup shape: no-op
    assert m._AUTOGUARD_STATE["round_index"] == 1 and m._AUTOGUARD_HISTORY == [10, 11, 12]

    cap = m._AUTOGUARD_HISTORY_CAP
    m._AUTOGUARD_HISTORY[:] = list(range(cap + 500))
    big = torch.arange(0, 7, dtype=torch.long).unsqueeze(0)
    m._autoguard_observe(big, torch.tensor([7]), [7])
    assert len(m._AUTOGUARD_HISTORY) == cap, len(m._AUTOGUARD_HISTORY)
    m._AUTOGUARD_HISTORY.clear()
    m._AUTOGUARD_STATE["round_index"] = 0
    print("  ok  observe(): round_index++, non-negative ids only, warmup no-op, history capped")


def test_empty_top_set_is_strict() -> None:
    import torch

    torch.manual_seed(0)
    n, v = 8, 64
    p = torch.rand(n, v).softmax(-1)
    q = torch.rand(n, v).softmax(-1)
    alpha = 0.3
    top1 = p.max(-1, keepdim=True).values
    mask = torch.ones(n, dtype=torch.bool)  # every row guarded

    in_top_set = p >= (1.0 - alpha) * top1
    in_top_set = in_top_set & ~mask.unsqueeze(-1)
    eta = 1.0 - (q * in_top_set).sum(-1)
    pi_rej = eta.unsqueeze(-1) * p + torch.where(in_top_set, q, torch.zeros_like(q))

    assert torch.allclose(eta, torch.ones(n)), eta
    assert torch.allclose(pi_rej, p, atol=1e-6), (pi_rej - p).abs().max()
    print("  ok  a guarded row: in_top_set empty => eta==1 => pi_rej==p (verified losslessly)")


if __name__ == "__main__":
    fns = [
        test_alpha_plumbing,
        test_autoguard_module_and_default,
        test_wrapper_degrades_safely,
        test_observe_bookkeeping,
        test_empty_top_set_is_strict,
    ]
    for fn in fns:
        print(fn.__name__)
        fn()
    print("\nall spec-casc-tok-autoguard checks passed")
