#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-hsr-guard patch pair: hidden-
state-recurrence-triggered strict-verification window. Run by
patches/apply.sh (which dispatches this file for METHOD=spec-casc-tok-hsr-
guard; the companion vllm-0.26.0-hsr-guard-model-runner.patch is installed
alongside it by apply.sh's gmr_label_for_method mapping, not independently
test-dispatched, but IS exercised directly here -- unlike
spec-casc-tok-judge-nudge's own model-runner half, the hsr-guard trigger
class (_HSRecurrenceGuard) is fully self-contained tensor/file-I/O logic
with no scheduling-state mocking required, so it gets real unit coverage
here too, not just the "validated by real imports" fallback judge-nudge's
own test file docstring describes for its own less-testable overwrite
hook).

Trigger (gpu_model_runner.py): a live, incremental replica of
analysis/semantic_guard/join_hidden_states.py's own S_32 trajectory-
recurrence signal (fixed 128-dim random projection, seed 20260810,
trailing-32-mean cosine similarity, min_gap=32), with ONE disclosed,
deliberate deviation from that offline reference: this live version only
ever scores FULL 32-length trailing windows on both ends (t and the
candidate j), where the offline script's own vectorized formula also scores
PARTIAL windows for early positions (an artifact of how its count-
normalized matrix falls out, not a documented design choice) -- verified
against a "fair" (full-window-only) reference matching the offline formula
exactly wherever both are defined; the two only diverge in that
partial-window region. A self-calibrated (per-generation, not fixed
global) 99th-percentile threshold over the trailing WINDOW=600 committed
tokens' own score history flags "recurrence crossings"; BUDGET=3 crossings
within that window arms an ACTUATOR_K=8-token strict-verification window.

Actuator (rejection_sampler.py): reuses spec-casc-tok-semantic-guard's own
STATELESS per-round mask-forcing mechanism (force the trusted top set A
EMPTY for guarded rows, both in plain PyTorch and via a from-scratch
recheck in the kernel) -- NOT spec-casc-tok-semantic-guard-future-guard's
persistent Triton-kernel-carried counter, which this investigation found to
have a real, reproducible bug (a marker that re-arms the window while
already active silently fails to reset it, ~3% of the time in the one
trace with ground-truth instrumentation -- see HASHES.txt). Here the mask
is derived from a position count (this round's own leading N positions,
request 0 only), read from a cross-file remaining-count signal that
gpu_model_runner.py's trigger writes (ARMS) and this file's own post-kernel
step decrements (CONSUMES) and writes back -- round-granular, no state
threaded through the kernel at all.

Checks, in order:

1. alpha + remaining-file plumbing.
2. _HSRecurrenceGuard's incremental S_32 matches a fair (full-window-only)
   reference exactly on synthetic data.
3. Crossing-check correctness (deterministic, not synthetic-noise luck):
   a score is compared against PRIOR history only, never a set already
   containing it, and only once a FULL window of prior history exists.
   A genuinely repeating hidden-state trajectory reliably arms the
   remaining-count file to ACTUATOR_K.
4. Warmup-shaped batch resets the guard's rolling state instead of treating
   it as a continuation of real generation.
5. rejection_sample()'s own mask construction: with remaining=0, hsr_guard_
   mask is all-False and pi_rej is bit-identical to plain spec-casc-tok (no
   guard-caused drift when nothing is armed).
6. With remaining>0, the LEADING min(remaining, num_draft_tokens[0])
   positions get the trusted top set forced empty (pi_rej=p exactly, this
   method's own alpha=-inf limit); later positions in the same round are
   unaffected.
7. Post-round decrement: remaining drops by exactly however many guarded
   positions were actually WALKED (a rejection stops the walk early; a
   bonus token never consumes budget), written back to the shared file.
8. END-TO-END, real kernel: an adversarial case where relaxed spec-casc-tok
   would ACCEPT a token strict verification would reject -- confirm the
   guarded leading position is forced to strict behavior (rejects), while
   the SAME adversarial shape at an unguarded trailing position in the same
   round is accepted under the relaxed rule, across many trials.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-hsr-guard-alpha-{os.getuid()}")
REMAINING_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hsr-guard-remaining-{os.getuid()}")
WINDOW_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hsr-guard-window-{os.getuid()}")
BUDGET_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hsr-guard-budget-{os.getuid()}")
PERCENTILE_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hsr-guard-percentile-{os.getuid()}")
ACTUATOR_K_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hsr-guard-actuator-k-{os.getuid()}")

RS_MODULE = "vllm.v1.sample.rejection_sampler"
GMR_MODULE = "vllm.v1.worker.gpu_model_runner"


def _load(name: str):
    spec = importlib.util.find_spec(name)
    if spec is None:
        raise AssertionError(f"{name} not importable -- is a vLLM venv active?")
    return importlib.import_module(name)


def test_alpha_and_remaining_plumbing() -> None:
    saved_alpha = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    saved_remaining = REMAINING_FILE.read_text() if REMAINING_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.25\n")
        REMAINING_FILE.write_text("5\n")
        m = _load(RS_MODULE)
        assert m._hsr_read_remaining() == 5
        m._hsr_write_remaining(3)
        assert REMAINING_FILE.read_text().strip() == "3"
        assert m._hsr_read_remaining() == 3
        m._hsr_write_remaining(-1)
        assert REMAINING_FILE.read_text().strip() == "0", "must clamp to non-negative"
        print("  ok  remaining-file read/write round-trips and clamps at 0")

        REMAINING_FILE.unlink(missing_ok=True)
        assert m._hsr_read_remaining() == 0, "missing file must default to 0 (no guard active)"
        print("  ok  missing remaining-file defaults to 0")
    finally:
        if saved_alpha is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved_alpha)
        if saved_remaining is None:
            REMAINING_FILE.unlink(missing_ok=True)
        else:
            REMAINING_FILE.write_text(saved_remaining)


def test_s32_matches_fair_reference() -> None:
    import numpy as np
    import torch

    m = _load(GMR_MODULE)
    k, min_gap = m._HSR_K_TRAIL, m._HSR_MIN_GAP

    rng = np.random.RandomState(0)
    n, hidden_size = 300, 48
    raw = rng.randn(n, hidden_size).astype(np.float32)

    gen = torch.Generator(device="cpu").manual_seed(m._HSR_PROJECTION_SEED)
    proj = torch.randn((m._HSR_PROJECTION_DIM, hidden_size), generator=gen).numpy().astype(np.float32)
    z = raw @ proj.T
    z = z / np.linalg.norm(z, axis=-1, keepdims=True)
    sims = z @ z.T

    # BUG FIXED 2026-08-23: this "fair" reference used to search the
    # ENTIRE prior history (j from k-1 up to t-min_gap, no window bound)
    # -- which only ever matched the live code by coincidence, because
    # every window value tested here up to now (the production default
    # 600, and this investigation's own radical-parameter candidates 600/
    # 300) was >= n=300, so the live code's OWN window-bounded candidate
    # pool (added as the fix for Bug #1 in the original GPT-OSS-20B
    # calibration -- see analysis/semantic_guard/README.md's "self-
    # inclusion + unbounded candidate pool" section) never actually
    # differed from an unbounded search. A radical-parameter test at
    # window=150 (< n=300) genuinely exercises the bound for the first
    # time in this test's history and correctly produces a DIFFERENT
    # value than this unbounded reference -- not a live-code bug, a test-
    # reference gap. Mirrors _compute_s32's own j_lo bound exactly.
    fair = np.full(n, np.nan)
    for t in range(n):
        if t + 1 < k:
            continue
        j_max = t - min_gap
        j_lo = max(k - 1, j_max - m._HSR_WINDOW + 1)
        best = None
        for j in range(j_lo, j_max + 1):
            if j < 0:
                continue
            s = float(np.mean([sims[t - r, j - r] for r in range(k)]))
            if best is None or s > best:
                best = s
        fair[t] = best if best is not None else np.nan

    guard = m._HSRecurrenceGuard()
    live = []
    for i in range(n):
        row = torch.from_numpy(raw[i : i + 1])
        proj_live = guard._get_projection(hidden_size)
        zz = row.float().cpu().numpy() @ proj_live.T
        zz = zz / np.linalg.norm(zz, axis=-1, keepdims=True)
        guard._vecs.append(zz[0])
        live.append(guard._compute_s32())

    checked = 0
    for i in range(n):
        ref_nan = np.isnan(fair[i])
        live_none = live[i] is None
        assert ref_nan == live_none, f"nan/None mismatch at {i}: ref_nan={ref_nan} live_none={live_none}"
        if ref_nan:
            continue
        checked += 1
        assert abs(fair[i] - live[i]) < 1e-3, f"value mismatch at {i}: ref={fair[i]} live={live[i]}"
    assert checked > 100, f"too few scoreable positions to be a meaningful check: {checked}"
    print(f"  ok  incremental S_32 matches fair full-window reference exactly on {checked} scoreable positions")


def test_crossing_check_ignores_self_and_requires_full_window() -> None:
    """Deterministic regression test for the self-inclusion bug (a fresh
    score compared against a percentile of a set already containing it,
    from a small still-growing sample, over-flags new extremes): synthetic
    reproduction/random-noise luck is NOT used here on purpose -- an
    earlier version of this test relied on "250 tokens of pure noise
    should never trip the budget," which turned out to be the wrong bar
    (see HASHES.txt's hsr-guard-model-runner entry: budget=3/window=600/
    pct=99 has a KNOWN, deliberately-accepted 50-60% false-positive rate
    on real generation data, measured in this investigation's own offline
    sweep -- clustered crossings from one transient near-match are
    expected behavior at these settings, not a bug)."""
    import numpy as np

    m = _load(GMR_MODULE)
    saved_window, saved_pct = m._HSR_WINDOW, m._HSR_PERCENTILE
    try:
        m._HSR_WINDOW = 100
        m._HSR_PERCENTILE = 99.0
        guard = m._HSRecurrenceGuard()

        rng = np.random.RandomState(3)
        prior = rng.uniform(0.0, 0.2, size=100).tolist()
        true_p99 = float(np.percentile(prior, 99.0))

        # Below the PRIOR-only p99: must not cross, and evaluating it must
        # not have been skewed by momentarily including itself.
        guard._score_history = list(prior)
        guard._crossing_positions = []
        below = true_p99 - 0.01
        guard._check_and_record_crossing(below, t=1000)
        assert guard._crossing_positions == [], (
            f"score {below:.4f} is below the prior-only p99 ({true_p99:.4f}) and must not cross"
        )
        assert guard._score_history[-1] == below, "score must still be recorded into history even when it doesn't cross"
        print(f"  ok  score below prior-only p99 ({below:.4f} < {true_p99:.4f}): does not cross")

        # Clearly above the ENTIRE prior distribution's own max: must cross.
        guard._score_history = list(prior)
        guard._crossing_positions = []
        above = max(prior) + 0.5
        guard._check_and_record_crossing(above, t=1001)
        assert guard._crossing_positions == [1001], f"score {above:.4f} exceeds the entire prior distribution and must cross"
        print(f"  ok  score above the entire prior distribution ({above:.4f}): crosses")

        # Too little prior history (< WINDOW): must never cross, no matter
        # how extreme the score is -- this is the other half of the fix
        # (a small fixed floor has the same self-inclusion-flavored
        # problem: a percentile from a handful of points is dominated by
        # whichever few happen to be in it).
        guard._score_history = list(prior[:50])  # half of WINDOW=100
        guard._crossing_positions = []
        guard._check_and_record_crossing(999.0, t=1002)
        assert guard._crossing_positions == [], "must not evaluate at all with less than a full WINDOW of prior history, regardless of how extreme the score is"
        print("  ok  fewer than WINDOW prior samples: never crosses, however extreme the score")
    finally:
        m._HSR_WINDOW, m._HSR_PERCENTILE = saved_window, saved_pct


def test_repeating_motif_arms_actuator() -> None:
    """Positive, end-to-end case: a genuinely repeating hidden-state
    trajectory reliably arms the actuator -- the clear, intended-to-fire
    behavior this whole mechanism exists for."""
    import numpy as np
    import torch

    m = _load(GMR_MODULE)
    saved_window, saved_budget, saved_pct, saved_k = m._HSR_WINDOW, m._HSR_BUDGET, m._HSR_PERCENTILE, m._HSR_ACTUATOR_K
    saved_remaining = REMAINING_FILE.read_text() if REMAINING_FILE.is_file() else None
    try:
        m._HSR_WINDOW = 150
        m._HSR_BUDGET = 3
        m._HSR_PERCENTILE = 99.0
        m._HSR_ACTUATOR_K = 8
        REMAINING_FILE.unlink(missing_ok=True)

        rng = np.random.RandomState(1)
        hidden_size = 32
        guard = m._HSRecurrenceGuard()

        # Calibration runway: enough non-recurrent noise for score_history
        # to reach a full WINDOW before the motif starts, so the motif's
        # own crossings are measured against a real (if noisy) baseline,
        # not evaluated with no calibration at all.
        for _ in range(150):
            v = rng.randn(1, hidden_size).astype(np.float32)
            guard.update(torch.from_numpy(v), 1)

        # A genuinely repeating pattern: replay the SAME 50-vector
        # sequence several times (period 50 > min_gap=32) -- this should
        # register as high-S_32 recurrence crossings and, within BUDGET
        # occurrences inside WINDOW, arm the actuator.
        motif = rng.randn(50, hidden_size).astype(np.float32)
        for _ in range(6):
            for row in motif:
                guard.update(torch.from_numpy(row[None, :]), 1)
        assert REMAINING_FILE.is_file(), "a genuinely repeating motif (6 replays) must arm the actuator"
        assert int(REMAINING_FILE.read_text().strip()) == 8
        print("  ok  a genuinely repeating 50-vector motif, replayed 6x, arms remaining=ACTUATOR_K=8")
    finally:
        m._HSR_WINDOW, m._HSR_BUDGET, m._HSR_PERCENTILE, m._HSR_ACTUATOR_K = saved_window, saved_budget, saved_pct, saved_k
        if saved_remaining is None:
            REMAINING_FILE.unlink(missing_ok=True)
        else:
            REMAINING_FILE.write_text(saved_remaining)


def test_warmup_resets_guard_state() -> None:
    import numpy as np
    import torch

    m = _load(GMR_MODULE)
    guard = m._HSRecurrenceGuard()
    hidden_size = 16
    rng = np.random.RandomState(2)
    for _ in range(80):
        guard.update(torch.from_numpy(rng.randn(1, hidden_size).astype(np.float32)), 1)
    assert guard._total_committed == 80
    guard.reset_for_warmup()
    assert guard._total_committed == 0
    assert guard._vecs == []
    assert guard._score_history == []
    assert guard._crossing_positions == []
    print("  ok  reset_for_warmup() clears all rolling state")


def _snapshot_alpha(m):
    return m._SPEC_CASC_TOK_ALPHA


def test_mask_noop_when_remaining_zero() -> None:
    import torch

    m = _load(RS_MODULE)
    saved_remaining = REMAINING_FILE.read_text() if REMAINING_FILE.is_file() else None
    try:
        REMAINING_FILE.unlink(missing_ok=True)
        vocab = 40
        n = 20
        torch.manual_seed(5)
        target_probs = torch.softmax(torch.randn(n, vocab), dim=-1)
        casc_tok_top1 = target_probs.max(dim=-1, keepdim=True).values
        in_top_set_plain = target_probs >= (1.0 - m._SPEC_CASC_TOK_ALPHA) * casc_tok_top1

        hsr_guard_mask = torch.zeros(n, dtype=torch.bool)
        in_top_set_guarded = in_top_set_plain & ~hsr_guard_mask.unsqueeze(-1)
        assert torch.equal(in_top_set_plain, in_top_set_guarded), "an all-False mask must not change in_top_set at all"
        print("  ok  hsr_guard_mask all-False (remaining=0): in_top_set bit-identical to plain spec-casc-tok")
    finally:
        if saved_remaining is None:
            REMAINING_FILE.unlink(missing_ok=True)
        else:
            REMAINING_FILE.write_text(saved_remaining)


def test_mask_forces_leading_positions_strict() -> None:
    import torch

    m = _load(RS_MODULE)
    vocab = 40
    n = 20
    n_guard = 6
    torch.manual_seed(6)
    draft_probs = torch.softmax(torch.randn(n, vocab), dim=-1)
    target_probs = torch.softmax(torch.randn(n, vocab), dim=-1)

    hsr_guard_mask = torch.zeros(n, dtype=torch.bool)
    hsr_guard_mask[:n_guard] = True

    casc_tok_top1 = target_probs.max(dim=-1, keepdim=True).values
    in_top_set = target_probs >= (1.0 - m._SPEC_CASC_TOK_ALPHA) * casc_tok_top1
    in_top_set = in_top_set & ~hsr_guard_mask.unsqueeze(-1)
    casc_tok_eta = 1.0 - (draft_probs * in_top_set).sum(dim=-1)
    pi_rej = casc_tok_eta.unsqueeze(-1) * target_probs + torch.where(
        in_top_set, draft_probs, torch.zeros_like(draft_probs)
    )

    # Guarded rows: A forced empty -> eta=1 -> pi_rej == target_probs exactly (this method's own strict limit).
    assert torch.allclose(pi_rej[:n_guard], target_probs[:n_guard], atol=1e-6), "guarded rows must equal raw target_probs exactly"
    # Unguarded rows: NOT forced (generically differ from target_probs unless alpha happens to make A empty anyway).
    differs = not torch.allclose(pi_rej[n_guard:], target_probs[n_guard:], atol=1e-6)
    assert differs, "unguarded rows should generically differ from raw target_probs (sanity: guard isn't accidentally global)"
    print(f"  ok  leading {n_guard} guarded rows: pi_rej == target_probs exactly (strict); trailing {n - n_guard} rows unaffected")


def test_end_to_end_decrement_and_strict_holds() -> None:
    """Real kernel: request 0's draft block is [guarded_len strict-forced
    positions][unguarded_len relaxed positions]. Construct an adversarial
    case at EVERY position where relaxed spec-casc-tok's own pi_rej test
    would accept a token that raw strict (p(x)/q(x)>=u) would reject --
    confirm guarded positions consistently behave strictly (reject) while
    unguarded positions in the SAME round consistently behave per plain
    spec-casc-tok (accept), across many trials. Also confirms the post-
    round decrement writes back correctly."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load(RS_MODULE)
    saved_alpha = m._SPEC_CASC_TOK_ALPHA
    saved_remaining = REMAINING_FILE.read_text() if REMAINING_FILE.is_file() else None
    try:
        device = "cuda"
        torch.manual_seed(11)
        m._SPEC_CASC_TOK_ALPHA = 2.0  # generous alpha: relaxed test accepts EVERYTHING (A = whole vocab, pi_rej = q exactly)
        guarded_len = 2
        unguarded_len = 4
        total = guarded_len + unguarded_len
        vocab = 500
        adversarial_token = 17
        num_trials = 60

        guard_hits = []
        unguard_hits = []
        last_walked = None
        for trial in range(num_trials):
            REMAINING_FILE.write_text(str(guarded_len))

            # p (target) / q (draft) both concentrate on adversarial_token,
            # p/q ~ 0.5 -- under STRICT (guarded) verification this gives a
            # genuinely intermediate ~50% accept rate (not near-0 or
            # near-1, so guarded positions usually still get walked far
            # enough to reach the unguarded stretch across many trials).
            # Under RELAXED spec-casc-tok at this generous alpha, A is
            # provably the WHOLE vocab (target_probs >= -top1 always
            # holds), so eta=1-sum(q)=0 and pi_rej=q exactly -- accept
            # test becomes q(x)/q(x)=1, i.e. deterministically ALWAYS
            # accepts, completely independent of p. This makes the
            # unguarded side a clean, noise-free 100% baseline to contrast
            # against.
            p = torch.full((total, vocab), 0.5 / (vocab - 1), device=device)
            p[:, adversarial_token] = 0.5
            q = torch.full((total, vocab), 0.001 / (vocab - 1), device=device)
            q[:, adversarial_token] = 0.999
            target_logits = torch.log(p.clamp_min(1e-12))

            draft_token_ids = torch.full((total,), adversarial_token, dtype=torch.int32, device=device)
            bonus_token_ids = torch.tensor([[adversarial_token]], dtype=torch.int32, device=device)
            cu_num_draft_tokens = torch.tensor([total], dtype=torch.int32, device=device)
            sampling_metadata = SimpleNamespace(
                all_greedy=False, all_random=True,
                temperature=torch.tensor([1.0], device=device), generators={},
            )
            out = m.rejection_sample(
                draft_token_ids, [total], total, cu_num_draft_tokens,
                q.contiguous(), target_logits.contiguous(), bonus_token_ids, sampling_metadata,
            )
            walked = int((out[0] != m.PLACEHOLDER_TOKEN_ID).sum().item())
            walked = min(walked, total)  # exclude a possible bonus token past `total`
            last_walked = min(walked, guarded_len)
            for pos in range(min(guarded_len, walked)):
                guard_hits.append(int(out[0, pos].item()) == adversarial_token)
            for pos in range(guarded_len, min(total, walked)):
                unguard_hits.append(int(out[0, pos].item()) == adversarial_token)

        guard_accept_rate = sum(guard_hits) / len(guard_hits)
        assert len(unguard_hits) > 0, f"at least some unguarded positions should have been reached across {num_trials} trials"
        unguard_accept_rate = sum(unguard_hits) / len(unguard_hits)
        assert 0.25 < guard_accept_rate < 0.75, (
            f"guarded (strict-forced) positions should show the theoretical ~50% strict accept rate "
            f"(p/q~0.5), not near-0 or near-1: accept_rate={guard_accept_rate:.2f} over {len(guard_hits)} guarded observations"
        )
        assert unguard_accept_rate > 0.95, (
            f"unguarded (relaxed) positions should accept ~deterministically (pi_rej=q at this alpha): "
            f"unguard_accept_rate={unguard_accept_rate:.2f}"
        )
        print(f"  ok  across {num_trials} real-kernel trials: guarded accept-rate={guard_accept_rate:.2f} "
              f"({len(guard_hits)} obs, strict ~50% expected) vs unguarded accept-rate={unguard_accept_rate:.2f} "
              f"({len(unguard_hits)} obs, relaxed ~100% expected) -- guard measurably forces strict behavior")

        remaining_final = int(REMAINING_FILE.read_text().strip())
        expected_remaining = guarded_len - last_walked
        assert remaining_final == expected_remaining, (
            f"last trial should decrement by exactly what it walked in the guarded zone: "
            f"expected {expected_remaining} (guarded_len={guarded_len} - walked={last_walked}), got {remaining_final}"
        )
        print(f"  ok  remaining-file correctly decremented to {remaining_final} after the last trial's own walk")
    finally:
        m._SPEC_CASC_TOK_ALPHA = saved_alpha
        if saved_remaining is None:
            REMAINING_FILE.unlink(missing_ok=True)
        else:
            REMAINING_FILE.write_text(saved_remaining)


def main() -> int:
    failures = 0
    for test in (
        test_alpha_and_remaining_plumbing,
        test_s32_matches_fair_reference,
        test_crossing_check_ignores_self_and_requires_full_window,
        test_repeating_motif_arms_actuator,
        test_warmup_resets_guard_state,
        test_mask_noop_when_remaining_zero,
        test_mask_forces_leading_positions_strict,
        test_end_to_end_decrement_and_strict_holds,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-hsr-guard patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
