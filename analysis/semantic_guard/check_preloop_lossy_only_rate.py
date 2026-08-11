#!/usr/bin/env python3
"""Tests the "ignition, not maintenance" hypothesis directly: for each
CONFIRMED (manually judge-validated, not raw detector output) loop onset,
computes Pr(lossy_only_accepted) in the trailing k-token window immediately
BEFORE the onset, for k in {8,16,32,64,128,256}, and compares it against
the SAME statistic computed at every other eligible position in that same
run -- not a fixed population baseline, a per-case empirical distribution,
so the comparison controls for how generally degenerate that specific case
already is (case_028, for instance, is one of r_fuzzy's worst cases
overall; a naive comparison against the AIME24-wide baseline would conflate
"this case is bad" with "the pre-onset window specifically is bad").

Motivating question (see the parent conversation): does elevated lossy-only
acceptance show up BEFORE a loop becomes visible (an "ignition" signal,
actionable) or only IN the loop itself (a "maintenance" signal the earlier
onset-detection work already found isn't enriched at the visible onset
point, 20.2% vs ~20% population baseline -- essentially flat)?

Deliberately only 3 hand-validated onsets as of this writing (2 from the
hidden-state recurrence check, 1 from the window-entropy ramp check) --
small n, reported as individual per-onset results, not pooled statistics
that would misrepresent the sample size as larger than it is.

Usage:
    python3 analysis/semantic_guard/check_preloop_lossy_only_rate.py
"""

from __future__ import annotations

import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# (label, run_dir, onset output_position) -- the 3 confirmed hits so far.
CONFIRMED_ONSETS = [
    (
        "window-entropy hit: case_028 pos=31322 (garbled congruence system, guessed non-answer)",
        REPO_ROOT / "runs/semantic_guard_pilot/aime24/case_028/seed_0/rFuzzy0p3",
        31322,
    ),
    (
        "hidden-state hit: case_020 pos=3673 (algebraic re-derivation loop)",
        REPO_ROOT / "runs/hidden_state_pilot/aime24/case_020/seed_0/rFuzzy0p3",
        3673,
    ),
    (
        "hidden-state hit: case_020 pos=28786 (repetitive mod-exponentiation confusion)",
        REPO_ROOT / "runs/hidden_state_pilot/aime24/case_020/seed_0/rFuzzy0p3",
        28786,
    ),
]

K_VALUES = (8, 16, 32, 64, 128, 256)
EXCLUSION_RADIUS = 256  # positions within this of the onset are excluded from the "other positions" population


def load_committed(run_dir: pathlib.Path) -> list[dict]:
    rows = [json.loads(line) for line in (run_dir / "proposals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows.sort(key=lambda r: r["output_position"])
    return [r for r in rows if r["emission_source"] in ("accepted_draft", "recovered")]


def rate_before(flags: list[bool], t_idx: int, k: int) -> float | None:
    """Fraction of lossy_only_accepted among the k committed positions
    immediately preceding index t_idx (exclusive of t_idx itself)."""
    if t_idx < k:
        return None
    window = flags[t_idx - k : t_idx]
    return sum(window) / k


def main() -> int:
    for label, run_dir, onset_output_pos in CONFIRMED_ONSETS:
        if not (run_dir / "proposals.jsonl").is_file():
            print(f"{label}: proposals.jsonl not found under {run_dir}, skipping")
            continue
        committed = load_committed(run_dir)
        flags = [bool(r.get("lossy_only_accepted")) for r in committed]
        # index of the onset within the COMMITTED sequence, matched by output_position
        t_idx = next((i for i, r in enumerate(committed) if r["output_position"] == onset_output_pos), None)
        if t_idx is None:
            print(f"{label}: output_position {onset_output_pos} not found among committed rows, skipping")
            continue

        n = len(flags)
        print(f"\n{'=' * 100}\n{label}\n  run: {run_dir}\n  onset at committed-index {t_idx} / {n}, output_position {onset_output_pos}")
        print(f"  {'k':>5s}  {'rate@onset':>10s}  {'case mean':>10s}  {'case std':>9s}  {'percentile':>10s}  {'n_other':>8s}")
        for k in K_VALUES:
            onset_rate = rate_before(flags, t_idx, k)
            if onset_rate is None:
                print(f"  {k:>5d}  not enough history before onset (t_idx={t_idx} < k={k})")
                continue

            other_rates = []
            for i in range(k, n):
                if abs(i - t_idx) <= EXCLUSION_RADIUS:
                    continue
                r = rate_before(flags, i, k)
                if r is not None:
                    other_rates.append(r)
            if not other_rates:
                print(f"  {k:>5d}  no comparable positions elsewhere in this run")
                continue

            mean_other = sum(other_rates) / len(other_rates)
            var_other = sum((r - mean_other) ** 2 for r in other_rates) / len(other_rates)
            std_other = var_other**0.5
            percentile = 100 * sum(1 for r in other_rates if r <= onset_rate) / len(other_rates)
            print(
                f"  {k:>5d}  {onset_rate:10.4f}  {mean_other:10.4f}  {std_other:9.4f}  "
                f"{percentile:9.1f}%  {len(other_rates):8d}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
