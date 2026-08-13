#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-force-commit patch. Run by
patches/apply.sh.

Reactive budget-exhaustion breaker on top of plain spec-casc-tok, for the
"never commits to a final-channel answer" failure shape (distinct from
spec-casc-tok-antiloop's literal token-repetition target): once cumulative
real emitted tokens for a sequence cross a threshold without the model
having naturally opened a harmony `final`-channel message, one-hot
target_probs onto the NEXT token of the fixed 6-token
`<|end|><|start|>assistant<|channel|>final<|message|>` boundary at the
first drafted position each round. A draft token that doesn't match is a
guaranteed rejection (target_prob=0 there), which terminates the round per
this repo's universal "stop at first rejection" behavior, so recovery
sampling picks up the one-hot mass and the round emits the forced token --
one pattern token advances per round. Progress is always read back from the
ACTUAL emitted history, never assumed. No kernel changes -- everything
downstream (eta, pi_rej, the accept-test kernel, recovery) is already a
pure function of target_probs, same pattern as spec-casc-tok-antiloop.

Checks, in order:

1. alpha AND threshold knob plumbing (own files, not plain spec-casc-tok's
   or spec-casc-tok-antiloop's -- aliasing was a real bug caught once
   already building antiloop),
2. _force_commit_pattern_progress: the longest-tail-suffix-matches-a-
   pattern-prefix logic in isolation,
3. _force_commit_apply: below threshold is a no-op returning the SAME
   tensor; at/above threshold forces the correct next pattern token
   one-hot at the first drafted position only, honoring prior progress;
   the sticky final_opened flag disables forcing permanently,
4. _force_commit_update: cross-round token-count/tail persistence, sticky
   completion detection, tail trimming, and the warmup-batch reset
   convention shared with this repo's other cross-round-state patches,
5. END-TO-END: drive the REAL, unmodified rejection_sample() (real kernel)
   round after round, past threshold, against a target/draft distribution
   that STRONGLY and confidently prefers a completely different token every
   round, and confirm the actually-emitted sequence is exactly the real
   6-token final-channel-open pattern, in order, then stops forcing -- the
   causally meaningful test, since it proves the force overrides a real
   confident competing preference, not just an artificially weak one.

(5) needs a GPU and is skipped without one; the rest do not.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-force-commit-alpha-{os.getuid()}")
THRESHOLD_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-force-commit-threshold-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "alpha_path": m._SPEC_CASC_TOK_FORCE_COMMIT_ALPHA_FILE,
    "threshold": m._FORCE_COMMIT_THRESHOLD,
    "threshold_path": m._FORCE_COMMIT_THRESHOLD_FILE,
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


def test_alpha_and_threshold_plumbing() -> None:
    saved_alpha = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    saved_threshold = THRESHOLD_FILE.read_text() if THRESHOLD_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.4\n")
        THRESHOLD_FILE.write_text("12345\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.4, got
        assert got["alpha_path"] == str(ALPHA_FILE), got
        assert got["threshold"] == 12345, got
        assert got["threshold_path"] == str(THRESHOLD_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.4 and {THRESHOLD_FILE} -> 12345 "
              f"(own files, not plain spec-casc-tok's or antiloop's)")

        ALPHA_FILE.unlink()
        THRESHOLD_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        assert got["threshold"] == 28000, got
        print("  ok  missing files fall back to alpha=-inf (strict point) and threshold=28000")
    finally:
        if saved_alpha is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved_alpha)
        if saved_threshold is None:
            THRESHOLD_FILE.unlink(missing_ok=True)
        else:
            THRESHOLD_FILE.write_text(saved_threshold)


def _load_patched_module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def _snapshot_state(m):
    return {k: (list(v) if isinstance(v, list) else v) for k, v in m._FORCE_COMMIT_STATE.items()}


def _restore_state(m, snapshot) -> None:
    m._FORCE_COMMIT_STATE.clear()
    m._FORCE_COMMIT_STATE.update(snapshot)


def test_pattern_progress() -> None:
    m = _load_patched_module()
    saved_pattern = list(m._FINAL_OPEN_PATTERN)
    try:
        m._FINAL_OPEN_PATTERN = [1, 2, 3]
        f = m._force_commit_pattern_progress
        assert f([]) == 0
        assert f([9, 9, 9]) == 0, "no suffix matches even the first pattern token"
        assert f([9, 1]) == 1, "tail suffix [1] matches pattern prefix [1]"
        assert f([9, 1, 2]) == 2
        assert f([1, 2, 3]) == 3, "full pattern present at the tail -- complete"
        assert f([5, 1, 2, 3]) == 3, "leading junk before the match must not matter"
        assert f([1, 2, 9]) == 0, "a broken match (right length, wrong last token) must not fool it"
        assert f([2, 3]) == 0, "a mid-pattern-only tail (doesn't start from pattern[0]) must not count"
        print("  ok  pattern-progress correctly finds the longest tail-suffix matching a pattern prefix")
    finally:
        m._FINAL_OPEN_PATTERN = saved_pattern


def test_apply_forces_onehot_and_respects_threshold() -> None:
    import torch

    m = _load_patched_module()
    saved_state = _snapshot_state(m)
    saved_pattern = list(m._FINAL_OPEN_PATTERN)
    try:
        m._FINAL_OPEN_PATTERN = [7, 8, 9]
        vocab = 16
        num_draft_tokens = [2]
        cu_num_draft_tokens = torch.tensor([2], dtype=torch.int64)
        target_probs = torch.full((2, vocab), 1.0 / vocab)

        # Below threshold: no-op, and returns the caller's SAME tensor (no
        # clone) -- the common-case fast path for the vast majority of
        # tokens in the vast majority of sequences.
        m._FORCE_COMMIT_STATE["token_count"] = 100
        m._FORCE_COMMIT_STATE["final_opened"] = False
        m._FORCE_COMMIT_STATE["tail"] = []
        out, mask = m._force_commit_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert not mask.any(), "must not force below threshold"
        assert out is target_probs, "must return the SAME tensor object when not forcing"
        print("  ok  below threshold: no-op, original tensor object returned unmodified")

        # At threshold, no progress yet (empty tail): forces EVERY
        # still-unforced pattern position available in the round (here
        # num_draft_tokens=[2], 3 pattern tokens remaining) -- NOT just the
        # first. This is the bugfix itself: only forcing start0 let a lucky
        # accept there leave the round's later positions fully
        # unconstrained, letting natural content diverge from the pattern
        # mid-force -- observed live as a real degenerate cycle (the
        # pattern's own opening repeating over and over, restarting each
        # time it diverged).
        m._FORCE_COMMIT_STATE["token_count"] = m._FORCE_COMMIT_THRESHOLD
        out, mask = m._force_commit_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert mask.tolist() == [True, True], f"must force BOTH available positions, got {mask.tolist()}"
        assert out[0, 7].item() == 1.0
        assert abs(out[0].sum().item() - 1.0) < 1e-6
        assert out[1, 8].item() == 1.0, "second position forces the NEXT pattern token, not left natural"
        print("  ok  at threshold with no progress: forces every available round position consecutively (0,1 -> pattern[0,1])")

        # Partial progress (tail already ends in pattern[:1]=[7]): forces
        # pattern[1] onward next, not pattern[0] again.
        m._FORCE_COMMIT_STATE["tail"] = [7]
        out, mask = m._force_commit_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert out[0, 8].item() == 1.0, "should now force pattern[1], not restart from pattern[0]"
        assert out[1, 9].item() == 1.0, "and pattern[2] at the second position"
        print("  ok  progress is read from the tail: forces the NEXT pattern tokens onward, not restarting")

        # Boundary: only 1 pattern token remains (progress=2 of 3) but the
        # round offers 2 positions -- must force exactly 1, never overshoot
        # past the pattern's own end.
        m._FORCE_COMMIT_STATE["tail"] = [7, 8]
        out, mask = m._force_commit_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert mask.tolist() == [True, False], f"only 1 pattern token remains, must force exactly 1: {mask.tolist()}"
        assert out[0, 9].item() == 1.0
        print("  ok  forces only as many positions as pattern tokens remain, never overshoots")

        # Sticky final_opened: no-op regardless of token_count or tail.
        m._FORCE_COMMIT_STATE["final_opened"] = True
        out, mask = m._force_commit_apply(target_probs, num_draft_tokens, cu_num_draft_tokens)
        assert not mask.any(), "must never force once final_opened is sticky-True"
        assert out is target_probs
        print("  ok  sticky final_opened flag permanently disables forcing")
    finally:
        _restore_state(m, saved_state)
        m._FINAL_OPEN_PATTERN = saved_pattern


def test_update_accumulates_and_detects_completion() -> None:
    import torch

    m = _load_patched_module()
    saved_state = _snapshot_state(m)
    saved_pattern = list(m._FINAL_OPEN_PATTERN)
    try:
        m._FINAL_OPEN_PATTERN = [7, 8, 9]
        m._FORCE_COMMIT_STATE["token_count"] = 0
        m._FORCE_COMMIT_STATE["final_opened"] = False
        m._FORCE_COMMIT_STATE["tail"] = []
        PLACEHOLDER = m.PLACEHOLDER_TOKEN_ID

        round1 = torch.tensor([[7, PLACEHOLDER]], dtype=torch.int32)
        m._force_commit_update(round1, [1], batch_size=1)
        assert m._FORCE_COMMIT_STATE["token_count"] == 1
        assert m._FORCE_COMMIT_STATE["tail"] == [7]
        assert m._FORCE_COMMIT_STATE["final_opened"] is False
        print("  ok  update accumulates real tokens, ignores PLACEHOLDER padding, not yet complete")

        round2 = torch.tensor([[8, PLACEHOLDER]], dtype=torch.int32)
        m._force_commit_update(round2, [1], batch_size=1)
        round3 = torch.tensor([[9, PLACEHOLDER]], dtype=torch.int32)
        m._force_commit_update(round3, [1], batch_size=1)
        assert m._FORCE_COMMIT_STATE["token_count"] == 3
        assert m._FORCE_COMMIT_STATE["final_opened"] is True
        print("  ok  full pattern completing across rounds sets the sticky final_opened flag")

        round4 = torch.tensor([[1, 2, 3]], dtype=torch.int32)
        m._force_commit_update(round4, [3], batch_size=1)
        assert m._FORCE_COMMIT_STATE["final_opened"] is True
        assert m._FORCE_COMMIT_STATE["token_count"] == 6
        print("  ok  final_opened stays sticky after further generation (still counts tokens)")

        assert m._FORCE_COMMIT_WARMUP_BATCH_THRESHOLD < 50
        n = m._FORCE_COMMIT_WARMUP_BATCH_THRESHOLD + 10
        warmup_round = torch.full((n, 2), 1, dtype=torch.int32)
        m._force_commit_update(warmup_round, [2] * n, batch_size=n)
        assert m._FORCE_COMMIT_STATE["token_count"] == 0
        assert m._FORCE_COMMIT_STATE["final_opened"] is False
        assert m._FORCE_COMMIT_STATE["tail"] == []
        print("  ok  warmup-shaped batch resets all state instead of extending it")

        m._FINAL_OPEN_PATTERN = [999999]  # won't spuriously match the content below
        maxlen = m._FORCE_COMMIT_HISTORY_MAXLEN
        big_round = torch.tensor([list(range(1, maxlen + 11))], dtype=torch.int32)
        m._force_commit_update(big_round, [maxlen + 10], batch_size=1)
        assert len(m._FORCE_COMMIT_STATE["tail"]) == maxlen, len(m._FORCE_COMMIT_STATE["tail"])
        assert m._FORCE_COMMIT_STATE["tail"][-1] == maxlen + 10
        print(f"  ok  tail trims to the trailing {maxlen} tokens (_FORCE_COMMIT_HISTORY_MAXLEN)")
    finally:
        _restore_state(m, saved_state)
        m._FINAL_OPEN_PATTERN = saved_pattern


def test_end_to_end_real_kernel_forces_full_pattern() -> None:
    """The causally meaningful test: prime state past threshold and drive
    the REAL rejection_sample() (real kernel, not reimplemented) round
    after round, with the model confidently drafting a completely
    different, unrelated token every round. Confirm the ACTUAL emitted
    sequence across those rounds is exactly the real final-channel-open
    pattern, in order, and that forcing then stops."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load_patched_module()
    saved_state = _snapshot_state(m)
    try:
        device = "cuda"
        torch.manual_seed(17)
        pattern = list(m._FINAL_OPEN_PATTERN)
        vocab = max(pattern) + 1000  # room above the largest real special-token id used
        natural_favorite = 5  # what the model "really wants" every round, never in the pattern
        assert natural_favorite not in pattern

        m._FORCE_COMMIT_STATE["token_count"] = m._FORCE_COMMIT_THRESHOLD
        m._FORCE_COMMIT_STATE["final_opened"] = False
        m._FORCE_COMMIT_STATE["tail"] = []

        emitted_sequence: list[int] = []
        for _ in range(len(pattern) + 3):  # a few spare rounds past completion
            # A real, confident target AND draft distribution strongly
            # favoring natural_favorite -- WITHOUT the force this would
            # almost always be accepted and emitted instead.
            p = torch.full((1, vocab), 0.01 / (vocab - 1), device=device)
            p[0, natural_favorite] = 0.99
            q = torch.full((1, vocab), 0.01 / (vocab - 1), device=device)
            q[0, natural_favorite] = 0.99
            target_logits = torch.log(p.clamp_min(1e-12))

            draft_token_ids = torch.tensor([natural_favorite], dtype=torch.int32, device=device)
            bonus_token_ids = torch.tensor([[natural_favorite]], dtype=torch.int32, device=device)
            cu_num_draft_tokens = torch.tensor([1], dtype=torch.int32, device=device)
            sampling_metadata = SimpleNamespace(
                all_greedy=False,
                all_random=True,
                temperature=torch.tensor([1.0], device=device),
                generators={},
            )
            out = m.rejection_sample(
                draft_token_ids,
                [1],
                1,  # max_spec_len
                cu_num_draft_tokens,
                q.contiguous(),
                target_logits.contiguous(),
                bonus_token_ids,
                sampling_metadata,
            )
            emitted_sequence.append(int(out[0, 0].item()))
            if m._FORCE_COMMIT_STATE["final_opened"]:
                break

        assert emitted_sequence[: len(pattern)] == pattern, (
            f"forced sequence did not match the real final-channel-open pattern: "
            f"{emitted_sequence} vs {pattern}"
        )
        assert m._FORCE_COMMIT_STATE["final_opened"] is True
        print(f"  ok  real end-to-end rounds forced the exact {len(pattern)}-token final-channel-open "
              f"pattern over a strongly-preferred competing natural token ({natural_favorite}), then stopped")
    finally:
        _restore_state(m, saved_state)


def main() -> int:
    failures = 0
    for test in (
        test_alpha_and_threshold_plumbing,
        test_pattern_progress,
        test_apply_forces_onehot_and_respects_threshold,
        test_update_accumulates_and_detects_completion,
        test_end_to_end_real_kernel_forces_full_pattern,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-force-commit patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
