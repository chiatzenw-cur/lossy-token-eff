#!/usr/bin/env python3
"""Step 9 orchestrator (campaign/addendum/step9/GOAL.md): the five rules on the remaining datasets of the five
dedicated step-8 pairs (Phase 1), then, only if time allows, the loosest-only rows of the standalone pairs (Phase 2).
Same machinery and protocol as step 8 (scripts/step8_campaign.py, whose pair definitions -- drafter paths, mirrors,
65536-position heads, the R1 tokenizer fix, per-pair compile caches, sampler paths -- are imported unchanged); only
the datasets, the run root, the lanes and the block order differ. Runs on the Mac and drives Killarney lanes.

  python3 scripts/step9_campaign.py estimate  # block list, GPU-h per block, projected finish
  python3 scripts/step9_campaign.py plan      # manifest + per-lane work lists from what is pulled locally
  python3 scripts/step9_campaign.py push      # code, prompt sets, work lists -> lane repos / lane roots
  python3 scripts/step9_campaign.py submit    # keep each lane's 3 h Slurm chain supplied
  python3 scripts/step9_campaign.py collect   # pull finished run dirs (no-clobber) + lane journals
  python3 scripts/step9_campaign.py grade     # Nibi CPU grading mirror (the campaign's own graders)
  python3 scripts/step9_campaign.py cycle     # collect -> plan -> push -> submit -> grade -> tables -> commit
  python3 scripts/step9_campaign.py events    # newly completed blocks since the last call (one line each)

Protocol per (pair, dataset) block, as step 8 (Bill 2026-10-03, unchanged for step 9): the pair's own lossless
reference on the full case set; the five rules at their 4-point grids on case_001-003; three shared l_bar targets
at the 20/55/90th percentile of the span the five rules reach together; each rule at the grid alpha nearest each
target on the full case set (campaign_run.pick_targets_and_alphas, which adds the grid extremes as "extra" arms when
two targets share one alpha). Seed 0, N_draft 6, T 1.0, top-p 1.0, the paper's budgets, --no-trace-proposals, one
persistent server per arm. Each block is gated on its Block 0 smoke run (lossless, case_001-002, outside the run
tree) and on a by-hand look at those outputs (state.json block0_passed).

Run layout: runs/addendum/step9/<pair>/<dataset>/<method>/<params>/case_NNN/seed_0/ (the step-8 trees are never
touched; a full arm's item lists only case_004 on, as in step 8).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import pathlib
import re
import shlex
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import addendum_campaign as ac  # noqa: E402
import step8_campaign as s8  # noqa: E402
from campaign_run import (  # noqa: E402
    ALPHA_GRIDS, MODEL_FAMILIES, TOKEN_BUDGETS, base_dataset, model_flags, pick_targets_and_alphas,
)

S9 = REPO / "campaign" / "addendum" / "step9"
MANIFEST = S9 / "manifest.csv"
STATE = S9 / "state.json"
LANES_DIR = S9 / "lanes"
GRADES = S9 / "grades.csv"
CALIB_DIR = REPO / "campaign" / "calibration"
RUN_SUBROOT = "runs/addendum/step9"
B0_SUBROOT = "runs/addendum/step9_block0"
FIVE = ac.FIVE
N_CASES = {**s8.N_CASES, "humaneval": 150, "longbench_v2": 150}
CALIB_CASES = s8.CALIB_CASES
SMOKE_CASES = ["case_001", "case_002"]
LOOSEST = s8.LOOSEST
KP, HF_LOCAL = ac.KILLARNEY_PROJECT, s8.HF_LOCAL
ET = dt.timezone(dt.timedelta(hours=-4))  # EDT
DEADLINE = dt.datetime(2026, 10, 9, 18, 0, tzinfo=ET)        # all blocks done and tables written
PHASE2_CUTOFF = dt.datetime(2026, 10, 8, 18, 0, tzinfo=ET)    # Phase 2 only if Phase 1 is done before this

# Killarney H100 lanes: K1-K8 are step 8's lane repos (each its own repo + patched .venv-vllm: patches are mutually
# exclusive on one installed file); K9-K16 are copies of K8 made for step 9 (README deviation 41). Killarney gives
# every job a private /tmp and stop_server.sh is job-scoped, so lanes may share a node (README deviation 15).
NP = ac.NIBI_PROJECT
N_LANES = 16
LANES: dict[str, dict] = {
    f"K{n}": {"host": "killarney", "account": "aip-hongyanz", "project": KP,
              "repo": f"{KP}/lossy-token-eff" + ("" if n == 1 else f"-lane{n}"),
              "root": f"/scratch/billxby/step9/laneK{n}", "exclude": ""} for n in range(1, N_LANES + 1)}
# Nibi H100 lanes (README deviation 42): N1/N2 are the addendum's lane repos A/B, N3/N4 copies of B (N4 on /scratch:
# /project holds 500K files). Nibi has no per-job /tmp and the patched samplers read per-user /tmp knob files, so two
# lanes must never share a node: each lane gets a disjoint set of the whole-H100 nodes g1-g29 (g30-g37 are
# MIG-partitioned; a gpu:h100 request never lands there).
LANES.update({
    "N1": {"host": "nibi", "account": "def-hongyanz_gpu", "project": NP, "repo": f"{NP}/lossy-token-eff",
           "root": "/scratch/billxby/step9/laneN1", "exclude": "g[8-37]"},
    "N2": {"host": "nibi", "account": "def-hongyanz_gpu", "project": NP, "repo": f"{NP}/lossy-token-eff-lane2",
           "root": "/scratch/billxby/step9/laneN2", "exclude": "g[1-7,15-37]"},
    "N3": {"host": "nibi", "account": "def-hongyanz_gpu", "project": NP, "repo": f"{NP}/lossy-token-eff-lane3",
           "root": "/scratch/billxby/step9/laneN3", "exclude": "g[1-14,22-37]"},
    "N4": {"host": "nibi", "account": "def-hongyanz_gpu", "project": NP,
           "repo": "/scratch/billxby/step9/repos/lossy-token-eff-lane4",
           "root": "/scratch/billxby/step9/laneN4", "exclude": "g[1-21]"},
})
STATIC_READY = {"K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "N1", "N2"}  # lane repos that predate step 9
HOSTS = ("killarney", "nibi")
MAX_CHAIN, JOB_TIME, JOB_HOURS = 3, "3:00:00", 3.0
STARTUP_H = 0.12  # per arm: stop + patch switch (self-test) + server start; step-8 calibration items took ~7 min
# Seconds per case on a Killarney/Nibi H100, for the work estimates only: the addendum's lane journals for GPT-OSS
# (nebius head) and Qwen3 (EAGLE-3) on these datasets (aime24 35-39, humaneval 3.7, longbench_v2 7.0 / 101, 17, 24),
# scaled by step 8's own per-case times of each pair on GSM8K / LiveCodeBench (DSpark ~0.67x Qwen3's EAGLE-3; the
# RH GPT-OSS head ~1.1x nebius; Llama answers short but its loose cactus / r_fuzzy arms run to the token cap;
# R1-Distill's head stops drafting past ~2048 positions, so its long answers run near 1 token per round).
T_CASE = {
    "gpt_oss_20b": {"aime24": 40, "humaneval": 4.5, "longbench_v2": 7.5, "mtbench": 5.8},
    "qwen3": {"aime24": 70, "humaneval": 12, "longbench_v2": 18, "mtbench": 7.6},
    "llama31": {"aime24": 35, "humaneval": 6, "longbench_v2": 9, "mtbench": 6.3},
    "r1llama": {"aime24": 75, "humaneval": 28, "longbench_v2": 35, "mtbench": 6.3},
}

P_GPT, P_QWEN, P_L3, P_L1, P_R1 = ("gpt-oss-20b__rh-eagle3", "qwen3-8b__dspark", "llama31-8b-instruct__eagle3",
                                   "llama31-8b-instruct__eagle1", "r1-distill-llama-8b__eagle3")
# (block, pair, base dataset) in Bill's order (GOAL.md): 1 GPT-OSS AIME24, 2 Qwen3 AIME24, 3 every pair on
# LongBench-v2, 4 every pair on HumanEval, 5 the Llama-3.1 heads on AIME24 (R1-Distill already has AIME24, MT-Bench /
# GSM8K / LiveCodeBench are step 8's)
BLOCKS = [("1", P_GPT, "aime24"), ("2", P_QWEN, "aime24"),
          ("3a", P_GPT, "longbench_v2"), ("3b", P_QWEN, "longbench_v2"), ("3c", P_L3, "longbench_v2"),
          ("3d", P_L1, "longbench_v2"), ("3e", P_R1, "longbench_v2"),
          ("4a", P_GPT, "humaneval"), ("4b", P_QWEN, "humaneval"), ("4c", P_L3, "humaneval"),
          ("4d", P_L1, "humaneval"), ("4e", P_R1, "humaneval"),
          ("5a", P_L3, "aime24"), ("5b", P_L1, "aime24")]
PHASE1 = [b for b, _, _ in BLOCKS]
# Phase 2 (GOAL.md; planned only once state.json phase2 is set, i.e. Phase 1 ended before 2026-10-08 18:00 ET): the
# standalone pairs at each rule's loosest grid alpha + lossless, like their existing rows, pair by pair in Bill's
# order, each on HumanEval, LongBench-v2, MT-Bench, AIME24 in that order. Qwen3-8B + Qwen3-0.6B is the addendum's
# step-4.3 pair (tables/lmdraft__*), defined here as a step-8-style pair with a compile cache of its own (deviation 34).
P_Q17, P_Q06, P_PE, P_L1B, P_R1B = ("qwen3-8b__qwen3-1.7b", "qwen3-8b__qwen3-0.6b", "qwen3-8b__peagle",
                                    "llama31-8b-instruct__llama32-1b", "r1-distill-llama-8b__llama32-1b")
PHASE2_PAIRS = [P_Q17, P_Q06, P_PE, P_L1B, P_R1B]
PHASE2_DATASETS = ["humaneval", "longbench_v2", "mtbench", "aime24"]
BLOCKS += [(f"{6 + i}{'abcd'[j]}", pid, base) for i, pid in enumerate(PHASE2_PAIRS)
           for j, base in enumerate(PHASE2_DATASETS)]
PHASE2 = [b for b, _, _ in BLOCKS if b not in PHASE1]
BLOCK_ORDER = {b: i for i, (b, _, _) in enumerate(BLOCKS)}
BLOCK_OF = {(pid, base): b for b, pid, base in BLOCKS}
# the projection rule (GOAL.md): if the projection misses the deadline, drop the HumanEval blocks first, then the
# Llama AIME24 blocks. block -> reason
DROPPED: dict[str, str] = {}
PAIRS = {p["id"]: p for p in s8.PAIRS}
PAIRS[P_Q06] = s8.pair("P2", "qwen3", "qwen3-0.6b", "Qwen/Qwen3-0.6B", "draft_model", "standalone",
                       PHASE2_DATASETS, "killarney")
KIND = {b: ("dedicated" if b in PHASE1 else "standalone") for b, _, _ in BLOCKS}
# seconds per case of the standalone drafters (step 8 Blocks 2, 3, 5, 7 on GSM8K / LiveCodeBench against the
# dedicated heads of the same target), for the estimates only
T_CASE_PAIR = {
    P_Q17: {"aime24": 105, "humaneval": 18, "longbench_v2": 27, "mtbench": 11},
    P_Q06: {"aime24": 100, "humaneval": 17, "longbench_v2": 26, "mtbench": 10},
    P_PE: {"aime24": 85, "humaneval": 14, "longbench_v2": 22, "mtbench": 9},
    P_L1B: {"aime24": 25, "humaneval": 3.5, "longbench_v2": 7, "mtbench": 5},
    P_R1B: {"aime24": 75, "humaneval": 25, "longbench_v2": 25, "mtbench": 7},
}
# Every block runs whole on one cluster (lossless and all arms on one node type, as step 8), and so does every pair's
# set of step-9 blocks. Both clusters' H100 queues were deep at launch (2026-10-05 ~19:30Z: Killarney estimated 1-4 h,
# Nibi ~9 h for our next job), so the two Llama-3.1 heads, whose models Nibi already held, run there (README deviation
# 42); GPT-OSS + RH head, Qwen3 + DSpark and R1-Distill run on Killarney with step 8's warm compile caches.
# 2026-10-05 ~22:00Z: Nibi's start estimate for the warm-up job slipped to 2026-10-08 13:00 while all 16 Killarney
# lanes ran; the Llama blocks (no run yet) moved to Killarney too (README deviation 42)
NIBI_PAIRS: set[str] = set()
BLOCK_HOST = {b: ("nibi" if pid in NIBI_PAIRS else "killarney") for b, pid, _ in BLOCKS}
# DSpark's config stops at 40960 positions (plain RoPE, theta 1e6); Qwen3's longest LongBench-v2 sequence is 51234 +
# 8192. This copy differs only in max_position_embeddings = 65536 (weights symlinked, sha256 5c922d1f...), with a
# compile cache of its own (README deviation 40, as deviations 19 and 31). Only LongBench-v2 uses it.
DSPARK_LONG = f"{HF_LOCAL}/dspark_qwen3_8b_block7-maxpos65536"
OVERRIDES = {(P_QWEN, "longbench_v2"): {
    "drafter_path": DSPARK_LONG,
    "env": {"VLLM_CACHE_ROOT": "/scratch/billxby/vllm_cache_step8/qwen3-8b__dspark-maxpos65536"}}}
# Phase 2: Qwen3-1.7B, Qwen3-0.6B and the P-EAGLE head declare 40960 positions too (plain RoPE): the same kind of
# copy for LongBench-v2 only, each with a cache of its own (README deviation 40)
for _pid, _name in ((P_Q17, "Qwen3-1.7B"), (P_Q06, "Qwen3-0.6B"), (P_PE, "Qwen3-8B-speculator.peagle")):
    OVERRIDES[(_pid, "longbench_v2")] = {
        "drafter_path": f"{HF_LOCAL}/{_name}-maxpos65536",
        "env": {"VLLM_CACHE_ROOT": f"/scratch/billxby/vllm_cache_step8/{_pid}-maxpos65536"}}


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def pair_cfg(pid: str, base: str, host: str = "killarney") -> dict:
    """The step-8 pair, with step 9's per-dataset overrides; on Nibi the local head copies live under Nibi's project
    (same files: config sha256 and weight sha256 checked in BLOCK0.md) and every pair compiles into a Nibi cache of its
    own (warmed by cmd_warm before any measured arm, README deviation 35)."""
    p = PAIRS[pid]
    o = OVERRIDES.get((pid, base), {})
    cfg = {**p, "drafter_path": o.get("drafter_path", p["drafter_path"]), "env": {**p["env"], **o.get("env", {})}}
    if host == "nibi":
        cfg["drafter_path"] = cfg["drafter_path"].replace(KP, NP)
        cfg["env"] = {k: (v.replace(KP, NP) if isinstance(v, str) else v) for k, v in cfg["env"].items()}
        cfg["env"]["VLLM_CACHE_ROOT"] = f"/scratch/billxby/vllm_cache_step9/{pid}"
    return cfg


def block_host(block: str) -> str:
    return BLOCK_HOST[block]


def ds_of(pid: str, base: str) -> str:
    return base + s8.SUFFIX[PAIRS[pid]["family"]]


def run_dir(pid: str, ds: str, method: str, alpha: str, case: str, subroot: str = RUN_SUBROOT) -> pathlib.Path:
    return REPO / subroot / pid / ds / method / s8.params_dir(method, alpha) / case / "seed_0"


def calib_path(pid: str, base: str) -> pathlib.Path:
    p = PAIRS[pid]
    return CALIB_DIR / f"{base}_{p['family']}_{p['slug']}.json"


def make_item(block: str, pid: str, base: str, method: str, alpha: str, stage: str, case_list: list[str],
              subroot: str = RUN_SUBROOT, prefix: str = "s9") -> dict:
    host = block_host(block)
    p = pair_cfg(pid, base, host)
    ds = ds_of(pid, base)
    target, _, served, rope = MODEL_FAMILIES[p["family"]]
    return {
        "id": f"{prefix}|{pid}|{ds}|{method}|{alpha}|{stage}",
        "step": f"9.{block}", "condition": f"step9/{pid}", "dataset": ds, "method": method,
        "alpha": alpha, "seed": 0, "cases": case_list, "prompt_root": f"prompts/{ds}",
        "runs_subroot": f"{subroot}/{pid}", "max_new_tokens": TOKEN_BUDGETS[ds],
        "model_flags": model_flags(target, p["drafter_path"], served, rope),
        "num_spec": 6, "temperature": 1.0, "top_p": 1.0, "env": {"SPEC_METHOD": p["spec"], **p["env"]},
        "host": host,
        # 3 of the first 88 servers (kn175, kn176) hung after their engine came up and never answered /health; a
        # healthy start takes 5-9 min (cold compile included), so give up after 20 min, not the default 30 (the
        # lane retries the item; no run is affected)
        "extra_flags": ["--startup-timeout", "1200"],
    }


def smoke_item(block: str) -> dict:
    """Block 0: lossless on case_001-002, on the block's own cluster (the run dir names it, so a smoke run on the other
    cluster never counts), outside the step-9 run tree."""
    _, pid, base = BLOCKS[BLOCK_ORDER[block]]
    return make_item(block, pid, base, "strict", "strict", "smoke", SMOKE_CASES,
                     subroot=f"{B0_SUBROOT}/{block_host(block)}", prefix="b0")


def item_missing(item: dict) -> list[str]:
    pid = item["id"].split("|")[1]
    sub = item["runs_subroot"].rsplit("/", 1)[0]
    return [c for c in item["cases"]
            if not s8.run_ok(run_dir(pid, item["dataset"], item["method"], item["alpha"], c, sub))]


def smoke_done(block: str) -> bool:
    return not item_missing(smoke_item(block))


def calibrate(block: str) -> dict | None:
    """Targets and chosen alphas once all 20 calibration arms are pulled; None while any is missing."""
    _, pid, base = BLOCKS[BLOCK_ORDER[block]]
    ds = ds_of(pid, base)
    grid: dict[str, list[tuple[float, float]]] = {}
    for method in FIVE:
        pts = []
        for alpha in ALPHA_GRIDS[method]:
            lbars = []
            for case in CALIB_CASES:
                run = s8.run_ok(run_dir(pid, ds, method, s8.fmt(alpha), case))
                if run is None:
                    return None
                lbars.append(run.get("l_bar"))
            lbars = [x for x in lbars if x is not None]
            if lbars:
                pts.append((alpha, sum(lbars) / len(lbars)))
        grid[method] = pts
    targets, chosen = pick_targets_and_alphas(grid, 3)
    p = pair_cfg(pid, base, block_host(block))
    out = calib_path(pid, base)
    record = {
        "step": "9", "block": block, "host": block_host(block), "dataset": ds, "pair": pid,
        "target": MODEL_FAMILIES[p["family"]][0],
        "drafter": p["drafter"], "drafter_path": p["drafter_path"], "spec_method": p["spec"],
        "probe_cases": CALIB_CASES, "full_cases": s8.cases(N_CASES[base]), "max_new_tokens": TOKEN_BUDGETS[ds],
        "alpha_grids": {m: ALPHA_GRIDS[m] for m in FIVE},
        "grid_results": {m: [{"alpha": a, "mean_l_bar": l} for a, l in pts] for m, pts in grid.items()},
        "targets_l_bar": targets, "chosen_alphas": chosen,
        "rule": "campaign_run.pick_targets_and_alphas (20/55/90th percentile of the shared span, nearest grid alpha)",
    }
    if out.is_file():
        old = json.loads(out.read_text(encoding="utf-8"))
        if old.get("step") != "9":  # a calibration file this step did not write is never replaced
            raise SystemExit(f"{out.relative_to(REPO)} exists and is not step 9's")
        if old.get("chosen_alphas") == chosen:
            return record
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    ac.progress(f"step 9 block {block}: calibrated {pid} {ds}: targets {[round(t, 3) for t in targets]}, "
                + ", ".join(f"{m} {chosen[m]}" for m in FIVE))
    return record


STAGE_RANK = {"smoke": 0, "calib": 1, "strict": 2, "full": 3}


def block_items(block: str, state: dict) -> list[dict]:
    """The block's work: its smoke item until Block 0 passed it, then lossless + calibration + (once calibrated) the
    full arms."""
    _, pid, base = BLOCKS[BLOCK_ORDER[block]]
    if block not in state.get("block0_passed", []):
        return [smoke_item(block)]
    n = N_CASES[base]
    items = [make_item(block, pid, base, "strict", "strict", "strict", s8.cases(n))]
    if KIND[block] == "standalone":  # Phase 2: each rule at its loosest grid alpha on the full case set
        return items + [make_item(block, pid, base, m, s8.fmt(LOOSEST[m]), "full", s8.cases(n)) for m in FIVE]
    for method in FIVE:
        for alpha in ALPHA_GRIDS[method]:
            items.append(make_item(block, pid, base, method, s8.fmt(alpha), "calib", CALIB_CASES))
    record = calibrate(block)
    if record:
        for method in FIVE:
            for alpha in record["chosen_alphas"][method]:
                items.append(make_item(block, pid, base, method, s8.fmt(alpha), "full",
                                       s8.cases(n, start=len(CALIB_CASES) + 1)))
    return items


def t_case(pid: str, base: str) -> float:
    return T_CASE_PAIR.get(pid, T_CASE[PAIRS[pid]["family"]])[base]


def est_hours(item: dict, n_missing: int) -> float:
    pid = item["id"].split("|")[1]
    return STARTUP_H + t_case(pid, base_dataset(item["dataset"])) * n_missing / 3600 if n_missing else 0.0


# The block formula below, fed step 8's own per-case times, gives 47.7 GPU-h for step-8 Block 1 (R1-Distill + EAGLE-3,
# four datasets incl. AIME24; actual 34.0) and 20.9 for Block 4 (GPT-OSS-20B + RH head, three datasets; actual 16.9):
# per-case times measured over whole items already carry part of the server starts. Estimates are scaled by the
# pooled ratio, (34.0 + 16.9) / (47.7 + 20.9) = 0.74 (GOAL.md: "use step-8 actuals").
STEP8_SCALE = 0.74


def block_estimate(block: str) -> float:
    """GPU-h of a whole block before any of it runs: lossless + 20 calibration arms + the full arms (14, the mean of
    step 8's dedicated blocks: 12-15 distinct alphas over the five rules), scaled to step 8's actuals."""
    _, pid, base = BLOCKS[BLOCK_ORDER[block]]
    t, n = t_case(pid, base), N_CASES[base]
    if KIND[block] == "standalone":  # lossless + five loosest arms, no calibration
        return STEP8_SCALE * 6 * (STARTUP_H + n * t / 3600)
    raw = (STARTUP_H + n * t / 3600) + 20 * (STARTUP_H + 3 * t / 3600) + 14 * (STARTUP_H + (n - 3) * t / 3600)
    return STEP8_SCALE * raw


def load_state() -> dict:
    if STATE.is_file():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"assign": {}, "lanes": {lane: {"jobs": []} for lane in LANES}, "block0_passed": [], "reported": []}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def active_blocks(state: dict | None = None) -> list[str]:
    """Phase 1 blocks not dropped, then Phase 2 blocks once state.json phase2 is set."""
    phase2 = bool((state or load_state()).get("phase2"))
    return [b for b, _, _ in BLOCKS if b not in DROPPED and (b in PHASE1 or phase2)]


def journal_hours() -> dict[str, float]:
    """item id -> GPU-h actual: the item wall time (item_end elapsed_s) summed over the lane journals, as step 8."""
    hours: dict[str, float] = {}
    for path in sorted(LANES_DIR.glob("*_status.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("event") == "item_end":
                hours[r["item"]] = hours.get(r["item"], 0.0) + float(r.get("elapsed_s") or 0) / 3600
    return hours


def journal_jobs() -> dict[str, set[str]]:
    jobs: dict[str, set[str]] = {}
    for path in sorted(LANES_DIR.glob("*_status.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("event") == "item_start":
                jobs.setdefault(r["item"], set()).add(str(r.get("job", "")))
    return jobs


def cmd_plan(args: argparse.Namespace) -> int:
    state = load_state()
    assign: dict[str, str] = state["assign"]
    planned = []
    for block in active_blocks(state):
        for item in block_items(block, state):
            missing = item_missing(item)
            planned.append((block, item, missing, est_hours(item, len(missing))))
    hours_actual, jobs = journal_hours(), journal_jobs()
    load = {lane: 0.0 for lane in LANES}
    for block, item, missing, hours in planned:
        # an item whose block moved cluster is reassigned (its old lane root holds none of its runs: the smoke run
        # dirs name the cluster, and a block only moves before its first measured run)
        if item["id"] in assign and LANES[assign[item["id"]]]["host"] != item["host"]:
            del assign[item["id"]]
        # only an item that has started stays on its lane (its partial runs live in that lane root); the others are
        # placed afresh every cycle (the journals were pulled just before), so work follows the lanes that run
        if item["id"] in assign and item["id"] not in jobs and missing:
            del assign[item["id"]]
        if item["id"] in assign and missing:
            load[assign[item["id"]]] += hours
    # unstarted items in priority order (block, then stage) to the lane of the block's cluster with the least work,
    # counting a lane whose job is still queued as 2 GPU-h busier (4 with no job): lanes that run take the earliest
    # blocks. Lanes that exist only: K9-K16 and N3-N4 once their copy is checked (lane_ready).
    ready = [l for l in LANES if l in STATIC_READY or l in state.get("lanes_ready", [])]
    job_states = {l: {j.get("state") for j in state["lanes"].get(l, {}).get("jobs", [])} for l in LANES}
    wait = {l: 0.0 if "RUNNING" in job_states[l] else 2.0 if job_states[l] & {"PENDING", "CONFIGURING"} else 4.0
            for l in LANES}
    # Block 0 smoke items first (two cases each, and they gate their whole block), then by block and stage
    order = lambda t: (t[1]["id"].startswith("b0|") is False, BLOCK_ORDER[t[0]], STAGE_RANK[t[1]["id"].rsplit("|", 1)[1]], -t[3])
    for block, item, missing, hours in sorted(planned, key=order):
        if item["id"] not in assign and missing:
            lane = min((l for l in ready if LANES[l]["host"] == item["host"]),
                       key=lambda l: (load[l] + wait[l], l[0], int(l[1:])))
            assign[item["id"]] = lane
            load[lane] += hours
    rows, per_lane = [], {lane: [] for lane in LANES}
    for block, item, missing, hours in planned:
        _, pid, base = BLOCKS[BLOCK_ORDER[block]]
        p = pair_cfg(pid, base, item["host"])
        lane = assign.get(item["id"], "")
        if missing and lane:
            per_lane[lane].append((block, item))
        rows.append({
            "block": block, "host": item["host"], "pair": pid,
            "target": s8.CANONICAL.get(MODEL_FAMILIES[p["family"]][0], MODEL_FAMILIES[p["family"]][0]),
            "drafter": s8.CANONICAL.get(p["drafter"], p["drafter"]), "drafter_path": p["drafter_path"],
            "spec_method": p["spec"], "drafter_family": p["drafter_family"], "sampler_path": p["sampler"],
            "dataset": item["dataset"], "method": item["method"], "alpha": item["alpha"], "beta": "",
            "stage": item["id"].rsplit("|", 1)[1], "n_cases": len(item["cases"]),
            "n_done": len(item["cases"]) - len(missing), "status": "done" if not missing else "pending",
            "lane": lane, "slurm_job_ids": " ".join(sorted(jobs.get(item["id"], set()))),
            "gpu_hours_est": f"{hours:.2f}", "gpu_hours_actual": f"{hours_actual.get(item['id'], 0.0):.2f}",
        })
    S9.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    LANES_DIR.mkdir(parents=True, exist_ok=True)
    for lane, entries in per_lane.items():
        host = LANES[lane]["host"]
        # a lane out of work keeps its GPU 30 min while its cluster still has work that has not started (the next
        # cycle places some on it) or a calibration / Block 0 check about to release more
        waiting = any(r["host"] == host and r["status"] != "done" and (r["stage"] in ("calib", "smoke") or
                                                                     not r["slurm_job_ids"]) for r in rows)
        entries.sort(key=lambda e: (not e[1]["id"].startswith("b0|"), BLOCK_ORDER[e[0]],
                                    STAGE_RANK[e[1]["id"].rsplit("|", 1)[1]]))
        # README deviation 43: FlashInfer JIT-builds its sampling module into ~/.cache/flashinfer under one file lock,
        # and its build.ninja names the lane's own venv, so 16 lanes kept rebuilding it in turn (servers hung >20 min
        # in warmup). A workspace per lane: built once per lane from the same sources and flags, then loaded.
        fi_env = {"FLASHINFER_WORKSPACE_BASE": f"/scratch/billxby/step9/flashinfer/{lane}"}
        work = {"items": [{**e[1], "env": {**e[1]["env"], **fi_env}} for e in entries],
                "hold_minutes": 30 if waiting else 0}
        (LANES_DIR / f"{lane}.json").write_text(json.dumps(work, indent=1) + "\n", encoding="utf-8")
    save_state(state)
    if not getattr(args, "quiet", False):
        print_summary(rows, load)
    return 0


def block_rows(rows: list[dict]) -> dict[str, dict]:
    by: dict[str, dict] = {}
    for r in rows:
        d = by.setdefault(r["block"], {"done": 0, "total": 0, "left": 0.0, "actual": 0.0, "stages": set(),
                                        "pair": r["pair"], "dataset": r["dataset"]})
        d["done"] += int(r["n_done"])
        d["total"] += int(r["n_cases"])
        d["left"] += float(r["gpu_hours_est"])
        d["actual"] += float(r.get("gpu_hours_actual") or 0)
        d["stages"].add(r["stage"])
    return by


def print_summary(rows: list[dict], load: dict | None = None) -> None:
    by = block_rows(rows)
    for block, _, _ in BLOCKS:
        if block in DROPPED:
            print(f"block {block:3s} DROPPED: {DROPPED[block]}")
            continue
        d = by.get(block)
        if not d:
            continue
        stage = "block 0 smoke" if "smoke" in d["stages"] else ("full arms planned" if "full" in d["stages"]
                                                                 else "lossless + calibration")
        print(f"block {block:3s} {d['pair']:30s} {d['dataset']:22s} {d['done']:5d}/{d['total']:5d} runs "
              f"({stage}), ~{d['left']:.1f} GPU-h left, {d['actual']:.1f} used")
    if load:
        print("lane load (GPU-h): " + ", ".join(f"{l} {h:.1f}" for l, h in load.items() if h))


def read_manifest() -> list[dict]:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def cmd_summary(args: argparse.Namespace) -> int:
    print_summary(read_manifest())
    return 0


def cmd_estimate(args: argparse.Namespace) -> int:
    """GOAL.md: the block list with a GPU-h estimate per block and the projected finish (at --lanes concurrent lanes,
    --duty of their wall time spent running)."""
    rate = args.lanes * args.duty
    for phase, blocks in (("Phase 1", PHASE1), ("Phase 2", PHASE2)):
        total = 0.0
        print(f"{phase}\n{'block':6s} {'cluster':10s} {'pair':32s} {'dataset':14s} {'GPU-h':>6s}  cumulative")
        for block, pid, base in BLOCKS:
            if block not in blocks:
                continue
            h = block_estimate(block)
            if block in DROPPED:
                print(f"{block:6s} {block_host(block):10s} {pid:32s} {base:14s} {h:6.1f}  (dropped: {DROPPED[block]})")
                continue
            total += h
            print(f"{block:6s} {block_host(block):10s} {pid:32s} {base:14s} {h:6.1f}  {total:6.1f}")
        print(f"{phase} total ~{total:.0f} GPU-h; at {args.lanes:g} lanes x {args.duty:.0%} duty = {rate:.1f} GPU-h/h: "
              f"~{total / rate:.1f} h of wall time")
    print(f"deadline {DEADLINE:%a %b %d %H:%M} ET; Phase 2 only if Phase 1 ends before {PHASE2_CUTOFF:%a %b %d %H:%M} ET")
    return 0


# ------------------------------------------------------------------ push / submit / collect

PUSH_FILES = s8.PUSH_FILES


def prompt_sets() -> list[str]:
    active = set(active_blocks())
    return sorted({f"prompts/{ds_of(pid, base)}" for b, pid, base in BLOCKS if b in active})


TOOLS = "/scratch/billxby/step9"           # sync_prompt_sets.py (same path on both clusters)
STAGE = f"{TOOLS}/prompts_stage"          # one verified copy of every step-9 prompt set per cluster


def sync_prompts(state: dict, lanes: list[str], host: str) -> list[str]:
    """Every lane repo's prompt sets byte-identical to the committed ones (digest per set), copied on the cluster
    from STAGE (scripts/sync_prompt_sets.py); a set missing or stale in STAGE is sent there from the Mac first (the
    Mac's link to Killarney ran at ~60 KB/s on 2026-10-05: ~85 MB per lane took >10 min). Returns the lanes whose
    sets are verified."""
    local = {rel: ac.prompt_digest(rel) for rel in prompt_sets()}
    key = json.dumps(local, sort_keys=True)
    synced = state.setdefault("prompts_synced", {})
    todo = [lane for lane in lanes if synced.get(lane) != key]
    if not todo:
        return lanes
    ac.ssh(f"mkdir -p {TOOLS} && cat > {TOOLS}/sync_prompt_sets.py",
           input_bytes=(REPO / "scripts" / "sync_prompt_sets.py").read_bytes(), host=host)
    repos = " ".join(shlex.quote(LANES[lane]["repo"]) for lane in todo)
    report: dict = {}
    for attempt in range(2):
        proc = ac.ssh(f"cd {TOOLS} && python3 sync_prompt_sets.py {STAGE} {repos}", input_bytes=key.encode(),
                      check=False, host=host, timeout=3600)
        report = json.loads(proc.stdout.decode() or "{}")
        bad_stage = sorted({rel for r in report.values() for rel, v in r.items() if v == "stage-mismatch"})
        if not bad_stage or attempt:
            break
        data = subprocess.run(["tar", "-cf", "-", *bad_stage], cwd=REPO, capture_output=True, check=True,
                              env={"COPYFILE_DISABLE": "1", "PATH": "/usr/bin:/bin"}).stdout
        ac.ssh(f"mkdir -p {STAGE} && cd {STAGE} && rm -rf {' '.join(bad_stage)} && tar -xf -", input_bytes=data,
               host=host, timeout=3600)
    for lane in todo:
        r = report.get(LANES[lane]["repo"], {})
        if r and all(v in ("ok", "replaced") for v in r.values()):
            synced[lane] = key
            replaced = [rel for rel, v in r.items() if v == "replaced"]
            if replaced:
                print(f"lane {lane}: prompt sets replaced from stage: {', '.join(replaced)}")
        else:
            print(f"lane {lane}: prompt sets NOT verified: {r}")
    return [lane for lane in lanes if synced.get(lane) == key]


def lane_order(lane: str) -> tuple:
    return (lane[0], int(lane[1:]))


def cmd_push(args: argparse.Namespace) -> int:
    files = [f for f in PUSH_FILES if (REPO / f).is_file()]
    env = {"COPYFILE_DISABLE": "1", "PATH": "/usr/bin:/bin"}
    code = subprocess.run(["tar", "-cf", "-", *files], cwd=REPO, capture_output=True, check=True, env=env).stdout
    state = load_state()
    verified = set(state.get("prompts_verified_lanes", []))
    for host in HOSTS:
        if not ac.reachable(host):
            print(f"{host} unreachable: not pushed")
            continue
        lanes = [lane for lane in LANES if LANES[lane]["host"] == host
                 and (getattr(args, "all_lanes", False) or lane_ready(lane, state))]
        ok = set(sync_prompts(state, lanes, host))
        verified = (verified - set(lanes)) | ok
        sent = state.setdefault("pushed", {})
        code_digest = __import__("hashlib").sha256(code).hexdigest()
        for lane in lanes:
            info = LANES[lane]
            # a lane whose prompt sets are not verified gets no work (its runs would use other prompts)
            work = (LANES_DIR / f"{lane}.json").read_bytes() if lane in ok else b'{"items": [], "hold_minutes": 0}\n'
            work_digest = __import__("hashlib").sha256(work).hexdigest()
            last = sent.get(lane, {})
            if last.get("code") != code_digest:  # unchanged code and work lists are not resent (slow Killarney link)
                ac.ssh(f"cd {shlex.quote(info['repo'])} && tar -xf -", input_bytes=code, host=host)
            if last.get("work") != work_digest:
                root = shlex.quote(info["root"])
                ac.ssh(f"mkdir -p {root}/slurm && cat > {root}/work.json.tmp && mv {root}/work.json.tmp {root}/work.json",
                       input_bytes=work, host=host)
            if last != {"code": code_digest, "work": work_digest}:
                print(f"pushed to lane {lane}: " + ("code + " if last.get("code") != code_digest else "")
                      + f"work list ({len(json.loads(work)['items'])} items)")
            sent[lane] = {"code": code_digest, "work": work_digest}
    state["prompts_verified_lanes"] = sorted(verified, key=lane_order)
    save_state(state)
    return 0


def lane_ready(lane: str, state: dict) -> bool:
    """K9-K16 and N3-N4 exist once their copy finished (lanecopy.log / nibi_setup.log in /scratch/billxby/step9);
    checked once, then remembered."""
    if lane in STATIC_READY:
        return True
    ready = state.setdefault("lanes_ready", [])
    if lane in ready:
        return True
    repo = LANES[lane]["repo"]
    ok = ac.ssh(f"test -x {shlex.quote(repo)}/.venv-vllm/bin/python && test -d {shlex.quote(repo)}/scripts",
                check=False, host=LANES[lane]["host"]).returncode == 0
    if ok:
        ready.append(lane)
    return ok


def squeue(host: str) -> dict[str, str] | None:
    out = ac.ssh("bash -lc 'squeue -u billxby -h -o \"%i %T\"'", host=host, check=False, timeout=180)
    if out.returncode != 0:
        return None
    return dict(line.split()[:2] for line in out.stdout.decode().splitlines() if line.strip())


def sbatch(info: dict, lane: str, dep: str) -> str:
    cmd = (f"cd {shlex.quote(info['repo'])} && mkdir -p {info['root']}/slurm && "
           f"LANE={lane} REPO_DIR={shlex.quote(info['repo'])} LANE_ROOT={info['root']} PROJECT_DIR={info['project']} "
           f"sbatch --parsable --job-name=s9-{lane} --account={info['account']} "
           + (f"--exclude={info['exclude']} " if info["exclude"] else "")
           + f"--time={JOB_TIME} --output={info['root']}/slurm/%x-%j.out {dep}cascade/cluster/addendum_lane.sbatch")
    out = ac.ssh(f"bash -lc {shlex.quote(cmd)}", host=info["host"]).stdout.decode().strip().splitlines()[-1]
    return out.split(";")[0].strip()


def cmd_submit(args: argparse.Namespace) -> int:
    state = load_state()
    rows = read_manifest()
    for host in HOSTS:
        live = squeue(host)
        if live is None:
            print(f"{host} unreachable: nothing submitted")
            continue
        warm = state.get("warm", {}).get(host)
        # while the cluster has unfinished work every lane keeps a job queued, assigned items or not: a lane whose job
        # starts holds its GPU (hold_minutes) and the next cycle places unstarted items on it (cmd_plan)
        host_pending = any(r["host"] == host and r["status"] != "done" for r in rows)
        for lane, info in LANES.items():
            if info["host"] != host:
                continue
            jobs = state["lanes"].setdefault(lane, {"jobs": []})["jobs"]
            for job in jobs:
                job["state"] = live.get(job["id"], "ENDED")
            active = [j for j in jobs if j["state"] in ("PENDING", "RUNNING", "CONFIGURING", "COMPLETING")]
            remaining = sum(float(r["gpu_hours_est"]) for r in rows if r["lane"] == lane and r["status"] != "done")
            if not host_pending or lane not in state.get("prompts_verified_lanes", []):
                continue
            want = max(1, min(MAX_CHAIN, math.ceil(remaining / (0.9 * JOB_HOURS))))
            while len(active) < want:
                if active:
                    dep = f"--dependency=afterany:{active[-1]['id']} "
                else:  # a lane's first job waits for its cluster's warm-up job (README deviation 35), if still queued
                    dep = f"--dependency=afterok:{warm} " if warm and live.get(warm) else ""
                job = {"id": sbatch(info, lane, dep), "state": "PENDING", "submitted": ac.utc_now(),
                       "dependency": dep.split(":")[-1].strip() if dep else ""}
                jobs.append(job)
                active.append(job)
                ac.progress(f"step 9 lane {lane}: submitted job {job['id']}"
                            + (f" ({dep.strip()})" if dep else "") + f", ~{remaining:.1f} GPU-h assigned")
                print(f"lane {lane}: submitted {job['id']}")
    save_state(state)
    return 0


WARM_ROOT = "/scratch/billxby/step9/warm_{host}"  # not a lane root: warm-up runs are never pulled or measured


def cmd_warm(args: argparse.Namespace) -> int:
    """README deviation 35: one throwaway server per pair (lossless, case_001, 64 tokens) on the pair's own compile
    cache of that cluster, so no measured arm (and no Block 0 smoke) runs on a freshly compiled server. One job per
    cluster; each lane's first job waits for it (afterok, cmd_submit). --only limits it to some pairs."""
    state = load_state()
    host = args.host
    seen, items = set(), []
    for block, pid, base in BLOCKS:
        if block_host(block) != host or pid in seen or (args.only and pid not in args.only):
            continue
        seen.add(pid)
        item = make_item(block, pid, base, "strict", "strict", "warm", ["case_001"],
                         subroot=f"runs/addendum/step9_warmup/{host}")
        item.update(id=f"warm|{pid}|{host}", max_new_tokens=64)
        items.append(item)
    if not items:
        print("no pairs to warm")
        return 0
    lane = next(l for l in LANES if LANES[l]["host"] == host)
    info = LANES[lane]
    root = WARM_ROOT.format(host=host)
    ac.ssh(f"mkdir -p {root}/slurm && cat > {root}/work.json",
           input_bytes=json.dumps({"items": items, "hold_minutes": 0}, indent=1).encode(), host=host)
    # no node set: every lane job of this cluster waits for this one (afterok), so no job of ours shares its node
    cmd = (f"cd {shlex.quote(info['repo'])} && LANE=warm-{host} REPO_DIR={shlex.quote(info['repo'])} LANE_ROOT={root} "
           f"PROJECT_DIR={info['project']} sbatch --parsable --job-name=s9-warm --account={info['account']} "
           f"--time=2:00:00 --output={root}/slurm/%x-%j.out cascade/cluster/addendum_lane.sbatch")
    job = ac.ssh(f"bash -lc {shlex.quote(cmd)}", host=host).stdout.decode().strip().splitlines()[-1].split(";")[0]
    state.setdefault("warm", {})[host] = job
    ac.progress(f"step 9: warm-up job {job} on {host} ({len(items)} pair caches: {', '.join(sorted(seen))})")
    print(f"{host}: warm-up job {job} for {sorted(seen)}")
    save_state(state)
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    ac.LANES_DIR = LANES_DIR  # lane journals land in campaign/addendum/step9/lanes/
    LANES_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state()
    pulled = []
    for host in HOSTS:
        if not ac.reachable(host):
            print(f"{host} unreachable")
            continue
        for lane in LANES:
            if LANES[lane]["host"] != host or not state["lanes"].get(lane, {}).get("jobs"):
                continue
            got = ac.pull_lane_runs(lane, LANES[lane])
            pulled += got
            if got:
                print(f"lane {lane}: pulled {len(got)} run dir(s)")
    if pulled:
        ac.progress(f"step 9: pulled {len(pulled)} run dir(s)")
    return 0


# ------------------------------------------------------------------ grading (Nibi CPU job, the campaign's graders)

MIRROR = "/scratch/billxby/step9/mirror"
GRADED_BASES = ("gsm8k", "livecodebench", "aime24", "humaneval", "longbench_v2")
GRADE_REPO = ac.LANES["A"]["repo"]  # Nibi repo the step-8 grading used; needs the prompt sets (HumanEval tests)


def cmd_grade(args: argparse.Namespace) -> int:
    """Upload not-yet-graded step-9 runs to the Nibi mirror, pull finished verdicts back, and submit one CPU grading
    job (cascade/cluster/addendum_grade.sbatch) when there is new work -- step 8's cmd_grade with step 9's paths."""
    import io
    import tarfile
    state = load_state()
    synced = state.setdefault("grade_prompts", {})
    env = {"COPYFILE_DISABLE": "1", "PATH": "/usr/bin:/bin"}
    local = {rel: ac.prompt_digest(rel) for rel in prompt_sets()}
    if any(synced.get(rel) != d for rel, d in local.items()):
        # the graders read prompts/<dataset>/<case>/source.json (HumanEval tests) and metadata.json from GRADE_REPO:
        # send the sets whose digest differs there
        digest_py = (REPO / "scripts" / "prompt_digest.py").read_text(encoding="utf-8")
        proc = ac.ssh(f"cd {shlex.quote(GRADE_REPO)} && python3 - . {' '.join(local)}", input_bytes=digest_py.encode(),
                      check=False, timeout=1800)
        remote = json.loads(proc.stdout.decode() or "{}")
        stale = [rel for rel, d in local.items() if remote.get(rel) != d]
        if stale:
            data = subprocess.run(["tar", "-cf", "-", *stale], cwd=REPO, capture_output=True, check=True, env=env).stdout
            ac.ssh(f"cd {shlex.quote(GRADE_REPO)} && rm -rf {' '.join(stale)} && tar -xf -", input_bytes=data,
                   timeout=3600)
            print(f"grading repo: sent {', '.join(stale)}")
        for rel, d in local.items():
            synced[rel] = d
        save_state(state)
    data = ac.ssh(f"cat {MIRROR}/grades.csv 2>/dev/null", check=False).stdout
    if data:
        GRADES.write_bytes(data)
    graded = set()
    if GRADES.is_file():
        with GRADES.open(newline="", encoding="utf-8") as handle:
            graded = {r["relpath"] for r in csv.DictReader(handle) if r.get("verdict")}
    uploaded_file = S9 / "mirror_uploaded.txt"
    uploaded = set(uploaded_file.read_text().split()) if uploaded_file.is_file() else set()
    rels = sorted(str(p.parent.relative_to(REPO / "runs"))
                  for p in (REPO / RUN_SUBROOT).glob("*/*/*/*/case_*/seed_*/run.json"))
    rels = [r for r in rels if base_dataset(r.split("/")[3]) in GRADED_BASES]
    new = [r for r in rels if r not in graded and r not in uploaded]
    if new:
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as tar:
            for rel in new:
                for name in ("run.json", "config.json", "output.txt"):
                    path = REPO / "runs" / rel / name
                    if path.is_file():
                        tar.add(path, arcname=f"{rel}/{name}")
        ac.ssh(f"mkdir -p {MIRROR}/runs && cd {MIRROR}/runs && tar -xf -", input_bytes=buf.getvalue(), timeout=1800)
        with uploaded_file.open("a") as handle:
            handle.write("\n".join(new) + "\n")
    queued = ac.ssh("bash -lc 'squeue -u billxby -h -n s9-grade -o %i'", check=False).stdout.decode().split()
    pending = [r for r in uploaded | set(new) if r not in graded]
    if pending and not queued:
        cmd = (f"cd {GRADE_REPO} && mkdir -p {MIRROR}/slurm && MIRROR={MIRROR} REPO_DIR={GRADE_REPO} sbatch --parsable "
               f"--job-name=s9-grade --account=def-hongyanz_cpu --time=1:00:00 --output={MIRROR}/slurm/%x-%j.out "
               f"cascade/cluster/addendum_grade.sbatch")
        out = ac.ssh(f"bash -lc {shlex.quote(cmd)}").stdout.decode().strip()
        ac.progress(f"step 9 grading: {len(new)} new run dir(s) uploaded, {len(pending)} pending, CPU job {out}")
    print(f"grading: {len(graded)} graded, {len(new)} uploaded now, {len(pending)} pending, "
          f"job {'queued' if queued else 'submitted' if pending else 'none'}")
    return 0


# ------------------------------------------------------------------ AIME boxed answers longer than 3 digits

BOXED_ANY = re.compile(r"\\boxed\{([^{}]*)\}")
AIME_LOG = S9 / "aime_boxed_long.csv"


def cmd_aimelog(args: argparse.Namespace) -> int:
    """GOAL.md: grade_aime.py (unchanged) reads only a 1-3 digit \\boxed{}; a longer boxed number falls through to the
    last 1-3 digit integer of the answer. Log every step-9 AIME24 run whose last boxed answer (in the answer segment)
    has more than 3 digits, with the grader's verdict, so they can be re-graded later."""
    sys.path.insert(0, str(REPO / "scripts"))
    from answer_extraction import final_segment
    import grade_aime
    verdicts = {}
    if GRADES.is_file():
        with GRADES.open(newline="", encoding="utf-8") as handle:
            verdicts = {r["relpath"]: r["verdict"] for r in csv.DictReader(handle)}
    rows = []
    for run_json in sorted((REPO / RUN_SUBROOT).glob("*/aime24*/*/*/case_*/seed_*/run.json")):
        out = run_json.parent / "output.txt"
        text = out.read_text(encoding="utf-8", errors="replace") if out.is_file() else ""
        final, _ = final_segment(text)
        boxed = BOXED_ANY.findall(final or "")
        if not boxed:
            continue
        digits = re.sub(r"[^0-9]", "", boxed[-1])
        if len(digits) <= 3:
            continue
        rel = str(run_json.parent.relative_to(REPO / "runs"))
        answer, how = grade_aime.extract_answer(text)
        parts = rel.split("/")
        rows.append({"relpath": rel, "dataset": parts[3], "method": parts[4], "params": parts[5], "case": parts[6],
                     "last_boxed": boxed[-1][:80], "grader_answer": answer or "", "grader_extracted_by": how,
                     "verdict": verdicts.get(rel, "")})
    with AIME_LOG.open("w", newline="", encoding="utf-8") as handle:
        fields = ["relpath", "dataset", "method", "params", "case", "last_boxed", "grader_answer",
                  "grader_extracted_by", "verdict"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} step-9 AIME24 runs with a boxed answer longer than 3 digits -> {AIME_LOG.relative_to(REPO)}")
    return 0


HE_LOG = S9 / "humaneval_lastblock.csv"


def cmd_helog(args: argparse.Namespace) -> int:
    """Block 0 (4c): grade_humaneval.py (unchanged) executes the LAST fenced block of the answer, and Llama-3.1 often
    ends with a usage block (`print(f(...))`) after the block that defines the function, which then fails with a
    NameError. Log every step-9 HumanEval run whose last block does not define the entry point while an earlier block
    does, with the grader's verdict, so they can be re-graded later. Tables keep the campaign's grader."""
    sys.path.insert(0, str(REPO / "scripts"))
    from answer_extraction import final_segment
    import grade_humaneval
    verdicts = {}
    if GRADES.is_file():
        with GRADES.open(newline="", encoding="utf-8") as handle:
            verdicts = {r["relpath"]: r["verdict"] for r in csv.DictReader(handle)}
    rows = []
    for run_json in sorted((REPO / RUN_SUBROOT).glob("*/humaneval*/*/*/case_*/seed_*/run.json")):
        rel = str(run_json.parent.relative_to(REPO / "runs"))
        parts = rel.split("/")
        source = json.loads((REPO / "prompts" / parts[3] / parts[6] / "source.json").read_text(encoding="utf-8"))
        entry = source.get("entry_point", "")
        out = run_json.parent / "output.txt"
        final, _ = final_segment(out.read_text(encoding="utf-8", errors="replace") if out.is_file() else "")
        for marker in grade_humaneval.END_MARKERS:
            if final and marker in final:
                final = final.split(marker, 1)[0]
        blocks = grade_humaneval.CODE_BLOCK.findall(final or "")
        defines = [f"def {entry}(" in b for b in blocks]
        if len(blocks) > 1 and not defines[-1] and any(defines):
            rows.append({"relpath": rel, "dataset": parts[3], "method": parts[4], "params": parts[5], "case": parts[6],
                         "n_blocks": len(blocks), "defining_block": defines.index(True) + 1,
                         "verdict": verdicts.get(rel, "")})
    with HE_LOG.open("w", newline="", encoding="utf-8") as handle:
        fields = ["relpath", "dataset", "method", "params", "case", "n_blocks", "defining_block", "verdict"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} step-9 HumanEval runs whose last code block does not define the entry point -> "
          f"{HE_LOG.relative_to(REPO)}")
    return 0


# ------------------------------------------------------------------ block completion events

def block_status() -> dict[str, dict]:
    """Per block: done (every run pulled), graded (every graded run has a verdict), completion time (latest
    item_end of the block), GPU-h actual (item wall time from the lane journals, as step 8)."""
    rows = read_manifest()
    graded = set()
    if GRADES.is_file():
        with GRADES.open(newline="", encoding="utf-8") as handle:
            graded = {r["relpath"] for r in csv.DictReader(handle) if r.get("verdict")}
    last_end: dict[str, str] = {}
    for path in sorted(LANES_DIR.glob("*_status.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("event") == "item_end" and str(r.get("item", "")).startswith("s9|"):
                _, pid, ds = r["item"].split("|")[:3]
                block = BLOCK_OF.get((pid, base_dataset(ds)))
                if block and r["t"] > last_end.get(block, ""):
                    last_end[block] = r["t"]
    out = {}
    for block, d in block_rows(rows).items():
        _, pid, base = BLOCKS[BLOCK_ORDER[block]]
        done = d["done"] == d["total"] and "full" in d["stages"]
        need = []
        if done and base in GRADED_BASES:
            need = [str(p.parent.relative_to(REPO / "runs"))
                    for p in (REPO / RUN_SUBROOT / pid / ds_of(pid, base)).glob("*/*/case_*/seed_0/run.json")]
        out[block] = {**d, "complete": done, "graded": done and all(r in graded for r in need),
                      "finished": last_end.get(block, "")}
    return out


def cmd_events(args: argparse.Namespace) -> int:
    """Print one line per block that became complete and graded since the last call (state.json reported); exit 0
    when there is something new, 3 when not."""
    state = load_state()
    reported = set(state.get("reported", []))
    new = []
    for block, d in block_status().items():
        if d["graded"] and block not in reported:
            new.append(block)
            print(f"BLOCK {block} complete {d['finished']} {d['pair']} {d['dataset']} {d['actual']:.1f} GPU-h")
    if new and not getattr(args, "dry", False):
        state["reported"] = sorted(reported | set(new), key=lambda b: BLOCK_ORDER[b])
        save_state(state)
    return 0 if new else 3


ALERT_EVENTS = ("env_not_ready", "quarantined", "disk_floor", "work_unreadable")


def cmd_alerts(args: argparse.Namespace) -> int:
    """New lane-journal events worth a look since the last call: an item that exited nonzero, a quarantined run
    dir, a job whose environment was not ready, the disk floor. Prints one line each; exit 0 if any, 3 if none."""
    state = load_state()
    seen = state.setdefault("alert_seen", {})
    lines = []
    for path in sorted(LANES_DIR.glob("*_status.jsonl")):
        lane = path.name.removesuffix("_status.jsonl")
        records = path.read_text(encoding="utf-8").splitlines()
        for line in records[seen.get(lane, 0):]:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            ev = r.get("event")
            if (ev == "item_end" and r.get("rc") not in (0, None)) or ev in ALERT_EVENTS:
                lines.append(f"ALERT {lane} job {r.get('job')} {r.get('host')} {r['t']} {ev} "
                             + " ".join(f"{k}={r[k]}" for k in ("item", "rc", "missing_before", "missing_after", "reason",
                                                                "case", "state") if k in r))
        seen[lane] = len(records)
    save_state(state)
    print("\n".join(lines[:40]) + (f"\n... {len(lines) - 40} more" if len(lines) > 40 else "") if lines else "", end="")
    return 0 if lines else 3


def cmd_b0(args: argparse.Namespace) -> int:
    """Blocks whose Block 0 smoke runs are all pulled but which are not yet passed (state block0_passed): one line
    each, newly done ones only unless --all. Exit 0 if any new, 3 if none."""
    state = load_state()
    notified = set(state.setdefault("b0_notified", []))
    new = []
    for block, pid, base in BLOCKS:
        if block in state.get("block0_passed", []) or block in DROPPED:
            continue
        if smoke_done(block) and (block not in notified or getattr(args, "all", False)):
            new.append(block)
            item = smoke_item(block)
            runs = [s8.run_ok(run_dir(pid, item["dataset"], "strict", "strict", c, item["runs_subroot"].rsplit("/", 1)[0]))
                    for c in SMOKE_CASES]
            print(f"B0 {block} {pid} {item['dataset']} {block_host(block)}: "
                  + ", ".join(f"{c} {r.get('output_tokens')} tok l_bar {r.get('l_bar'):.2f} {r.get('finish_reason')}"
                              for c, r in zip(SMOKE_CASES, runs) if r))
    state["b0_notified"] = sorted(notified | set(new), key=lambda b: BLOCK_ORDER[b])
    save_state(state)
    return 0 if new else 3


def cmd_assign(args: argparse.Namespace) -> int:
    """Move the not-yet-run items whose id contains --match to --lane (same cluster only), e.g. to put Block 0 smoke
    items on a lane whose job is already running."""
    state = load_state()
    if args.lane not in LANES:
        raise SystemExit(f"unknown lane {args.lane}")
    for item_id in sorted(state["assign"]):
        if args.match in item_id:
            if LANES[state["assign"][item_id]]["host"] != LANES[args.lane]["host"]:
                print(f"skip {item_id}: other cluster")
                continue
            state["assign"][item_id] = args.lane
            print(f"{item_id} -> {args.lane}")
    save_state(state)
    return 0


def cmd_phase2(args: argparse.Namespace) -> int:
    """Turn on Phase 2 (GOAL.md: only if Phase 1 ended before 2026-10-08 18:00 ET; checked here)."""
    state = load_state()
    rows = read_manifest()
    open_p1 = [r for r in rows if r["block"] in PHASE1 and r["status"] != "done"]
    if open_p1:
        raise SystemExit(f"Phase 1 not done: {len(open_p1)} items open")
    if utc_now() >= PHASE2_CUTOFF:
        raise SystemExit("past the Phase 2 cutoff: Phase 2 is skipped")
    state["phase2"] = True
    save_state(state)
    ac.progress("step 9: Phase 1 complete; Phase 2 (standalone pairs, loosest + lossless) started")
    print("phase2 on")
    return 0


def cmd_pass(args: argparse.Namespace) -> int:
    """Mark blocks as having passed Block 0 (after the smoke outputs were looked at): their work is planned."""
    state = load_state()
    passed = set(state.setdefault("block0_passed", []))
    for block in args.blocks:
        if block not in BLOCK_ORDER:
            raise SystemExit(f"unknown block {block}")
        passed.add(block)
    state["block0_passed"] = sorted(passed, key=lambda b: BLOCK_ORDER[b])
    save_state(state)
    ac.progress(f"step 9 Block 0 passed: {', '.join(args.blocks)}")
    print(f"block0_passed: {state['block0_passed']}")
    return 0


# ------------------------------------------------------------------ cycle

def cmd_cycle(args: argparse.Namespace) -> int:
    cmd_collect(args)
    cmd_plan(argparse.Namespace(quiet=True))
    cmd_push(args)
    cmd_submit(args)
    try:
        cmd_grade(args)
    except Exception as exc:  # grading lives on Nibi; its outage must not stop the Killarney lanes
        print(f"grading skipped: {type(exc).__name__}: {exc}")
    cmd_plan(argparse.Namespace(quiet=False))
    cmd_aimelog(args)
    cmd_helog(args)
    # tables and RESULTS.md regenerated from what is pulled and graded so far (never edited by hand)
    for script, arg in (("addendum_tables.py", "step9"), ("addendum_results.py", None)):
        subprocess.run([sys.executable, str(REPO / "scripts" / script), *([arg] if arg else [])], cwd=REPO,
                       capture_output=True, check=False)
    # runs/** is gitignored; the manifest, calibration, tables and journals are committed. Never pushed (GOAL.md).
    paths = ["campaign/addendum/step9", "campaign/addendum/PROGRESS.md", "campaign/calibration", "campaign/addendum/tables",
             "campaign/addendum/RESULTS.md"]
    ac.commit(f"step 9: cycle {ac.utc_now()}", [p for p in paths if (REPO / p).exists()])
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", choices=["plan", "push", "submit", "collect", "cycle", "summary", "grade", "estimate",
                                        "aimelog", "events", "warm", "alerts", "b0", "pass", "assign", "helog", "phase2"])
    parser.add_argument("--match", default="", help="assign: substring of the item ids to move")
    parser.add_argument("--lane", default="", help="assign: the lane to move them to")
    parser.add_argument("blocks", nargs="*", help="pass: the blocks whose Block 0 passed")
    parser.add_argument("--all", action="store_true", help="b0: also blocks already reported")
    parser.add_argument("--lanes", type=float, default=12, help="estimate: concurrent lanes")
    parser.add_argument("--duty", type=float, default=0.85, help="estimate: share of lane wall time spent running")
    parser.add_argument("--block0-hours", type=float, default=1.5, help="estimate: hours before Phase 1 starts")
    parser.add_argument("--all-lanes", action="store_true", help="push: also lanes not yet checked ready")
    parser.add_argument("--dry", action="store_true", help="events: do not mark as reported")
    parser.add_argument("--host", default="nibi", choices=HOSTS, help="warm: the cluster")
    parser.add_argument("--only", nargs="*", help="warm: only these pair ids")
    parser.add_argument("--quiet", action="store_true", help="plan: no summary")
    args = parser.parse_args()
    # one command at a time: the cycle loop and a manual command must not both rewrite state.json
    import fcntl
    S9.mkdir(parents=True, exist_ok=True)
    lock = (S9 / ".lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    return {"plan": cmd_plan, "push": cmd_push, "submit": cmd_submit, "collect": cmd_collect, "cycle": cmd_cycle,
            "summary": cmd_summary, "grade": cmd_grade, "estimate": cmd_estimate, "aimelog": cmd_aimelog,
            "events": cmd_events, "warm": cmd_warm, "alerts": cmd_alerts, "b0": cmd_b0, "pass": cmd_pass,
            "assign": cmd_assign, "helog": cmd_helog, "phase2": cmd_phase2}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
