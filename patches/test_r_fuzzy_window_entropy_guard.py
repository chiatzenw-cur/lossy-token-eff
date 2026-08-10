#!/usr/bin/env python3
"""Acceptance test for the r-fuzzy-window-entropy-guard patch. Run by patches/apply.sh.

Kernel contract is identical to plain r-fuzzy's (still just reads
defer_mask_ptr; the window-entropy logic lives entirely in the Python-side
mask construction and the post-kernel history update), so
test_kernel_obeys_defer_mask is imported from test_r_fuzzy.py rather than
duplicated, same as the two token-marker guards' own tests.

Checks specific to this variant:

1. alpha plumbing, own file (not aliased with any sibling arm's).
2. the window sizes match what's documented -- (64, 32, 16, 8), no
   calibrated threshold (deliberately unquantified, see the patch's own
   module comment).
3. _is_monotonic_ramp itself: true only when mean(w64) < mean(w32) <
   mean(w16) < mean(w8) holds exactly; a single out-of-order pair anywhere
   in the staircase breaks it, including a high-but-FLAT window (which a
   level threshold would have let through).
4. _window_entropy_gate_and_update's pre-kernel call: no guard fires before
   the window has 64 entries of history (cold start); a genuine 4-scale
   ramp triggers it, jointly for both target and draft (only one metric
   ramping must NOT trigger it).
5. the post-kernel call appends exactly the committed positions' entropy to
   history, in order, and stops at the first rejected position (mirroring
   relaxation_trace.py's own walk, checked independently here since this
   patch's version must not depend on tracing being enabled).
6. the module-level history is a real per-process deque, not reset between
   calls within one test process (this repo's one-request-per-server
   protocol is what makes that a correct simplification -- see the patch's
   own module comment).
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import subprocess
import sys

ALPHA_FILE = pathlib.Path(f"/tmp/lossy-token-eff-r-fuzzy-window-entropy-guard-alpha-{os.getuid()}")
MODULE = "vllm.v1.sample.rejection_sampler"

READ_BACK = """
import importlib, json, sys
m = importlib.import_module(sys.argv[1])
print("JSON:" + json.dumps({
    "alpha": m._R_FUZZY_ALPHA,
    "path": m._R_FUZZY_ALPHA_FILE,
    "window_sizes": list(m._WINDOW_ENTROPY_SIZES),
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


def test_alpha_plumbing() -> None:
    saved = ALPHA_FILE.read_text() if ALPHA_FILE.is_file() else None
    try:
        ALPHA_FILE.write_text("0.2\n")
        got = read_back_in_subprocess()
        assert got["alpha"] == 0.2, got
        assert got["path"] == str(ALPHA_FILE), got
        print(f"  ok  module reads {ALPHA_FILE} -> 0.2 (own file, not any sibling arm's)")

        ALPHA_FILE.unlink()
        got = read_back_in_subprocess()
        assert got["alpha"] == float("-inf"), got
        print("  ok  missing file falls back to -inf (Div < -inf never true -> strict spec-dec)")
    finally:
        if saved is None:
            ALPHA_FILE.unlink(missing_ok=True)
        else:
            ALPHA_FILE.write_text(saved)


def test_window_sizes() -> None:
    got = read_back_in_subprocess()
    assert got["window_sizes"] == [64, 32, 16, 8], got
    print("  ok  window_sizes = (64, 32, 16, 8), unquantified -- no calibrated threshold used")


def _load_patched_module():
    spec = importlib.util.find_spec(MODULE)
    if spec is None:
        raise AssertionError(f"{MODULE} not importable -- is a vLLM venv active?")
    return importlib.import_module(MODULE)


def _flat_dist(vocab: int, hot_idx: int, hot_mass: float, device: str = "cpu"):
    import torch

    d = torch.full((vocab,), (1.0 - hot_mass) / (vocab - 1))
    d[hot_idx] = hot_mass
    return d


def _uniform_dist(vocab: int, device: str = "cpu"):
    import torch

    return torch.full((vocab,), 1.0 / vocab, device=device)


def test_is_monotonic_ramp_formula() -> None:
    """CPU-only, no GPU/module needed: a hand-built history whose w64/w32/
    w16/w8 means are exactly increasing must pass; the same history with
    just the LAST 8 entries flattened out (breaking only the final step of
    the staircase) must fail -- one broken link is enough."""
    m = _load_patched_module()
    w64, w32, w16, w8 = m._WINDOW_ENTROPY_SIZES

    # Construct history so each nested window's mean is strictly higher than
    # the one enclosing it: oldest 32 entries near 0.0, next 16 near 1.0,
    # next 8 near 2.0, last 8 near 3.0 -- a coarse but unambiguous ramp.
    history = [0.0] * (w64 - w32) + [1.0] * (w32 - w16) + [2.0] * (w16 - w8) + [3.0] * w8
    assert len(history) == w64
    assert m._is_monotonic_ramp(history), "hand-built ramp did not register as monotonic"
    print("  ok  a genuine 4-scale ramp registers as monotonic")

    flattened = history[:-w8] + [1.0] * w8  # last-8 mean now BELOW the w16 mean -> breaks only the last step
    assert not m._is_monotonic_ramp(flattened), "flattening just the final step did not break monotonicity"
    print("  ok  breaking even one step of the staircase (here: the final w8 step) fails the check")

    flat_high = [3.5] * w64  # high level, but flat throughout -- must not register as a ramp
    assert not m._is_monotonic_ramp(flat_high), "flat-but-high history incorrectly registered as a ramp"
    print("  ok  a high-but-FLAT history does not register as a ramp (this is the point of using shape, not level)")


def test_cold_start_never_guards() -> None:
    """Before the window has 64 entries of history (the largest scale
    checked), the pre-kernel call must never guard."""
    import torch

    m = _load_patched_module()
    m._window_entropy_target_history.clear()
    m._window_entropy_draft_history.clear()

    vocab = 8
    n = 5  # well under 64
    target_probs = torch.stack([_uniform_dist(vocab) for _ in range(n)])
    draft_probs = torch.stack([_uniform_dist(vocab) for _ in range(n)])
    draft_token_ids = torch.zeros(n, dtype=torch.int64)
    cu = torch.tensor([n], dtype=torch.int32)

    mask = m._window_entropy_gate_and_update(target_probs, draft_probs, None, draft_token_ids, cu, [n])
    assert mask is not None
    assert not bool(mask.any()), f"guard fired cold (history len={len(m._window_entropy_target_history)}): {mask.tolist()}"
    print("  ok  no guard activity before the window has 64 entries of history")


def test_joint_ramp_and_history_update() -> None:
    """The behavioural core of this design: a genuine joint 4-scale ramp in
    BOTH target and draft entropy triggers the guard; a ramp in only one of
    the two does not (joint AND, not OR)."""
    import torch

    m = _load_patched_module()
    vocab = 64
    w64 = m._WINDOW_ENTROPY_SIZES[0]

    def entropy_of(dist: torch.Tensor) -> float:
        return float(-(dist * dist.clamp_min(1e-12).log()).sum())

    high_dist = _uniform_dist(vocab)  # near-max entropy, ~log(64)=4.16
    # Ramp: hot_mass falling linearly across the window -> entropy rising.
    ramp_masses = [0.99 - i * (0.99 - 1.0 / vocab) / (w64 - 1) for i in range(w64)]
    ramp_entropies = [entropy_of(_flat_dist(vocab, 0, mass)) for mass in ramp_masses]
    flat_high_entropies = [entropy_of(high_dist)] * w64

    target_probs = high_dist.unsqueeze(0)
    draft_probs = high_dist.unsqueeze(0)
    draft_token_ids = torch.zeros(1, dtype=torch.int64)
    cu = torch.tensor([1], dtype=torch.int32)

    # Case A: both target and draft histories ramping -> guard should fire.
    m._window_entropy_target_history.clear()
    m._window_entropy_draft_history.clear()
    m._window_entropy_target_history.extend(ramp_entropies)
    m._window_entropy_draft_history.extend(ramp_entropies)
    mask = m._window_entropy_gate_and_update(target_probs, draft_probs, None, draft_token_ids, cu, [1])
    assert bool(mask[0]), "jointly-ramping window did not trigger the guard"
    print("  ok  guard fires when both target and draft windows show the 4-scale ramp")

    # Case B: both HIGH but FLAT -> must NOT fire (no ramp, regardless of level).
    m._window_entropy_target_history.clear()
    m._window_entropy_draft_history.clear()
    m._window_entropy_target_history.extend(flat_high_entropies)
    m._window_entropy_draft_history.extend(flat_high_entropies)
    mask = m._window_entropy_gate_and_update(target_probs, draft_probs, None, draft_token_ids, cu, [1])
    assert not bool(mask[0]), "flat-but-high window incorrectly triggered the (ramp) guard"
    print("  ok  guard does NOT fire on a high-but-FLAT window")

    # Case C: target ramping, draft FLAT -> joint AND must not fire.
    m._window_entropy_target_history.clear()
    m._window_entropy_draft_history.clear()
    m._window_entropy_target_history.extend(ramp_entropies)
    m._window_entropy_draft_history.extend(flat_high_entropies)
    mask = m._window_entropy_gate_and_update(target_probs, draft_probs, None, draft_token_ids, cu, [1])
    assert not bool(mask[0]), "target-only-ramping window incorrectly triggered the (joint) guard"
    print("  ok  guard does NOT fire when only one of target/draft is ramping (joint AND, not OR)")

    # History update: post-kernel call with output_token_ids marking position
    # 0 accepted (== draft_token_ids) should append exactly one entry.
    m._window_entropy_target_history.clear()
    m._window_entropy_draft_history.clear()
    n = 3
    target_probs3 = torch.stack([high_dist, high_dist, high_dist])
    draft_probs3 = torch.stack([high_dist, high_dist, high_dist])
    draft_token_ids3 = torch.tensor([0, 0, 0], dtype=torch.int64)
    cu3 = torch.tensor([3], dtype=torch.int32)
    # position 0 accepted, position 1 rejected (emitted != draft), position 2 never reached (-1)
    output_token_ids = torch.tensor([[0, 5, -1, -1]], dtype=torch.int64)
    result = m._window_entropy_gate_and_update(target_probs3, draft_probs3, output_token_ids, draft_token_ids3, cu3, [3])
    assert result is None, "post-kernel call must return None (it updates state, not a mask)"
    assert len(m._window_entropy_target_history) == 2, (
        f"expected 2 committed entries (accepted pos 0 + rejected-but-reached pos 1), "
        f"got {len(m._window_entropy_target_history)}"
    )
    print("  ok  history update appends exactly the reached positions (accepted + the one rejection), stops there")


def main() -> int:
    here = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    from test_r_fuzzy import test_kernel_obeys_defer_mask  # noqa: E402 -- shared kernel contract

    failures = 0
    for test in (
        test_alpha_plumbing,
        test_window_sizes,
        test_is_monotonic_ramp_formula,
        test_cold_start_never_guards,
        test_joint_ramp_and_history_update,
        test_kernel_obeys_defer_mask,
    ):
        print(f"{test.__name__}:")
        try:
            test()
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {exc}")
    print("FAILED" if failures else "all r-fuzzy-window-entropy-guard patch checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
