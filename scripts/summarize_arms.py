#!/usr/bin/env python3
"""Per-arm summary: mean accept length (l_bar), mean completion length
(output_tokens), and total score, from a graded runs directory.

Reads the same runs/<case>/seed_<N>/<tag>/{run.json,config.json} artifacts
grade_humaneval.py and grade_aime.py already read, rather than requiring
their --out JSON as an intermediate -- one source of truth (the run
directory itself), usable against either benchmark's runs-root.

"score" auto-detects the grading scheme present in the run directory:
  - HumanEval-style: re-executes each candidate exactly like
    grade_humaneval.py (pass@1).
  - AIME-style: re-extracts the boxed answer exactly like grade_aime.py
    (accuracy against reference_answer).
Detection is by which prompt-root layout is present (source.json+test/
entry_point -> HumanEval; metadata.json+reference_answer -> AIME), not by a
flag, so this never silently grades against the wrong scheme.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grade_aime  # noqa: E402
import grade_humaneval  # noqa: E402


def detect_benchmark(prompt_root: pathlib.Path, cases: list[str]) -> str:
    for case in cases:
        source = prompt_root / case / "source.json"
        if source.is_file():
            data = json.loads(source.read_text(encoding="utf-8"))
            if "test" in data and "entry_point" in data:
                return "humaneval"
        metadata = prompt_root / case / "metadata.json"
        if metadata.is_file() and "reference_answer" in json.loads(metadata.read_text(encoding="utf-8")):
            return "aime"
    raise ValueError(f"could not detect benchmark type from cases under {prompt_root}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--prompt-root", type=pathlib.Path, required=True)
    parser.add_argument("--timeout", type=float, default=10.0, help="HumanEval execution timeout per candidate.")
    parser.add_argument("--memory-limit-mb", type=int, default=1024)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    return parser.parse_args()


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def main() -> int:
    args = parse_args()
    run_dirs = sorted({p.parent for p in args.runs_root.glob("*/seed_*/*/run.json")})
    if not run_dirs:
        print(f"no runs under {args.runs_root}", file=sys.stderr)
        return 1
    cases = sorted({d.parent.parent.name for d in run_dirs})
    benchmark = detect_benchmark(args.prompt_root, cases)
    print(f"detected benchmark: {benchmark}", file=sys.stderr)

    rows: list[dict[str, Any]] = []
    for run_dir in run_dirs:
        if benchmark == "humaneval":
            row = grade_humaneval.grade(run_dir, args.prompt_root, args.timeout, args.memory_limit_mb)
            success = row is not None and row["verdict"] == "passed"
        else:
            row = grade_aime.grade(run_dir, args.prompt_root)
            success = row is not None and row["verdict"] == "correct"
        if row is None:
            continue
        row["success"] = success
        rows.append(row)

    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_tag[row["tag"]].append(row)

    print(f"\n{benchmark} summary, {len(rows)} runs across {len(by_tag)} arms:\n")
    columns = ("arm", "runs", "score", "score_pct", "mean_l_bar", "mean_completion_len", "errored_or_no_answer")
    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join("---" for _ in columns) + "|")
    summary: dict[str, dict[str, Any]] = {}
    for tag, group in sorted(by_tag.items()):
        n = len(group)
        successes = sum(1 for r in group if r["success"])
        l_bars = [r.get("l_bar") for r in group]
        lengths = [r.get("output_tokens") for r in group]
        no_answer = sum(1 for r in group if r["verdict"] in ("no_answer", "timeout") or r.get("status") == "error")
        m_lbar = mean(l_bars)
        m_len = mean(lengths)
        summary[tag] = {
            "runs": n,
            "score": successes,
            "score_pct": round(successes / n, 4) if n else None,
            "mean_l_bar": round(m_lbar, 4) if m_lbar is not None else None,
            "mean_completion_len": round(m_len, 2) if m_len is not None else None,
            "errored_or_no_answer": no_answer,
        }
        print(
            f"| {tag} | {n} | {successes}/{n} | {successes / n:.3f} | "
            f"{'' if m_lbar is None else round(m_lbar, 3)} | "
            f"{'' if m_len is None else round(m_len, 1)} | {no_answer} |"
        )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"benchmark": benchmark, "summary": summary, "rows": rows}, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
