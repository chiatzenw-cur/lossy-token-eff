#!/usr/bin/env python3
"""Grade archived GSM8K runs against their reference answers.

Adapted from scripts/grade_aime.py (same run-directory layout, same
Harmony final-channel convention, same correct/wrong/no_answer verdict
split) -- the one real difference is the answer format: GSM8K prompts
(prompts/gsm8k/build_gsm8k_prompts.py) explicitly ask for "#### <answer>"
on its own line (the dataset's own canonical convention), not a
\\boxed{...}. Extraction prefers that marker, falling back to the last
integer in the final channel for a response that got the numeral right but
dropped the "####" formatting.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from answer_extraction import final_segment  # noqa: E402 -- covers both Harmony (GPT-OSS) and Qwen3's </think> convention

HASH_ANSWER = re.compile(r"####\s*\$?(-?[0-9][0-9,]*(?:\.[0-9]+)?)")
INTEGER = re.compile(r"(-?[0-9][0-9,]*(?:\.[0-9]+)?)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--prompt-root", type=pathlib.Path, default=pathlib.Path("prompts/gsm8k"))
    parser.add_argument("--tags", nargs="+", default=None, help="Restrict to these run tags.")
    parser.add_argument("--out", type=pathlib.Path, default=None, help="Write the rows as JSON here.")
    return parser.parse_args()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def normalize(num: str) -> float:
    return float(num.replace(",", ""))


def extract_answer(text: str) -> tuple[str | None, str]:
    """Return (answer, how). None means the run produced no final answer."""
    final, how = final_segment(text)
    if final is None:
        return None, how
    hashed = HASH_ANSWER.findall(final)
    if hashed:
        return hashed[-1], "hash_marker"
    integers = INTEGER.findall(final)
    if integers:
        return integers[-1], "last_number"
    return None, "final_channel_without_number"


def grade(run_dir: pathlib.Path, prompt_root: pathlib.Path) -> dict[str, Any] | None:
    run = read_json(run_dir / "run.json")
    config = read_json(run_dir / "config.json")
    if not run and not config:
        return None
    case = run_dir.parent.name
    params = run_dir.parent.parent.name
    method = run_dir.parent.parent.parent.name
    reference = config.get("reference_answer")
    if reference is None:
        meta = read_json(prompt_root / case / "metadata.json")
        reference = meta.get("reference_answer")
    try:
        text = (run_dir / "output.txt").read_text(encoding="utf-8")
    except OSError:
        text = ""

    answer, how = extract_answer(text)
    if answer is None:
        verdict = "no_answer"
    elif reference is not None and normalize(answer) == normalize(str(reference)):
        verdict = "correct"
    else:
        verdict = "wrong"
    return {
        "case": case,
        "seed": config.get("seed", run_dir.name.removeprefix("seed_")),
        "tag": f"{method}/{params}",
        "method": method,
        "params": params,
        "mode": config.get("mode"),
        "lossy_method": config.get("lossy_method"),
        "alpha": (config.get("lossy_parameters") or {}).get("alpha"),
        "reference": None if reference is None else str(reference),
        "answer": answer,
        "extracted_by": how,
        "verdict": verdict,
        "output_tokens": run.get("output_tokens"),
        "finish_reason": run.get("finish_reason"),
        "hit_cap": run.get("finish_reason") == "length",
        "l_bar": run.get("l_bar"),
    }


def render(rows: list[dict[str, Any]]) -> str:
    columns = ("case", "seed", "tag", "reference", "answer", "verdict", "output_tokens", "finish_reason", "l_bar")
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        cells = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float):
                value = round(value, 3)
            cells.append("" if value is None else str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    rows = []
    for run_json in sorted(args.runs_root.glob("*/*/*/seed_*/run.json")):
        tag = f"{run_json.parent.parent.parent.name}/{run_json.parent.parent.name}"
        if args.tags and tag not in args.tags:
            continue
        row = grade(run_json.parent, args.prompt_root)
        if row is not None:
            rows.append(row)
    if not rows:
        print(f"no runs under {args.runs_root}", file=sys.stderr)
        return 1

    rows.sort(key=lambda r: (str(r["case"]), str(r["tag"]), str(r["seed"])))
    print(render(rows))

    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_tag[row["tag"]].append(row)

    print("\n| tag | runs | correct | wrong | no answer | hit cap |")
    print("|---|---:|---:|---:|---:|---:|")
    for tag, group in sorted(by_tag.items()):
        counts = {verdict: sum(1 for r in group if r["verdict"] == verdict) for verdict in ("correct", "wrong", "no_answer")}
        capped = sum(1 for r in group if r["hit_cap"])
        print(
            f"| {tag} | {len(group)} | {counts['correct']} | {counts['wrong']} | "
            f"{counts['no_answer']} | {capped} |"
        )

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"runs": rows}, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
