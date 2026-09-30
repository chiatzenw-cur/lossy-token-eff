#!/usr/bin/env python3
"""Measured throughput per arm, and an estimate of the drafter's relative
cost c_rel (DIRECTIONS.md D4 and D6).

Reads run.json under one or more runs roots (e.g. runs/, or runs_nspec4/
runs_nspec8/ from a draft-length sweep) and reports, per (root, dataset,
method, params): n, mean wall seconds, output tokens, tokens/s (total
tokens / total wall), rounds/s, mean accepted length, and speedups vs strict
and vs baseline (no drafter) in the same root.

If a `baseline` arm is present, c_rel is estimated from Xia et al. Eq. 2:
    S_strict = tok/s(strict) / tok/s(baseline) ~= (l_bar + 1) / (1 + N * c_rel)
    =>  c_rel = ((l_bar + 1) / S_strict - 1) / N
with N = --num-spec (the EAGLE3 draft length the runs used). Both wall
times include vLLM's per-request overhead, so this is the *deployed* c_rel
of this stack (what Xia et al. measured as 0.85 for their vLLM), not the
kernel-ideal one.

Only ordinal-1 requests are directly comparable across arms (fresh server
per measurement); runs made with persistent_arm_replay.py carry
`server_request_ordinal` > 1 and are flagged in the `warm` column.

Usage:
  python3 cascade/analysis/timing_report.py --dataset gsm8k --runs-root runs
  python3 cascade/analysis/timing_report.py --dataset gsm8k --runs-root runs_nspec4 runs_nspec6 runs_nspec8 --num-spec 4 6 8
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import statistics
from collections import defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CASE_RE = re.compile(r"^case_\d{3}$")


def collect(root: pathlib.Path, dataset: str) -> dict[tuple[str, str], list[dict]]:
    arms: dict[tuple[str, str], list[dict]] = defaultdict(list)
    ds = root / dataset
    if not ds.is_dir():
        return arms
    for method_dir in sorted(ds.iterdir()):
        if not method_dir.is_dir():
            continue
        for params_dir in sorted(method_dir.iterdir()):
            if not params_dir.is_dir():
                continue
            for case_dir in sorted(params_dir.iterdir()):
                if not CASE_RE.match(case_dir.name):
                    continue
                for seed_dir in sorted(case_dir.glob("seed_*")):
                    rj = seed_dir / "run.json"
                    if not rj.is_file():
                        continue
                    meta = json.loads(rj.read_text())
                    if meta.get("status") != "ok":
                        continue
                    meta["_case"] = case_dir.name
                    arms[(method_dir.name, params_dir.name)].append(meta)
    return arms


def summarise(runs: list[dict]) -> dict:
    wall = sum(float(r["wall_time_seconds"]) for r in runs)
    toks = sum(int(r["output_tokens"]) for r in runs)
    rounds = sum(float(r.get("draft_rounds") or 0) for r in runs)
    lbars = [float(r["l_bar"]) for r in runs if r.get("l_bar") is not None]
    return {
        "n": len(runs),
        "wall_mean": wall / len(runs),
        "tokens_mean": toks / len(runs),
        "tok_per_s": toks / wall if wall else 0.0,
        "rounds_per_s": rounds / wall if wall else 0.0,
        "l_bar": statistics.fmean(lbars) if lbars else None,
        "warm": sum(1 for r in runs if (r.get("server_request_ordinal") or 1) > 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--runs-root", nargs="+", type=pathlib.Path, default=[REPO_ROOT / "runs"])
    parser.add_argument("--num-spec", nargs="+", type=int, default=None,
                        help="draft length per runs root (same order); default 6 for every root")
    parser.add_argument("--out", type=pathlib.Path, default=None, help="also write the markdown here")
    args = parser.parse_args()
    num_specs = args.num_spec or [6] * len(args.runs_root)
    if len(num_specs) != len(args.runs_root):
        parser.error("--num-spec needs one value per --runs-root")

    lines = [
        f"# Throughput report: {args.dataset}",
        "",
        "| runs root | N | method | params | n (warm) | wall s | tokens | tok/s | rounds/s | l̄ | tok/s vs strict | tok/s vs baseline | c_rel est. |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for root, n_spec in zip(args.runs_root, num_specs):
        arms = collect(root, args.dataset)
        if not arms:
            lines.append(f"| {root} | {n_spec} | (no runs) | | | | | | | | | | |")
            continue
        summaries = {arm: summarise(runs) for arm, runs in arms.items()}
        strict = summaries.get(("strict", "strict"))
        baseline = summaries.get(("baseline", "baseline"))
        c_rel = None
        if strict and baseline and baseline["tok_per_s"] and strict["l_bar"] is not None:
            s_strict = strict["tok_per_s"] / baseline["tok_per_s"]
            c_rel = ((strict["l_bar"] + 1.0) / s_strict - 1.0) / n_spec
        for (method, params), s in sorted(summaries.items(), key=lambda kv: (kv[0][0] not in ("baseline", "strict"), kv[0])):
            vs_strict = s["tok_per_s"] / strict["tok_per_s"] if strict and strict["tok_per_s"] else None
            vs_base = s["tok_per_s"] / baseline["tok_per_s"] if baseline and baseline["tok_per_s"] else None
            lines.append(
                f"| {root.name} | {n_spec} | {method} | {params} | {s['n']} ({s['warm']}) | {s['wall_mean']:.1f} | "
                f"{s['tokens_mean']:.0f} | {s['tok_per_s']:.1f} | {s['rounds_per_s']:.1f} | "
                f"{'--' if s['l_bar'] is None else f'{s[chr(108)+chr(95)+chr(98)+chr(97)+chr(114)]:.2f}'} | "
                f"{'--' if vs_strict is None else f'{vs_strict:.2f}x'} | {'--' if vs_base is None else f'{vs_base:.2f}x'} | "
                f"{'--' if c_rel is None or method != 'strict' else f'{c_rel:.2f}'} |"
            )
    text = "\n".join(lines) + "\n"
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
