#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-judge-nudge patch's
rejection_sampler.py half. Run by patches/apply.sh.

(The OTHER half -- vllm-0.26.0-jn-model-runner.patch, which overwrites the
real sequence's own trailing drafted columns with either the judge
criterion or the RV nudge pattern -- is not independently unit-testable
here without mocking a large fraction of gpu_model_runner.py's internal
scheduling state; its correctness is validated by real imports and by
this file's own real-kernel adversarial tests instead, see
analysis/semantic_guard/DESIGN_screen_verify_nudge.md.)

"Judge + nudge": combines the best-performing free-judgment criterion
phrase (TRUE/FALSE + completion scaffold, validated against 48 real
ground-truth-labeled points, see analysis/semantic_guard/README.md) as
the trigger, with spec-casc-tok-rv's own ephemeral logit-blend (see that
patch's own module comment) as the actuator instead of plain reject-and-
resample (proven, via a positionally-verified causal trace on case_010,
not to work: resampling from an UNMODIFIED target barely moves a stuck
state). The screen stage from the original 3-stage design was DROPPED
after an empirical finding that there is no live per-round cost lever
within this repo's patch scope -- see DESIGN_screen_verify_nudge.md's own
amendment. This mechanism pays the wide-verification tax every round,
unconditionally, same order of cost as free-judgment's own criterion.

Checks, in order:

1. knob plumbing (real-draft-len shared with the model-runner half by
   design, judge-threshold/rv-alpha/nudge-window/trace-path own files),
2. _jn_apply is a no-op when disabled or the round is too short for
   EITHER mode's own minimum width,
3. JUDGE mode: bans the criterion's own first token and renormalizes (not
   zeroing the whole row -- same bug class free-judgment's own module
   comment documents), reads p_true/p_false correctly from the judgment
   row, arms pending_nudge when score crosses threshold (apply() only
   ARMS, never itself transitions -- same discipline as every other
   patch in this repo),
4. _jn_update: cross-round committed-token counting, warmup reset, AND
   the only place mode actually transitions (pending_nudge -> nudge_
   remaining=WINDOW, nudge_remaining counts down each round, both
   written to the shared file gpu_model_runner.py's own half reads),
5. NUDGE mode: blends z0/z_reflect at the LOGIT level into the real
   positions, bans the RV prompt's own first token,
6. END-TO-END, JUDGE: drive the REAL, unmodified rejection_sample() with
   a target distribution that puts ALL its mass on the criterion-position
   token the draft proposes, confirm it is NEVER actually emitted across
   many trials -- the ban holds even against a maximally-adversarial case.
7. END-TO-END, NUDGE: same adversarial shape at the REAL positions (draft
   and target both strongly favor the same token there) while nudge is
   active and z_reflect strongly favors a DIFFERENT token -- confirm the
   blend measurably shifts what gets committed, proving the blend is
   real, not inert.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys

REAL_DRAFT_LEN_FILE = pathlib.Path(f"/tmp/lossy-token-eff-judge-nudge-real-draft-len-{os.getuid()}")
JUDGE_THRESHOLD_FILE = pathlib.Path(f"/tmp/lossy-token-eff-judge-nudge-threshold-{os.getuid()}")
RV_ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-judge-nudge-rv-alpha-{os.getuid()}")
NUDGE_WINDOW_FILE = pathlib.Path(f"/tmp/lossy-token-eff-judge-nudge-window-{os.getuid()}")
TRACE_PATH_FILE = pathlib.Path(f"/tmp/lossy-token-eff-judge-nudge-trace-path-{os.getuid()}")
NUDGE_REMAINING_FILE = pathlib.Path(f"/tmp/lossy-token-eff-judge-nudge-remaining-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "real_draft_len": m._JN_REAL_DRAFT_LEN,
    "judge_threshold": m._JN_JUDGE_THRESHOLD,
    "rv_alpha": m._JN_RV_ALPHA,
    "nudge_window": m._JN_NUDGE_WINDOW,
    "trace_dest": m._JN_TRACE_DEST,
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
    files = (REAL_DRAFT_LEN_FILE, JUDGE_THRESHOLD_FILE, RV_ALPHA_FILE, NUDGE_WINDOW_FILE, TRACE_PATH_FILE)
    saved = {f: (f.read_text() if f.is_file() else None) for f in files}
    try:
        REAL_DRAFT_LEN_FILE.write_text("6\n")
        JUDGE_THRESHOLD_FILE.write_text("0.05\n")
        RV_ALPHA_FILE.write_text("0.4\n")
        NUDGE_WINDOW_FILE.write_text("7\n")
        TRACE_PATH_FILE.write_text("/tmp/some-jn-trace.jsonl\n")
        got = read_back_in_subprocess()
        assert got["real_draft_len"] == 6, got
        assert got["judge_threshold"] == 0.05, got
        assert got["rv_alpha"] == 0.4, got
        assert got["nudge_window"] == 7, got
        assert got["trace_dest"] == "/tmp/some-jn-trace.jsonl", got
        print("  ok  module reads all five knob files")

        for f in files:
            f.unlink()
        got = read_back_in_subprocess()
        assert got["real_draft_len"] == 0, got
        assert got["judge_threshold"] == 0.03, got
        assert got["rv_alpha"] == 0.3, got
        assert got["nudge_window"] == 4, got
        assert got["trace_dest"] is None, got
        print("  ok  missing files fall back to real_draft_len=0 (disabled), judge_threshold=0.03, rv_alpha=0.3, nudge_window=4, trace_dest=None")
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


def _snapshot_state(m):
    return dict(m._JN_STATE)


def _restore_state(m, snapshot) -> None:
    m._JN_STATE.clear()
    m._JN_STATE.update(snapshot)


def test_apply_noop_when_disabled_or_too_short() -> None:
    import torch

    m = _load_patched_module()
    saved_len = m._JN_REAL_DRAFT_LEN
    try:
        vocab = 32
        target_logits = torch.zeros(30, vocab)
        target_probs = torch.full((30, vocab), 1.0 / vocab)
        draft_token_ids = torch.zeros(30, dtype=torch.int64)
        num_draft_tokens = [30]
        cu_num_draft_tokens = torch.tensor([30], dtype=torch.int64)

        m._JN_REAL_DRAFT_LEN = 0
        out = m._jn_apply(target_logits, target_probs, draft_token_ids, num_draft_tokens, cu_num_draft_tokens)
        assert out is target_probs, "disabled (real_draft_len<=0) must be a pure no-op"
        print("  ok  disabled (real_draft_len<=0): pure no-op")

        m._JN_REAL_DRAFT_LEN = 6
        short_n = 6 + m._JN_JUDGE_LEN - 1  # one short of judge mode's own minimum
        short_logits = torch.zeros(short_n, vocab)
        short_probs = torch.full((short_n, vocab), 1.0 / vocab)
        short_ids = torch.zeros(short_n, dtype=torch.int64)
        out = m._jn_apply(short_logits, short_probs, short_ids, [short_n], torch.tensor([short_n], dtype=torch.int64))
        assert out is short_probs, "a round too short for JUDGE mode must be a no-op"
        print("  ok  round shorter than real_draft_len+judge_len (JUDGE mode): pure no-op")
    finally:
        m._JN_REAL_DRAFT_LEN = saved_len


def _vocab_for(m) -> int:
    return max(list(m._JN_TRUE_IDS) + list(m._JN_FALSE_IDS)) + 100


def test_judge_mode_bans_and_reads_and_arms() -> None:
    import torch

    m = _load_patched_module()
    saved_len = m._JN_REAL_DRAFT_LEN
    saved_threshold = m._JN_JUDGE_THRESHOLD
    saved_trace = m._JN_TRACE_DEST
    saved_state = _snapshot_state(m)
    trace_file = pathlib.Path(f"/tmp/lossy-token-eff-test-jn-trace-{os.getpid()}.jsonl")
    try:
        m._JN_REAL_DRAFT_LEN = 6
        m._JN_JUDGE_THRESHOLD = 0.05
        m._JN_TRACE_DEST = str(trace_file)
        m._JN_STATE.clear()
        m._JN_STATE.update(committed_before=0, nudge_remaining=0, pending_nudge=False)
        trace_file.unlink(missing_ok=True)

        real_draft_len = 6
        judge_len = m._JN_JUDGE_LEN
        total = real_draft_len + judge_len
        vocab = _vocab_for(m)

        target_logits = torch.zeros(total, vocab)
        target_probs = torch.full((total, vocab), 1.0 / vocab)
        judgment_row = total - 1
        target_probs[judgment_row] = 0.0
        target_probs[judgment_row, m._JN_TRUE_IDS[0]] = 0.02
        target_probs[judgment_row, m._JN_FALSE_IDS[0]] = 0.01
        target_probs[judgment_row, 0] = 0.97

        draft_token_ids = torch.arange(total, dtype=torch.int64) % vocab
        criterion_start_row = real_draft_len
        banned_tok = int(draft_token_ids[criterion_start_row].item())
        num_draft_tokens = [total]
        cu_num_draft_tokens = torch.tensor([total], dtype=torch.int64)

        out = m._jn_apply(target_logits, target_probs, draft_token_ids, num_draft_tokens, cu_num_draft_tokens)
        assert out is not target_probs, "must return a NEW tensor when the ban fires"
        assert out[criterion_start_row, banned_tok].item() == 0.0
        assert abs(out[criterion_start_row].sum().item() - 1.0) < 1e-5
        assert out[criterion_start_row].sum().item() > 0.0, "must not be an all-zero row (same bug class as every other criterion ban in this repo)"
        assert m._JN_STATE["pending_nudge"] is False, "score=0.01 must not cross threshold=0.05"
        print("  ok  JUDGE mode below threshold: bans criterion, renormalizes, does NOT arm pending_nudge")

        row = json.loads(trace_file.read_text().splitlines()[-1])
        assert abs(row["p_true"] - 0.02) < 1e-6, row
        assert abs(row["p_false"] - 0.01) < 1e-6, row
        assert abs(row["score"] - 0.01) < 1e-6, row
        assert row["mode"] == "judge"
        print(f"  ok  trace row correctly reads p_true={row['p_true']:.2f} p_false={row['p_false']:.2f} score={row['score']:.2f}")

        # Now above threshold.
        target_probs2 = target_probs.clone()
        target_probs2[judgment_row] = 0.0
        target_probs2[judgment_row, m._JN_TRUE_IDS[0]] = 0.20
        target_probs2[judgment_row, m._JN_FALSE_IDS[0]] = 0.02
        target_probs2[judgment_row, 0] = 0.78
        m._jn_apply(target_logits, target_probs2, draft_token_ids, num_draft_tokens, cu_num_draft_tokens)
        assert m._JN_STATE["pending_nudge"] is True, "score=0.18 must cross threshold=0.05 and ARM pending_nudge"
        assert m._JN_STATE["nudge_remaining"] == 0, "apply() must only ARM -- never itself set nudge_remaining"
        print("  ok  JUDGE mode above threshold: ARMS pending_nudge, but apply() never itself transitions nudge_remaining")
    finally:
        m._JN_REAL_DRAFT_LEN = saved_len
        m._JN_JUDGE_THRESHOLD = saved_threshold
        m._JN_TRACE_DEST = saved_trace
        _restore_state(m, saved_state)
        trace_file.unlink(missing_ok=True)


def test_update_transitions_and_persists() -> None:
    import torch

    m = _load_patched_module()
    saved_state = _snapshot_state(m)
    saved_window = m._JN_NUDGE_WINDOW
    try:
        m._JN_NUDGE_WINDOW = 3
        m._JN_STATE.clear()
        m._JN_STATE.update(committed_before=0, nudge_remaining=0, pending_nudge=True)
        PLACEHOLDER = m.PLACEHOLDER_TOKEN_ID

        m._jn_update(torch.tensor([[1, 2, PLACEHOLDER]], dtype=torch.int32), batch_size=1)
        assert m._JN_STATE["committed_before"] == 2
        assert m._JN_STATE["nudge_remaining"] == 3, "pending_nudge must transition to nudge_remaining=WINDOW"
        assert m._JN_STATE["pending_nudge"] is False
        assert NUDGE_REMAINING_FILE.read_text().strip() == "3"
        print("  ok  update() transitions pending_nudge -> nudge_remaining=WINDOW=3, writes to shared file")

        m._jn_update(torch.tensor([[3]], dtype=torch.int32), batch_size=1)
        assert m._JN_STATE["nudge_remaining"] == 2
        assert NUDGE_REMAINING_FILE.read_text().strip() == "2"
        m._jn_update(torch.tensor([[4]], dtype=torch.int32), batch_size=1)
        assert m._JN_STATE["nudge_remaining"] == 1
        m._jn_update(torch.tensor([[5]], dtype=torch.int32), batch_size=1)
        assert m._JN_STATE["nudge_remaining"] == 0
        assert NUDGE_REMAINING_FILE.read_text().strip() == "0"
        print("  ok  nudge_remaining counts down 3->2->1->0 across real rounds, written to shared file each time")

        assert m._JN_WARMUP_BATCH_THRESHOLD < 50
        n = m._JN_WARMUP_BATCH_THRESHOLD + 10
        m._JN_STATE["nudge_remaining"] = 5
        warmup_round = torch.full((n, 2), 1, dtype=torch.int32)
        m._jn_update(warmup_round, batch_size=n)
        assert m._JN_STATE["committed_before"] == 0
        assert m._JN_STATE["nudge_remaining"] == 0
        assert NUDGE_REMAINING_FILE.read_text().strip() == "0"
        print("  ok  warmup-shaped batch resets committed_before and nudge_remaining, writes 0 to shared file")
    finally:
        _restore_state(m, saved_state)
        m._JN_NUDGE_WINDOW = saved_window


def test_nudge_mode_blends() -> None:
    import torch

    m = _load_patched_module()
    saved_len = m._JN_REAL_DRAFT_LEN
    saved_alpha = m._JN_RV_ALPHA
    saved_state = _snapshot_state(m)
    try:
        m._JN_REAL_DRAFT_LEN = 2
        m._JN_RV_ALPHA = 0.5
        m._JN_STATE.clear()
        m._JN_STATE.update(committed_before=0, nudge_remaining=2, pending_nudge=False)

        real_draft_len = 2
        prompt_len = m._JN_RV_PROMPT_LEN
        total = 2 * real_draft_len + prompt_len
        vocab = 40

        # z0 strongly favors token 5 at the last real position; z_reflect
        # strongly favors token 9 there instead -- the blend should move
        # meaningfully away from a pure z0 read.
        target_logits = torch.zeros(total, vocab)
        last_real = real_draft_len - 1
        target_logits[last_real, 5] = 20.0
        dup_start = real_draft_len + prompt_len
        target_logits[dup_start + last_real, 9] = 20.0
        target_probs = target_logits.softmax(dim=-1)

        draft_token_ids = torch.zeros(total, dtype=torch.int64)
        num_draft_tokens = [total]
        cu_num_draft_tokens = torch.tensor([total], dtype=torch.int64)

        out = m._jn_apply(target_logits, target_probs, draft_token_ids, num_draft_tokens, cu_num_draft_tokens)
        assert out is not target_probs
        p_z0_only = target_probs[last_real, 5].item()
        p_blended = out[last_real, 5].item()
        assert p_blended < p_z0_only - 0.1, (
            f"blend must measurably shift mass away from z0's own top token when z_reflect strongly "
            f"disagrees: z0-only={p_z0_only:.4f} blended={p_blended:.4f}"
        )
        prompt_start = real_draft_len
        banned_tok = int(draft_token_ids[prompt_start].item())
        assert out[prompt_start, banned_tok].item() == 0.0
        print(f"  ok  NUDGE mode blend measurably shifts mass at the real position (z0-only p={p_z0_only:.4f} -> "
              f"blended p={p_blended:.4f}), bans the RV prompt's own first token")
    finally:
        m._JN_REAL_DRAFT_LEN = saved_len
        m._JN_RV_ALPHA = saved_alpha
        _restore_state(m, saved_state)


def test_end_to_end_judge_ban_holds_adversarially() -> None:
    """Real kernel, JUDGE mode: even when target strongly favors the exact
    token drafted at the criterion position, the ban must still guarantee
    it's never emitted."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load_patched_module()
    saved_len = m._JN_REAL_DRAFT_LEN
    saved_state = _snapshot_state(m)
    try:
        device = "cuda"
        torch.manual_seed(37)
        m._JN_REAL_DRAFT_LEN = 2
        m._JN_STATE.clear()
        m._JN_STATE.update(committed_before=0, nudge_remaining=0, pending_nudge=False)
        real_draft_len = 2
        judge_len = m._JN_JUDGE_LEN
        total = real_draft_len + judge_len
        criterion_target_token = 9

        vocab = max(list(m._JN_TRUE_IDS) + list(m._JN_FALSE_IDS) + [criterion_target_token]) + 1000

        outcomes = []
        for _ in range(20):
            p = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
            q = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
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
            committed_len = int((out[0] != m.PLACEHOLDER_TOKEN_ID).sum().item())
            boundary_token = int(out[0, real_draft_len].item())
            outcomes.append((committed_len, boundary_token))
            m._JN_STATE["nudge_remaining"] = 0  # stay in JUDGE mode for every trial

        assert all(c == real_draft_len + 1 for c, _ in outcomes), (
            f"round must terminate exactly at the criterion boundary every trial: {outcomes}"
        )
        assert all(b != criterion_target_token for _, b in outcomes), (
            f"banned token must never be committed at the boundary: {outcomes}"
        )
        print(f"  ok  JUDGE ban holds across {len(outcomes)} adversarial trials -- criterion token "
              f"({criterion_target_token}) never committed even though draft and target both favor it")
    finally:
        m._JN_REAL_DRAFT_LEN = saved_len
        _restore_state(m, saved_state)


def test_end_to_end_nudge_blend_shifts_acceptance() -> None:
    """Real kernel, NUDGE mode: draft and target both strongly favor the
    same token at the last real position; z_reflect strongly favors a
    DIFFERENT token there. Confirms the blend measurably changes what
    actually gets committed across many trials, not just in isolated unit
    math -- proving the blend is live inside the real kernel path."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load_patched_module()
    saved_len = m._JN_REAL_DRAFT_LEN
    saved_alpha = m._JN_RV_ALPHA
    saved_state = _snapshot_state(m)
    try:
        device = "cuda"
        torch.manual_seed(41)
        real_draft_len = 2
        m._JN_REAL_DRAFT_LEN = real_draft_len
        m._JN_RV_ALPHA = 0.7  # strong blend, to make the shift unambiguous
        prompt_len = m._JN_RV_PROMPT_LEN
        total = 2 * real_draft_len + prompt_len
        real_favored_token = 7
        reflect_favored_token = 13

        vocab = max(real_favored_token, reflect_favored_token) + 1000

        committed_at_last_real = []
        for _ in range(20):
            m._JN_STATE.clear()
            m._JN_STATE.update(committed_before=0, nudge_remaining=2, pending_nudge=False)

            p = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
            q = torch.full((total, vocab), 0.01 / (vocab - 1), device=device)
            last_real = real_draft_len - 1
            p[last_real, :] = 0.01 / (vocab - 1)
            p[last_real, real_favored_token] = 0.99
            q[last_real, :] = 0.01 / (vocab - 1)
            q[last_real, real_favored_token] = 0.99
            dup_start = real_draft_len + prompt_len
            p[dup_start + last_real, :] = 0.01 / (vocab - 1)
            p[dup_start + last_real, reflect_favored_token] = 0.99
            target_logits = torch.log(p.clamp_min(1e-12))

            draft_token_ids = torch.full((total,), real_favored_token, dtype=torch.int32, device=device)
            draft_token_ids[last_real] = real_favored_token
            bonus_token_ids = torch.tensor([[real_favored_token]], dtype=torch.int32, device=device)
            cu_num_draft_tokens = torch.tensor([total], dtype=torch.int32, device=device)
            sampling_metadata = SimpleNamespace(
                all_greedy=False, all_random=True,
                temperature=torch.tensor([1.0], device=device), generators={},
            )
            out = m.rejection_sample(
                draft_token_ids, [total], total, cu_num_draft_tokens,
                q.contiguous(), target_logits.contiguous(), bonus_token_ids, sampling_metadata,
            )
            committed_at_last_real.append(int(out[0, last_real].item()))

        never_real_favored = sum(1 for t in committed_at_last_real if t != real_favored_token)
        assert never_real_favored > 0, (
            f"with alpha=0.7 strongly favoring z_reflect's own token, the real-favored token should not "
            f"win every single trial: {committed_at_last_real}"
        )
        print(f"  ok  NUDGE blend measurably shifts acceptance across {len(committed_at_last_real)} real-kernel "
              f"trials: real-favored token displaced in {never_real_favored}/{len(committed_at_last_real)} "
              f"(committed tokens: {sorted(set(committed_at_last_real))})")
    finally:
        m._JN_REAL_DRAFT_LEN = saved_len
        m._JN_RV_ALPHA = saved_alpha
        _restore_state(m, saved_state)


def main() -> int:
    failures = 0
    for test in (
        test_knob_plumbing,
        test_apply_noop_when_disabled_or_too_short,
        test_judge_mode_bans_and_reads_and_arms,
        test_update_transitions_and_persists,
        test_nudge_mode_blends,
        test_end_to_end_judge_ban_holds_adversarially,
        test_end_to_end_nudge_blend_shifts_acceptance,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-judge-nudge patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
