#!/usr/bin/env python3
"""Alternative HumanEval verdicts for the runs `humaneval_lastblock_scan.py` flagged: execute the last fenced block
that DEFINES the entry point (grade_humaneval.py executes the last block, which in these runs is a usage / test
block), with grade_humaneval.execute unchanged (subprocess, 10 s, 1 GB RLIMIT_AS -- Linux only). Stdlib only.

  python3 scripts/humaneval_regrade.py --list flagged.csv --runs-base <dir holding the uploaded run trees> --out alt.csv
"""
import argparse
import csv
import concurrent.futures as cf
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import grade_humaneval  # noqa: E402
from humaneval_lastblock_scan import blocks_of  # noqa: E402


def regrade(args_row):
    base, row = args_row
    run_dir = pathlib.Path(base) / row["tree"] / row["relpath"]
    src = json.loads((REPO / "prompts" / row["dataset"] / run_dir.parts[-2] / "source.json").read_text(encoding="utf-8"))
    entry = src["entry_point"]
    blocks = blocks_of((run_dir / "output.txt").read_text(encoding="utf-8", errors="replace"))
    import textwrap
    candidate = textwrap.dedent([b for b in blocks if f"def {entry}(" in b][-1]).strip("\n")
    verdict, detail = grade_humaneval.execute(candidate, src["test"], entry, 10.0, 1024)
    return {**row, "verdict_alt": verdict, "detail_alt": detail[:160]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", type=pathlib.Path, required=True)
    p.add_argument("--runs-base", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    p.add_argument("--workers", type=int, default=16)
    a = p.parse_args()
    rows = list(csv.DictReader(a.list.open(newline="", encoding="utf-8")))
    with cf.ProcessPoolExecutor(a.workers) as pool:
        out = list(pool.map(regrade, [(str(a.runs_base), r) for r in rows], chunksize=8))
    with a.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    print(f"{len(out)} runs re-graded; passed: {sum(r['verdict_alt'] == 'passed' for r in out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
