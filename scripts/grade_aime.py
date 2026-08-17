#!/usr/bin/env python3
"""Grade archived AIME runs against their reference answers.

Ported from lossy-spec-decode-repetition/scripts/grade_aime.py. One field
adapted for this repo's config.json schema: "alpha" instead of the sibling
repo's "lenience_factor" -- this repo's run_experiment_vllm.py records every
method's knob uniformly as lossy_parameters.alpha (see scripts/lossy_methods.py),
not a method-specific key name.

Accuracy alone doesn't survive a seed/case sweep by hand, which is why this
extracts the answer mechanically and reports, per arm, both accuracy and the
rate of the failure mode that matters here -- runs that never reach the
`final` channel and so produce no answer at all.

Extraction is deliberately narrow: the last \\boxed{...} in the `final`
channel, falling back to the last integer in it. A run with no `final`
channel is scored `no_answer`, never `wrong`; the distinction is the whole
point.
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

BOXED = re.compile(r"\\boxed\{\s*([0-9]{1,3})\s*\}")
INTEGER = re.compile(r"\b([0-9]{1,3})\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--prompt-root", type=pathlib.Path, default=pathlib.Path("prompts/aime24"))
    parser.add_argument("--tags", nargs="+", default=None, help="Restrict to these run tags.")
    parser.add_argument("--out", type=pathlib.Path, default=None, help="Write the rows as JSON here.")
    return parser.parse_args()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def extract_answer(text: str) -> tuple[str | None, str]:
    """Return (answer, how). None means the run produced no final answer."""
    final, how = final_segment(text)
    if final is None:
        return None, how
    boxed = BOXED.findall(final)
    if boxed:
        return str(int(boxed[-1])), "boxed"
    integers = INTEGER.findall(final)
    if integers:
        return str(int(integers[-1])), "last_integer"
    return None, "final_channel_without_integer"


def grade(run_dir: pathlib.Path, prompt_root: pathlib.Path) -> dict[str, Any] | None:
    # run_dir layout: <runs-root>/<method>/<params>/<case>/<seed_N>/ -- run_dir
    # IS the seed_N directory (case is its parent, params its grandparent).
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
    elif reference is not None and int(answer) == int(reference):
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
        "server_request_ordinal": config.get("server_request_ordinal"),
        "reference": None if reference is None else str(int(reference)),
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
    # runs_root layout: <runs-root>/<method>/<params>/<case>/<seed_N>/run.json
    # (runs-root is expected to be a per-benchmark path, e.g. runs/aime24).
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

    seeds = {row["seed"] for row in rows}
    if len(seeds) > 1:
        # With repeated seeds the useful quantity is a rate, not a single
        # outcome: one failure out of one seed is an anecdote.
        print(f"\nPer-case failure rate over {len(seeds)} seeds (failure = no answer):\n")
        tags = sorted(by_tag)
        print("| case | " + " | ".join(tags) + " |")
        print("|---|" + "|".join("---:" for _ in tags) + "|")
        for case in sorted({row["case"] for row in rows}):
            cells = []
            for tag in tags:
                group = [r for r in rows if r["case"] == case and r["tag"] == tag]
                if not group:
                    cells.append("")
                    continue
                failures = sum(1 for r in group if r["verdict"] == "no_answer")
                cells.append(f"{failures}/{len(group)}")
            print(f"| {case} | " + " | ".join(cells) + " |")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"runs": rows}, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
