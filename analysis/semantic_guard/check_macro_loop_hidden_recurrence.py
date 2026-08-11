#!/usr/bin/env python3
"""Does the ONE confirmed macro-loop restart (case_028, hidden_state_pilot
run, output_position 31478 -- see find_macro_loop_restarts.py and the
README's "Single-event counterfactual" section for how this pattern was
first noticed) show elevated hidden-state recurrence, the way the
token-level repetition loops the recurrence detector was originally built
for do?

Two separate tests, since a macro-loop's surface tokens are mostly
DIFFERENT across cycles (it's a fresh derivation each time, not a repeated
phrase) -- a generic trailing-window test and a structurally-targeted one
may not agree:

1. GENERIC: the same S_k windowed-recurrence score
   (join_hidden_states.recurrence_scores) used by
   find_hidden_state_recurrence_onsets.py, evaluated at the restart
   position and ranked against this run's own full score distribution
   (same per-run empirical-percentile framing used there).

2. TARGETED: this run has two structurally analogous "start of an attempt"
   points -- the FIRST time it opens `<|channel|>final<|message|>`
   (position 30953, immediately abandoned) and the restart itself
   (position 31478, re-opening `<|channel|>analysis<|message|>`). Does the
   raw (unwindowed) hidden-state cosine similarity between THESE TWO
   SPECIFIC points sit unusually high relative to the run's own background
   distribution of pairwise similarities -- i.e. does "restarting" mean
   returning to a state resembling the PREVIOUS attempt's own start, not
   just "some" earlier state (which is all test 1 can see)?

n=1 macro-loop restart in the current dataset (only 8 cases have hidden-
state capture, only case_028 shows this exact channel-boundary pattern --
see find_macro_loop_restarts.py's output). Treat everything below as a
single case study, not a rate.

Usage:
    python3 analysis/semantic_guard/check_macro_loop_hidden_recurrence.py
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "analysis" / "semantic_guard"))
from join_hidden_states import build_sequence, load_committed_rows, load_hidden_states, recurrence_scores  # noqa: E402

RUN_DIR = REPO_ROOT / "runs/hidden_state_pilot/aime24/case_028/seed_0/rFuzzy0p3"
FINAL_OPEN_POS = 30953   # first <|channel|>final<|message|> -- abandoned
RESTART_POS = 31478      # <|end|><|start|>assistant<|channel|>analysis<|message|> -- the restart
K_VALUES = (8, 16, 32, 64)
MIN_GAP = 32


def main() -> int:
    hidden = load_hidden_states(RUN_DIR / "hidden_states.bin")
    committed = load_committed_rows(RUN_DIR / "proposals.jsonl")
    matched_rows, vecs = build_sequence(committed, hidden)
    positions = [r["output_position"] for r in matched_rows]
    pos_to_idx = {p: i for i, p in enumerate(positions)}

    print(f"case_028 hidden_state_pilot run: {len(matched_rows)} matched positions, "
          f"range [{positions[0]}, {positions[-1]}]")

    if FINAL_OPEN_POS not in pos_to_idx or RESTART_POS not in pos_to_idx:
        print(f"one or both target positions not found in matched rows "
              f"(final_open={FINAL_OPEN_POS in pos_to_idx}, restart={RESTART_POS in pos_to_idx})")
        return 1

    final_idx = pos_to_idx[FINAL_OPEN_POS]
    restart_idx = pos_to_idx[RESTART_POS]

    # --- Test 1: generic windowed S_k, per-run percentile rank ---
    print(f"\n{'='*80}\nTest 1: generic windowed recurrence (S_k), at the restart position\n{'='*80}")
    scores = recurrence_scores(vecs, min_gap=MIN_GAP, k_values=K_VALUES)
    for k in K_VALUES:
        s = scores[k]
        valid = s[~np.isnan(s)]
        at_restart = s[restart_idx]
        if np.isnan(at_restart) or valid.size == 0:
            print(f"  S{k}: not available at restart position")
            continue
        percentile = 100 * float(np.mean(valid <= at_restart))
        print(f"  S{k} at restart: {at_restart:.4f}  (this run's own {percentile:.1f}th percentile; "
              f"run mean={float(np.mean(valid)):.4f}, run max={float(np.max(valid)):.4f})")

    # --- Test 2: targeted attempt-start-to-attempt-start similarity ---
    print(f"\n{'='*80}\nTest 2: raw hidden-state similarity, restart vs. the PREVIOUS attempt's own start\n{'='*80}")
    v_final_open = vecs[final_idx]
    v_restart = vecs[restart_idx]
    targeted_sim = float(np.dot(v_final_open, v_restart))
    print(f"  cos(final-channel-open @ {FINAL_OPEN_POS}, restart @ {RESTART_POS}) = {targeted_sim:.4f}")

    # Background distribution: cosine similarity of the restart's vector
    # against ALL earlier positions (respecting the same min_gap exclusion
    # as the windowed test), for a like-for-like percentile comparison.
    earlier_idx = np.arange(0, restart_idx - MIN_GAP)
    if earlier_idx.size == 0:
        print("  not enough earlier history for a background distribution")
        return 0
    background_sims = vecs[earlier_idx] @ v_restart
    percentile = 100 * float(np.mean(background_sims <= targeted_sim))
    print(f"  background: restart's raw single-state similarity against all {earlier_idx.size} earlier "
          f"positions -- mean={float(np.mean(background_sims)):.4f}, max={float(np.max(background_sims)):.4f}, "
          f"the final-channel-open point sits at the {percentile:.1f}th percentile of that distribution")

    # Where does the single BEST (max) earlier match for the restart point
    # actually fall -- is it the final-channel-open point, or something
    # else entirely?
    best_j = int(np.argmax(background_sims))
    best_sim = float(background_sims[best_j])
    best_pos = positions[best_j]
    print(f"  restart's single BEST-matching earlier position: output_position={best_pos} "
          f"(sim={best_sim:.4f}) -- {'IS' if best_pos == FINAL_OPEN_POS else 'is NOT'} the final-channel-open point")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
