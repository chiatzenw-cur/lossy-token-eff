#!/usr/bin/env python3
"""Acceptance test for the r-fuzzy-semantic-guard-v2 patch. Run by patches/apply.sh.

Structurally identical to test_r_fuzzy_semantic_guard.py (v1's test) -- same
mechanism, same kernel, same contract -- just checking v2's wider token set
and its own, separate alpha file instead. See that file's docstring for why
each check exists; not re-explained here.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-semantic-guard-v2-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

# The 35 ids (18 from v1, 17 new) the patch's own module comment documents.
EXPECTED_GUARD_TOKEN_IDS = frozenset(
    {
        # v1's original 5 markers
        29126, 17114, 5238, 24305,  # wait / Wait / " wait" / " Wait"
        112576, 186402, 165972,  # Hmm / " hmm" / " Hmm"
        138925, 87471, 4771, 50557,  # actually / Actually / " actually" / " Actually"
        8293, 7943, 889, 3072,  # but / But / " but" / " But"
        58369, 35717, 41021,  # Let's / " let's" / " Let's"
        # v2's additions
        84787, 23586,  # Thus / " Thus"
        2167, 1416,  # We / " We"
        5808, 2632,  # So / " So"
        10620, 6549,  # Now / " Now"
        12845,  # Let (sentence-initial only)
        56734, 45438,  # Compute / " Compute"
        151907, 65037,  # Similarly / " Similarly"
        55292, 38966,  # Define / " Define"
        3879, 7217,  # From / " From"
    }
)

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._R_FUZZY_ALPHA,
    "path": m._R_FUZZY_ALPHA_FILE,
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


def test_alpha_plumbing() -> None:
    saved = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.2\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.2, got
        assert got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.2 (own file, not v1's or plain r-fuzzy's)")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (Div < -inf never true -> strict spec-dec)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def test_guard_token_ids() -> None:
    got = read_back_in_subprocess()
    ids = set(got["guard_ids"])
    assert ids == EXPECTED_GUARD_TOKEN_IDS, (
        f"installed patch's guard set differs from the documented v2 list -- "
        f"missing {EXPECTED_GUARD_TOKEN_IDS - ids}, extra {ids - EXPECTED_GUARD_TOKEN_IDS}"
    )
    assert len(ids) == 35, f"expected 35 guard ids, got {len(ids)}"
    print(f"  ok  {len(ids)} guard token ids match the documented v2 list exactly")


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


def test_guard_only_adds_deferrals() -> None:
    import torch

    m = _load_patched_module()
    torch.manual_seed(0)
    guarded_id = next(iter(m._SEMANTIC_GUARD_TOKEN_IDS))
    n = 64
    draft_token_ids = torch.randint(0, 200000, (n,), dtype=torch.int64)
    draft_token_ids[0] = guarded_id
    jsd_only_mask = torch.zeros(n, dtype=torch.bool)
    merged_mask = jsd_only_mask | m._semantic_guard_mask(draft_token_ids)
    assert bool((merged_mask | jsd_only_mask).eq(merged_mask).all()), "merged mask is not a superset of jsd_only_mask"
    assert bool(merged_mask[0]), "the deliberately-guarded position at index 0 was not deferred"
    print(f"  ok  merged defer_mask is a strict superset of the JSD-only mask ({int(merged_mask.sum())}/{n} deferred)")


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    from test_r_fuzzy import test_kernel_obeys_defer_mask  # noqa: E402 -- shared kernel contract, see v1's test docstring

    failures = 0
    for test in (
        test_alpha_plumbing,
        test_guard_token_ids,
        test_guard_mask_formula,
        test_guard_only_adds_deferrals,
        test_kernel_obeys_defer_mask,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all r-fuzzy-semantic-guard-v2 patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
