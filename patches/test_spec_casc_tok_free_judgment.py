#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-free-judgment patch's
rejection_sampler.py half. Run by patches/apply.sh.

(The OTHER half -- vllm-0.26.0-free-judgment-model-runner.patch, which
overwrites the real sequence's own last drafted columns with the fixed
criterion pattern -- is not independently unit-testable here without
mocking a large fraction of gpu_model_runner.py's internal scheduling
state; its correctness is validated by a real server smoke test instead,
see analysis/semantic_guard/README.md.)

"Free judgment via extended verification span": exploits that EAGLE
verification is already ONE parallel forward pass over the whole drafted
block, so a fixed criterion-question sequence appended after the real
drafted tokens lets the target's SAME pass also compute a judgment, at
marginal FLOPs cost (not an extra round-trip) and zero real
generation-budget cost (the criterion tokens are always force-rejected
here, via BANNING the specific drafted token at the first criterion
position and renormalizing -- not zeroing the whole row, which was tried
and found to be a real bug: an all-zero row makes spec-casc-tok's own
trusted-top-set condition vacuously true everywhere, causing the accept
test to ALWAYS pass instead of always fail).

Checks, in order:

1. alpha/real-draft-len/trace-path/reject-threshold knob plumbing (the
   middle two intentionally SHARED with the gpu_model_runner.py half --
   see the patch's own module comment for why sharing is correct here,
   unlike every other cross-patch alpha file which must never be shared),
2. _free_judgment_apply is a no-op (same tensor, no trace write) when
   disabled, or when the round is too short to hold the full criterion,
3. _free_judgment_apply correctly bans the SPECIFIC criterion-position
   token and renormalizes (not zeroing the whole row), reads p_yes/p_no
   from the judgment position correctly, and writes a trace row,
4. REJECT-AND-RESAMPLE: when this round's score (p_yes - p_no) crosses
   _FREE_JUDGMENT_REJECT_THRESHOLD, apply() ALSO bans the last real
   drafted token (same ban-and-renormalize operation, not a forced
   pattern); below threshold, that position is left completely untouched.
   Stateless -- no EMA, no trend, nothing persisted across rounds (the
   design this replaces was proven, via a real 6-case rollout AND
   extensive offline replay against those traces, to have NO transform of
   this per-round reading that separates "needs it" from "doesn't" -- see
   analysis/semantic_guard/README.md -- so this design doesn't pretend to
   fix that; it just makes a false positive here cost one resampled
   token instead of a forced, unrelated paragraph),
5. _free_judgment_update: cross-round committed-token counting and
   warmup reset (all that's left to persist -- no mode/state machine),
6. END-TO-END: drive the REAL, unmodified rejection_sample() (real
   kernel) with a target distribution that puts ALL its mass on the
   criterion-position token the draft proposes, and confirm it is NEVER
   actually emitted across many trials -- the ban holds even against a
   maximally-adversarial (draft==target-favored) case, proving this is a
   real guarantee, not a probabilistic one.
7. END-TO-END REJECT-AND-RESAMPLE: same kernel, but this time also rig
   the LAST REAL position to be maximally adversarial (draft==target
   both strongly favor the same token there) AND rig the judgment row to
   score above threshold -- confirm the real position's drafted token is
   likewise never actually emitted, and that a genuinely different token
   (the resampled one) lands there instead. A companion low-score trial
   confirms the real position is untouched (normal accept/reject) when
   the trigger doesn't fire.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-free-judgment-alpha-{os.getuid()}")
REAL_DRAFT_LEN_FILE = pathlib.Path(f"/tmp/lossy-token-eff-free-judgment-real-draft-len-{os.getuid()}")
TRACE_PATH_FILE = pathlib.Path(f"/tmp/lossy-token-eff-free-judgment-trace-path-{os.getuid()}")
REJECT_THRESHOLD_FILE = pathlib.Path(f"/tmp/lossy-token-eff-free-judgment-reject-threshold-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "real_draft_len": m._FREE_JUDGMENT_REAL_DRAFT_LEN,
    "trace_dest": m._FREE_JUDGMENT_TRACE_DEST,
    "reject_threshold": m._FREE_JUDGMENT_REJECT_THRESHOLD,
}))
"""


def read_back_in_subprocess() -> dict[str, object]:
    proc = subprocess.run([sys.executable, "-c", READ_BACK, MODULE], capture_output=True, text=True)
    if proc.returncode != 0:
        raise AssertionError(f"import failed:\n{proc.stderr[-3000:]}")
    for line in proc.stdout.splitlines():
        if line.startswith("JSON:"):
            return json.loads(line[5:])
    raise AssertionError(f"no result from subprocess:\n{proc.stdout[-2000:]}")


def test_knob_plumbing() -> None:
    files = (ALPHA_FILE, REAL_DRAFT_LEN_FILE, TRACE_PATH_FILE, REJECT_THRESHOLD_FILE)
    saved = {f: (f.read_text() if f.is_file() else None) for f in files}
    try:
        ALPHA_FILE.write_text("0.6\n")
        REAL_DRAFT_LEN_FILE.write_text("6\n")
        TRACE_PATH_FILE.write_text("/tmp/some-trace.jsonl\n")
        REJECT_THRESHOLD_FILE.write_text("0.12\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.6, got
        assert got["real_draft_len"] == 6, got
        assert got["trace_dest"] == "/tmp/some-trace.jsonl", got
        assert got["reject_threshold"] == 0.12, got
        print("  ok  module reads all four knob files (real-draft-len and trace-path shared with the model-runner half by design)")

        for f in files:
            f.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        assert got["real_draft_len"] == 0, got
        assert got["trace_dest"] is None, got
        assert got["reject_threshold"] == 0.08, got
        print("  ok  missing files fall back to alpha=-inf, real_draft_len=0 (disabled), trace_dest=None, reject_threshold=0.08")
    finally:
        for f, content in saved.items():
            if content is None:
                f.unlink(missing_ok=True)
            else:
                f.write_text(content)


def _load_patched_module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def test_apply_noop_when_disabled_or_too_short() -> None:
    import torch

    m = _load_patched_module()
    saved_len = m._FREE_JUDGMENT_REAL_DRAFT_LEN
    try:
        vocab = 32
        target_probs = torch.full((30, vocab), 1.0 / vocab)
        draft_token_ids = torch.zeros(30, dtype=torch.int64)
        num_draft_tokens = [30]
        cu_num_draft_tokens = torch.tensor([30], dtype=torch.int64)

        m._FREE_JUDGMENT_REAL_DRAFT_LEN = 0
        out = m._free_judgment_apply(target_probs, draft_token_ids, num_draft_tokens, cu_num_draft_tokens)
        assert out is target_probs, "disabled (real_draft_len<=0) must be a pure no-op"
        print("  ok  disabled (real_draft_len<=0): pure no-op")

        m._FREE_JUDGMENT_REAL_DRAFT_LEN = 6
        short_num_draft_tokens = [6 + m._FREE_JUDGMENT_CRITERION_LEN - 1]  # one short of the full criterion
        short_cu = torch.tensor([short_num_draft_tokens[0]], dtype=torch.int64)
        short_target_probs = torch.full((short_num_draft_tokens[0], vocab), 1.0 / vocab)
        short_draft_ids = torch.zeros(short_num_draft_tokens[0], dtype=torch.int64)
        out = m._free_judgment_apply(short_target_probs, short_draft_ids, short_num_draft_tokens, short_cu)
        assert out is short_target_probs, "a round too short to hold the full criterion must be a no-op"
        print("  ok  round shorter than real_draft_len+criterion_len: pure no-op, no truncated/garbage forcing")
    finally:
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = saved_len


def _vocab_for(m) -> int:
    return max(
        list(m._FREE_JUDGMENT_YES_TOKEN_IDS) + list(m._FREE_JUDGMENT_NO_TOKEN_IDS)
        + list(m._FREE_JUDGMENT_CONFIDENT_TOKEN_IDS) + list(m._FREE_JUDGMENT_HEDGE_TOKEN_IDS)
    ) + 100


def test_apply_bans_criterion_and_reads_judgment() -> None:
    import torch

    m = _load_patched_module()
    saved_len = m._FREE_JUDGMENT_REAL_DRAFT_LEN
    saved_trace = m._FREE_JUDGMENT_TRACE_DEST
    saved_threshold = m._FREE_JUDGMENT_REJECT_THRESHOLD
    trace_file = pathlib.Path(f"/tmp/lossy-token-eff-test-free-judgment-trace-{os.getpid()}.jsonl")
    try:
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = 6
        m._FREE_JUDGMENT_TRACE_DEST = str(trace_file)
        m._FREE_JUDGMENT_REJECT_THRESHOLD = 0.5  # high enough that this test's own reading (below) never rejects
        trace_file.unlink(missing_ok=True)

        real_draft_len = 6
        criterion_len = m._FREE_JUDGMENT_CRITERION_LEN
        total = real_draft_len + criterion_len
        vocab = _vocab_for(m)

        target_probs = torch.full((total, vocab), 1.0 / vocab)
        # Rig the judgment row (the last position, right after the full
        # criterion) with a moderate "yes"-leaning reading, well below the
        # 0.5 threshold set above, so this test stays focused on the
        # criterion ban + trace-reading behavior (reject-threshold behavior
        # is its own test below).
        judgment_row = total - 1
        target_probs[judgment_row] = 0.0
        target_probs[judgment_row, m._FREE_JUDGMENT_YES_TOKEN_IDS[0]] = 0.15
        target_probs[judgment_row, m._FREE_JUDGMENT_NO_TOKEN_IDS[0]] = 0.05
        target_probs[judgment_row, m._FREE_JUDGMENT_HEDGE_TOKEN_IDS[0]] = 0.03
        target_probs[judgment_row, m._FREE_JUDGMENT_CONFIDENT_TOKEN_IDS[0]] = 0.01
        target_probs[judgment_row, 0] = 0.76

        draft_token_ids = torch.arange(total, dtype=torch.int64) % vocab
        criterion_start_row = real_draft_len
        real_last_row = criterion_start_row - 1
        banned_tok = int(draft_token_ids[criterion_start_row].item())
        real_last_tok = int(draft_token_ids[real_last_row].item())
        num_draft_tokens = [total]
        cu_num_draft_tokens = torch.tensor([total], dtype=torch.int64)

        out = m._free_judgment_apply(target_probs, draft_token_ids, num_draft_tokens, cu_num_draft_tokens)
        assert out is not target_probs, "must return a NEW tensor when banning fires"
        assert out[criterion_start_row, banned_tok].item() == 0.0, "the drafted token at the first criterion position must be banned"
        assert abs(out[criterion_start_row].sum().item() - 1.0) < 1e-5, "banned row must renormalize to a valid distribution"
        # Row must NOT be all-zero (the bug this patch's module comment
        # documents: an all-zero row makes the trusted-top-set condition
        # vacuously true everywhere, which flips the accept test to ALWAYS
        # pass instead of always fail).
        assert out[criterion_start_row].sum().item() > 0.0
        assert out[real_last_row, real_last_tok].item() == target_probs[real_last_row, real_last_tok].item(), (
            "below-threshold score must leave the real content untouched"
        )
        untouched_row = 0
        assert torch.allclose(out[untouched_row], target_probs[untouched_row]), "positions before the criterion must be untouched"
        print("  ok  bans the SPECIFIC criterion-position token and renormalizes (not zeroing the whole row); real content untouched below threshold")

        assert trace_file.is_file(), "must have written a trace row"
        row = json.loads(trace_file.read_text().splitlines()[-1])
        assert abs(row["p_yes"] - 0.15) < 1e-6, row
        assert abs(row["p_no"] - 0.05) < 1e-6, row
        assert abs(row["p_hedge"] - 0.03) < 1e-6, row
        assert abs(row["p_confident"] - 0.01) < 1e-6, row
        assert abs(row["score"] - 0.10) < 1e-6, f"score must be p_yes-p_no: {row}"
        assert row["rejected"] is False, "0.10 must not cross the 0.5 threshold set for this test"
        print(f"  ok  trace row correctly reads p_yes={row['p_yes']:.2f} p_no={row['p_no']:.2f} "
              f"score={row['score']:.2f} rejected={row['rejected']}")
    finally:
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = saved_len
        m._FREE_JUDGMENT_TRACE_DEST = saved_trace
        m._FREE_JUDGMENT_REJECT_THRESHOLD = saved_threshold
        trace_file.unlink(missing_ok=True)


def test_apply_reject_threshold_bans_real_token() -> None:
    """The reject-and-resample mechanism itself: crossing
    _FREE_JUDGMENT_REJECT_THRESHOLD must ALSO ban the last real drafted
    token (same ban-and-renormalize operation as the criterion token),
    on top of the criterion ban that always fires. Below threshold, that
    position must be left completely untouched -- checked directly above
    in test_apply_bans_criterion_and_reads_judgment, re-confirmed here as
    the negative case alongside the positive one for a direct A/B."""
    import torch

    m = _load_patched_module()
    saved_len = m._FREE_JUDGMENT_REAL_DRAFT_LEN
    saved_trace = m._FREE_JUDGMENT_TRACE_DEST
    saved_threshold = m._FREE_JUDGMENT_REJECT_THRESHOLD
    try:
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = 6
        m._FREE_JUDGMENT_TRACE_DEST = None
        m._FREE_JUDGMENT_REJECT_THRESHOLD = 0.08

        real_draft_len = 6
        criterion_len = m._FREE_JUDGMENT_CRITERION_LEN
        total = real_draft_len + criterion_len
        vocab = _vocab_for(m)
        judgment_row = total - 1
        criterion_start_row = real_draft_len
        real_last_row = criterion_start_row - 1

        def make_round(p_yes: float, p_no: float):
            target_probs = torch.full((total, vocab), 1.0 / vocab)
            target_probs[judgment_row] = 0.0
            target_probs[judgment_row, m._FREE_JUDGMENT_YES_TOKEN_IDS[0]] = p_yes
            target_probs[judgment_row, m._FREE_JUDGMENT_NO_TOKEN_IDS[0]] = p_no
            target_probs[judgment_row, 0] = max(1e-6, 1.0 - p_yes - p_no)
            draft_token_ids = torch.arange(total, dtype=torch.int64) % vocab
            return target_probs, draft_token_ids, [total], torch.tensor([total], dtype=torch.int64)

        # Below threshold (score=0.03 < 0.08): real content untouched.
        target_probs, draft_token_ids, ndt, cndt = make_round(p_yes=0.05, p_no=0.02)
        real_tok = int(draft_token_ids[real_last_row].item())
        out = m._free_judgment_apply(target_probs, draft_token_ids, ndt, cndt)
        assert out[real_last_row, real_tok].item() == target_probs[real_last_row, real_tok].item(), (
            "score below threshold must leave the real content position completely untouched"
        )
        print("  ok  score below threshold (0.03 < 0.08): last real drafted token left untouched")

        # Above threshold (score=0.15 > 0.08): real content's drafted
        # token must be banned and its row renormalized, same as the
        # criterion ban -- NOT a forced pattern, no specific replacement
        # token asserted (that's rejection sampling's own job at kernel
        # time, checked end-to-end below).
        target_probs, draft_token_ids, ndt, cndt = make_round(p_yes=0.20, p_no=0.05)
        real_tok = int(draft_token_ids[real_last_row].item())
        out = m._free_judgment_apply(target_probs, draft_token_ids, ndt, cndt)
        assert out is not target_probs, "must return a NEW tensor when the reject ban fires"
        assert out[real_last_row, real_tok].item() == 0.0, "score above threshold must ban the last real drafted token"
        assert abs(out[real_last_row].sum().item() - 1.0) < 1e-5, "banned real-content row must renormalize to a valid distribution"
        assert out[real_last_row].sum().item() > 0.0, "must not be zeroed to an all-zero row (same bug class as the criterion ban)"
        # Position BEFORE the last real one must be untouched -- only the
        # single last real position is ever touched by this mechanism.
        earlier_row = real_last_row - 1
        assert torch.allclose(out[earlier_row], target_probs[earlier_row]), "only the LAST real position should ever be banned, not earlier ones"
        print("  ok  score above threshold (0.15 > 0.08): last real drafted token banned + renormalized (single position only, no forced pattern)")
    finally:
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = saved_len
        m._FREE_JUDGMENT_TRACE_DEST = saved_trace
        m._FREE_JUDGMENT_REJECT_THRESHOLD = saved_threshold


def test_update_tracks_committed_tokens() -> None:
    import torch

    m = _load_patched_module()
    saved_state = dict(m._FREE_JUDGMENT_STATE)
    try:
        m._FREE_JUDGMENT_STATE["committed_before"] = 0
        PLACEHOLDER = m.PLACEHOLDER_TOKEN_ID
        round1 = torch.tensor([[1, 2, 3, PLACEHOLDER]], dtype=torch.int32)
        m._free_judgment_update(round1, batch_size=1)
        assert m._FREE_JUDGMENT_STATE["committed_before"] == 3
        round2 = torch.tensor([[4, PLACEHOLDER, PLACEHOLDER, PLACEHOLDER]], dtype=torch.int32)
        m._free_judgment_update(round2, batch_size=1)
        assert m._FREE_JUDGMENT_STATE["committed_before"] == 4
        print("  ok  cross-round committed-token count accumulates real tokens, ignores PLACEHOLDER padding")

        assert m._FREE_JUDGMENT_WARMUP_BATCH_THRESHOLD < 50
        n = m._FREE_JUDGMENT_WARMUP_BATCH_THRESHOLD + 10
        warmup_round = torch.full((n, 2), 1, dtype=torch.int32)
        m._free_judgment_update(warmup_round, batch_size=n)
        assert m._FREE_JUDGMENT_STATE["committed_before"] == 0
        print("  ok  warmup-shaped batch resets the count instead of extending it")
    finally:
        m._FREE_JUDGMENT_STATE.clear()
        m._FREE_JUDGMENT_STATE.update(saved_state)


def test_end_to_end_real_kernel_ban_holds_adversarially() -> None:
    """The causally meaningful test: even when the TARGET model itself
    strongly favors the exact token the draft proposed at the criterion
    position (the case where a NORMAL accept test would almost always
    accept it), the ban must still guarantee it's never emitted -- proving
    this is a hard guarantee, not merely likely."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load_patched_module()
    saved_len = m._FREE_JUDGMENT_REAL_DRAFT_LEN
    saved_threshold = m._FREE_JUDGMENT_REJECT_THRESHOLD
    try:
        device = "cuda"
        torch.manual_seed(29)
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = 2  # small, for a fast test
        m._FREE_JUDGMENT_REJECT_THRESHOLD = 1.0  # unreachable: isolate the criterion ban from the reject-resample mechanism
        real_draft_len = 2
        criterion_len = m._FREE_JUDGMENT_CRITERION_LEN
        total = real_draft_len + criterion_len
        criterion_target_token = 9  # what the draft AND target both strongly favor at the first criterion position

        vocab = max(
            list(m._FREE_JUDGMENT_YES_TOKEN_IDS) + list(m._FREE_JUDGMENT_NO_TOKEN_IDS)
            + list(m._FREE_JUDGMENT_CONFIDENT_TOKEN_IDS) + list(m._FREE_JUDGMENT_HEDGE_TOKEN_IDS)
            + [criterion_target_token]
        ) + 1000

        outcomes = []
        for _ in range(20):
            p = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
            q = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
            # Every position (including the criterion span) strongly favors
            # the SAME token both in draft and target -- maximally
            # adversarial to the ban: without it, this would almost always
            # be accepted.
            p[:, criterion_target_token] = 0.99
            q[:, criterion_target_token] = 0.99
            target_logits = torch.log(p.clamp_min(1e-12))

            draft_token_ids = torch.full((total,), criterion_target_token, dtype=torch.int32, device=device)
            bonus_token_ids = torch.tensor([[criterion_target_token]], dtype=torch.int32, device=device)
            cu_num_draft_tokens = torch.tensor([total], dtype=torch.int32, device=device)
            sampling_metadata = SimpleNamespace(
                all_greedy=False, all_random=True,
                temperature=torch.tensor([1.0], device=device), generators={},
            )
            out = m.rejection_sample(
                draft_token_ids, [total], total, cu_num_draft_tokens,
                q.contiguous(), target_logits.contiguous(), bonus_token_ids, sampling_metadata,
            )
            # A rejection at the criterion boundary still commits ONE
            # recovered substitute token there before the round
            # terminates -- rejection doesn't mean "nothing gets
            # committed", it means "the draft's own token gets replaced".
            # So the causally meaningful checks are: (1) the round must
            # terminate right there (committed length == real_draft_len+1,
            # never further into the criterion phrase), and (2) whatever
            # got committed at that boundary position must never be the
            # banned token itself.
            committed_len = int((out[0] != m.PLACEHOLDER_TOKEN_ID).sum().item())
            boundary_token = int(out[0, real_draft_len].item())
            outcomes.append((committed_len, boundary_token))

        assert all(c == real_draft_len + 1 for c, _ in outcomes), (
            f"the round must terminate exactly at the criterion boundary (real_draft_len+1 committed "
            f"tokens), never further into the criterion phrase: {outcomes}"
        )
        assert all(b != criterion_target_token for _, b in outcomes), (
            f"the banned token must never be the one actually committed at the boundary position: {outcomes}"
        )
        print(f"  ok  ban holds across {len(outcomes)} adversarial trials -- round always terminates at "
              f"real_draft_len+1={real_draft_len + 1} committed tokens, and the banned token "
              f"({criterion_target_token}) is never the one actually committed there, even though draft "
              f"and target both strongly favor it (recovered instead: {sorted({b for _, b in outcomes})})")
    finally:
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = saved_len
        m._FREE_JUDGMENT_REJECT_THRESHOLD = saved_threshold


def test_end_to_end_reject_resample_adversarial() -> None:
    """Reject-and-resample under the REAL kernel: rig the judgment row to
    score above threshold AND rig the last real position to be maximally
    adversarial (draft==target both strongly favor the same token there,
    same shape as the criterion-ban test above) -- confirm that token is
    never actually committed at that position across many trials, and
    that a genuinely different (resampled) token lands there instead. A
    companion low-score trial confirms the position is left to normal
    accept/reject when the trigger doesn't fire."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load_patched_module()
    saved_len = m._FREE_JUDGMENT_REAL_DRAFT_LEN
    saved_threshold = m._FREE_JUDGMENT_REJECT_THRESHOLD
    try:
        device = "cuda"
        torch.manual_seed(31)
        real_draft_len = 2
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = real_draft_len
        m._FREE_JUDGMENT_REJECT_THRESHOLD = 0.08
        criterion_len = m._FREE_JUDGMENT_CRITERION_LEN
        total = real_draft_len + criterion_len
        real_target_token = 7  # what draft AND target both strongly favor at the LAST real position
        criterion_target_token = 9

        vocab = max(
            list(m._FREE_JUDGMENT_YES_TOKEN_IDS) + list(m._FREE_JUDGMENT_NO_TOKEN_IDS)
            + list(m._FREE_JUDGMENT_CONFIDENT_TOKEN_IDS) + list(m._FREE_JUDGMENT_HEDGE_TOKEN_IDS)
            + [real_target_token, criterion_target_token]
        ) + 1000
        judgment_row = total - 1
        real_last_row = real_draft_len - 1

        def run_trial(p_yes: float, p_no: float):
            p = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
            q = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
            p[:, criterion_target_token] = 0.99
            q[:, criterion_target_token] = 0.99
            # Maximally adversarial at the LAST real position: draft and
            # target both strongly favor real_target_token there.
            p[real_last_row, :] = 0.01 / (vocab - 1)
            p[real_last_row, real_target_token] = 0.99
            q[real_last_row, :] = 0.01 / (vocab - 1)
            q[real_last_row, real_target_token] = 0.99
            # Rig the judgment row's own yes/no mass directly on TARGET
            # (p), since that's what free-judgment reads.
            p[judgment_row, :] = 0.0
            p[judgment_row, m._FREE_JUDGMENT_YES_TOKEN_IDS[0]] = p_yes
            p[judgment_row, m._FREE_JUDGMENT_NO_TOKEN_IDS[0]] = p_no
            p[judgment_row, criterion_target_token] = max(1e-6, 1.0 - p_yes - p_no)
            target_logits = torch.log(p.clamp_min(1e-12))

            draft_token_ids = torch.full((total,), criterion_target_token, dtype=torch.int32, device=device)
            draft_token_ids[real_last_row] = real_target_token
            bonus_token_ids = torch.tensor([[criterion_target_token]], dtype=torch.int32, device=device)
            cu_num_draft_tokens = torch.tensor([total], dtype=torch.int32, device=device)
            sampling_metadata = SimpleNamespace(
                all_greedy=False, all_random=True,
                temperature=torch.tensor([1.0], device=device), generators={},
            )
            out = m.rejection_sample(
                draft_token_ids, [total], total, cu_num_draft_tokens,
                q.contiguous(), target_logits.contiguous(), bonus_token_ids, sampling_metadata,
            )
            return int(out[0, real_last_row].item())

        rejected_outcomes = [run_trial(p_yes=0.30, p_no=0.05) for _ in range(20)]  # score=0.25 > 0.08
        assert all(t != real_target_token for t in rejected_outcomes), (
            f"score above threshold must guarantee the adversarially-favored real token is never committed "
            f"at the last real position: {rejected_outcomes}"
        )
        print(f"  ok  reject-and-resample holds across {len(rejected_outcomes)} adversarial trials when "
              f"score=0.25>0.08 -- the favored real token ({real_target_token}) is never the one actually "
              f"committed there (resampled instead: {sorted(set(rejected_outcomes))})")

        accepted_outcomes = [run_trial(p_yes=0.02, p_no=0.01) for _ in range(20)]  # score=0.01 < 0.08
        assert all(t == real_target_token for t in accepted_outcomes), (
            f"score below threshold must leave the last real position to NORMAL accept/reject -- with draft "
            f"and target both at 0.99 on the same token, it should be accepted essentially always: {accepted_outcomes}"
        )
        print(f"  ok  below threshold (score=0.01<0.08): the same adversarially-favored real token IS "
              f"committed normally across {len(accepted_outcomes)} trials -- the reject mechanism is truly "
              f"conditional on the score, not always-on")
    finally:
        m._FREE_JUDGMENT_REAL_DRAFT_LEN = saved_len
        m._FREE_JUDGMENT_REJECT_THRESHOLD = saved_threshold


def main() -> int:
    failures = 0
    for test in (
        test_knob_plumbing,
        test_apply_noop_when_disabled_or_too_short,
        test_apply_bans_criterion_and_reads_judgment,
        test_apply_reject_threshold_bans_real_token,
        test_update_tracks_committed_tokens,
        test_end_to_end_real_kernel_ban_holds_adversarially,
        test_end_to_end_reject_resample_adversarial,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-free-judgment patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
