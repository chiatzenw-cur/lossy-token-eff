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


def count_trace_rounds(run_dir: pathlib.Path) -> int | None:
    """Total verifier rounds for this run, from proposals.jsonl's own
    "round" field -- one _TRACER.record() call (== one verify-kernel launch,
    one draft+verify cycle) per round, 0-indexed, so the last row's round
    number + 1 is the total. Reads only the last line, not the whole file
    (up to several MB / thousands of lines per run): rounds are written
    strictly in increasing order by the tracer's own single-threaded
    sequential-append design, so the last row already holds the max.
    """
    path = run_dir / "proposals.jsonl"
    if not path.is_file():
        return None
    last_line = None
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        if size == 0:
            return None
        # Read backwards in chunks until a newline is found, rather than
        # loading the whole (potentially multi-MB) file to get one field
        # from the last line.
        chunk = 4096
        pos = size
        buf = b""
        while pos > 0:
            pos = max(0, pos - chunk)
            handle.seek(pos)
            buf = handle.read(size - pos)
            lines = buf.splitlines()
            if len(lines) > 1 or pos == 0:
                last_line = lines[-1] if lines[-1].strip() else (lines[-2] if len(lines) > 1 else None)
                break
    if not last_line:
        return None
    try:
        row = json.loads(last_line)
    except json.JSONDecodeError:
        return None
    round_value = row.get("round")
    return None if round_value is None else int(round_value) + 1


def read_run_json_field(run_dir: pathlib.Path, field: str) -> Any:
    try:
        data = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get(field) if isinstance(data, dict) else None


def main() -> int:
    args = parse_args()
    # runs_root layout: <runs-root>/<method>/<params>/<case>/<seed_N>/ (runs-root
    # is expected to be a per-benchmark path, e.g. runs/aime24 or runs/humaneval).
    run_dirs = sorted({p.parent for p in args.runs_root.glob("*/*/*/seed_*/run.json")})
    if not run_dirs:
        print(f"no runs under {args.runs_root}", file=sys.stderr)
        return 1
    cases = sorted({d.parent.name for d in run_dirs})
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
        row["trace_rounds"] = count_trace_rounds(run_dir)
        row["metrics_draft_rounds"] = read_run_json_field(run_dir, "draft_rounds")
        rows.append(row)

    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_tag[row["tag"]].append(row)

    print(f"\n{benchmark} summary, {len(rows)} runs across {len(by_tag)} arms:\n")
    columns = (
        "arm", "runs", "score", "score_pct", "mean_l_bar", "mean_completion_len",
        "mean_verifier_rounds", "rounds_offset_anomaly", "errored_or_no_answer",
    )
    print("| " + " | ".join(columns) + " |")
    print("|" + "|".join("---" for _ in columns) + "|")
    summary: dict[str, dict[str, Any]] = {}
    for tag, group in sorted(by_tag.items()):
        n = len(group)
        successes = sum(1 for r in group if r["success"])
        l_bars = [r.get("l_bar") for r in group]
        lengths = [r.get("output_tokens") for r in group]
        rounds = [r.get("trace_rounds") for r in group]
        no_answer = sum(1 for r in group if r["verdict"] in ("no_answer", "timeout") or r.get("status") == "error")
        # trace_rounds is +1 vs metrics_draft_rounds essentially always: every
        # finish_reason=="stop" run (1120/1120 across both full datasets, zero
        # exceptions) and most finish_reason=="length" runs (37/44) show
        # exactly +1. An initial theory that "length" runs are offset=0
        # instead turned out to be an over-generalisation from a 7-run
        # sample -- the real split is 37-vs-7 within "length" runs
        # specifically, not a clean rule keyed on finish_reason alone. +1 is
        # therefore still the single expected value; what's flagged below is
        # the genuine minority (7/1204 total) that comes in at 0 instead,
        # unexplained so far -- see README.md's anomaly section rather than
        # re-deriving this inline. A run with no proposals.jsonl (tracing
        # off, or a failed request that never reached the sampler) has
        # trace_rounds=None and is excluded rather than counted as one.
        EXPECTED_TRACE_OFFSET = 1
        mismatches = sum(
            1
            for r in group
            if r.get("trace_rounds") is not None
            and r.get("metrics_draft_rounds") is not None
            and r["trace_rounds"] - round(r["metrics_draft_rounds"]) != EXPECTED_TRACE_OFFSET
        )
        m_lbar = mean(l_bars)
        m_len = mean(lengths)
        m_rounds = mean(rounds)
        summary[tag] = {
            "runs": n,
            "score": successes,
            "score_pct": round(successes / n, 4) if n else None,
            "mean_l_bar": round(m_lbar, 4) if m_lbar is not None else None,
            "mean_completion_len": round(m_len, 2) if m_len is not None else None,
            "mean_verifier_rounds": round(m_rounds, 2) if m_rounds is not None else None,
            "rounds_offset_anomaly": mismatches,
            "errored_or_no_answer": no_answer,
        }
        print(
            f"| {tag} | {n} | {successes}/{n} | {successes / n:.3f} | "
            f"{'' if m_lbar is None else round(m_lbar, 3)} | "
            f"{'' if m_len is None else round(m_len, 1)} | "
            f"{'' if m_rounds is None else round(m_rounds, 1)} | {mismatches} | {no_answer} |"
        )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"benchmark": benchmark, "summary": summary, "rows": rows}, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
