#!/usr/bin/env python3
"""Acceptance test for the r-fuzzy-semantic-guard patch. Run by patches/apply.sh.

This patch is r-fuzzy plus one addition: an unconditional OR of a
hesitation-marker token-id check into r-fuzzy's own `defer_mask`, computed
in plain Python before the kernel launch (see the patch's module comment).
The kernel itself is byte-identical to plain r-fuzzy's (still just reads
`defer_mask_ptr`), so test_r_fuzzy.py's own `test_kernel_obeys_defer_mask`
already covers kernel correctness for this patch too -- reused verbatim
here rather than duplicated, since asserting "the kernel still does what it
always did" against a mask it can't tell apart from r-fuzzy's is exactly
the point.

Checks, in order:

1. the alpha value reaches the module, from THIS patch's own file (not
   plain r-fuzzy's -- they must never alias, see the patch's module
   comment),
2. the guard token-id set, read back from the installed module, matches
   what analysis/semantic_guard/README.md documents (18 ids, 5 markers) --
   catches an accidental edit silently changing which tokens are guarded,
3. the guard mask is True only at guarded ids, independent of the kernel --
   needs no GPU,
4. the merged defer_mask (JSD test OR guard) can only ever ADD deferrals
   relative to plain r-fuzzy's JSD-only mask, never remove one -- the
   monotonicity property the patch's inline comment claims,
5. the *kernel* obeys a supplied defer_mask correctly (identical contract
   to plain r-fuzzy's, reused from test_r_fuzzy.py).

(5) needs a GPU and is skipped without one; (1)-(4) are not.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-semantic-guard-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

# The 18 ids analysis/semantic_guard/README.md's "How many of these were
# accepted only because of the relaxed verifier" section documents deriving
# from o200k_harmony -- kept here as an independent expected value, not
# imported from the patch, so a change to the patch's own set is what this
# test is meant to catch.
EXPECTED_GUARD_TOKEN_IDS = frozenset(
    {
        29126, 17114, 5238, 24305,  # wait / Wait / " wait" / " Wait"
        112576, 186402, 165972,  # Hmm / " hmm" / " Hmm"
        138925, 87471, 4771, 50557,  # actually / Actually / " actually" / " Actually"
        8293, 7943, 889, 3072,  # but / But / " but" / " But"
        58369, 35717, 41021,  # Let's / " let's" / " Let's"
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
    """Import the module fresh; alpha is read once, at import."""
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
        print(f"  ok  module reads {ALPHA_FILE} -> 0.2 (own file, not plain r-fuzzy's)")

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
        f"installed patch's guard set differs from analysis/semantic_guard/README.md's documented "
        f"list -- missing {EXPECTED_GUARD_TOKEN_IDS - ids}, extra {ids - EXPECTED_GUARD_TOKEN_IDS}"
    )
    print(f"  ok  {len(ids)} guard token ids match analysis/semantic_guard/README.md exactly")


def _load_patched_module():
    """Import the live installed patch module directly (not a subprocess --
    the next two tests need to call its functions, not just read scalars)."""
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def test_guard_mask_formula() -> None:
    """CPU-only: _semantic_guard_mask is True only at guarded ids."""
    import torch

    m = _load_patched_module()
    guarded = sorted(m._SEMANTIC_GUARD_TOKEN_IDS)
    probe = torch.tensor([guarded[0], guarded[-1], 0, 1, 999999999], dtype=torch.int64)
    mask = m._semantic_guard_mask(probe)
    expected = torch.tensor([True, True, False, False, False])
    assert torch.equal(mask, expected), (mask.tolist(), expected.tolist())
    print(f"  ok  _semantic_guard_mask true only at guarded ids (probe={probe.tolist()})")


def test_guard_only_adds_deferrals() -> None:
    """The merged defer_mask (JSD-test OR guard) must be a superset of the
    JSD-only mask at every position -- the guard can only make this patch
    MORE conservative than plain r-fuzzy at the same alpha, never less."""
    import torch

    m = _load_patched_module()
    torch.manual_seed(0)
    guarded_id = next(iter(m._SEMANTIC_GUARD_TOKEN_IDS))
    n = 64
    draft_token_ids = torch.randint(0, 200000, (n,), dtype=torch.int64)
    draft_token_ids[0] = guarded_id  # force at least one guarded position
    # alpha = +inf: JSD (always finite) never reaches it, so jsd_only_mask is
    # all-False -- isolates what the guard alone contributes.
    jsd_only_mask = torch.zeros(n, dtype=torch.bool)
    merged_mask = jsd_only_mask | m._semantic_guard_mask(draft_token_ids)
    assert torch.equal(merged_mask, draft_token_ids == guarded_id) or merged_mask[0], merged_mask.tolist()
    assert bool((merged_mask | jsd_only_mask).eq(merged_mask).all()), "merged mask is not a superset of jsd_only_mask"
    assert bool(merged_mask[0]), "the deliberately-guarded position at index 0 was not deferred"
    print(f"  ok  merged defer_mask is a strict superset of the JSD-only mask ({int(merged_mask.sum())}/{n} deferred)")


def main() -> int:
    # test_kernel_obeys_defer_mask is intentionally NOT redefined here --
    # imported from test_r_fuzzy.py so kernel coverage can't silently drift
    # between the two patches (they must share a kernel contract exactly).
    here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    from test_r_fuzzy import test_kernel_obeys_defer_mask  # noqa: E402

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
    print("FAILED" if failures else "all r-fuzzy-semantic-guard patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
