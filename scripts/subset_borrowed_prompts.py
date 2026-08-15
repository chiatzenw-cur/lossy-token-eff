#!/usr/bin/env python3
"""Copy an evenly-strided case subset from the sibling repo's already-fetched
prompt sets (livecodebench, mtbench, longbench_v2) into this repo's prompts/,
renumbered case_001..case_N.

Why strided, not first-N: mtbench's 80 cases are 8 solid 10-case category
blocks (see campaign/PLAN.md); first-N would give near-zero category spread.
Applied uniformly to all three borrowed sets for consistency.

Not a general-purpose tool -- one-shot script for campaign/PLAN.md's prompt
setup, kept for reproducibility/audit rather than deleted after running.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, required=True, help="Sibling repo's prompts/<dataset> dir.")
    parser.add_argument("--dest", type=pathlib.Path, required=True, help="This repo's prompts/<dataset> dir.")
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--replace-dest", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dest.exists():
        if not args.replace_dest:
            raise SystemExit(f"{args.dest} already exists (use --replace-dest)")
        shutil.rmtree(args.dest)
    args.dest.mkdir(parents=True)

    index_lines = [json.loads(line) for line in (args.source / "candidate_index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    total = len(index_lines)
    if args.count > total:
        raise SystemExit(f"requested {args.count} cases but only {total} available in {args.source}")

    stride = total / args.count
    picked_positions = sorted({int(i * stride) for i in range(args.count)})
    # Dedup from rounding can leave < count positions; top up from the front
    # of whatever's left, in order, rather than silently under-delivering.
    remaining = [p for p in range(total) if p not in picked_positions]
    while len(picked_positions) < args.count and remaining:
        picked_positions.append(remaining.pop(0))
    picked_positions = sorted(picked_positions)[: args.count]

    new_index = []
    for new_pos, old_pos in enumerate(picked_positions, start=1):
        old_row = index_lines[old_pos]
        old_case = old_row["case"]
        new_case = f"case_{new_pos:03d}"
        shutil.copytree(args.source / old_case, args.dest / new_case)
        new_row = dict(old_row)
        new_row["case"] = new_case
        new_row["source_case_in_sibling_repo"] = old_case
        (args.dest / new_case / "metadata.json").write_text(
            json.dumps({**json.loads((args.dest / new_case / "metadata.json").read_text()), "source_case_in_sibling_repo": old_case}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        new_index.append(new_row)
        label = old_row.get("category") or old_row.get("difficulty") or ""
        print(f"{new_case} <- {old_case}  {label}")

    with (args.dest / "candidate_index.jsonl").open("w", encoding="utf-8") as handle:
        for row in new_index:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    source_summary = json.loads((args.source / "selection_summary.json").read_text(encoding="utf-8"))
    (args.dest / "selection_summary.json").write_text(
        json.dumps(
            {
                **source_summary,
                "selected": len(new_index),
                "subset_of": str(args.source),
                "subset_method": f"evenly-strided, {args.count} of {total}",
            },
            ensure_ascii=False, indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"\nwrote {len(new_index)} cases to {args.dest} (strided from {total} in {args.source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
