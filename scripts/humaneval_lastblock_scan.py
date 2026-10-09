#!/usr/bin/env python3
"""HumanEval grader check (Bill, 2026-10-06): grade_humaneval.py executes the LAST fenced block of the answer. Find,
under the given run roots, every HumanEval run whose last block does not define the entry point while an earlier
block does (the answer ends with a usage / test block), and write them as a work list for the alternative grading
(`humaneval_regrade.py`, which executes the last DEFINING block instead). Stdlib only.

  python3 scripts/humaneval_lastblock_scan.py --out list.csv <runs root> [<runs root> ...]
"""
import argparse
import csv
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import grade_humaneval  # noqa: E402
from answer_extraction import final_segment  # noqa: E402


def blocks_of(text: str) -> list[str]:
    final, _ = final_segment(text)
    for marker in grade_humaneval.END_MARKERS:
        if final and marker in final:
            final = final.split(marker, 1)[0]
    return grade_humaneval.CODE_BLOCK.findall(final or "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("roots", nargs="+", type=pathlib.Path)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    rows, totals = [], {}
    for root in args.roots:
        for run_json in root.rglob("run.json"):
            run_dir = run_json.parent
            ds = run_dir.parts[-5]
            if not ds.startswith("humaneval"):
                continue
            src = REPO / "prompts" / ds / run_dir.parts[-2] / "source.json"
            if not src.is_file():
                continue
            entry = json.loads(src.read_text(encoding="utf-8"))["entry_point"]
            out = run_dir / "output.txt"
            blocks = blocks_of(out.read_text(encoding="utf-8", errors="replace") if out.is_file() else "")
            defines = [f"def {entry}(" in b for b in blocks]
            key = (str(root), ds)
            t = totals.setdefault(key, [0, 0])
            t[0] += 1
            if len(blocks) > 1 and not defines[-1] and any(defines):
                t[1] += 1
                rows.append({"root": str(root), "relpath": str(run_dir.relative_to(root)), "dataset": ds,
                             "defining_block": max(i for i, d in enumerate(defines) if d) + 1, "n_blocks": len(blocks)})
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["root", "relpath", "dataset", "defining_block", "n_blocks"],
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for (root, ds), (n, k) in sorted(totals.items()):
        print(f"{k:5d} / {n:6d} flagged  {ds:22s} {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
