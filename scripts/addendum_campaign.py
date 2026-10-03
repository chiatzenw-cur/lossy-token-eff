#!/usr/bin/env python3
"""Mac-side orchestrator for the NAACL-2027 addendum campaign
(campaign/addendum/README.md). Nibi runs the GPU work through
scripts/addendum_lane.py; this script owns everything else:

  plan     build campaign/addendum/manifest.csv (the single source of truth)
           from the local runs/ tree + campaign/results/*.csv, and write each
           lane's ordered work list (campaign/addendum/lanes/<lane>.json)
  push     copy code + work lists to the lanes' repo copies / run roots
  submit   keep every lane with work supplied with a chain of 12 h jobs
           (--dependency=afterany:<previous>)
  collect  pull finished run dirs back into runs/ (never overwriting),
           recount n_done, commit once per completed arm, push the branch
  cycle    collect -> plan -> push -> submit, then print the manifest summary
  summary  print the manifest summary only

Nothing here ever deletes or overwrites a run directory: pulled runs are
staged and moved into place only where the target does not exist yet.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from campaign_run import MODEL_FAMILIES, TOKEN_BUDGETS, model_flags  # noqa: E402

RUNS = REPO / "runs"
ADD = REPO / "campaign" / "addendum"
MANIFEST = ADD / "manifest.csv"
PROGRESS = ADD / "PROGRESS.md"
LANES_DIR = ADD / "lanes"
STATE = LANES_DIR / "state.json"
JOB_TMP = pathlib.Path(os.environ.get("CLAUDE_JOB_DIR", tempfile.gettempdir())) / "tmp"

HOST = "nibi"  # the grading mirror and lanes A/B


def ssh_cmd(host: str = HOST) -> list[str]:
    return ["ssh", "-o", "BatchMode=yes", "-o", "ControlMaster=no", host]


SSH = ssh_cmd()
REMOTE_HOME = "/home/billxby"
NIBI_PROJECT, KILLARNEY_PROJECT = f"{REMOTE_HOME}/projects/def-hongyanz/billxby", f"{REMOTE_HOME}/projects/aip-hongyanz/billxby"
LANES = {
    "A": {"host": "nibi", "account": "def-hongyanz_gpu", "project": NIBI_PROJECT,
          "repo": f"{NIBI_PROJECT}/lossy-token-eff", "root": "/scratch/billxby/lossy-addendum/laneA", "exclude": "g[15-28]"},
    "B": {"host": "nibi", "account": "def-hongyanz_gpu", "project": NIBI_PROJECT,
          "repo": f"{NIBI_PROJECT}/lossy-token-eff-lane2", "root": "/scratch/billxby/lossy-addendum/laneB", "exclude": "g[1-14]"},
    # Killarney (PAICE allocation aip-hongyanz) from 2026-09-30: the Qwen3 rows move here (README deviation 12)
    # four lanes from 2026-10-01 14:55Z at Bill's suggestion (README deviation 14); no node sets since 15:50Z:
    # Killarney gives every job a private /tmp (job_container/tmpfs) and remote/stop_server.sh now stops only
    # its own job's processes, so lanes may share a node (README deviation 15)
    "K1": {"host": "killarney", "account": "aip-hongyanz", "project": KILLARNEY_PROJECT,
           "repo": f"{KILLARNEY_PROJECT}/lossy-token-eff", "root": "/scratch/billxby/lossy-addendum/laneK1", "exclude": ""},
    "K2": {"host": "killarney", "account": "aip-hongyanz", "project": KILLARNEY_PROJECT,
           "repo": f"{KILLARNEY_PROJECT}/lossy-token-eff-lane2", "root": "/scratch/billxby/lossy-addendum/laneK2", "exclude": ""},
    "K3": {"host": "killarney", "account": "aip-hongyanz", "project": KILLARNEY_PROJECT,
           "repo": f"{KILLARNEY_PROJECT}/lossy-token-eff-lane3", "root": "/scratch/billxby/lossy-addendum/laneK3", "exclude": ""},
    "K4": {"host": "killarney", "account": "aip-hongyanz", "project": KILLARNEY_PROJECT,
           "repo": f"{KILLARNEY_PROJECT}/lossy-token-eff-lane4", "root": "/scratch/billxby/lossy-addendum/laneK4", "exclude": ""},
}
QWEN3_LANES = ["K1", "K2", "K3", "K4"]  # where Qwen3 rows without a lane go
MAX_CHAIN = 4          # jobs per lane queued at once (running + pending)
# 3 h jobs since 2026-09-30 19:20Z: with ~850 H100 jobs pending, 12 h jobs stopped fitting any backfill
# window (a lane waited 6 h); a 3 h job loses at most the case in progress when it ends (skip-if-done)
JOB_TIME, JOB_HOURS = "3:00:00", 3.0
# Nibi H100 SXM request time / old-box H100 PCIe request time, measured 2026-09-29 from strict seed-0
# runs of the same cases (old box 7.1 ms/token, Nibi 2.2-2.4 ms/token; longbench_v2 is prefill-bound
# on the old box: 72.6 s/case vs 4.7 s/case)
HW_FACTOR = {"longbench_v2": 0.12}
HW_DEFAULT = 0.33
STARTUP_S = 270.0      # per arm: stop + patch check/switch + server start (smoke test: 523 s cold, Sept logs ~5.7 min with the self-test)

BASE = ["gsm8k", "humaneval", "longbench_v2", "livecodebench", "mtbench", "aime24"]
N_CASES = {"gsm8k": 150, "humaneval": 150, "longbench_v2": 150, "livecodebench": 90, "mtbench": 80, "aime24": 30,
           "speedbench": 880}
FIVE = ["mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok"]
# strict runs on spec_casc_opt's carrier patch (scripts/lossy_methods.py), so the two
# adjacent cost one patch switch fewer per dataset
ARMS6 = ["strict", "spec_casc_opt", "mentored_dec", "cactus", "r_fuzzy", "spec_casc_tok"]
GRID_51 = {"mentored_dec": [0.15, 0.35, 0.55, 0.75], "spec_casc_tok": [0.15, 0.35, 0.55, 0.8]}

# step 7 (SPEED-Bench qualitative, added 2026-09-29 from Prof. Zhang; README deviations 8-10)
SB = "speedbench"
SB_CASES_CSV = ADD / "speedbench" / "cases.csv"
SB_ARMS = {"strict": "strict", "spec_casc_opt": "0.05", "mentored_dec": "0.75", "cactus": "0.35",
           "r_fuzzy": "0.25", "spec_casc_tok": "0.8"}  # the five rules at the loosest alpha step 7 lists
SB_LANE = {"strict": "B", "spec_casc_opt": "B", "mentored_dec": "B", "cactus": "A", "r_fuzzy": "A", "spec_casc_tok": "A"}
SB_BUDGET, SB_RAISED, SB_CAPOUT = 8192, 16384, 0.10  # a pilot category with >10% strict cap-outs gets 16384
SB_PILOT_CATS, SB_PILOT_N = ("reasoning", "math"), 20
SB_FIRST, SB_PER_CAT, SB_N_CATS = 40, 40, 11  # time-estimate sample per arm; per-category subset if over budget
SB_BUDGET_H = 24.0   # the lane budget: one 12 h job on each GPT-OSS lane (A and B)
SB_HOLD_MIN = 40     # a lane out of work while step 7 waits on a phase keeps its GPU this long
SB_NOTE_MARKERS = ("waits for step-7 phase", "first-40 estimate:", "token budget 8192",
                   "need the cais/hle prompts", "are cais/hle prompts", "wait for the Math budget pilot",
                   "GPU-h vs lane budget", "waits for the GPT-OSS step-7 run")  # regenerated every plan

FIELDS = ["step", "condition", "target", "dataset", "method", "alpha", "seeds", "run_root", "n_cases_target",
          "n_done", "status", "slurm_job_ids", "gpu_hours_est", "gpu_hours_actual", "notes"]
QWEN3_BLOCK = "blocked: Qwen3 needs the consolidated V2 sampler (cascade/DIRECTIONS.md D8), not obtainable yet -- see PROGRESS.md Needs Bill"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_qwen(ds: str) -> bool:
    return ds.endswith("_qwen3")


def base_of(ds: str) -> str:
    return ds.removesuffix("_qwen3")


def target_of(ds: str) -> str:
    return "qwen3-8b" if is_qwen(ds) else "gpt-oss-20b"


def params_dir(method: str, alpha: str) -> str:
    if method in ("strict", "baseline"):
        return method
    return f"alpha{float(alpha):g}".replace("-", "neg")


def fmt_alpha(a) -> str:
    return "strict" if a == "strict" else f"{float(a):g}"


def cases_for(ds: str) -> list[str]:
    return [f"case_{i:03d}" for i in range(1, N_CASES[base_of(ds)] + 1)]


def row_cases(row: dict) -> list[str]:
    """The cases a row targets: case_001..case_<n_cases_target>, or the step-7 pilot's case list."""
    if row["condition"] == "speedbench_pilot":
        return sb_pilot_cases()
    return [f"case_{i:03d}" for i in range(1, int(row["n_cases_target"]) + 1)]


_sb_table: list[dict] | None = None


def sb_cases_table() -> list[dict]:
    """campaign/addendum/speedbench/cases.csv (scripts/build_speedbench_prompts.py), in case order."""
    global _sb_table
    if _sb_table is None:
        _sb_table = []
        if SB_CASES_CSV.is_file():
            with SB_CASES_CSV.open(newline="", encoding="utf-8") as handle:
                _sb_table = list(csv.DictReader(handle))
    return _sb_table


def sb_category(case: str) -> str:
    return next((r["category"] for r in sb_cases_table() if r["case"] == case), "")


def sb_pilot_cases() -> list[str]:
    """The first 20 cases of each pilot category (dataset order within the category)."""
    out = []
    for cat in SB_PILOT_CATS:
        out += [r["case"] for r in sb_cases_table() if r["category"] == cat][:SB_PILOT_N]
    return sorted(out)


def sb_prompt_built(ds: str, case: str) -> bool:
    return (REPO / "prompts" / ds / case / "rendered_prompt.txt").is_file()


def row_key(row: dict) -> str:
    return "|".join([row["condition"], row["dataset"], row["method"], row["alpha"], str(row["seeds"])])


# ---------------------------------------------------------------- selections

def loosest_alphas() -> dict[str, dict[str, str]]:
    """dataset -> method -> loosest chosen alpha (the max; every rule loosens as alpha grows)."""
    out: dict[str, dict[str, str]] = {}
    for base in BASE:
        for ds in (base, f"{base}_qwen3"):
            with (REPO / "campaign" / "results" / f"{ds}.csv").open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            out[ds] = {}
            for method in FIVE:
                alphas = [float(r["alpha"]) for r in rows if r["method"] == method]
                out[ds][method] = fmt_alpha(max(alphas))
    return out


# ------------------------------------------------------------ local run tree

_state_cache: dict[pathlib.Path, str] = {}


def local_state(run_dir: pathlib.Path) -> str:
    """ok | missing | other; 'ok' results are cached (runs are never rewritten)."""
    cached = _state_cache.get(run_dir)
    if cached == "ok":
        return cached
    run_json = run_dir / "run.json"
    if not run_json.is_file():
        state = "missing"
    else:
        try:
            state = "ok" if json.loads(run_json.read_text(encoding="utf-8")).get("status") == "ok" else "other"
        except (OSError, json.JSONDecodeError):
            state = "other"
    _state_cache[run_dir] = state
    return state


def row_run_dir(row: dict, case: str) -> pathlib.Path:
    return (REPO / row["run_root"] / row["dataset"] / row["method"] / params_dir(row["method"], row["alpha"])
            / case / f"seed_{row['seeds']}")


def missing_local(row: dict) -> list[str]:
    return [c for c in row_cases(row) if local_state(row_run_dir(row, c)) != "ok"]


def load_run(run_dir: pathlib.Path) -> dict | None:
    if local_state(run_dir) != "ok":
        return None
    return json.loads((run_dir / "run.json").read_text(encoding="utf-8"))


def sb_measured_seconds(row: dict) -> float | None:
    """Mean wall time per case over the row's finished runs (Nibi), once the first 40 are in."""
    times = [r["wall_time_seconds"] for r in (load_run(row_run_dir(row, c)) for c in row_cases(row)) if r]
    return sum(times) / len(times) if len(times) >= SB_FIRST else None


_case_time_cache: dict[tuple, float | None] = {}


def mean_case_seconds(ds: str, method: str, alpha: str) -> float | None:
    key = (ds, method, alpha)
    if key not in _case_time_cache:
        root = RUNS / ds / method / params_dir(method, alpha)
        times = []
        for run_json in root.glob("case_*/seed_0/run.json"):
            try:
                data = json.loads(run_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("status") == "ok" and data.get("wall_time_seconds") is not None:
                times.append(float(data["wall_time_seconds"]))
        _case_time_cache[key] = sum(times) / len(times) if times else None
    return _case_time_cache[key]


def estimate_hours(row: dict, n_missing: int) -> float:
    if n_missing == 0:
        return 0.0
    ds, method, alpha = row["dataset"], row["method"], row["alpha"]
    if base_of(ds) == SB:  # Nibi-measured once 40 cases are in; 10 s/case (about 4k tokens) until then
        per_case = sb_measured_seconds(row) or 10.0
        return round((n_missing * per_case + STARTUP_S) / 3600.0, 2)
    per_case = mean_case_seconds(ds, method, alpha) if row["condition"] in ("main", "qwenT0.6") else None
    if per_case is None:
        per_case = mean_case_seconds(ds, "strict", "strict") or 60.0
    if row["condition"] == "lmdraft":
        per_case *= 1.3
    factor = HW_FACTOR.get(base_of(ds), HW_DEFAULT)
    return round((n_missing * per_case * factor + STARTUP_S) / 3600.0, 2)


# ------------------------------------------------------------------ the plan

def server_settings(condition: str) -> dict:
    s = {"num_spec": 6, "temperature": 1.0, "top_p": 1.0}
    if condition.startswith("nspec"):
        s["num_spec"] = int(condition.removeprefix("nspec"))
    elif condition.startswith("temp"):
        s["temperature"] = float(condition.removeprefix("temp"))
    elif condition == "qwenT0.6":
        s.update(temperature=0.6, top_p=0.95)
    return s


def make_row(step: str, condition: str, ds: str, method: str, alpha: str, seed: int, notes: str = "",
             n_cases: int | None = None) -> dict:
    if base_of(ds) == SB:  # step 7: runs/addendum/speedbench/<family>/ (the prompt root name follows)
        run_root = f"runs/addendum/{condition}/{target_of(ds)}"
    else:
        run_root = "runs" if condition == "main" else f"runs/addendum/{condition}"
    return {
        "step": step, "condition": condition, "target": target_of(ds), "dataset": ds, "method": method,
        "alpha": alpha, "seeds": str(seed), "run_root": run_root,
        "n_cases_target": str(n_cases or N_CASES[base_of(ds)]), "n_done": "0", "status": "pending",
        "slurm_job_ids": "", "gpu_hours_est": "", "gpu_hours_actual": "", "notes": notes,
    }


# Lane C = the plan's Qwen3 lane (step 2.1 -> 3 -> 4.2 -> 5.1 -> 4.3 -> 6 -> 2.2 -> 5.2, with the
# Qwen3 nibiref before step 3 and step 4.1 after it). There is no third GPU lane (user: "like 2
# GPUs"); once Qwen3 is unblocked its rows are spread over lanes A and B after their GPT-OSS work.
# Reordered 2026-09-30 19:35Z with Bill (congested Nibi queue): the rows the paper's two-model claims
# rest on first -- seed replication (2.1, then the AIME24 seeds of 2.2 and 6), Qwen3's recommended
# sampler (4.2), the standalone LM drafter (4.3) -- then the confirmations (0.5 Nibi reference before
# the Nibi-timed 3 and 4.1), the alpha grid (5.1 -> 5.2), and Qwen3 SPEED-Bench last.
LANE_C_PRIORITY = {"2.1": 0, "2.2": 1, "6": 1, "4.2": 2, "4.3": 3, "0.5": 4, "3": 5, "4.1": 6, "5.1": 7, "5.2": 8, "7": 10}


def all_rows(keep: set[str] | None = None) -> tuple[list[dict], dict[str, list[str]]]:
    """Every addendum row, plus lane -> [row keys] in run order. GPT-OSS rows go to lanes A/B;
    every Qwen3 row goes to the virtual lane C. `keep` = keys already in the manifest (a step-5.1
    cell stays a row after it completes)."""
    loose = loosest_alphas()
    keep = keep or set()
    rows: list[dict] = []
    lanes: dict[str, list[str]] = {"A": [], "B": [], "C": []}

    def add(row: dict, lane: str | None) -> None:
        rows.append(row)
        lanes["C" if is_qwen(row["dataset"]) else lane].append(row_key(row))

    def arm_alpha(ds: str, arm: str) -> str:
        return "strict" if arm == "strict" else loose[ds][arm]

    # step 0.5 (added, see README): strict seed 0 at the campaign settings on Nibi -- the
    # hardware-matched reference for wall-time ratios of Nibi-produced cells (N_draft=6 row of
    # step 3, T=1.0 row of step 4.1, time ratios of the step 5.1 cells in step 5.2).
    for ds in ("gsm8k", "livecodebench"):
        add(make_row("0.5", "nibiref", ds, "strict", "strict", 0), "B")
    # step 2.1 -- lane A
    for fam in ("", "_qwen3"):
        for base in ("gsm8k", "humaneval", "mtbench", "livecodebench"):
            ds = base + fam
            for arm in ARMS6:
                for seed in (1, 2):
                    add(make_row("2.1", "main", ds, arm, arm_alpha(ds, arm), seed), "A")
    for ds in ("humaneval", "mtbench", "longbench_v2", "aime24"):
        add(make_row("0.5", "nibiref", ds, "strict", "strict", 0), "A")
    for ds in (f"{b}_qwen3" for b in BASE):
        add(make_row("0.5", "nibiref", ds, "strict", "strict", 0), None)
    # step 3 -- lane B
    for fam in ("", "_qwen3"):
        for k in (2, 3, 4, 8, 10):
            for base in ("gsm8k", "livecodebench"):
                add(make_row("3", f"nspec{k}", base + fam, "strict", "strict", 0), "B")
    # step 4.1 -- lane B
    for fam in ("", "_qwen3"):
        for temp in ("1.2", "1.5"):
            for base in ("gsm8k", "livecodebench"):
                add(make_row("4.1", f"temp{temp}", base + fam, "strict", "strict", 0), "B")
    # step 4.2 (Qwen3 only)
    for base in ("gsm8k", "livecodebench"):
        ds = base + "_qwen3"
        for arm in ARMS6:
            add(make_row("4.2", "qwenT0.6", ds, arm, arm_alpha(ds, arm), 0), None)
    # step 4.3 (Qwen3 only)
    for base in ("gsm8k", "livecodebench"):
        for arm, alpha in (("strict", "strict"), ("mentored_dec", "0.75"), ("cactus", "0.35"), ("spec_casc_tok", "0.8")):
            add(make_row("4.3", "lmdraft", base + "_qwen3", arm, alpha, 0), None)
    # step 5.1 -- lane A: every grid alpha of the two rules whose cell is not complete yet
    for fam in ("", "_qwen3"):
        for base in BASE:
            ds = base + fam
            for method, grid in GRID_51.items():
                for a in grid:
                    row = make_row("5.1", "main", ds, method, fmt_alpha(a), 0)
                    if row_key(row) in keep or missing_local(row):
                        add(row, "A")
    # step 6 (+ step 2.2 for aime24 seeds 1-2) -- lane B, seed-major
    for fam in ("", "_qwen3"):
        ds = "aime24" + fam
        for seed in (1, 2, 3, 4):
            for arm in ARMS6:
                if seed <= 2 and (not fam or arm in ("strict", "spec_casc_opt", "r_fuzzy")):
                    step, note = "2.2", "seeds 1-2 shared by step 6"
                else:
                    step, note = "6", ""
                add(make_row(step, "main", ds, arm, arm_alpha(ds, arm), seed, note), "B")
    # step 2.2 longbench_v2 (GPT-OSS) -- lane B (moved from A at launch: A 18.3 h vs B 10.8 h estimated)
    for arm in ("strict", "spec_casc_opt", "mentored_dec", "r_fuzzy"):
        for seed in (1, 2):
            add(make_row("2.2", "main", "longbench_v2", arm, arm_alpha("longbench_v2", arm), seed), "B")
    # rows added later by other steps (step 5.2's seed-1 arms): stored in lanes/state.json
    for extra in load_state().get("extra_rows", []):
        row = make_row(extra["step"], extra["condition"], extra["dataset"], extra["method"], extra["alpha"],
                       int(extra["seed"]), extra.get("notes", ""))
        if row_key(row) not in {row_key(r) for r in rows}:
            add(row, extra.get("lane", "B"))
    # step 7 (SPEED-Bench): the budget pilot first on lane B, the six GPT-OSS arms over lanes A and B
    # after their other work, the Qwen3 arms last on lane C. Relaxed arms drop to 40 prompts per
    # category if the first-40 estimate of the full split exceeds SB_BUDGET_H (sb_advance).
    if sb_cases_table():  # rows appear once scripts/build_speedbench_prompts.py has written cases.csv
        state = load_state()
        for fam in ("", "_qwen3"):  # each model gets its own token-budget pilot and phases
            ds = SB + fam
            subset = sb_state(state, ds).get("subset_relaxed")
            pilot = make_row("7", "speedbench_pilot", ds, "strict", "strict", 0,
                             f"first {SB_PILOT_N} Reasoning + first {SB_PILOT_N} Math cases at {SB_BUDGET}; >10% cap-outs "
                             f"raise that category to {SB_RAISED}", n_cases=len(sb_pilot_cases()))
            rows.append(pilot)
            if fam:
                lanes["C"].append(row_key(pilot))
            else:
                lanes["B"].insert(0, row_key(pilot))
            for arm, alpha in SB_ARMS.items():
                n = SB_PER_CAT * SB_N_CATS if (subset and arm != "strict") else N_CASES[SB]
                add(make_row("7", "speedbench", ds, arm, alpha, 0, n_cases=n), SB_LANE[arm])
    by_key = {row_key(r): r for r in rows}
    lanes["C"].sort(key=lambda k: LANE_C_PRIORITY.get(by_key[k]["step"], 8))  # stable within a step
    return rows, lanes


def load_manifest() -> list[dict]:
    if not MANIFEST.is_file():
        return []
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_manifest(rows: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDS})
    tmp.replace(MANIFEST)


def load_state() -> dict:
    if STATE.is_file():
        state = json.loads(STATE.read_text(encoding="utf-8"))
    else:
        state = {"lanes": {}, "blocked_qwen3": True}
    for name in LANES:  # lanes added later (K1/K2) start empty
        state["lanes"].setdefault(name, {"jobs": [], "rows": []})
    return state


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def lane_status_events(lane: str) -> list[dict]:
    path = LANES_DIR / f"{lane}_status.jsonl"
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def progress(line: str) -> None:
    PROGRESS.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS.open("a", encoding="utf-8") as handle:
        handle.write(f"- {utc_now()} {line}\n")


# The EAGLE-3 drafter's own config stops at 40960 positions (its rope table; --hf-overrides only reaches the target),
# so longbench_v2_qwen3's longest sequences (~59k) crash its compiled rope kernel on Killarney. This copy of snapshot
# 08610ffa differs only in transformer_layer_config.max_position_embeddings = 65536 (README deviation 19).
LONG_DRAFTER = f"{KILLARNEY_PROJECT}/hf/local/Qwen3-8B-speculator.eagle3-maxpos65536"
LONG_DRAFTER_CACHE = "/scratch/billxby/vllm_cache_longdrafter"  # not the cache holding the 40960-bound kernel


def work_item(row: dict, cases: list[str], max_new_tokens: int | None = None) -> dict:
    ds = row["dataset"]
    family = MODEL_FAMILIES["qwen3" if is_qwen(ds) else "gpt_oss_20b"]
    flags = model_flags(*family)
    if row["condition"] == "lmdraft":
        flags = model_flags(family[0], "Qwen/Qwen3-0.6B", family[2], family[3])
    elif ds == "longbench_v2_qwen3":
        flags = model_flags(family[0], LONG_DRAFTER, family[2], family[3])
    item = {
        "id": row_key(row), "step": row["step"], "condition": row["condition"], "dataset": ds,
        "method": row["method"], "alpha": row["alpha"], "seed": int(row["seeds"]), "cases": cases,
        "prompt_root": f"prompts/{ds}", "runs_subroot": row["run_root"],
        "max_new_tokens": max_new_tokens or TOKEN_BUDGETS[ds], "model_flags": flags, **server_settings(row["condition"]),
    }
    if not is_qwen(ds):
        # GPT-OSS-20B runs the V1 sampler only; the V2 file on Nibi is pristine (README deviation 5)
        item["env"] = {"MENTORED_DEC_TEST_V1_ONLY": "1"}
    if row["condition"] == "lmdraft":
        item["env"] = {"SPEC_METHOD": "draft_model"}
    if row["condition"] == "qwenT0.6":
        item["extra_flags"] = ["--top-k", "20"]  # Qwen3's recommended sampler: T 0.6, top-p 0.95, top-k 20
    if is_qwen(ds) and row["condition"].startswith("nspec") and server_settings(row["condition"])["num_spec"] >= 10:
        # vLLM's sampler warmup over Qwen3's 152k-token vocabulary at 10 draft tokens runs out of memory once the KV
        # cache holds 0.85 of the GPU (short by 0.6 GiB; job 5839007, 2026-10-01). The KV pool's size does not change
        # a single request's computation (no prefix caching, one request at a time): 0.80 (README deviation 18)
        item["env"] = {**item.get("env", {}), "GPU_UTIL": "0.80"}
    if ds == "longbench_v2_qwen3" and row["condition"] != "lmdraft":
        item["env"] = {**item.get("env", {}), "VLLM_CACHE_ROOT": LONG_DRAFTER_CACHE}
    return item


# ------------------------------------------------------------ step 7 phases
# pilot:   strict on the first 20 Reasoning + first 20 Math cases at 8192 decides each category's budget
# first40: every arm runs the first 40 runnable cases (built, budget decided) -> per-arm time estimate
# full:    the rest; relaxed arms stop at 40 per category if the estimate exceeded SB_BUDGET_H

def sb_state(state: dict, ds: str = SB) -> dict:
    """Step-7 phase state of one model: state['speedbench'] (GPT-OSS) or state['speedbench_qwen3']."""
    return state.setdefault(ds, {"phase": "pilot", "budget": {c: None for c in SB_PILOT_CATS},
                                 "first40": [], "subset_relaxed": None, "estimate": {}})


def sb_case_budget(sbs: dict, case: str) -> int | None:
    cat = sb_category(case)
    if cat not in SB_PILOT_CATS:
        return SB_BUDGET
    budget = sbs["budget"].get(cat)
    if budget is None and cat == "math" and sbs["phase"] == "full" and not sb_is_hle(case):
        # Math's budget waits for its 16 cais/hle pilot cases; its 18 other rows (Spec-Bench's GSM8K-style
        # problems, <= 636 completion tokens in the pilot) cannot come near either cap, so they run now
        return SB_BUDGET
    return budget


def sb_is_hle(case: str) -> bool:
    return any(r["case"] == case and "cais/hle" in r["source"] for r in sb_cases_table())


def sb_advance(sbs: dict, by_key: dict, ds: str = SB) -> bool:
    """Move one model's step 7 through its phases from the local runs. True when its relaxed rows'
    case count changed."""
    pilot = next((r for r in by_key.values() if r["condition"] == "speedbench_pilot" and r["dataset"] == ds), None)
    if pilot is None or not sb_cases_table():
        return False
    tag = f"step 7 ({target_of(ds)})"
    for cat in SB_PILOT_CATS:
        if sbs["budget"].get(cat) is not None:
            continue
        cases = [r["case"] for r in sb_cases_table() if r["category"] == cat][:SB_PILOT_N]
        runs = [load_run(row_run_dir(pilot, c)) for c in cases]
        if len(cases) < SB_PILOT_N or any(r is None for r in runs):
            continue
        capped = sum(bool(r.get("reached_max_new_tokens")) for r in runs)
        sbs["budget"][cat] = SB_RAISED if capped / len(runs) > SB_CAPOUT else SB_BUDGET
        progress(f"{tag}: budget pilot {cat}: {capped}/{len(runs)} strict cap-outs at {SB_BUDGET} tokens "
                 f"-> {cat} runs at {sbs['budget'][cat]}")
    if sbs["phase"] == "pilot":
        waiting = [c for c in pilot["_missing"] if sb_prompt_built(ds, c)]
        if not waiting and int(pilot["n_done"]) > 0:
            first = [r["case"] for r in sb_cases_table()
                     if sb_prompt_built(ds, r["case"]) and sb_case_budget(sbs, r["case"]) is not None][:SB_FIRST]
            sbs.update(phase="first40", first40=first)
            progress(f"{tag}: pilot done; time-estimate sample = the first {len(first)} runnable cases "
                     f"({first[0]}..{first[-1]}; Math waits for its budget) on every arm")
    if sbs["phase"] == "first40":
        arms = [r for r in by_key.values() if r["condition"] == "speedbench" and r["dataset"] == ds]
        runs = {r["method"]: [load_run(row_run_dir(r, c)) for c in sbs["first40"]] for r in arms}
        if arms and all(x is not None for v in runs.values() for x in v):
            per_case = {m: sum(x["wall_time_seconds"] for x in v) / len(v) for m, v in runs.items()}
            full_h = sum(s * N_CASES[SB] + STARTUP_S for s in per_case.values()) / 3600.0
            subset = full_h > SB_BUDGET_H
            sbs.update(phase="full", subset_relaxed=subset,
                       estimate={"s_per_case": {m: round(s, 2) for m, s in per_case.items()},
                                 "full_split_gpu_h": round(full_h, 2), "lane_budget_gpu_h": SB_BUDGET_H})
            progress(f"{tag}: first-40 estimate of the full split (6 arms x {N_CASES[SB]}): {full_h:.1f} GPU-h "
                     f"vs lane budget {SB_BUDGET_H:.0f} GPU-h -> "
                     + (f"relaxed arms run {SB_PER_CAT} per category ({SB_PER_CAT * SB_N_CATS}), strict all {N_CASES[SB]}"
                        if subset else f"all arms run the full {N_CASES[SB]}")
                     + "; s/case " + ", ".join(f"{m} {s:.1f}" for m, s in per_case.items()))
            return bool(subset)
    return False


def sb_items(row: dict, sbs: dict, gate_open: bool = True) -> list[dict]:
    """Work items of a step-7 row: its runnable missing cases, one item per token budget. Qwen3 rows
    (pilot included) wait for the GPT-OSS run: gate_open = GPT-OSS has nothing runnable left."""
    pilot = row["condition"] == "speedbench_pilot"
    if not gate_open or (not pilot and sbs["phase"] == "pilot"):
        return []
    groups: dict[int, list[str]] = {}
    for case in row["_missing"]:
        if not sb_prompt_built(row["dataset"], case):
            continue
        if not pilot and sbs["phase"] == "first40" and case not in sbs["first40"]:
            continue
        budget = SB_BUDGET if pilot else sb_case_budget(sbs, case)
        if budget is not None:
            groups.setdefault(budget, []).append(case)
    items = []
    for budget, cases in sorted(groups.items()):
        item = work_item(row, cases, max_new_tokens=budget)
        item["id"] = f"{row_key(row)}@{budget}"
        items.append(item)
    return items


def sb_wait_note(row: dict, sbs: dict, gate_open: bool = True) -> tuple[str, str]:
    """(status, note) for a step-7 row with missing cases but nothing runnable now."""
    if not gate_open:
        return "pending", "waits for the GPT-OSS step-7 run to finish"
    unbuilt = [c for c in row["_missing"] if not sb_prompt_built(row["dataset"], c)]
    undecided = [c for c in row["_missing"] if c not in unbuilt and sb_case_budget(sbs, c) is None]
    if row["condition"] != "speedbench_pilot" and sbs["phase"] != "full":
        return "pending", f"waits for step-7 phase '{sbs['phase']}' to finish"
    if unbuilt or undecided:
        return "blocked", (f"{len(unbuilt)} case(s) are cais/hle prompts, not run: dropped by Bill's decision "
                           "2026-10-02 (README deviation 21)"
                           + (f"; {len(undecided)} wait for the Math budget pilot" if undecided else ""))
    return "pending", ""


def cmd_plan(args: argparse.Namespace) -> int:
    old = {row_key(r): r for r in load_manifest()}
    rows, lanes = all_rows(keep=set(old))
    by_key = {row_key(r): r for r in rows}
    state = load_state()
    blocked_qwen = state.get("blocked_qwen3", True)

    # counts and estimates first (lane balancing needs them)
    for row in rows:
        prev = old.get(row_key(row), {})
        for keep in ("slurm_job_ids", "gpu_hours_actual", "notes"):
            if prev.get(keep):
                row[keep] = prev[keep]
        row["_missing"] = missing_local(row)
        row["n_done"] = str(int(row["n_cases_target"]) - len(row["_missing"]))
        row["gpu_hours_est"] = f"{estimate_hours(row, len(row['_missing'])):.2f}"
    sbs_of = {ds: sb_state(state, ds) for ds in (SB, SB + "_qwen3")}
    resized = [sb_advance(sbs_of[ds], by_key, ds) for ds in sbs_of]
    if any(resized):  # a model's relaxed step-7 rows changed size: rebuild the rows from the new state
        save_state(state)
        return cmd_plan(args)
    # Qwen3's step 7 starts once GPT-OSS has nothing runnable left (the cais/hle cases may still be missing)
    sb_gate = {SB: True, SB + "_qwen3": not any(
        sb_items(r, sbs_of[SB]) for r in rows if base_of(r["dataset"]) == SB and not is_qwen(r["dataset"]) and r["_missing"])}

    # A row keeps the lane it first got (a row with progress in one lane's run root must never
    # move to another lane: skip-if-done only sees the lane's own root).
    lane_of: dict[str, str] = {}
    for lane, info in state["lanes"].items():
        for key in info.get("rows", []):
            lane_of[key] = lane
    for lane in LANES:
        for key in lanes.get(lane, []):
            lane_of.setdefault(key, lane)
    if not blocked_qwen:  # spread new lane-C (Qwen3) rows over the Qwen3 lanes by remaining estimated hours
        targets = [lane for lane in QWEN3_LANES if lane in LANES] or list(LANES)
        load = {lane: sum(float(by_key[k]["gpu_hours_est"]) for k in by_key if lane_of.get(k) == lane) for lane in targets}
        # ...except an extra row (step 5.2) that names its Qwen3 lane: a seed-1 pair must share a lane
        extra_lane = {row_key(make_row(e["step"], e["condition"], e["dataset"], e["method"], e["alpha"], int(e["seed"]))):
                      e.get("lane") for e in state.get("extra_rows", [])}
        for key in lanes["C"]:
            if key not in lane_of:
                lane = extra_lane[key] if extra_lane.get(key) in load else min(load, key=load.get)
                lane_of[key] = lane
                load[lane] += float(by_key[key]["gpu_hours_est"])
    # run order per lane: its GPT-OSS rows in plan order, then its Qwen3 rows in lane-C order (a row moved
    # between lanes keeps its place: rows are taken from every lane list, by their assigned lane)
    gpt_order = list(dict.fromkeys(k for name in lanes if name != "C" for k in lanes[name]))
    order = {lane: [k for k in gpt_order if lane_of.get(k) == lane] + [k for k in lanes["C"] if lane_of.get(k) == lane]
             for lane in LANES}

    job_state = {j["id"]: j.get("state", "") for info in state["lanes"].values() for j in info.get("jobs", [])}
    active_item = {}
    for lane in LANES:
        started = {}
        for ev in lane_status_events(lane):
            if ev.get("event") == "item_start":
                started[ev["job"]] = ev["item"]
            elif ev.get("event") in ("item_end", "job_end"):
                started.pop(ev["job"], None)
        for job, item in started.items():
            if job_state.get(job) == "RUNNING":
                active_item[lane] = item.split("@")[0]  # step-7 items are <row key>@<token budget>

    work: dict[str, list[dict]] = {lane: list(state.get("extra_items", {}).get(lane, [])) for lane in LANES}
    for lane in LANES:
        lane_jobs = [j for j in state["lanes"][lane]["jobs"] if j.get("state") in ("RUNNING", "PENDING")]
        for key in order[lane]:
            row = by_key[key]
            if not row["_missing"] or (is_qwen(row["dataset"]) and blocked_qwen):
                continue
            if base_of(row["dataset"]) == SB:
                ds = row["dataset"]
                items = sb_items(row, sbs_of[ds], sb_gate[ds])
                if not items:
                    row["status"], note = sb_wait_note(row, sbs_of[ds], sb_gate[ds])
                    row["_sb_note"] = note
                    continue
                work[lane].extend(items)
            else:
                work[lane].append(work_item(row, row["_missing"]))
            row["status"] = "running" if active_item.get(lane) == key else ("queued" if lane_jobs else "pending")
        # a model's short pilot / first-40 items gate the rest of its step 7: run them first
        work[lane].sort(key=lambda item: 0 if item["step"] == "7" and sbs_of[item["dataset"]]["phase"] != "full" else 1)
    for row in rows:
        key = row_key(row)
        lane = lane_of.get(key)
        blocked = is_qwen(row["dataset"]) and blocked_qwen
        if not row["_missing"]:
            row["status"] = "done"
        elif blocked:
            row["status"] = "blocked"
        elif lane not in LANES:
            row["status"] = "pending"
        notes = [x for x in row["notes"].split("; ")
                 if x and x != QWEN3_BLOCK and not any(m in x for m in SB_NOTE_MARKERS)
                 and not re.fullmatch(r"(reasoning|math) \d+", x)  # fragments of an older budget note
                 and not re.fullmatch(r"lane=\w+", x)]  # the current lane is re-added below
        if blocked and row["_missing"]:
            notes.append(QWEN3_BLOCK)
        if lane in LANES and not blocked and f"lane={lane}" not in notes:
            notes.insert(0, f"lane={lane}")
        if base_of(row["dataset"]) == SB and not blocked:
            sbs = sbs_of[row["dataset"]]
            if row.get("_sb_note"):
                notes.append(row["_sb_note"])
            if row["condition"] == "speedbench" and sbs.get("estimate"):
                est = sbs["estimate"]
                notes.append(f"first-40 estimate: {est['s_per_case'].get(row['method'], 0):.1f} s/case, full split "
                             f"{est['full_split_gpu_h']:.1f} GPU-h vs lane budget {est['lane_budget_gpu_h']:.0f}")
            budgets = ", ".join(f"{c} {b}" for c, b in sbs["budget"].items() if b)
            if budgets:
                notes.append(f"token budget 8192 (pilot: {budgets})")
        row["notes"] = "; ".join(notes)
        if lane in LANES:  # job ids and measured hours from the lane journals
            jobs, secs = [], 0.0
            for ev in lane_status_events(lane):
                if (ev.get("item") or "").split("@")[0] != key:
                    continue
                if ev.get("event") == "item_start" and ev["job"] not in jobs:
                    jobs.append(ev["job"])
                if ev.get("event") == "item_end":
                    secs += float(ev.get("elapsed_s") or 0.0)
            if jobs:
                row["slurm_job_ids"] = " ".join(jobs)
            if secs:
                row["gpu_hours_actual"] = f"{secs / 3600:.2f}"

    write_manifest(rows)
    for lane in LANES:
        assigned = [k for k in order[lane] if not (is_qwen(by_key[k]["dataset"]) and blocked_qwen)]
        state["lanes"][lane]["rows"] = list(dict.fromkeys(state["lanes"][lane].get("rows", []) + assigned))
        path = LANES_DIR / f"{lane}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        # a lane that runs out of work while step 7 waits on a phase (pilot, first-40 estimate) keeps its
        # GPU for SB_HOLD_MIN minutes: the next poll queues the following phase (scripts/addendum_lane.py)
        sb_waiting = any(
            lane_of.get(row_key(r)) == lane and r["_missing"] for r in rows
            if r["condition"] == "speedbench" and base_of(r["dataset"]) == SB and sb_gate[r["dataset"]]
            and sbs_of[r["dataset"]]["phase"] != "full" and not (is_qwen(r["dataset"]) and blocked_qwen))
        path.write_text(json.dumps({"lane": lane, "written": utc_now(), "hold_minutes": SB_HOLD_MIN if sb_waiting else 0,
                                    "items": work[lane]}, indent=1) + "\n", encoding="utf-8")
    save_state(state)
    if not args.quiet:
        print_summary(rows)
    return 0


def print_summary(rows: list[dict]) -> None:
    from collections import Counter, defaultdict
    by_status = Counter(r["status"] for r in rows)
    hours = defaultdict(float)
    for r in rows:
        if r["status"] in ("running", "queued", "pending"):
            hours[r["notes"].split(";")[0] if r["notes"].startswith("lane=") else "unassigned"] += float(r["gpu_hours_est"] or 0)
    print(f"manifest: {len(rows)} rows; " + ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    print("est. GPU-hours remaining by lane: " + ", ".join(f"{k}: {v:.1f}" for k, v in sorted(hours.items())))
    steps = defaultdict(Counter)
    for r in rows:
        steps[r["step"]][r["status"]] += 1
    for step in sorted(steps, key=lambda s: [float(x) for x in s.split("/")[0].split(".")]):
        print(f"  step {step}: " + ", ".join(f"{k}={v}" for k, v in sorted(steps[step].items())))


def cmd_summary(args: argparse.Namespace) -> int:
    print_summary(load_manifest())
    return 0


# ------------------------------------------------------------------- remote

def ssh(command: str, *, input_bytes: bytes | None = None, check: bool = True, timeout: float = 600,
        host: str = HOST) -> subprocess.CompletedProcess:
    return subprocess.run([*ssh_cmd(host), command], input=input_bytes, capture_output=True, check=check, timeout=timeout)


PUSH_FILES = [
    "scripts/addendum_lane.py", "cascade/cluster/addendum_lane.sbatch", "cascade/cluster/addendum_smoke.sbatch",
    "cascade/cluster/addendum_grade.sbatch", "scripts/addendum_grade.py",
    "scripts/persistent_arm_replay.py", "scripts/fresh_server_replay.py", "scripts/run_experiment_vllm.py",
    "scripts/lossy_methods.py", "scripts/campaign_run.py", "remote/run_server_vllm.sh", "remote/stop_server.sh",
    "patches/apply.sh", "patches/HASHES.txt", "patches/test_mentored_dec.py",
]


# gitignored prompt roots (step 7, licence): copied to every lane repo whenever their content changes
PROMPT_SYNC = ["prompts/speedbench", "prompts/speedbench_qwen3"]


def prompt_digest(rel: str) -> str | None:
    root = REPO / rel
    files = sorted(p for p in root.glob("case_*/*") if p.is_file()) if root.is_dir() else []
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def sync_prompts(up: dict[str, bool] | None = None) -> None:
    state = load_state()
    synced = state.setdefault("prompt_sync", {})
    for rel in PROMPT_SYNC:
        digest = prompt_digest(rel)
        stale = [lane for lane in LANES if digest and synced.get(f"{lane}:{rel}") != digest
                 and (up is None or up.get(LANES[lane]["host"], True))]
        if not stale:
            continue
        tar = subprocess.run(["tar", "-cf", "-", rel], cwd=REPO, capture_output=True, check=True,
                             env={**os.environ, "COPYFILE_DISABLE": "1"}).stdout
        for lane in stale:
            ssh(f"cd {shlex.quote(LANES[lane]['repo'])} && tar -xf -", input_bytes=tar, timeout=1800,
                host=LANES[lane]["host"])
            synced[f"{lane}:{rel}"] = digest
            progress(f"lane {lane}: synced {rel} ({len(tar) / 1e6:.1f} MB tar) to the lane repo")
            print(f"synced {rel} to lane {lane}")
    save_state(state)


def cmd_push(args: argparse.Namespace) -> int:
    files = [f for f in PUSH_FILES if (REPO / f).is_file()]
    tar = subprocess.run(["tar", "-cf", "-", *files], cwd=REPO, capture_output=True, check=True).stdout
    up = {host: reachable(host) for host in dict.fromkeys(info["host"] for info in LANES.values())}
    sync_prompts(up)  # before the work lists that reference them
    for lane, info in LANES.items():
        if not up[info["host"]]:
            print(f"lane {lane}: {info['host']} unreachable, not pushed")
            continue
        ssh(f"cd {shlex.quote(info['repo'])} && tar -xf -", input_bytes=tar, host=info["host"])
        work = (LANES_DIR / f"{lane}.json").read_bytes()
        root = shlex.quote(info["root"])
        ssh(f"mkdir -p {root}/slurm && cat > {root}/work.json.tmp && mv {root}/work.json.tmp {root}/work.json",
            input_bytes=work, host=info["host"])
        n = len(json.loads(work)["items"])
        print(f"pushed {len(files)} code files + work list ({n} items) to lane {lane}")
    return 0


def squeue_states(host: str = HOST) -> dict[str, str] | None:
    """job id -> state for this user on `host`; None when the host cannot be reached (ssh exit 255,
    e.g. its ControlMaster dropped) -- never an empty map that would mark every job ENDED."""
    # squeue is not on the PATH of a non-login shell on Killarney
    proc = ssh("bash -lc \"squeue -u billxby -h -o '%i|%T'\"", check=False, host=host)
    if proc.returncode == 255:
        return None
    states = {}
    for line in proc.stdout.decode().splitlines():
        if "|" in line:
            job, st = line.strip().split("|", 1)
            states[job] = st
    return states


def reachable(host: str) -> bool:
    return ssh("true", check=False, host=host, timeout=60).returncode == 0


LIVE_STATES = {"PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "SUSPENDED", "REQUEUED", "RESIZING", "", None}


def refresh_job_states(state: dict) -> dict[str, dict[str, str] | None]:
    """Update every lane job's state; lanes on an unreachable host keep their last known states."""
    live_by_host = {host: squeue_states(host) for host in dict.fromkeys(info["host"] for info in LANES.values())}
    for lane, info in state["lanes"].items():
        live = live_by_host.get(LANES.get(lane, {}).get("host", HOST))
        if live is None:
            continue
        for job in info.get("jobs", []):
            if job["id"] in live:
                job["state"] = live[job["id"]]
            elif job.get("state") in ("PENDING", "RUNNING", "CONFIGURING", "COMPLETING", "", None):
                job["state"] = "ENDED"
    return live_by_host


def cmd_submit(args: argparse.Namespace) -> int:
    state = load_state()
    live_by_host = refresh_job_states(state)
    manifest = {row_key(r): r for r in load_manifest()}
    for lane, info in LANES.items():
        items = json.loads((LANES_DIR / f"{lane}.json").read_text(encoding="utf-8"))["items"]
        if not items:
            continue
        if live_by_host.get(info["host"]) is None:  # job states unknown: submitting could double the chain
            print(f"lane {lane}: {info['host']} unreachable, nothing submitted")
            continue
        # step-7 items are <row key>@<budget>; a row split into two budget items counts once
        remaining_h = sum(float(manifest.get(key, {}).get("gpu_hours_est") or 0)
                          for key in dict.fromkeys(i["id"].split("@")[0] for i in items))
        want = max(1, min(MAX_CHAIN, int(remaining_h / (0.9 * JOB_HOURS)) + 1))
        jobs = state["lanes"][lane]["jobs"]
        active = [j for j in jobs if j.get("state") in ("PENDING", "RUNNING", "CONFIGURING", "COMPLETING")]
        while len(active) < want:
            dep = f"--dependency=afterany:{active[-1]['id']} " if active else ""
            cmd = (
                f"cd {shlex.quote(info['repo'])} && mkdir -p {info['root']}/slurm && "
                f"LANE={lane} REPO_DIR={shlex.quote(info['repo'])} LANE_ROOT={info['root']} PROJECT_DIR={info['project']} "
                f"sbatch --parsable --job-name=add-{lane} --account={info['account']} "
                + (f"--exclude={info['exclude']} " if info["exclude"] else "")
                + f"--time={JOB_TIME} --output={info['root']}/slurm/%x-%j.out {dep}cascade/cluster/addendum_lane.sbatch"
            )
            out = ssh(f"bash -lc {shlex.quote(cmd)}", host=info["host"]).stdout.decode().strip().splitlines()[-1]
            job_id = out.split(";")[0].strip()
            job = {"id": job_id, "state": "PENDING", "submitted": utc_now(), "dependency": active[-1]["id"] if active else ""}
            jobs.append(job)
            active.append(job)
            progress(f"lane {lane}: submitted job {job_id}" + (f" (afterany:{job['dependency']})" if job["dependency"] else "")
                     + f"; lane has {len(items)} work items, est. {remaining_h:.1f} GPU-h")
            print(f"lane {lane}: submitted {job_id} {('after ' + job['dependency']) if job['dependency'] else ''}")
    save_state(state)
    return 0


# ------------------------------------------------------------------ collect

def pull_lane_runs(lane: str, info: dict) -> list[str]:
    """Pull every ok run dir from the lane's run root that does not exist locally. Returns rel paths."""
    root = info["root"]
    script = (
        f"cd {root} 2>/dev/null || exit 0; T=$(date +%s); "
        f"if [ -f .collect_marker ]; then F='-newer .collect_marker'; else F=''; fi; "
        f"find runs -name run.json $F 2>/dev/null | xargs -r grep -l '\"status\": \"ok\"' ; echo \"__T=$T\""
    )
    host = info["host"]
    out = ssh(script, timeout=900, host=host).stdout.decode().splitlines()
    stamp = next((l.split("=", 1)[1] for l in out if l.startswith("__T=")), None)
    rels = [l.strip()[: -len("/run.json")] for l in out if l.strip().endswith("/run.json")]
    rels = [r for r in rels if not r.startswith("runs/addendum/smoke")]  # step-0.2 smoke runs are deleted, not kept
    new = [r for r in rels if not (REPO / r).exists()]
    pulled = []
    if new:
        JOB_TMP.mkdir(parents=True, exist_ok=True)
        stage = pathlib.Path(tempfile.mkdtemp(prefix=f"pull_{lane}_", dir=JOB_TMP))
        listing = ("\n".join(new) + "\n").encode()
        proc = subprocess.run([*ssh_cmd(host), f"cd {root} && tar -cf - -T -"], input=listing, capture_output=True,
                              timeout=1800)
        if proc.returncode != 0:
            raise RuntimeError(f"remote tar failed for lane {lane}: {proc.stderr.decode()[-500:]}")
        subprocess.run(["tar", "-xf", "-", "-C", str(stage)], input=proc.stdout, check=True)
        for rel in new:
            src, dst = stage / rel, REPO / rel
            if not (src / "run.json").is_file():
                continue
            if dst.exists():  # appeared meanwhile; never merge two runs' files
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            os.rename(src, dst)
            pulled.append(rel)
        shutil.rmtree(stage, ignore_errors=True)
    if stamp:
        ssh(f"cd {root} && touch -d @{stamp} .collect_marker", check=False, host=host)
    # journals and batch manifests (small; our own copies, refreshed every collect)
    status = ssh(f"cat {root}/status.jsonl 2>/dev/null", check=False, host=host).stdout
    if status:
        (LANES_DIR / f"{lane}_status.jsonl").write_bytes(status)
    return pulled


def git(*argv: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *argv], cwd=REPO, capture_output=True, text=True, check=check)


COAUTHOR = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"


def commit(message: str, paths: list[str]) -> bool:
    git("add", "--", *paths)
    if not git("diff", "--cached", "--quiet", check=False).returncode:
        return False
    git("commit", "-q", "-m", message + COAUTHOR)
    return True


def cmd_collect(args: argparse.Namespace) -> int:
    state = load_state()
    refresh_job_states(state)
    save_state(state)
    before = {row_key(r): r for r in load_manifest()}
    total = 0
    for lane, info in LANES.items():
        # A lane none of whose jobs is live, and whose every job had already ended at its last successful collect,
        # cannot hold new runs: skip it (its find over the run root took 10-15 min on Nibi's /scratch, 2026-10-02).
        lane_state = state["lanes"].setdefault(lane, {})
        jobs = lane_state.get("jobs", [])
        ended = sorted(j["id"] for j in jobs if j.get("state") not in LIVE_STATES)
        if len(ended) == len(jobs) and lane_state.get("collected_jobs") == ended:
            continue
        try:
            pulled = pull_lane_runs(lane, info)
        except (RuntimeError, subprocess.SubprocessError) as exc:
            progress(f"lane {lane}: collect FAILED ({exc}); will retry next cycle")
            print(f"lane {lane}: collect failed: {exc}", file=sys.stderr)
            continue
        lane_state["collected_jobs"] = ended
        save_state(state)
        total += len(pulled)
        if pulled:
            progress(f"lane {lane}: pulled {len(pulled)} new run dir(s) into runs/")
    # recount (plan writes the manifest) and commit once per newly completed arm
    cmd_plan(argparse.Namespace(quiet=True))
    after = load_manifest()
    done_now = [r for r in after if r["status"] == "done" and before.get(row_key(r), {}).get("status") not in ("done", None)]
    # rows that were never in the old manifest but are done already (first plan) are not "completed arms" of this run
    staged = ["campaign/addendum/manifest.csv", "campaign/addendum/PROGRESS.md", "campaign/addendum/lanes"]
    for row in done_now:
        progress(f"step {row['step']} {row['condition']} {row['dataset']} {row['method']} alpha={row['alpha']} "
                 f"seed={row['seeds']}: done, {row['n_done']}/{row['n_cases_target']} cases "
                 f"(jobs {row['slurm_job_ids'] or '-'}, {row['gpu_hours_actual'] or '?'} GPU-h)")
        msg = (f"addendum: step{row['step']} {row['condition']} {row['dataset']} {row['method']} "
               f"alpha={row['alpha']} seed={row['seeds']}: {row['n_done']}/{row['n_cases_target']} cases")
        commit(msg, staged)
    if total and not done_now:
        commit(f"addendum: progress {utc_now()} ({total} runs pulled, no arm completed)", staged)
    if not args.no_push:
        pushed = git("push", "-q", "origin", "addendum-oct2026", check=False)
        if pushed.returncode != 0:
            print(f"git push failed: {pushed.stderr[-300:]}", file=sys.stderr)
    print(f"collect: {total} run dir(s) pulled, {len(done_now)} arm(s) completed")
    return 0


# ------------------------------------------------------------------ grading

MIRROR = "/scratch/billxby/lossy-addendum/mirror"
GRADES_LOCAL = ADD / "analysis" / "grades.csv"
UPLOADED = JOB_TMP / "mirror_uploaded.txt"


def local_run_rels() -> list[str]:
    """Every run dir under runs/ (campaign datasets + runs/addendum/<condition>/), relative to runs/."""
    rels = []
    for base in BASE:
        for ds in (base, f"{base}_qwen3"):
            rels += [str(p.parent.relative_to(RUNS)) for p in (RUNS / ds).glob("*/*/case_*/seed_*/run.json")]
    addendum = RUNS / "addendum"
    if addendum.is_dir():
        rels += [str(p.parent.relative_to(RUNS)) for p in addendum.glob("*/*/*/*/case_*/seed_*/run.json")]
    return sorted(rels)


def cmd_grade(args: argparse.Namespace) -> int:
    """Upload not-yet-graded runs to the Nibi mirror and submit one CPU grading job."""
    import io
    import tarfile

    graded = set()
    if GRADES_LOCAL.is_file():
        with GRADES_LOCAL.open(newline="", encoding="utf-8") as handle:
            graded = {r["relpath"] for r in csv.DictReader(handle) if r.get("verdict")}
    uploaded = set(UPLOADED.read_text().split()) if UPLOADED.is_file() else set()
    new = [r for r in local_run_rels() if r not in graded and r not in uploaded]
    if new:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            for rel in new:
                for name in ("run.json", "config.json", "output.txt"):
                    path = RUNS / rel / name
                    if path.is_file():
                        tar.add(path, arcname=f"{rel}/{name}")
        ssh(f"mkdir -p {MIRROR}/runs && cd {MIRROR}/runs && tar -xf -", input_bytes=buf.getvalue(), timeout=1800)
        UPLOADED.parent.mkdir(parents=True, exist_ok=True)
        with UPLOADED.open("a") as handle:
            handle.write("\n".join(new) + "\n")
        print(f"uploaded {len(new)} run dir(s) ({len(buf.getvalue()) / 1e6:.0f} MB) to {MIRROR}/runs")
    live = squeue_states()
    queued = ssh("squeue -u billxby -h -n add-grade -o %i", check=False).stdout.decode().split()
    if queued:
        print(f"grading job already queued/running: {' '.join(queued)}")
        return 0
    repo = LANES["A"]["repo"]
    out = ssh(f"cd {repo} && mkdir -p {MIRROR}/slurm && MIRROR={MIRROR} REPO_DIR={repo} "
              f"sbatch --parsable --output={MIRROR}/slurm/%x-%j.out cascade/cluster/addendum_grade.sbatch").stdout.decode().strip()
    progress(f"grading: uploaded {len(new)} run dir(s) to the Nibi mirror, submitted CPU grading job {out}")
    print(f"submitted grading job {out}")
    return 0


def cmd_grade_pull(args: argparse.Namespace) -> int:
    data = ssh(f"cat {MIRROR}/grades.csv", check=False).stdout
    if not data:
        print("no grades.csv on the mirror yet")
        return 1
    GRADES_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    GRADES_LOCAL.write_bytes(data)
    n = data.count(b"\n") - 1
    progress(f"grading: pulled {n} verdicts into campaign/addendum/analysis/grades.csv")
    print(f"pulled {n} verdicts -> {GRADES_LOCAL}")
    return 0


def cmd_cycle(args: argparse.Namespace) -> int:
    cmd_collect(argparse.Namespace(no_push=True))
    cmd_plan(argparse.Namespace(quiet=True))
    cmd_push(args)
    cmd_submit(args)
    cmd_plan(argparse.Namespace(quiet=True))  # statuses reflect the jobs just submitted
    commit(f"addendum: cycle {utc_now()}", ["campaign/addendum/manifest.csv", "campaign/addendum/PROGRESS.md",
                                             "campaign/addendum/lanes"])
    git("push", "-q", "origin", "addendum-oct2026", check=False)
    print_summary(load_manifest())
    return 0


ANALYSIS_PY = os.environ.get("ADDENDUM_ANALYSIS_PY", str(JOB_TMP / "venv" / "bin" / "python"))


def strict_seed1_machine(ds: str) -> str:
    """killarney / nibi / oldbox for a dataset's existing strict seed-1 runs (config.json venv path), '' if none."""
    for cfg in sorted((REPO / "runs" / ds / "strict" / "strict").glob("case_*/seed_1/config.json")):
        site = json.loads(cfg.read_text(encoding="utf-8")).get("vllm", {}).get("site_packages", "")
        if "/6101837/" in site or "/aip-hongyanz/" in site:
            return "killarney"
        return "nibi" if "/6071935/" in site or "/def-hongyanz/" in site else "oldbox"
    return ""


def cmd_add52(args: argparse.Namespace) -> int:
    """Step 5.2: once the step-5.1 grid is complete, add seed-1 rows at each cell's chosen alpha
    (scripts/addendum_tables.py best --plan), plus strict seed 1 where that dataset lacks it. A Qwen3 seed-1 arm runs
    on Killarney, so when the dataset's strict seed 1 ran elsewhere (Nibi, step 2.1) its partner is a Killarney strict
    seed 1 under runs/addendum/nibiref, and each dataset's rows share one Killarney lane (README deviation 20)."""
    done = subprocess.run([ANALYSIS_PY, str(REPO / "scripts" / "addendum_tables.py"), "best", "--plan"],
                          cwd=REPO, capture_output=True, text=True, check=True)
    plan = json.loads(done.stdout.strip().splitlines()[-1])
    state = load_state()
    extra = state.setdefault("extra_rows", [])
    have = {(e["dataset"], e["method"], e["alpha"], int(e["seed"]), e.get("condition", "main")) for e in extra}
    qwen_lane = {e["dataset"]: e["lane"] for e in extra if e["step"] == "5.2" and is_qwen(e["dataset"])}
    added = []
    for p in plan:
        arm = make_row("5.2", "main", p["dataset"], p["method"], p["alpha"], 1)
        if not missing_local(arm):  # this seed-1 pair already exists (step 2.1 / 2.2)
            continue
        lane, ref_condition = getattr(args, "lane", "A"), "main"
        if is_qwen(p["dataset"]):
            if p["dataset"] not in qwen_lane:  # round-robin over the Killarney lanes by dataset
                used = list(qwen_lane.values())
                qwen_lane[p["dataset"]] = min(QWEN3_LANES, key=lambda l: (used.count(l), QWEN3_LANES.index(l)))
            lane = qwen_lane[p["dataset"]]
            if strict_seed1_machine(p["dataset"]) not in ("killarney", ""):
                ref_condition = "nibiref"
        for method, alpha, condition in ((p["method"], p["alpha"], "main"), ("strict", "strict", ref_condition)):
            row = make_row("5.2", condition, p["dataset"], method, alpha, 1)
            key = (p["dataset"], method, alpha, 1, condition)
            if key in have or not missing_local(row):
                continue
            have.add(key)
            extra.append({"step": "5.2", "condition": condition, "dataset": p["dataset"], "method": method,
                          "alpha": alpha, "seed": 1, "lane": lane,
                          "notes": "best-setting validation" if method != "strict" else "strict seed 1 for the step-5.2 pair"})
            added.append(f"{p['dataset']}/{method}/{alpha}" + (" (nibiref)" if condition == "nibiref" else "") + f" -> {lane}")
    save_state(state)
    progress(f"step 5.2: {len(plan)} cells have an eligible best setting; added {len(added)} seed-1 row(s): {', '.join(added) or '-'}")
    print(f"added {len(added)} row(s)")
    return 0


def cmd_move_qwen3(args: argparse.Namespace) -> int:
    """Move the not-done Qwen3 rows from the Nibi lanes to the Killarney lanes (README deviation 12),
    balanced by estimated hours in lane-C order. Steps in --keep stay on Nibi (2.1: its remaining arms keep
    the step on one machine). Run right after a collect, so every finished case of a moved row is local."""
    state = load_state()
    rows = [r for r in load_manifest() if r["target"] == "qwen3-8b" and r["status"] != "done" and r["step"] not in args.keep]
    keys = {row_key(r) for r in rows}
    for lane in ("A", "B"):
        state["lanes"][lane]["rows"] = [k for k in state["lanes"][lane]["rows"] if k not in keys]
    load = {lane: sum(float(r["gpu_hours_est"] or 0) for r in load_manifest() if row_key(r) in state["lanes"][lane]["rows"])
            for lane in QWEN3_LANES}
    moved = {lane: 0 for lane in QWEN3_LANES}
    for r in sorted(rows, key=lambda r: LANE_C_PRIORITY.get(r["step"], 8)):
        if any(row_key(r) in state["lanes"][lane]["rows"] for lane in QWEN3_LANES):
            continue
        lane = min(load, key=load.get)
        state["lanes"][lane]["rows"].append(row_key(r))
        load[lane] += float(r["gpu_hours_est"] or 0)
        moved[lane] += 1
    save_state(state)
    progress(f"moved {sum(moved.values())} Qwen3 row(s) to Killarney ({', '.join(f'{l}: {n}' for l, n in moved.items())}; "
             f"est. {', '.join(f'{l} {h:.1f} GPU-h' for l, h in load.items())}); kept on Nibi: steps {', '.join(args.keep)}")
    print(f"moved {moved}; est load {load}")
    return 0


def cmd_poll(args: argparse.Namespace) -> int:
    """One iteration of the campaign loop: cycle, incremental grading, tables, RESULTS.md, commit, push."""
    cmd_cycle(args)
    try:
        cmd_grade(args)
        cmd_grade_pull(args)
    except (RuntimeError, subprocess.SubprocessError, OSError) as exc:
        progress(f"grading step failed ({exc}); retried next poll")
    if pathlib.Path(ANALYSIS_PY).exists():  # needs numpy + matplotlib (campaign_report.py)
        for sub in ("seeds", "nspec", "temp", "qwenT", "lmdraft", "aime", "best", "speedbench"):
            done = subprocess.run([ANALYSIS_PY, str(REPO / "scripts" / "addendum_tables.py"), sub], cwd=REPO,
                                  capture_output=True, text=True)
            if done.returncode != 0:
                print(f"tables {sub} failed: {done.stderr[-400:]}", file=sys.stderr)
        subprocess.run([ANALYSIS_PY, str(REPO / "scripts" / "addendum_hardware.py")], cwd=REPO, capture_output=True)
        subprocess.run([ANALYSIS_PY, str(REPO / "scripts" / "addendum_results.py")], cwd=REPO, capture_output=True)
    commit(f"addendum: tables and RESULTS.md refresh {utc_now()}", ["campaign/addendum"])
    git("push", "-q", "origin", "addendum-oct2026", check=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("poll").set_defaults(fn=cmd_poll)
    p = sub.add_parser("add52")
    p.add_argument("--lane", default="A", choices=sorted(LANES), help="Lane for the new seed-1 rows (default A: it finishes step 5.1 first).")
    p.set_defaults(fn=cmd_add52)
    p = sub.add_parser("plan"); p.add_argument("--quiet", action="store_true"); p.set_defaults(fn=cmd_plan)
    sub.add_parser("push").set_defaults(fn=cmd_push)
    sub.add_parser("submit").set_defaults(fn=cmd_submit)
    p = sub.add_parser("collect"); p.add_argument("--no-push", action="store_true"); p.set_defaults(fn=cmd_collect)
    sub.add_parser("cycle").set_defaults(fn=cmd_cycle)
    sub.add_parser("summary").set_defaults(fn=cmd_summary)
    sub.add_parser("grade").set_defaults(fn=cmd_grade)
    p = sub.add_parser("move-qwen3")
    p.add_argument("--keep", nargs="*", default=["2.1"], help="Steps whose Qwen3 rows stay on the Nibi lanes.")
    p.set_defaults(fn=cmd_move_qwen3)
    sub.add_parser("grade-pull").set_defaults(fn=cmd_grade_pull)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
