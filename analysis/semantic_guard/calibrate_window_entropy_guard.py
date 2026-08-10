#!/usr/bin/env python3
"""Baseline trigger-rate check for `patches/vllm-0.26.0-r-fuzzy-window-entropy-guard.patch`'s
monotonic-ramp condition: mean(w64) < mean(w32) < mean(w16) < mean(w8),
jointly for target and draft entropy.

Not a calibration in the threshold-fitting sense -- the guard is
deliberately unquantified (a structural shape check, not a magnitude
check against a population percentile). What this answers instead: how
often does that exact 4-scale staircase occur BY CHANCE in ordinary
(strict, lossless) decoding, for target-only, draft-only, and the joint
condition the guard actually uses? That's the guard's expected baseline
trigger rate on well-behaved trajectories -- worth knowing before reading
pilot results, same way a p-value's null distribution is worth knowing
before reading the effect it's tested against.

Only accepted_draft/recovered rows carry entropy (bonus rows don't -- see
the patch's own module comment), so those are what enters the window; a
window is valid once 64 consecutive such rows exist within one run (never
crossing into a different run/case).

Usage:
    python3 analysis/semantic_guard/calibrate_window_entropy_guard.py \\
        --runs-roots runs/aime24_fresh runs/humaneval_fresh --tag strict
"""

from __future__ import annotations

import argparse
import json
import pathlib

WINDOW_SIZES = (64, 32, 16, 8)


def is_monotonic_ramp(history: list[float]) -> bool:
    means = [sum(history[-w:]) / w for w in WINDOW_SIZES]
    return all(means[i] < means[i + 1] for i in range(len(means) - 1))


def collect_entropy_sequences(runs_root: pathlib.Path, tag: str) -> list[tuple[list[float], list[float]]]:
    sequences = []
    for proposals_path in sorted(runs_root.glob(f"*/seed_*/{tag}/proposals.jsonl")):
        rows = [json.loads(line) for line in proposals_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        rows.sort(key=lambda r: r["output_position"])
        ent_t = [r["target_entropy"] for r in rows if r["emission_source"] in ("accepted_draft", "recovered")]
        ent_d = [
            r["draft_entropy"]
            for r in rows
            if r["emission_source"] in ("accepted_draft", "recovered") and r.get("draft_entropy") is not None
        ]
        sequences.append((ent_t, ent_d))
    return sequences


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-roots", type=pathlib.Path, nargs="+", required=True)
    parser.add_argument("--tag", default="strict")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    w = max(WINDOW_SIZES)
    n_windows = n_target = n_draft = n_joint = 0
    n_runs = 0
    for runs_root in args.runs_roots:
        for ent_t, ent_d in collect_entropy_sequences(runs_root, args.tag):
            n_runs += 1
            for i in range(w, min(len(ent_t), len(ent_d)) + 1):
                n_windows += 1
                t_ramp = is_monotonic_ramp(ent_t[i - w : i])
                d_ramp = is_monotonic_ramp(ent_d[i - w : i])
                n_target += t_ramp
                n_draft += d_ramp
                n_joint += t_ramp and d_ramp

    if not n_windows:
        print(f"no windows found under {args.runs_roots} (tag={args.tag})")
        return 1

    print(f"{n_runs} {args.tag} runs, {n_windows} valid {w}-token windows\n")
    print(f"target-only ramp:  {n_target:>8} ({100*n_target/n_windows:.3f}%)")
    print(f"draft-only ramp:   {n_draft:>8} ({100*n_draft/n_windows:.3f}%)")
    print(f"joint ramp (used): {n_joint:>8} ({100*n_joint/n_windows:.3f}%)  <- baseline guard trigger rate on {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
