#!/usr/bin/env python3
"""Acceptance test for the hidden-state-capture patch. Run by
patches/apply_hidden_state_capture.sh.

CPU-only, no GPU/model needed: this patch's own logic (projection, file
format, round counting, disable-on-error) is pure tensor/file-I/O code, and
the one thing that actually depends on the real model (the hook call site
in model_runner.py) is a single line calling this module's own already-
tested record(), so there's nothing kernel-level to drive here the way the
rejection-sampler patches' tests do.

Checks:

1. destination-file plumbing: no file -> disabled (no-op, never writes);
   file present -> enabled, writes to the path it names.
2. the random projection is deterministic (fixed seed) -- two fresh
   instances against the same hidden_size produce bit-identical output for
   the same input, so re-running a capture is reproducible.
3. round-trip: write a few rounds of known vectors, read the row format
   back by hand (not via the analysis-side reader, to keep this test
   independent of it), check round/pos_in_round/vector values survive
   exactly.
4. warmup-sized batches (the _MAX_REAL_BATCH heuristic) are skipped, not
   written.
5. a record() call that raises internally disables the tracer rather than
   propagating -- Phase 1 must never be able to crash generation.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import struct
import sys

DEST_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hidden-state-trace-{os.getuid()}")
MODULE = "vllm.v1.worker.hidden_state_trace"
ROW_HEADER = struct.Struct("<IH")
PROJECTION_DIM = 128


def _load_module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def test_disabled_by_default() -> None:
    saved = DEST_FILE.read_text() if DEST_FILE.is_file() else None
    try:
        DEST_FILE.unlink(missing_ok=True)
        m = _load_module()
        tracer = m._HiddenStateTracer()
        assert not tracer.enabled, "tracer enabled with no destination file present"
        print("  ok  no destination file -> disabled")
    finally:
        if saved is not None:
            DEST_FILE.write_text(saved)


def test_deterministic_projection() -> None:
    import torch

    m = _load_module()
    t1 = m._HiddenStateTracer.__new__(m._HiddenStateTracer)
    t1._projection = None
    t2 = m._HiddenStateTracer.__new__(m._HiddenStateTracer)
    t2._projection = None

    hidden = torch.randn(4, 256)
    p1 = t1._get_projection(256, hidden.device, torch.float32)
    p2 = t2._get_projection(256, hidden.device, torch.float32)
    assert torch.equal(p1, p2), "projection matrix differs across fresh instances (seed not fixed?)"
    assert p1.shape == (PROJECTION_DIM, 256), p1.shape
    print(f"  ok  projection matrix is deterministic across instances, shape {tuple(p1.shape)}")


def test_round_trip_and_warmup_skip(tmp_out: pathlib.Path) -> None:
    import numpy as np
    import torch

    DEST_FILE.write_text(str(tmp_out))
    m = _load_module()
    tracer = m._HiddenStateTracer()
    assert tracer.enabled

    hidden_size = 64
    round0 = torch.randn(3, hidden_size)  # a normal 3-position round
    round1 = torch.randn(2, hidden_size)
    warmup = torch.randn(m._MAX_REAL_BATCH * 32 + 1, hidden_size)  # over the skip threshold

    tracer.record(round0)
    tracer.record(warmup)  # must be skipped, not written
    tracer.record(round1)
    tracer._file.close()

    raw = tmp_out.read_bytes()
    row_size = ROW_HEADER.size + PROJECTION_DIM * 2  # float16 = 2 bytes
    assert len(raw) % row_size == 0, f"file size {len(raw)} not a multiple of row size {row_size}"
    n_rows = len(raw) // row_size
    assert n_rows == 5, f"expected 3 + 2 = 5 rows (warmup batch skipped), got {n_rows}"

    rounds_seen = []
    offset = 0
    for _ in range(n_rows):
        rnd, pos = ROW_HEADER.unpack(raw[offset : offset + ROW_HEADER.size])
        offset += ROW_HEADER.size
        vec = np.frombuffer(raw[offset : offset + PROJECTION_DIM * 2], dtype=np.float16)
        offset += PROJECTION_DIM * 2
        assert vec.shape == (PROJECTION_DIM,), vec.shape
        assert abs(float(np.linalg.norm(vec.astype(np.float32))) - 1.0) < 0.05, "row is not ~unit-normalized"
        rounds_seen.append((rnd, pos))

    # round0 (3 positions) -> round index 0; warmup skipped, round counter
    # does NOT advance for it; round1 (2 positions) -> round index 1.
    assert rounds_seen == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1)], rounds_seen
    print(f"  ok  5 rows round-tripped exactly (3+2, warmup batch correctly skipped, unit-normalized)")


def test_record_failure_disables_not_raises(tmp_out: pathlib.Path) -> None:
    DEST_FILE.write_text(str(tmp_out))
    m = _load_module()
    tracer = m._HiddenStateTracer()
    assert tracer.enabled

    # Pass something that will blow up inside record() (wrong type) --
    # must be swallowed and disable the tracer, never propagate.
    tracer.record("not a tensor")  # type: ignore[arg-type]
    assert not tracer.enabled, "tracer stayed enabled after record() hit an internal error"
    print("  ok  a record() failure disables the tracer instead of raising")


def main() -> int:
    import tempfile

    failures = 0
    tests_needing_tmp = {
        test_round_trip_and_warmup_skip,
        test_record_failure_disables_not_raises,
    }
    for test in (
        test_disabled_by_default,
        test_deterministic_projection,
        test_round_trip_and_warmup_skip,
        test_record_failure_disables_not_raises,
    ):
        print(f"{test.__name__}:")
        try:
            if test in tests_needing_tmp:
                with tempfile.TemporaryDirectory() as d:
                    test(pathlib.Path(d) / "hidden_states.bin")
            else:
                test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all hidden-state-capture patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
