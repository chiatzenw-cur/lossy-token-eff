#!/usr/bin/env python3
"""Add more cases to an already-populated (via subset_borrowed_prompts.py)
prompt dir, without touching the existing case_NNN dirs or renumbering them
-- unlike subset_borrowed_prompts.py, which always starts fresh from case_001.

Selects --add new cases from the sibling repo's full candidate_index.jsonl,
excluding any source_id already present in --dest, evenly strided across
the REMAINING pool (same rationale as subset_borrowed_prompts.py: mtbench's
80 cases are solid category blocks, so first-N would give near-zero spread).
One-shot script, not general-purpose -- kept for reproducibility/audit.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, required=True, help="Sibling repo's prompts/<dataset> dir.")
    parser.add_argument("--dest", type=pathlib.Path, required=True, help="This repo's prompts/<dataset> dir (already populated).")
    parser.add_argument("--add", type=int, required=True, help="How many new cases to add.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.dest.is_dir():
        raise SystemExit(f"{args.dest} does not exist -- use subset_borrowed_prompts.py for a fresh dest")

    existing_index = [json.loads(line) for line in (args.dest / "candidate_index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    existing_source_ids = {row["source_id"] for row in existing_index}
    existing_case_nums = [int(row["case"].removeprefix("case_")) for row in existing_index]
    next_num = max(existing_case_nums) + 1 if existing_case_nums else 1

    source_index = [json.loads(line) for line in (args.source / "candidate_index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    pool = [row for row in source_index if row["source_id"] not in existing_source_ids]
    if args.add > len(pool):
        raise SystemExit(f"requested {args.add} new cases but only {len(pool)} remain unused in {args.source} (total {len(source_index)}, {len(existing_source_ids)} already used)")

    stride = len(pool) / args.add
    picked_positions = sorted({int(i * stride) for i in range(args.add)})
    remaining = [p for p in range(len(pool)) if p not in picked_positions]
    while len(picked_positions) < args.add and remaining:
        picked_positions.append(remaining.pop(0))
    picked_positions = sorted(picked_positions)[: args.add]

    new_index = []
    for offset, old_pos in enumerate(picked_positions):
        old_row = pool[old_pos]
        old_case = old_row["case"]
        new_case = f"case_{next_num + offset:03d}"
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

    with (args.dest / "candidate_index.jsonl").open("a", encoding="utf-8") as handle:
        for row in new_index:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary_path = args.dest / "selection_summary.json"
    if summary_path.is_file():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary["selected"] = len(existing_index) + len(new_index)
        summary["subset_method"] = summary.get("subset_method", "") + f"; +{args.add} more evenly-strided from the {len(pool)} remaining unused"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nadded {len(new_index)} cases ({args.dest}/case_{next_num:03d}..case_{next_num + len(new_index) - 1:03d}), total now {len(existing_index) + len(new_index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
