#!/usr/bin/env python3
"""Count hesitation-marker words in archived completions, per case and per arm.

Motivation: the main README's failure-mode narrative (`cactus`, `spec_casc_opt`,
`r_fuzzy` accepting more per round without a matching accuracy return) is
inferred indirectly, from length/round counts. This is a direct textual
proxy for the same "rambling/self-correction" behaviour: count occurrences
of a small set of hesitation/self-correction markers --

    wait, hmm, let's, actually, but

-- in each run's full completion text (analysis + final channel together,
exactly what's on disk in `output.txt`), then compare per case across the
six arms and roll up into a per-arm total across all cases in a benchmark.

Matching is whole-word (or whole-phrase for "let's"), case-insensitive,
regex `\\b...\\b`. "but" is the least specific of the five -- it's ordinary
prose as often as it's a self-correction -- so it's reported broken out by
marker, not just folded into one undifferentiated total, precisely so that
"but"'s high base rate doesn't drown the sharper signal from the other four.

Reads the same runs/<case>/seed_<N>/<tag>/{run.json,config.json,output.txt}
artifacts scripts/summarize_arms.py reads, so it stays consistent with the
figures already in the top-level README without re-deriving anything from
them.

Usage:
    python3 analysis/semantic_guard/count_hesitation.py \\
        --runs-root runs/aime24_fresh --out-prefix analysis/semantic_guard/results/aime24

    python3 analysis/semantic_guard/count_hesitation.py \\
        --runs-root runs/humaneval_fresh --out-prefix analysis/semantic_guard/results/humaneval
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
from collections import defaultdict
from typing import Any

MARKERS: dict[str, re.Pattern[str]] = {
    "wait": re.compile(r"\bwait\b", re.IGNORECASE),
    "hmm": re.compile(r"\bhmm+\b", re.IGNORECASE),
    "lets": re.compile(r"\blet's\b", re.IGNORECASE),
    "actually": re.compile(r"\bactually\b", re.IGNORECASE),
    "but": re.compile(r"\bbut\b", re.IGNORECASE),
}
MARKER_NAMES = list(MARKERS)  # fixed column order, reused everywhere below


def arm_label(config: dict[str, Any]) -> str:
    """Human-readable arm name matching the top-level README's prose
    ("mentored_dec (α=0.37)"), derived from config.json rather than the
    directory-name tag, so it stays correct even if tags are ever renamed.
    """
    method = config.get("lossy_method")
    if not method:
        return "strict"
    alpha = config.get("lossy_parameters", {}).get("alpha")
    return f"{method} (α={alpha:g})" if isinstance(alpha, (int, float)) else method


def count_markers(text: str) -> dict[str, int]:
    return {name: len(pattern.findall(text)) for name, pattern in MARKERS.items()}


def collect_rows(runs_root: pathlib.Path) -> list[dict[str, Any]]:
    # runs_root layout: <runs-root>/<method>/<params>/<case>/<seed_N>/ (runs-root
    # is expected to be a per-benchmark path, e.g. runs/aime24 or runs/humaneval).
    run_dirs = sorted({p.parent for p in runs_root.glob("*/*/*/seed_*/run.json")})
    if not run_dirs:
        print(f"no runs under {runs_root}", file=sys.stderr)
        return []

    rows: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        config_path = run_dir / "config.json"
        output_path = run_dir / "output.txt"
        run_path = run_dir / "run.json"
        if not (config_path.is_file() and output_path.is_file()):
            print(f"skipping {run_dir}: missing config.json or output.txt", file=sys.stderr)
            continue
        config = json.loads(config_path.read_text(encoding="utf-8"))
        text = output_path.read_text(encoding="utf-8", errors="replace")
        run_data = json.loads(run_path.read_text(encoding="utf-8")) if run_path.is_file() else {}

        counts = count_markers(text)
        params = run_dir.parent.parent.name
        method = run_dir.parent.parent.parent.name
        row = {
            "case": config.get("prompt_case", run_dir.parent.name),
            "tag": f"{method}/{params}",
            "arm": arm_label(config),
            "completion_tokens": run_data.get("output_tokens"),
            **counts,
            "total": sum(counts.values()),
        }
        rows.append(row)
    return rows


def write_case_by_arm(rows: list[dict[str, Any]], out_path: pathlib.Path) -> None:
    fields = ["case", "tag", "arm", "completion_tokens", *MARKER_NAMES, "total"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda r: (r["case"], r["arm"])):
            writer.writerow(row)


def write_case_by_arm_pivot_md(rows: list[dict[str, Any]], out_path: pathlib.Path) -> None:
    """One row per case, one column per arm, cell = total hesitation-marker
    count -- the "comparison between methods, each case" view.
    """
    arms = sorted({r["arm"] for r in rows})
    by_case: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        by_case[row["case"]][row["arm"]] = row["total"]

    lines = ["| case | " + " | ".join(arms) + " |", "|---|" + "|".join("---:" for _ in arms) + "|"]
    for case in sorted(by_case):
        cells = [str(by_case[case].get(arm, "")) for arm in arms]
        lines.append(f"| {case} | " + " | ".join(cells) + " |")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compute_totals_by_arm(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_arm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_arm[row["arm"]].append(row)

    totals: dict[str, dict[str, Any]] = {}
    for arm, group in by_arm.items():
        n = len(group)
        marker_totals = {name: sum(r[name] for r in group) for name in MARKER_NAMES}
        total = sum(marker_totals.values())
        completion_tokens = [r["completion_tokens"] for r in group if r["completion_tokens"] is not None]
        total_tokens = sum(completion_tokens) if completion_tokens else None
        totals[arm] = {
            "runs": n,
            **marker_totals,
            "total": total,
            "mean_per_run": round(total / n, 3) if n else None,
            "per_1k_completion_tokens": round(1000 * total / total_tokens, 3) if total_tokens else None,
        }
    return totals


def write_totals_by_arm(totals: dict[str, dict[str, Any]], out_path: pathlib.Path) -> None:
    fields = ["arm", "runs", *MARKER_NAMES, "total", "mean_per_run", "per_1k_completion_tokens"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for arm in sorted(totals):
            writer.writerow({"arm": arm, **totals[arm]})


def print_totals_md(totals: dict[str, dict[str, Any]], title: str) -> None:
    print(f"\n{title}\n")
    columns = ["arm", "runs", *MARKER_NAMES, "total", "mean/run", "per 1k tok"]
    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join("---" for _ in columns) + "|")
    # sort by total hesitation count, descending -- most-hesitant arm first
    for arm in sorted(totals, key=lambda a: totals[a]["total"], reverse=True):
        t = totals[arm]
        cells = [arm, str(t["runs"])] + [str(t[name]) for name in MARKER_NAMES]
        cells += [str(t["total"]), str(t["mean_per_run"]), str(t["per_1k_completion_tokens"])]
        print("| " + " | ".join(cells) + " |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--out-prefix", type=pathlib.Path, required=True, help="Path prefix for output files, e.g. analysis/semantic_guard/results/aime24")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = collect_rows(args.runs_root)
    if not rows:
        return 1

    benchmark = args.out_prefix.name
    write_case_by_arm(rows, args.out_prefix.with_name(f"{benchmark}_case_by_arm.csv"))
    write_case_by_arm_pivot_md(rows, args.out_prefix.with_name(f"{benchmark}_case_by_arm.md"))

    totals = compute_totals_by_arm(rows)
    write_totals_by_arm(totals, args.out_prefix.with_name(f"{benchmark}_totals_by_arm.csv"))
    print_totals_md(totals, f"{benchmark}: total hesitation-marker counts by arm ({len(rows)} runs)")

    combined_path = args.out_prefix.with_name(f"{benchmark}_all_rows.json")
    combined_path.write_text(
        json.dumps({"runs_root": str(args.runs_root), "markers": MARKER_NAMES, "rows": rows, "totals_by_arm": totals}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {args.out_prefix.with_name(f'{benchmark}_case_by_arm.csv')}")
    print(f"wrote {args.out_prefix.with_name(f'{benchmark}_case_by_arm.md')}")
    print(f"wrote {args.out_prefix.with_name(f'{benchmark}_totals_by_arm.csv')}")
    print(f"wrote {combined_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
