#!/usr/bin/env python3
"""Acceptance test for the spec-casc-tok-antiloop patch. Run by
patches/apply.sh.

Reactive repetition breaker on top of plain spec-casc-tok: the moment a
drafted continuation would complete a genuine periodic repeat (period k in
[1,12], 3rd consecutive occurrence -- the ground-truth definition this
investigation validated, not a new threshold), that specific (position,
token) gets zeroed out of target_probs and the row renormalized, BEFORE
spec-casc-tok's own eta/pi_rej math runs. No kernel changes -- everything
downstream (eta, pi_rej, the accept-test kernel, recovery) is already a
pure function of target_probs, so a banned token automatically falls out of
the trusted top set, gets pi_rej=0 (guaranteed rejection regardless of
alpha/u), and gets zero recovery mass too.

Checks, in order:

1. _antiloop_completes_repeat: the periodic-repeat detector in isolation,
   various periods and edge cases, no GPU needed,
2. _antiloop_apply_ban: given a drafted continuation that completes a
   repeat, the flagged (position, token) entry is zeroed and its row
   renormalized to a valid distribution; unflagged rows are untouched byte-
   for-byte,
3. _antiloop_update_history: cross-round persistence trims correctly and a
   warmup-shaped batch resets it, same convention as this repo's future-
   guard patches,
4. END-TO-END: drive the REAL, unmodified rejection_sample() (real kernel,
   not a Python re-implementation) with history pre-seeded so the next
   drafted token would complete a repeat, and confirm the token ACTUALLY
   emitted is never the banned one across many repeated trials -- the
   causally meaningful test, since it exercises the exact code path a real
   server round would.

(4) needs a GPU and is skipped without one; the rest do not.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-spec-casc-tok-antiloop-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._SPEC_CASC_TOK_ALPHA,
    "path": m._SPEC_CASC_TOK_ANTILOOP_ALPHA_FILE,
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


def _load_patched_module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def test_completes_repeat_detector() -> None:
    m = _load_patched_module()
    f = m._antiloop_completes_repeat
    R = m._ANTILOOP_MIN_REPEATS  # 3

    # Period-1 (single-token) repeat: [7,7,7] should trigger, [7,7,x] should not.
    assert f([7, 7, 7]), "period-1 triple repeat should be flagged"
    assert not f([7, 7, 8]), "not a real repeat (last token differs)"
    assert not f([7, 7]), "too short to reach R=3 repeats at any period"

    # Period-2 repeat: [1,2,1,2,1,2] (three repeats of "1,2") should trigger.
    assert f([1, 2, 1, 2, 1, 2]), "period-2 triple repeat should be flagged"
    assert not f([1, 2, 1, 2, 1, 3]), "third repeat broken by a mismatched tail token"
    assert not f([1, 2, 3, 1, 2, 1, 2]), "only two repeats of the period-2 block, not three"

    # Longer period (k=5), exactly R=3 repeats -- the shape closest to this
    # investigation's real case_004 example (a multi-token cycle).
    block = [10, 20, 30, 40, 50]
    seq = block * 3
    assert f(seq), "period-5 triple repeat should be flagged"
    assert not f(block * 2), "only two repeats, not three -- must not fire early"

    # Smallest-period preference: a period-1 repeat embedded in a longer tail
    # should still be detected (via the smallest matching k, not missed
    # because a larger k's own check ran first and didn't match).
    assert f([9, 1, 1, 1]), "period-1 repeat at the very end should still be caught"

    # Max period boundary: exactly at _ANTILOOP_MAX_PERIOD should still work;
    # one longer than max should not (by construction -- not this method's
    # job to catch periods it was never configured to check).
    max_k = m._ANTILOOP_MAX_PERIOD
    at_max = list(range(max_k)) * R
    assert f(at_max), f"period exactly at MAX_PERIOD={max_k} should be caught"
    too_long = list(range(max_k + 1)) * R
    assert not f(too_long), f"period beyond MAX_PERIOD={max_k} is out of scope by design"

    print(f"  ok  periodic-repeat detector correct across period-1, period-2, period-{max_k} "
          f"(MAX_PERIOD), and the out-of-range boundary")


def test_apply_ban_zeroes_and_renormalizes() -> None:
    import torch

    m = _load_patched_module()
    saved_history = list(m._ANTILOOP_HISTORY["tokens"])
    try:
        # History primes a period-2 pattern "5,6" already repeated twice
        # (4 tokens: 5,6,5,6); the next drafted token completing "5,6" a
        # THIRD time (token 5 at position 0, matching_id6 at position1) should
        # get banned. Single request (batch_size=1), 2 drafted positions.
        m._ANTILOOP_HISTORY["tokens"] = [5, 6, 5, 6]
        vocab = 16
        draft_token_ids = torch.tensor([5, 6], dtype=torch.int64)
        num_draft_tokens = [2]
        cu_num_draft_tokens = torch.tensor([2], dtype=torch.int64)
        target_probs = torch.full((2, vocab), 1.0 / vocab)
        target_probs = target_probs / target_probs.sum(dim=-1, keepdim=True)

        banned, mask = m._antiloop_apply_ban(target_probs, draft_token_ids, num_draft_tokens, cu_num_draft_tokens)

        # history=[5,6,5,6], drafting 5 (pos0) then 6 (pos1). After appending
        # 5: seq=[5,6,5,6,5] -- period-2 check needs span=3*2=6, seq len=5<6,
        # no match yet at pos0. After appending 6: seq=[5,6,5,6,5,6], len=6,
        # tail=seq itself, blocks [5,6],[5,6],[5,6] all equal -> matches at pos1.
        assert mask.tolist() == [False, True], f"got {mask.tolist()}"
        assert banned[1, 6].item() == 0.0, "banned token's probability must be exactly zero"
        assert abs(banned[1].sum().item() - 1.0) < 1e-5, "banned row must renormalize to a valid distribution"
        assert torch.allclose(banned[0], target_probs[0]), "unflagged row must be untouched"
        print("  ok  banned entry zeroed, row renormalizes to 1.0, unflagged row untouched byte-for-byte")
    finally:
        m._ANTILOOP_HISTORY["tokens"] = saved_history


def test_history_persistence_and_warmup_reset() -> None:
    import torch

    m = _load_patched_module()
    saved_history = list(m._ANTILOOP_HISTORY["tokens"])
    try:
        m._ANTILOOP_HISTORY["tokens"] = []
        # Simulate 3 rounds' worth of real output (slot 0 only), including a
        # PLACEHOLDER-padded row (positions after an in-round rejection never
        # got written -- must be excluded, not treated as token id -1).
        PLACEHOLDER = m.PLACEHOLDER_TOKEN_ID
        round1 = torch.tensor([[100, 101, 102, PLACEHOLDER]], dtype=torch.int32)
        m._antiloop_update_history(round1, [3], batch_size=1)
        assert m._ANTILOOP_HISTORY["tokens"] == [100, 101, 102], m._ANTILOOP_HISTORY["tokens"]

        round2 = torch.tensor([[200, PLACEHOLDER, PLACEHOLDER, PLACEHOLDER]], dtype=torch.int32)
        m._antiloop_update_history(round2, [1], batch_size=1)
        assert m._ANTILOOP_HISTORY["tokens"] == [100, 101, 102, 200], m._ANTILOOP_HISTORY["tokens"]
        print("  ok  history accumulates real emitted tokens across rounds, ignoring PLACEHOLDER padding")

        # Trim check: push past _ANTILOOP_HISTORY_MAXLEN, confirm only the
        # trailing MAXLEN tokens survive.
        maxlen = m._ANTILOOP_HISTORY_MAXLEN
        big_round = torch.tensor([list(range(9000, 9000 + maxlen + 10))], dtype=torch.int32)
        m._antiloop_update_history(big_round, [maxlen + 10], batch_size=1)
        assert len(m._ANTILOOP_HISTORY["tokens"]) == maxlen, len(m._ANTILOOP_HISTORY["tokens"])
        assert m._ANTILOOP_HISTORY["tokens"][-1] == 9000 + maxlen + 10 - 1
        print(f"  ok  history trims to the trailing {maxlen} tokens (_ANTILOOP_HISTORY_MAXLEN)")

        # Warmup reset: a batch shaped like vLLM's own warmup/CUDA-graph-
        # capture passes must clear history rather than extend it.
        assert m._ANTILOOP_WARMUP_BATCH_THRESHOLD < 50
        warmup_round = torch.full((m._ANTILOOP_WARMUP_BATCH_THRESHOLD + 10, 2), 1, dtype=torch.int32)
        m._antiloop_update_history(warmup_round, [2] * (m._ANTILOOP_WARMUP_BATCH_THRESHOLD + 10),
                                    batch_size=m._ANTILOOP_WARMUP_BATCH_THRESHOLD + 10)
        assert m._ANTILOOP_HISTORY["tokens"] == [], "warmup-shaped batch must reset history to empty"
        print("  ok  warmup-shaped batch resets history instead of extending it")
    finally:
        m._ANTILOOP_HISTORY["tokens"] = saved_history


def test_end_to_end_real_kernel_avoids_banned_token() -> None:
    """The causally meaningful test: drive the REAL rejection_sample()
    (real kernel, not reimplemented) with history primed so the drafted
    continuation completes a repeat, and confirm the token actually
    emitted at that position is never the banned one, across many trials
    (accept/recovery both involve real randomness, so this needs repetition
    to be convincing, not a single draw)."""
    import torch
    from types import SimpleNamespace

    if not torch.cuda.is_available():
        print("  skip  no CUDA device; end-to-end test not run")
        return

    m = _load_patched_module()
    saved_history = list(m._ANTILOOP_HISTORY["tokens"])
    try:
        device = "cuda"
        torch.manual_seed(11)
        vocab = 32
        banned_token = 6  # period-1 repeat: history already has it twice
        # ([6,6]); this single drafted position proposing it again would
        # complete the 3rd consecutive occurrence -- period-1 is the only
        # period a SINGLE drafted position can complete on its own (a
        # period-k>1 repeat needs k new positions to finish a new block,
        # not just one -- caught once already in this test file's own
        # test_apply_ban_zeroes_and_renormalizes, which uses 2 positions
        # for exactly this reason).

        # Strongly favor the banned token in BOTH draft and target, so that
        # WITHOUT the ban this would almost always be accepted and repeated
        # again -- the ban has real work to do here, not a vacuous case.
        p = torch.full((1, vocab), 0.01 / (vocab - 1), device=device)
        p[0, banned_token] = 0.99
        q = torch.full((1, vocab), 0.01 / (vocab - 1), device=device)
        q[0, banned_token] = 0.99
        target_logits = torch.log(p.clamp_min(1e-12))

        draft_token_ids = torch.tensor([banned_token], dtype=torch.int32, device=device)
        bonus_token_ids = torch.tensor([[7]], dtype=torch.int32, device=device)
        cu_num_draft_tokens = torch.tensor([1], dtype=torch.int32, device=device)

        sampling_metadata = SimpleNamespace(
            all_greedy=False,
            all_random=True,
            temperature=torch.tensor([1.0], device=device),
            generators={},
        )

        outcomes = []
        for trial in range(30):
            m._ANTILOOP_HISTORY["tokens"] = [banned_token, banned_token]  # primes the 3rd-repeat completion
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
            outcomes.append(int(out[0, 0].item()))

        assert all(t != banned_token for t in outcomes), (
            f"banned token {banned_token} was emitted at the flagged position in at least one "
            f"of {len(outcomes)} trials -- the ban did not take effect end-to-end: {outcomes}"
        )
        distinct = set(outcomes)
        print(f"  ok  banned token never emitted across {len(outcomes)} real end-to-end trials "
              f"(outcomes drawn from {len(distinct)} distinct token ids instead)")
    finally:
        m._ANTILOOP_HISTORY["tokens"] = saved_history


def main() -> int:
    failures = 0
    for test in (
        test_alpha_plumbing,
        test_completes_repeat_detector,
        test_apply_ban_zeroes_and_renormalizes,
        test_history_persistence_and_warmup_reset,
        test_end_to_end_real_kernel_avoids_banned_token,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all spec-casc-tok-antiloop patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
