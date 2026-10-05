#!/usr/bin/env python3
"""CPU plumbing test for the Qwen3 V2 force-commit hook (installed sampler module).

Run by patches/apply.sh qwen3-force-commit-v2, or directly with .venv-vllm/bin/python.
Covers the stateless per-request rule: threshold gating, prompt-length offset, first-row
only, closing-token history, and independence between requests in one batch and
across calls. The GPU check is separate (3 Qwen3 aime24 cases, see FINDINGS).
"""

import importlib
import sys
from types import SimpleNamespace

import torch

MODULE = "vllm.v1.worker.gpu.spec_decode.rejection_sampler"
mod = importlib.import_module(MODULE)
CLOSE = 7
V = 16


class Gen:
    def __init__(self, t):
        self.gpu = t


def states(prompt_lens, buffers):
    return SimpleNamespace(prompt_len=Gen(torch.tensor(prompt_lens)), all_token_ids=Gen(buffers))


def batch(rows, reqs):
    return SimpleNamespace(
        expanded_local_pos=torch.tensor(rows),
        expanded_idx_mapping=torch.tensor(reqs),
    )


def configure(threshold, close=CLOSE):
    mod._QWEN3_FC_THRESHOLD = threshold
    mod._QWEN3_FC_CLOSE_ID = close


def forced(out, row):
    return out[row].argmax().item() == CLOSE and torch.softmax(out[row], -1)[CLOSE].item() > 0.999


def test_disabled_returns_same_object():
    configure(0)
    logits = torch.randn(2, V)
    out = mod._qwen3_force_commit(logits, batch([0, 1], [0, 0]), torch.tensor([50, 51]), states([10], torch.zeros(1, 64, dtype=torch.long)))
    assert out is logits


def test_forces_first_row_past_threshold():
    configure(20)
    logits = torch.randn(3, V)
    buf = torch.zeros(1, 64, dtype=torch.long)
    out = mod._qwen3_force_commit(logits, batch([0, 1, 2], [0, 0, 0]), torch.tensor([35, 36, 37]), states([10], buf))
    assert forced(out, 0), "first row past threshold must be forced"
    assert torch.equal(out[1:], logits[1:]), "non-first rows must be untouched"
    assert torch.isfinite(torch.softmax(out[0], -1)).all()


def test_below_threshold_untouched():
    configure(20)
    logits = torch.randn(1, V)
    buf = torch.zeros(1, 64, dtype=torch.long)
    out = mod._qwen3_force_commit(logits, batch([0], [0]), torch.tensor([25]), states([10], buf))
    assert out is logits, "generated count 15 < threshold 20 must not force"


def test_prompt_length_offset_respected():
    configure(20)
    logits = torch.randn(1, V)
    buf = torch.zeros(1, 64, dtype=torch.long)
    out = mod._qwen3_force_commit(logits, batch([0], [0]), torch.tensor([45]), states([40], buf))
    assert out is logits, "pos 45 with prompt 40 is 5 generated tokens, below threshold 20"


def test_close_in_history_disables_force():
    configure(20)
    logits = torch.randn(1, V)
    buf = torch.zeros(1, 64, dtype=torch.long)
    buf[0, 30] = CLOSE
    out = mod._qwen3_force_commit(logits, batch([0], [0]), torch.tensor([50]), states([10], buf))
    assert out is logits, "closing token already emitted must not be forced again"


def test_independent_requests_in_one_batch():
    configure(20)
    logits = torch.randn(2, V)
    buf = torch.zeros(2, 64, dtype=torch.long)
    buf[0, 30] = CLOSE  # request 0 already closed its think block
    out = mod._qwen3_force_commit(logits, batch([0, 0], [0, 1]), torch.tensor([50, 50]), states([10, 10], buf))
    assert not forced(out, 0), "request 0 already closed: must not be forced"
    assert forced(out, 1), "request 1 has no closing token: must be forced"


def test_stateless_across_calls():
    configure(20)
    buf = torch.zeros(1, 64, dtype=torch.long)
    st_closed = states([10], torch.where(torch.arange(64) == 30, CLOSE, 0).unsqueeze(0))
    st_open = states([10], buf)
    logits = torch.randn(1, V)
    closed_out = mod._qwen3_force_commit(logits, batch([0], [0]), torch.tensor([50]), st_closed)
    open_out = mod._qwen3_force_commit(logits, batch([0], [0]), torch.tensor([50]), st_open)
    assert closed_out is logits and forced(open_out, 0), "a request's decision must not depend on earlier calls"


def main() -> int:
    failures = 0
    for test in (
        test_disabled_returns_same_object,
        test_forces_first_row_past_threshold,
        test_below_threshold_untouched,
        test_prompt_length_offset_respected,
        test_close_in_history_disables_force,
        test_independent_requests_in_one_batch,
        test_stateless_across_calls,
    ):
        print(f"{test.__name__}:")
        try:
            test()
            print("  PASS")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all qwen3-force-commit-v2 hook checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
