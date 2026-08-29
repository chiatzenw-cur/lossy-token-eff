#!/usr/bin/env python3
"""Follow-up to campaign_extend_reuse.py: push gsm8k/humaneval/longbench_v2
to 150 cases and livecodebench/mtbench to their real pool caps (90/80 --
150 isn't reachable for either; see this file's own DATASETS table).
aime24 stays at 30 (its true full pool, already done).

User (2026-08-27), mid-run on the 50-target extension, asked "maybe we
could do something more like 150" after seeing gsm8k/humaneval finish
fast. Checked real pool sizes before committing to a number: gsm8k's
real test split is 1,319 rows (datasets-server confirmed), humaneval 164,
longbench_v2 153 -- all comfortably above 150. livecodebench's pool here
is capped at 90 (the sibling repo's own fetched set, not the full
upstream benchmark) and mtbench at 80 (its true full question count) --
150 would need fetching new data this repo doesn't have, so those two
are extended to their real ceiling instead.

Deliberately a SEPARATE script/pass rather than editing
campaign_extend_reuse.py's DATASETS list in place: that script was
already running (in fact already past gsm8k and into humaneval) when
this request came in, and its DATASETS list was already loaded into the
running process's memory -- editing the file on disk would not have
changed what the live process does, and killing it mid-arm to swap
targets risked losing in-flight work for no real gain (the 50-target
pass was healthy, zero errors, no reason to disturb it). The cost of
this approach is a second round of per-arm restarts for the SAME arms
already run once at 50 -- ~137 extra restarts, ~3.6h of overhead the
campaign wouldn't otherwise pay -- accepted deliberately as a small,
known price for not touching a stable running job. All five datasets
below start their new range at case_051, since campaign_extend_reuse.py
takes every one of them to exactly case_050 before this ever runs.

Chained after campaign_extend_reuse.py the same way that script was
chained after the aime24 finish job: a wait-wrapper polls the earlier
stage's pid and launches this once it exits.
"""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from campaign_extend_reuse import (  # noqa: E402
    REPO_ROOT, PY_BIN, MIN_FREE_GB, QWEN3_FLAGS,
    free_gb, read_arms, run_arm, clean_partial,
)
import datetime as dt

# (dataset, max_new_tokens, first_new_case, last_new_case)
DATASETS = [
    ("gsm8k", 2048, 51, 150),
    ("humaneval", 9000, 51, 150),
    ("livecodebench", 12000, 51, 90),
    ("longbench_v2", 8192, 51, 150),
    ("mtbench", 4096, 51, 80),
]


def main() -> int:
    ts = lambda: dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== campaign_extend_150.py starting {ts()} ===")
    clean_partial([name for name, _, _, _ in DATASETS])

    for dataset, max_new_tokens, first_new, last_new in DATASETS:
        cases = [f"case_{n:03d}" for n in range(first_new, last_new + 1)]
        csvs = {
            "gptoss": REPO_ROOT / "campaign" / "results" / f"{dataset}.csv",
            "qwen3": REPO_ROOT / "campaign" / "results" / f"{dataset}_qwen3.csv",
        }
        print(f"\n### dataset={dataset} starting {ts()}, {len(cases)} new case(s) ({cases[0]}..{cases[-1]}), max_new_tokens={max_new_tokens} ###")
        for family in ("gptoss", "qwen3"):
            arms = read_arms(csvs[family])
            print(f"\n-- {dataset}/{family}: {len(arms)} arm(s) (incl. strict) --")
            for method, alpha in arms:
                free = free_gb()
                if free < MIN_FREE_GB:
                    print(f"STOPPING: only {free}G free (< {MIN_FREE_GB}G floor) before {dataset}/{family}/{method}/alpha={alpha}.", file=sys.stderr)
                    print(f"\n=== campaign_extend_150.py stopped early {ts()} ===")
                    return 1
                print(f"\n## {dataset}/{family}/{method}/alpha={alpha} started {ts()} ##")
                rc = run_arm(dataset, family, method, alpha, cases, max_new_tokens)
                print(f"## {dataset}/{family}/{method}/alpha={alpha} finished {ts()}, exited {rc} ##")
        print(f"### dataset={dataset} finished {ts()} ###")

    print(f"\n=== campaign_extend_150.py done {ts()} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
