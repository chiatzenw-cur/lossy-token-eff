#!/usr/bin/env python3
"""Extend gsm8k/humaneval/livecodebench/longbench_v2/mtbench (both GPT-OSS
and Qwen3 families) to 50 cases each, at the campaign's already-SELECTED
alphas (campaign/results/<dataset>{,_qwen3}.csv), using
scripts/persistent_arm_replay.py (one server per arm, reused across that
arm's cases) instead of fresh_server_replay.py. aime24 is NOT included here
-- it's already maxed at its full 30-problem pool and being finished
separately by scripts/aime24_finish_reuse_collect.sh.

User request 2026-08-26: "work autonomously to collect data for all
remaining datasets, pushing them to 50 each dataset first ... if disk is
not enough disable tracing". This script always passes
--no-trace-proposals (matches aime24's own precedent, and this dataset set
skews larger/longer than aime24 in aggregate case count, so tracing is off
by default here rather than something to fall back to only if disk runs
low) -- run.json's summary fields (accept length l_bar, completion length,
accuracy, verifier-round counts) are unaffected either way; only the
per-token proposal breakdown is skipped.

Reads each dataset's campaign/results/*.csv directly for its arm list
(method, alpha, including the "strict" row) rather than hardcoding it --
one source of truth, no risk of drifting from what was actually selected.

Case ranges (existing case_001..NNN untouched, only case_(NNN+1)..050 are
new): gsm8k/humaneval/livecodebench/longbench_v2 go 12->50 (case_013..050,
38 new each); mtbench goes 30->50 (case_031..050, 20 new) since it was
already extended once this campaign (2026-08-25).

Runs sequentially (single GPU, no parallelism possible -- same constraint
as everything else in this campaign). A dataset's own two families
(gptoss, qwen3) run back to back; datasets run in the order listed below.
Disk floor checked before every arm, same MIN_FREE_GB=2 pattern as the
other *_extend_collect.sh scripts -- stops cleanly (not mid-arm) if
tripped, safe to resume later since persistent_arm_replay.py recomputes
skip-if-done itself.
"""

from __future__ import annotations

import csv
import datetime as dt
import pathlib
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PY_BIN = str(REPO_ROOT / ".venv-vllm" / "bin" / "python3")
MIN_FREE_GB = 2

QWEN3_FLAGS = [
    "--model-path", "Qwen/Qwen3-8B",
    "--draft-model-path", "RedHatAI/Qwen3-8B-speculator.eagle3",
    "--served-model-name", "qwen3-8b",
    "--rope-scaling-json", '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}',
]

# (dataset, max_new_tokens, first_new_case) -- last_new_case is always 50.
DATASETS = [
    ("gsm8k", 2048, 13),
    ("humaneval", 9000, 13),
    ("livecodebench", 12000, 13),
    ("longbench_v2", 8192, 13),
    ("mtbench", 4096, 31),
]


def free_gb() -> int:
    total, used, free = shutil.disk_usage(REPO_ROOT)
    return free // (1024 ** 3)


def read_arms(csv_path: pathlib.Path) -> list[tuple[str, str]]:
    """[(method, alpha_str), ...] straight from the selected-alphas CSV,
    strict included (alpha_str=="strict" for it)."""
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return [(row["method"], row["alpha"]) for row in rows]


def run_arm(dataset: str, family: str, method: str, alpha: str, cases: list[str], max_new_tokens: int) -> int:
    if family == "gptoss":
        prompt_root = f"prompts/{dataset}"
        log_root = f"logs/campaign_{dataset}_extend50_reuse"
        extra: list[str] = []
    else:
        prompt_root = f"prompts/{dataset}_qwen3"
        log_root = f"logs/campaign_{dataset}_qwen3_extend50_reuse"
        extra = list(QWEN3_FLAGS)

    cmd = [
        PY_BIN, "scripts/persistent_arm_replay.py",
        "--arms", method,
        "--cases", *cases,
        "--prompt-root", prompt_root, "--runs-root", "runs", "--log-root", log_root,
        "--max-new-tokens", str(max_new_tokens), "--port", "30000", "--no-trace-proposals",
    ]
    if method != "strict":
        flag = f"--{method.replace('_', '-')}-alpha"
        cmd += [flag, alpha]
    cmd += extra

    proc = subprocess.run(cmd, cwd=REPO_ROOT)
    return proc.returncode


def clean_partial(datasets: list[str]) -> None:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from campaign_run import clean_partial_runs
    for ds in datasets:
        for name in (ds, f"{ds}_qwen3"):
            n = clean_partial_runs(REPO_ROOT / "runs", name)
            print(f"clean_partial_runs({name}): removed {n}")


def main() -> int:
    ts = lambda: dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== campaign_extend_reuse.py starting {ts()} ===")
    clean_partial([name for name, _, _ in DATASETS])

    for dataset, max_new_tokens, first_new in DATASETS:
        cases = [f"case_{n:03d}" for n in range(first_new, 51)]
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
                    print(f"\n=== campaign_extend_reuse.py stopped early {ts()} ===")
                    return 1
                print(f"\n## {dataset}/{family}/{method}/alpha={alpha} started {ts()} ##")
                rc = run_arm(dataset, family, method, alpha, cases, max_new_tokens)
                print(f"## {dataset}/{family}/{method}/alpha={alpha} finished {ts()}, exited {rc} ##")
        print(f"### dataset={dataset} finished {ts()} ###")

    print(f"\n=== campaign_extend_reuse.py done {ts()} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
