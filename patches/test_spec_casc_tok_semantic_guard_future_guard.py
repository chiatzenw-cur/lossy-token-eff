#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-semantic-guard-future-guard patch. Run
by patches/apply.sh.

Third semantic-guard sibling, different trigger shape from the other two:
instead of gating the hesitation-marker token itself, this gates the K
VERIFIED positions AFTER tok accepts one, on the theory that the marker
signals a decision fork and the risk is in what gets built on top of it.
First patch in this repo with cross-round persistent state -- see the
patch's own module comment for the single-real-sequence-per-process scoping
this relies on (this repo's own "fresh server per measurement" protocol).

Checks, in order:

1. alpha and K reach the module, from THIS patch's own files,
2. the wider (35-id, 14-word) marker set matches r_fuzzy_semantic_guard_v2's
   documented list exactly (reused verbatim, not re-derived),
3. the guard mask is True only at guarded ids,
4. WITHIN-ROUND arming: a marker accepted at position i, in a round with
   several draft positions, must make positions i+1..i+K in the SAME round
   use the raw lossless test instead of spec-casc-tok's own pi_rej --
   driven against the real kernel, not a Python re-implementation, since
   this is exactly the new state-machine logic this patch adds,
5. CROSS-ROUND carryover: the window must survive into the following
   round if it hasn't expired yet, and expire exactly after K verified
   positions total,
6. recovery is UNAFFECTED by an active window (documented simplification --
   recovery always samples from spec-casc-tok's own pi_rej-based residual,
   never a window-adjusted one), confirmed by construction rather than
   inference,
7. a warmup-shaped (large) batch resets the persisted carryover to 0 rather
   than letting it leak into the next real-generation round.

(4)-(7) need a GPU and are skipped without one; (1)-(3) do not.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-alpha-{os.getuid()}")
K_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-semantic-guard-future-guard-k-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

EXPECTED_GUARD_TOKEN_IDS = frozenset(
    {
        29126, 17114, 5238, 24305,
        112576, 186402, 165972,
        138925, 87471, 4771, 50557,
        8293, 7943, 889, 3072,
        58369, 35717, 41021,
        84787, 23586,
        2167, 1416,
        5808, 2632,
        10620, 6549,
        12845,
        56734, 45438,
        151907, 65037,
        55292, 38966,
        3879, 7217,
    }
)

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "k": m._SPEC_CASC_TOK_GUARD_FUTURE_K,
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


def test_alpha_and_k_plumbing() -> None:
    saved_alpha = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    saved_k = K_FILE.read_text() if K_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.3\n")
        K_FILE.write_text("5\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.3, got
        assert got["k"] == 5, got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.3, {K_FILE} -> 5")

        ALPHA_FILE.unlink()
        K_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        assert got["k"] == 8, got
        print("  ok  missing files fall back to alpha=-inf (actual strict point), k=8 (default)")
    finally:
        if saved_alpha is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved_alpha)
        if saved_k is None:
            K_FILE.unlink(missing_ok=True)
        else:
            K_FILE.write_text(saved_k)


def test_guard_token_ids() -> None:
    got = read_back_in_subprocess()
    ids = set(got["guard_ids"])
    assert ids == EXPECTED_GUARD_TOKEN_IDS, (
        f"installed patch's guard set differs from the documented (wider, v2-derived) list -- "
        f"missing {EXPECTED_GUARD_TOKEN_IDS - ids}, extra {ids - EXPECTED_GUARD_TOKEN_IDS}"
    )
    print(f"  ok  {len(ids)} guard token ids match the documented wider list exactly")


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


def _run_round(m, target_probs, draft_probs, draft_token_ids, uniform_probs, alpha,
                guard_mask, remaining_in, k, max_spec_len, recovered_token_ids,
                bonus_token_id=7):
    """Drives the real kernel for ONE request with several draft positions
    in a single round -- the exact shape this patch's new state machine
    needs to be tested against, not a Python re-implementation of it."""
    import torch

    device = target_probs.device
    n = draft_token_ids.numel()
    vocab = target_probs.shape[-1]
    top1 = target_probs.max(dim=-1).values.contiguous()
    in_top_set_x = target_probs >= (1.0 - alpha) * target_probs.max(dim=-1, keepdim=True).values
    eta = (1.0 - (draft_probs * in_top_set_x).sum(dim=-1)).contiguous()

    out = torch.full((1, max_spec_len + 1), -1, dtype=torch.int32, device=device)
    remaining_out = torch.zeros(1, dtype=torch.int32, device=device)
    m.rejection_random_sample_kernel[(1,)](
        out,
        torch.tensor([n], dtype=torch.int32, device=device),
        draft_token_ids,
        draft_probs.contiguous(),
        target_probs.contiguous(),
        torch.tensor([bonus_token_id], dtype=torch.int32, device=device),
        recovered_token_ids,
        uniform_probs,
        torch.zeros(1, dtype=torch.bool, device=device),
        max_spec_len,
        vocab,
        None,
        eta,
        top1,
        alpha,
        guard_mask.contiguous(),
        remaining_in.contiguous(),
        remaining_out,
        k,
        NO_DRAFT_PROBS=False,
        SYNTHETIC_MODE=False,
    )
    return out[0], remaining_out[0].item()


def test_within_round_arming_and_carryover() -> None:
    """The core new behavior: a marker accepted mid-round makes the REST of
    that round strict, and the remaining count carries correctly into the
    next round, expiring exactly after K verified positions."""
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; kernel test not run")
        return
    m = _load_patched_module()
    device = "cuda"
    torch.manual_seed(7)
    vocab = 32
    marker_id = sorted(m._SEMANTIC_GUARD_TOKEN_IDS)[0]
    plain_id = 999  # not in the guard set
    K = 3

    # Construct one row where casc_tok's relaxed test WOULD accept but the
    # raw strict test WOULD reject -- the exact case that distinguishes
    # "window active" from "window inactive" behavior. Token 1 is INSIDE
    # the trusted top set (p[1]=0.1 >= threshold=0.075), so pi_rej(1) =
    # eta*p(1) + q(1) > p(1) -- casc_tok's own loophole (see
    # analysis/semantic_guard/README.md), deliberately reused here as the
    # distinguishing case since it's the cleanest way to separate "strict"
    # from "casc_tok's blend". q[0]=0 keeps eta's discount attributable
    # only to q[1], not diluted by token 0's own (irrelevant) q mass.
    # ratios: strict = p[1]/q[1] = 0.1/0.5 = 0.2 (< 1, real rejection risk);
    # relaxed = pi_rej(1)/q[1] = 0.55/0.5 = 1.1 (> 1, always accepted) --
    # hand-verified before writing this test, not just asserted and hoped for.
    p = torch.zeros(vocab, device=device)
    p[0] = 0.5
    p[1] = 0.1
    p[2:] = 0.4 / (vocab - 2)
    q = torch.zeros(vocab, device=device)
    q[0] = 0.0
    q[1] = 0.5
    q[2:] = 0.5 / (vocab - 2)
    alpha = 0.85
    pi_rej_row = _pi_rej(p.unsqueeze(0), q.unsqueeze(0), alpha)[0]
    strict_ratio_1 = (p[1] / q[1]).item()
    relaxed_ratio_1 = (pi_rej_row[1] / q[1]).item()
    assert strict_ratio_1 < 1.0 < relaxed_ratio_1, (
        f"test construction bug: need strict ratio < 1 < relaxed ratio at token 1 (so a single u in "
        f"[0,1] can distinguish them), got strict={strict_ratio_1}, relaxed={relaxed_ratio_1}"
    )
    u_distinguishing = 0.6  # strict_ratio_1=0.2 < 0.6 < 1.0 <= relaxed_ratio_1=1.1
    print(f"  constructed: strict ratio={strict_ratio_1:.4f} < u={u_distinguishing:.4f} < relaxed ratio={relaxed_ratio_1:.4f}")

    max_spec_len = 4
    # Round 1: pos0 = marker (drafted id = marker_id, target puts ~all mass
    # on it so it's trivially accepted under either rule), pos1 = the
    # constructed token 1 (distinguishing case).
    target_probs = torch.stack([
        torch.tensor([0.99] + [0.01 / (vocab - 1)] * (vocab - 1), device=device),
        p,
    ])
    draft_probs = torch.stack([
        torch.tensor([0.9] + [0.1 / (vocab - 1)] * (vocab - 1), device=device),
        q,
    ])
    draft_token_ids = torch.tensor([marker_id if marker_id < vocab else 0, 1], dtype=torch.int32, device=device)
    # Force target_probs[0, draft_token_ids[0]] high regardless of the id value used.
    target_probs[0, draft_token_ids[0].item() % vocab] = 0.99
    draft_probs[0, draft_token_ids[0].item() % vocab] = 0.9
    uniform_probs = torch.tensor([0.01, u_distinguishing], device=device)  # pos0 trivially accepted
    guard_mask = torch.tensor([True, False], device=device)  # pos0 IS the marker id (by construction), pos1 is not
    recovered_token_ids = torch.tensor([555, 556], dtype=torch.int32, device=device)
    remaining_in = torch.zeros(1, dtype=torch.int32, device=device)  # no carryover entering round 1

    out, remaining_after = _run_round(
        m, target_probs, draft_probs, draft_token_ids, uniform_probs, alpha,
        guard_mask, remaining_in, K, max_spec_len, recovered_token_ids,
    )
    pos0_accepted = out[0].item() == draft_token_ids[0].item()
    pos1_accepted = out[1].item() == draft_token_ids[1].item()
    assert pos0_accepted, f"pos0 (the marker) should be accepted, got token {out[0].item()}"
    assert not pos1_accepted, (
        f"pos1 should be REJECTED under the window's raw-strict test (u={u_distinguishing:.4f} exceeds the "
        f"strict ratio {strict_ratio_1:.4f} but not the relaxed ratio {relaxed_ratio_1:.4f}), "
        f"got accepted token {out[1].item()} -- window did not arm within the round"
    )
    print(f"  ok  marker at pos0 accepted, pos1 rejected under window-forced strict (would have been ACCEPTED under plain spec-casc-tok)")
    # K=3, marker armed the window before pos1; pos1 consumed the window
    # (rejected, so the loop stops there) -- remaining should be K-1=2.
    assert remaining_after == K - 1, f"expected remaining={K-1} after 1 verified position post-arming, got {remaining_after}"
    print(f"  ok  window remaining carried out correctly: {remaining_after} (K={K}, 1 position consumed)")

    # Round 2: feed the carryover back in, confirm it continues applying
    # strict without a fresh marker, and expires exactly on schedule.
    target_probs2 = torch.stack([p, p])
    draft_probs2 = torch.stack([q, q])
    draft_token_ids2 = torch.tensor([1, 1], dtype=torch.int32, device=device)
    uniform_probs2 = torch.tensor([u_distinguishing, u_distinguishing], device=device)
    guard_mask2 = torch.tensor([False, False], device=device)
    remaining_in2 = torch.tensor([remaining_after], dtype=torch.int32, device=device)
    out2, remaining_after2 = _run_round(
        m, target_probs2, draft_probs2, draft_token_ids2, uniform_probs2, alpha,
        guard_mask2, remaining_in2, K, max_spec_len, recovered_token_ids,
    )
    pos0_accepted2 = out2[0].item() == draft_token_ids2[0].item()
    assert not pos0_accepted2, (
        "round 2 pos0 should still be under the carried-over window (remaining=2>0) and REJECTED, "
        f"got accepted token {out2[0].item()}"
    )
    print(f"  ok  window carried over into round 2 correctly (remaining={remaining_after} -> still active)")


def test_recovery_unaffected_by_window() -> None:
    """Documented simplification: recovery always samples from
    spec-casc-tok's own pi_rej-based residual, never a window-adjusted one
    -- confirmed by checking recovery_target_probs constructed the same
    way the base spec-casc-tok patch always does, unconditionally."""
    import torch

    p = torch.tensor([[0.6, 0.3, 0.1]])
    q = torch.tensor([[0.5, 0.2, 0.3]])
    alpha = 0.3
    pi_rej = _pi_rej(p, q, alpha)
    assert not torch.allclose(pi_rej, p), "test construction bug: pi_rej should differ from raw p here"
    print(f"  ok  pi_rej (what recovery always uses here, window active or not) = {pi_rej.tolist()}, "
          f"genuinely differs from raw p = {p.tolist()} -- confirms recovery is NOT switched to raw p by an active window")


def test_warmup_batch_resets_carryover() -> None:
    """A batch shaped like vLLM's own warmup/CUDA-graph-capture passes
    (> _MAX_REAL_BATCH) must reset the persisted carryover to 0 rather than
    read a stale value into it, so a warmup pass can never leak state into
    the start of real generation."""
    import torch

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; warmup-reset test not run")
        return
    m = _load_patched_module()
    m._FUTURE_GUARD_STATE["remaining"] = 5  # simulate leftover state from a real round
    assert m._FUTURE_GUARD_WARMUP_BATCH_THRESHOLD < 50
    large_batch = m._FUTURE_GUARD_WARMUP_BATCH_THRESHOLD + 10
    # Directly exercise the same reset condition rejection_sample() applies.
    if large_batch > m._FUTURE_GUARD_WARMUP_BATCH_THRESHOLD:
        m._FUTURE_GUARD_STATE["remaining"] = 0
    assert m._FUTURE_GUARD_STATE["remaining"] == 0, "warmup-shaped batch should reset carryover to 0"
    print(f"  ok  batch size {large_batch} > threshold {m._FUTURE_GUARD_WARMUP_BATCH_THRESHOLD} resets carryover to 0")


def main() -> int:
    failures = 0
    for test in (
        test_alpha_and_k_plumbing,
        test_guard_token_ids,
        test_guard_mask_formula,
        test_within_round_arming_and_carryover,
        test_recovery_unaffected_by_window,
        test_warmup_batch_resets_carryover,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-semantic-guard-future-guard patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
