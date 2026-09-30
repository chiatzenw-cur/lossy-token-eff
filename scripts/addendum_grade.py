#!/usr/bin/env python3
"""Grade every run under a runs root with the campaign's own graders
(scripts/grade_*.py, exactly the GRADERS table of scripts/campaign_report.py),
writing one CSV row per run. Used by the addendum (campaign/addendum/README.md)
because the code graders (humaneval, livecodebench) cap memory with
RLIMIT_AS and must run on Linux: the Mac packs run.json + config.json +
output.txt of every run into a mirror on Nibi scratch and this script runs
there in a CPU job (cascade/cluster/addendum_grade.sbatch).

  python3 scripts/addendum_grade.py --runs-root <mirror>/runs --out grades.csv \
      [--cache grades_old.csv] [--workers 16]

--runs-root is scanned for <dataset>/<method>/<params>/<case>/seed_N/run.json
(the repo's own layout, so runs/ and runs/addendum/<condition>/ both work;
the path relative to --runs-root is the row key). Runs already present in
--cache (same relpath) are copied over, not re-graded -- verdicts of
finished runs never change.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import importlib
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Mirrors scripts/campaign_report.py GRADERS (kept literal here so importing
# this module does not pull in matplotlib).
GRADERS = {
    "gsm8k": ("grade_gsm8k", {"correct"}, {}),
    "aime24": ("grade_aime", {"correct"}, {}),
    "humaneval": ("grade_humaneval", {"passed"}, {"timeout": 10.0, "memory_limit_mb": 1024}),
    "longbench_v2": ("grade_longbench", {"correct"}, {}),
    "livecodebench": ("grade_livecodebench", {"passed"}, "lcb"),
}
FIELDS = ["relpath", "dataset", "method", "params", "case", "seed", "verdict", "correct"]

_modules: dict[str, tuple] = {}


def grader_for(base: str):
    if base not in _modules:
        name, correct, kwargs = GRADERS[base]
        module = importlib.import_module(name)
        if kwargs == "lcb":
            kwargs = {
                "test_cases_by_qid": module.load_test_cases(REPO_ROOT / "prompts" / "livecodebench" / "test_cases.json"),
                "timeout": 10.0, "memory_limit_mb": 1024,
            }
        _modules[base] = (module, correct, kwargs)
    return _modules[base]


def grade_one(args: tuple[str, str]) -> dict:
    runs_root, rel = args
    run_dir = pathlib.Path(runs_root) / rel
    parts = pathlib.Path(rel).parts  # [..., dataset, method, params, case, seed_N]
    dataset, method, params, case, seed_dir = parts[-5:]
    base = dataset.removesuffix("_qwen3")
    row = {"relpath": rel, "dataset": dataset, "method": method, "params": params, "case": case,
           "seed": seed_dir.removeprefix("seed_"), "verdict": "", "correct": ""}
    if base not in GRADERS:
        row["verdict"] = "no_grader"
        return row
    module, correct, kwargs = grader_for(base)
    try:
        result = module.grade(run_dir, REPO_ROOT / "prompts" / dataset, **kwargs)
    except Exception as exc:  # a grader crash must not lose the other rows
        row["verdict"] = f"grade_exception:{type(exc).__name__}"
        return row
    if result is None:
        row["verdict"] = "not_gradable"
        return row
    row["verdict"] = result["verdict"]
    row["correct"] = "1" if result["verdict"] in correct else "0"
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, required=True)
    parser.add_argument("--out", type=pathlib.Path, required=True)
    parser.add_argument("--cache", type=pathlib.Path, default=None)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    cached: dict[str, dict] = {}
    if args.cache and args.cache.is_file():
        with args.cache.open(newline="", encoding="utf-8") as handle:
            cached = {r["relpath"]: r for r in csv.DictReader(handle) if r.get("verdict")}
    rels = sorted(str(p.parent.relative_to(args.runs_root)) for p in args.runs_root.rglob("run.json"))
    todo = [r for r in rels if r not in cached]
    print(f"{len(rels)} runs, {len(cached)} cached, {len(todo)} to grade", flush=True)
    rows = [cached[r] for r in rels if r in cached]
    with cf.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, row in enumerate(pool.map(grade_one, [(str(args.runs_root), r) for r in todo], chunksize=8), 1):
            rows.append(row)
            if i % 500 == 0:
                print(f"  graded {i}/{len(todo)}", flush=True)
    rows.sort(key=lambda r: r["relpath"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
