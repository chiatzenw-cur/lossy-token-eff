#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-self-check patch. Run by
patches/apply.sh.

Periodic self-assessment + reactive pivot on top of plain spec-casc-tok:
every _SELF_CHECK_INTERVAL real emitted tokens, force-inject a fixed
self-assessment question (one-hot target_probs, same mechanism as
spec-casc-tok-antiloop/force-commit -- no kernel changes), let the next few
tokens generate completely unconstrained, and read back whether the
model's own genuine answer starts with "yes" or "no". "No" resumes
unchanged. "Yes" force-injects a pivot phrase if budget remains, or
force-commit's own final-channel-open push if the budget is nearly
exhausted.

Checks, in order:

1. alpha/interval/final-threshold knob plumbing (own files),
2. _self_check_pattern_progress and _self_check_read_answer in isolation,
3. _self_check_apply: a pure read of state -- forces the right pattern
   token for whichever mode is active, is a no-op in "idle"/"reading",
   and is permanently a no-op once final_opened,
4. _self_check_update: the full state-machine walk -- idle's threshold
   crossing, the asking->reading->(pivoting|final_forcing|idle) branches
   driven by a real yes/no readback, pattern completion advancing modes,
   warmup reset, and the "ambiguous answer defaults to no" safety rule,
5. END-TO-END: drive the REAL, unmodified rejection_sample() (real
   kernel) through a full asking->reading->pivoting cycle against a target/
   draft distribution that strongly prefers something else entirely, and
   confirm the actually-emitted sequence matches the question, then a
   real single-token "Yes" answer, then the full pivot phrase, then
   returns to idle -- the causally meaningful test.

(5) needs a GPU and is skipped without one; the rest do not.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-self-check-alpha-{os.getuid()}")
INTERVAL_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-self-check-interval-{os.getuid()}")
FINAL_THRESHOLD_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-self-check-final-threshold-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "interval": m._SELF_CHECK_INTERVAL,
    "final_threshold": m._SELF_CHECK_FINAL_THRESHOLD,
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


def test_knob_plumbing() -> None:
    saved = {f: (f.read_text() if f.is_file() else None) for f in (ALPHA_FILE, INTERVAL_FILE, FINAL_THRESHOLD_FILE)}
    try:
        ALPHA_FILE.write_text("0.5\n")
        INTERVAL_FILE.write_text("777\n")
        FINAL_THRESHOLD_FILE.write_text("9999\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.5, got
        assert got["interval"] == 777, got
        assert got["final_threshold"] == 9999, got
        print("  ok  module reads all three own knob files")

        for f in (ALPHA_FILE, INTERVAL_FILE, FINAL_THRESHOLD_FILE):
            f.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        assert got["interval"] == 3000, got
        assert got["final_threshold"] == 28000, got
        print("  ok  missing files fall back to alpha=-inf, interval=3000, final_threshold=28000")
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
    return {k: (list(v) if isinstance(v, list) else v) for k, v in m._SELF_CHECK_STATE.items()}


def _restore_state(m, snapshot) -> None:
    m._SELF_CHECK_STATE.clear()
    m._SELF_CHECK_STATE.update(snapshot)


def test_pattern_progress_and_read_answer() -> None:
    m = _load_patched_module()
    f = m._self_check_pattern_progress
    assert f([], [1, 2, 3]) == 0
    assert f([9, 1], [1, 2, 3]) == 1
    assert f([9, 1, 2], [1, 2, 3]) == 2
    assert f([1, 2, 3], [1, 2, 3]) == 3
    assert f([1, 2, 9], [1, 2, 3]) == 0
    print("  ok  pattern-progress: longest tail-suffix matching a pattern prefix")

    r = m._self_check_read_answer
    yes_id = 11377  # " Yes"
    no_id = 3004  # " No"
    assert r([yes_id]) is True, "a real single-token ' Yes' must read as True"
    assert r([no_id]) is False, "a real single-token ' No' must read as False"
    # Ambiguous / not-yet-resolved cases must return None, not guess.
    assert r([]) is None
    print("  ok  read-answer: real 'Yes'/'No' tokens decode correctly, ambiguous stays None")


def test_apply_is_pure_and_mode_gated() -> None:
    import torch

    m = _load_patched_module()
    saved = _snapshot_state(m)
    try:
        # Real question/pivot/final-open patterns use real, large harmony
        # vocab ids (up to ~200008 for the special final-channel tokens) --
        # vocab must be sized to cover them, unlike antiloop/force-commit's
        # own tests which use small synthetic ids throughout.
        vocab = max(m._SELF_CHECK_QUESTION_PATTERN + m._SELF_CHECK_PIVOT_PATTERN + m._SELF_CHECK_FINAL_OPEN_PATTERN) + 1000
        num_draft_tokens = [2]
        cu_num_draft_tokens = torch.tensor([2], dtype=torch.int64)
        target_probs = torch.full((2, vocab), 1.0 / vocab)

        # idle: no-op regardless of token_count (the idle->asking transition
        # belongs to _self_check_update, not _self_check_apply).
        m._SELF_CHECK_STATE.update(mode="idle", token_count=999_999, next_check_at=1, tail=[], final_opened=False)
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert not mask.any() and out is target_probs
        print("  ok  idle mode: pure no-op even with token_count past next_check_at (apply never transitions modes)")

        # reading: also a no-op -- the answer must be genuinely unconstrained.
        m._SELF_CHECK_STATE.update(mode="reading")
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert not mask.any() and out is target_probs
        print("  ok  reading mode: pure no-op (answer position left fully unconstrained)")

        # asking: forces EVERY still-unforced pattern position available in
        # the round (here num_draft_tokens=[2], plenty of question tokens
        # remaining) -- NOT just the first. This is the bugfix itself: only
        # forcing start0 let a lucky accept there leave later same-round
        # positions fully unconstrained, letting natural content diverge
        # from the pattern mid-force (observed live: the pivot phrase's own
        # opening repeating over and over, restarting each time).
        m._SELF_CHECK_STATE.update(mode="asking", tail=[])
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert mask.tolist() == [True, True], f"must force BOTH available positions, got {mask.tolist()}"
        assert out[0, m._SELF_CHECK_QUESTION_PATTERN[0]].item() == 1.0
        assert out[1, m._SELF_CHECK_QUESTION_PATTERN[1]].item() == 1.0, "second position forces the NEXT pattern token, not left natural"
        print("  ok  asking mode: forces every available round position consecutively (positions 0,1 -> pattern[0,1])")

        # Progress readback still works correctly when only PART of a
        # forced round was actually confirmed emitted (e.g. the kernel's
        # own accept/recovery randomness only landed on the first token so
        # far) -- the next round must resume from the real progress, not
        # from 0 and not from where we last forced blindly.
        m._SELF_CHECK_STATE.update(tail=[m._SELF_CHECK_QUESTION_PATTERN[0]])
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert out[0, m._SELF_CHECK_QUESTION_PATTERN[1]].item() == 1.0, "progress read from tail, not restarted"
        assert out[1, m._SELF_CHECK_QUESTION_PATTERN[2]].item() == 1.0
        print("  ok  asking mode: progress read back from tail, forces the NEXT question tokens onward")

        # Boundary: when fewer pattern tokens remain than the round offers,
        # only force as many positions as the pattern actually has left --
        # never force a position past the pattern's own end.
        near_end = len(m._SELF_CHECK_QUESTION_PATTERN) - 1
        m._SELF_CHECK_STATE.update(tail=list(m._SELF_CHECK_QUESTION_PATTERN[:near_end]))
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert mask.tolist() == [True, False], f"only 1 pattern token remains, must force exactly 1 position: {mask.tolist()}"
        assert out[0, m._SELF_CHECK_QUESTION_PATTERN[near_end]].item() == 1.0
        print("  ok  asking mode: forces only as many positions as pattern tokens remain, never overshoots")

        # pivoting / final_forcing force their own patterns the same way.
        m._SELF_CHECK_STATE.update(mode="pivoting", tail=[])
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert out[0, m._SELF_CHECK_PIVOT_PATTERN[0]].item() == 1.0
        assert out[1, m._SELF_CHECK_PIVOT_PATTERN[1]].item() == 1.0
        m._SELF_CHECK_STATE.update(mode="final_forcing", tail=[])
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert out[0, m._SELF_CHECK_FINAL_OPEN_PATTERN[0]].item() == 1.0
        assert out[1, m._SELF_CHECK_FINAL_OPEN_PATTERN[1]].item() == 1.0
        print("  ok  pivoting/final_forcing modes force their own fixed patterns across all available positions")

        # Sticky final_opened: no-op regardless of mode.
        m._SELF_CHECK_STATE.update(final_opened=True)
        out, mask = m._self_check_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert not mask.any() and out is target_probs
        print("  ok  sticky final_opened permanently disables forcing regardless of mode")
    finally:
        _restore_state(m, saved)


def test_update_full_state_machine() -> None:
    import torch

    m = _load_patched_module()
    saved = _snapshot_state(m)
    try:
        PLACEHOLDER = m.PLACEHOLDER_TOKEN_ID
        m._SELF_CHECK_STATE.update(
            token_count=0, next_check_at=5, mode="idle", tail=[], answer_buffer=[], final_opened=False,
        )

        # idle -> asking once token_count reaches next_check_at.
        m._self_check_update(torch.tensor([[1, 2, 3, PLACEHOLDER]], dtype=torch.int32), [3], batch_size=1)
        assert m._SELF_CHECK_STATE["token_count"] == 3
        assert m._SELF_CHECK_STATE["mode"] == "idle", "not yet at threshold (3 < 5)"
        m._self_check_update(torch.tensor([[4, 5, PLACEHOLDER, PLACEHOLDER]], dtype=torch.int32), [2], batch_size=1)
        assert m._SELF_CHECK_STATE["token_count"] == 5
        assert m._SELF_CHECK_STATE["mode"] == "asking", "5 >= next_check_at=5 should arm asking"
        print("  ok  idle -> asking exactly when cumulative token_count reaches next_check_at")

        # asking -> reading once the full question pattern has been emitted.
        q = m._SELF_CHECK_QUESTION_PATTERN
        row = torch.tensor([q + [PLACEHOLDER] * (len(q) - len(q) + 1)][0:1], dtype=torch.int32)
        # simplest: feed the whole pattern in one synthetic round.
        row = torch.tensor([q], dtype=torch.int32)
        m._self_check_update(row, [len(q)], batch_size=1)
        assert m._SELF_CHECK_STATE["mode"] == "reading", m._SELF_CHECK_STATE["mode"]
        assert m._SELF_CHECK_STATE["answer_buffer"] == []
        print("  ok  asking -> reading once the full question pattern is confirmed emitted")

        # reading -> pivoting on a real "yes" answer, well under final_threshold.
        m._SELF_CHECK_STATE["final_threshold_probe"] = None  # no-op, just documenting intent
        yes_id = 11377  # " Yes"
        m._self_check_update(torch.tensor([[yes_id, PLACEHOLDER]], dtype=torch.int32), [1], batch_size=1)
        assert m._SELF_CHECK_STATE["mode"] == "pivoting", m._SELF_CHECK_STATE["mode"]
        print("  ok  reading -> pivoting on a real 'yes' answer under the final threshold")

        # pivoting -> idle (with next_check_at rescheduled) once the pivot completes.
        piv = m._SELF_CHECK_PIVOT_PATTERN
        before_count = m._SELF_CHECK_STATE["token_count"]
        m._self_check_update(torch.tensor([piv], dtype=torch.int32), [len(piv)], batch_size=1)
        assert m._SELF_CHECK_STATE["mode"] == "idle"
        assert m._SELF_CHECK_STATE["next_check_at"] == m._SELF_CHECK_STATE["token_count"] + m._SELF_CHECK_INTERVAL
        print("  ok  pivoting -> idle once the pivot phrase completes, next check rescheduled")

        # reading -> final_forcing on "yes" once token_count is past final_threshold.
        m._SELF_CHECK_STATE.update(mode="reading", answer_buffer=[], tail=[],
                                    token_count=m._SELF_CHECK_FINAL_THRESHOLD + 10)
        m._self_check_update(torch.tensor([[yes_id, PLACEHOLDER]], dtype=torch.int32), [1], batch_size=1)
        assert m._SELF_CHECK_STATE["mode"] == "final_forcing", m._SELF_CHECK_STATE["mode"]
        print("  ok  reading -> final_forcing on 'yes' once past final_threshold (not pivoting)")

        fin = m._SELF_CHECK_FINAL_OPEN_PATTERN
        m._self_check_update(torch.tensor([fin], dtype=torch.int32), [len(fin)], batch_size=1)
        assert m._SELF_CHECK_STATE["final_opened"] is True
        print("  ok  final_forcing completing sets the sticky final_opened flag")

        # Ambiguous answer (never resolves to yes/no) must default to "no"
        # (idle, no pivot) once ANSWER_MAX_TOKENS is reached -- the safe
        # default, never treated as license to intervene.
        m._SELF_CHECK_STATE.update(mode="reading", answer_buffer=[], tail=[], final_opened=False, token_count=0)
        gibberish = 42  # decodes to something that starts with neither "yes" nor "no"
        for _ in range(m._SELF_CHECK_ANSWER_MAX_TOKENS):
            m._self_check_update(torch.tensor([[gibberish, PLACEHOLDER]], dtype=torch.int32), [1], batch_size=1)
        assert m._SELF_CHECK_STATE["mode"] == "idle", (
            f"an answer that never resolves to yes/no must default to 'no' (idle), got {m._SELF_CHECK_STATE['mode']}"
        )
        print(f"  ok  an answer that never resolves within ANSWER_MAX_TOKENS defaults to 'no' (safe default)")

        # Warmup reset.
        assert m._SELF_CHECK_WARMUP_BATCH_THRESHOLD < 50
        n = m._SELF_CHECK_WARMUP_BATCH_THRESHOLD + 10
        m._self_check_update(torch.full((n, 2), 1, dtype=torch.int32), [2] * n, batch_size=n)
        assert m._SELF_CHECK_STATE["token_count"] == 0
        assert m._SELF_CHECK_STATE["mode"] == "idle"
        assert m._SELF_CHECK_STATE["final_opened"] is False
        print("  ok  warmup-shaped batch resets all state instead of extending it")
    finally:
        _restore_state(m, saved)


def test_end_to_end_real_kernel_full_cycle() -> None:
    """The causally meaningful test: drive the REAL, unmodified
    rejection_sample() (real kernel) through a full asking -> reading ->
    pivoting cycle, against a target/draft distribution that STRONGLY
    prefers a completely unrelated token every round, and confirm the
    actually-emitted sequence is exactly: the question, then a real
    single-token "Yes" answer, then the full pivot phrase -- then the
    state machine returns to idle."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load_patched_module()
    saved = _snapshot_state(m)
    try:
        device = "cuda"
        torch.manual_seed(23)
        question = list(m._SELF_CHECK_QUESTION_PATTERN)
        pivot = list(m._SELF_CHECK_PIVOT_PATTERN)
        yes_id = 11377  # " Yes" -- the real answer we'll bias the model toward during "reading"
        natural_favorite = 5  # what the model prefers everywhere else; never in question/pivot/yes_id
        assert natural_favorite not in question and natural_favorite not in pivot and natural_favorite != yes_id
        vocab = max(question + pivot + [yes_id]) + 1000

        m._SELF_CHECK_STATE.update(
            token_count=0, next_check_at=0, mode="asking", tail=[], answer_buffer=[], final_opened=False,
        )

        def run_one_round(favored_token: int):
            p = torch.full((1, vocab), 0.01 / (vocab - 1), device=device)
            p[0, favored_token] = 0.99
            q = torch.full((1, vocab), 0.01 / (vocab - 1), device=device)
            q[0, favored_token] = 0.99
            target_logits = torch.log(p.clamp_min(1e-12))
            draft_token_ids = torch.tensor([favored_token], dtype=torch.int32, device=device)
            bonus_token_ids = torch.tensor([[favored_token]], dtype=torch.int32, device=device)
            cu_num_draft_tokens = torch.tensor([1], dtype=torch.int32, device=device)
            sampling_metadata = SimpleNamespace(
                all_greedy=False, all_random=True,
                temperature=torch.tensor([1.0], device=device), generators={},
            )
            out = m.rejection_sample(
                draft_token_ids, [1], 1, cu_num_draft_tokens,
                q.contiguous(), target_logits.contiguous(), bonus_token_ids, sampling_metadata,
            )
            return int(out[0, 0].item())

        emitted: list[int] = []
        # Drive rounds: during "asking"/"pivoting" the draft always proposes
        # natural_favorite (irrelevant -- it'll be force-rejected and
        # recovered to the pattern token instead). During "reading", drive
        # the draft with yes_id itself so the model's "genuine" (here:
        # scripted-favorite) answer is a real, unconstrained "Yes".
        for _ in range(len(question) + len(pivot) + 3):
            favored = yes_id if m._SELF_CHECK_STATE["mode"] == "reading" else natural_favorite
            emitted.append(run_one_round(favored))
            if m._SELF_CHECK_STATE["mode"] == "idle" and m._SELF_CHECK_STATE["token_count"] > 0 and len(emitted) >= len(question) + 1 + len(pivot):
                break

        assert emitted[: len(question)] == question, f"question mismatch: {emitted[:len(question)]} vs {question}"
        after_q = emitted[len(question):]
        assert after_q and after_q[0] == yes_id, f"expected a real 'Yes' answer right after the question: {after_q[:3]}"
        pivot_start = len(question) + 1
        assert emitted[pivot_start:pivot_start + len(pivot)] == pivot, (
            f"pivot mismatch: {emitted[pivot_start:pivot_start + len(pivot)]} vs {pivot}"
        )
        assert m._SELF_CHECK_STATE["mode"] == "idle"
        print(f"  ok  real end-to-end cycle: question ({len(question)} tok) -> genuine 'Yes' answer -> "
              f"pivot ({len(pivot)} tok) -> back to idle, all over a strongly-preferred competing token")
    finally:
        _restore_state(m, saved)


def main() -> int:
    failures = 0
    for test in (
        test_knob_plumbing,
        test_pattern_progress_and_read_answer,
        test_apply_is_pure_and_mode_gated,
        test_update_full_state_machine,
        test_end_to_end_real_kernel_full_cycle,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-self-check patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
