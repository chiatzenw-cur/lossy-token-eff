#!/usr/bin/env python3
"""CPU plumbing test for the Qwen3 V2 force-commit core. No GPU, no vLLM import.

Run: .venv-vllm/bin/python patches/test_qwen3_force_commit_v2_core.py
"""

import importlib.util
import pathlib
import sys

import torch

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("q3core", HERE / "qwen3_force_commit_v2_core.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

V, CLOSE = 32, 7


def make(rows, reqs):
    logits = torch.randn(rows, V, generator=torch.Generator().manual_seed(0))
    return logits


def case(name, fn):
    try:
        fn()
        print(f"PASS {name}")
    except AssertionError as exc:
        print(f"FAIL {name}: {exc}")
        raise SystemExit(1)


def below_threshold_is_identity():
    logits = torch.randn(3, V)
    idx = torch.tensor([0, 0, 0])
    loc = torch.tensor([0, 1, 2])
    pos = torch.tensor([100, 101, 102])
    buf = torch.zeros(1, 512, dtype=torch.long)
    plen = torch.tensor([10])
    out, mask = core.force_commit_rows(logits, idx, loc, pos, buf, plen, CLOSE, threshold=1000)
    assert out is logits and not mask.any(), "expected unchanged tensor and empty mask"


def forces_first_row_one_hot():
    logits = torch.randn(3, V)
    before = logits.clone()
    idx = torch.tensor([0, 0, 0])
    loc = torch.tensor([0, 1, 2])
    pos = torch.tensor([50, 51, 52])
    buf = torch.zeros(1, 512, dtype=torch.long)
    plen = torch.tensor([10])
    out, mask = core.force_commit_rows(logits, idx, loc, pos, buf, plen, CLOSE, threshold=30)
    assert mask.tolist() == [True, False, False], mask.tolist()
    probs = torch.softmax(out[0], dim=-1)
    assert probs.argmax().item() == CLOSE and probs[CLOSE].item() > 0.999999, probs
    assert torch.equal(out[1:], logits[1:]), "non-first rows must be untouched"
    assert torch.equal(logits, before), "input must not be mutated"


def close_in_history_disables_force():
    logits = torch.randn(2, V)
    idx = torch.tensor([0, 0])
    loc = torch.tensor([0, 1])
    pos = torch.tensor([50, 51])
    buf = torch.zeros(1, 512, dtype=torch.long)
    buf[0, 30] = CLOSE
    plen = torch.tensor([10])
    out, mask = core.force_commit_rows(logits, idx, loc, pos, buf, plen, CLOSE, threshold=30)
    assert out is logits and not mask.any(), "close already emitted must be a permanent no-op"


def per_request_first_rows_only():
    logits = torch.randn(4, V)
    idx = torch.tensor([0, 0, 1, 1])
    loc = torch.tensor([0, 1, 0, 1])
    pos = torch.tensor([50, 51, 60, 61])
    buf = torch.zeros(2, 512, dtype=torch.long)
    plen = torch.tensor([10, 10])
    out, mask = core.force_commit_rows(logits, idx, loc, pos, buf, plen, CLOSE, threshold=30)
    assert mask.tolist() == [True, False, True, False], mask.tolist()


def request_past_threshold_only():
    logits = torch.randn(2, V)
    idx = torch.tensor([0, 1])
    loc = torch.tensor([0, 0])
    pos = torch.tensor([45, 80])
    buf = torch.zeros(2, 512, dtype=torch.long)
    plen = torch.tensor([10, 10])
    out, mask = core.force_commit_rows(logits, idx, loc, pos, buf, plen, CLOSE, threshold=50)
    assert mask.tolist() == [False, True], mask.tolist()


def closing_token_is_single_token():
    try:
        from transformers import AutoTokenizer
    except ImportError:
        print("SKIP closing_token_is_single_token (no transformers)")
        return
    snap = pathlib.Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-8B/snapshots"
    snaps = sorted(snap.glob("*/")) if snap.is_dir() else []
    if not snaps:
        print("SKIP closing_token_is_single_token (no cached Qwen3 tokenizer)")
        return
    tok = AutoTokenizer.from_pretrained(str(snaps[0]), local_files_only=True)
    assert core.closing_token_id(tok) == 151668


for name, fn in [
    ("below_threshold_is_identity", below_threshold_is_identity),
    ("forces_first_row_one_hot", forces_first_row_one_hot),
    ("close_in_history_disables_force", close_in_history_disables_force),
    ("per_request_first_rows_only", per_request_first_rows_only),
    ("request_past_threshold_only", request_past_threshold_only),
    ("closing_token_is_single_token", closing_token_is_single_token),
]:
    case(name, fn)
print("ALL PASS")
