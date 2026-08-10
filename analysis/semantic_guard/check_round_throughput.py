#!/usr/bin/env python3
"""Per-round wall-clock throughput by arm -- the check `count_hesitation.py`
and `count_relaxed_only_hesitation.py` don't do, because round counts and
l_bar are event-count metrics, not timing ones. A guard's own per-round
overhead (the mask check it runs every verification round, whether or not
it fires) only shows up here, not in round/accepted-length numbers.

Uses `run.json`'s own `wall_time_seconds` (pure generation time, measured by
run_experiment_vllm.py around just the completion request) and
`draft_rounds` (from vLLM's /metrics counters, already recorded per run) --
NOT the outer fresh-server-replay wall time, which also includes ~80-100s of
server startup/shutdown per run and would swamp a few-percent per-round
signal completely.

Usage:
    python3 analysis/semantic_guard/check_round_throughput.py \\
        --runs-root runs/aime24_fresh --tags rFuzzy0p3 rFuzzySemanticGuard0p3
"""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict
from typing import Any


def collect(runs_root: pathlib.Path, tags: list[str] | None) -> dict[str, list[dict[str, Any]]]:
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run_json in sorted(runs_root.glob("*/seed_*/*/run.json")):
        tag = run_json.parent.name
        if tags is not None and tag not in tags:
            continue
        data = json.loads(run_json.read_text(encoding="utf-8"))
        wall = data.get("wall_time_seconds")
        rounds = data.get("draft_rounds")
        tokens = data.get("output_tokens")
        if wall is None or not rounds:
            continue
        by_tag[tag].append({
            "case": run_json.parent.parent.parent.name,
            "wall": wall,
            "rounds": rounds,
            "tokens": tokens,
        })
    return by_tag


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--tags", nargs="+", default=None, help="Restrict to these tags; default is every tag present.")
    args = parser.parse_args()

    by_tag = collect(args.runs_root, args.tags)
    if not by_tag:
        print(f"no runs under {args.runs_root} matching {args.tags}")
        return 1

    print(f"{args.runs_root}: per-round wall-clock throughput\n")
    columns = ("tag", "runs", "total_wall_s", "total_rounds", "total_tokens", "mean_s_per_round", "mean_tok_per_s")
    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join("---" for _ in columns) + "|")
    summary = {}
    for tag in sorted(by_tag):
        rows = by_tag[tag]
        total_wall = sum(r["wall"] for r in rows)
        total_rounds = sum(r["rounds"] for r in rows)
        total_tokens = sum(r["tokens"] for r in rows if r["tokens"])
        s_per_round = total_wall / total_rounds if total_rounds else None
        tok_per_s = total_tokens / total_wall if total_wall else None
        summary[tag] = {
            "runs": len(rows), "total_wall_s": round(total_wall, 1), "total_rounds": total_rounds,
            "total_tokens": total_tokens, "mean_s_per_round": round(s_per_round, 5) if s_per_round else None,
            "mean_tok_per_s": round(tok_per_s, 1) if tok_per_s else None,
        }
        print(
            f"| {tag} | {len(rows)} | {total_wall:.1f} | {total_rounds:.0f} | {total_tokens} | "
            f"{'' if s_per_round is None else round(s_per_round, 5)} | {'' if tok_per_s is None else round(tok_per_s, 1)} |"
        )

    tags_sorted = sorted(summary)
    if len(tags_sorted) == 2:
        a, b = tags_sorted
        sa, sb = summary[a]["mean_s_per_round"], summary[b]["mean_s_per_round"]
        if sa and sb:
            pct = 100 * (sb - sa) / sa
            print(f"\n{a} -> {b}: mean s/round {sa} -> {sb} ({pct:+.1f}%)")
        wa, wb = summary[a]["total_wall_s"], summary[b]["total_wall_s"]
        pct_wall = 100 * (wb - wa) / wa
        print(f"{a} -> {b}: total generation wall-time {wa}s -> {wb}s ({pct_wall:+.1f}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
