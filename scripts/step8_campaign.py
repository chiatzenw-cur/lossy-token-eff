#!/usr/bin/env python3
"""Step 8 orchestrator (campaign/addendum/step8/GOAL.md): more drafters, the Llama-3.1-8B family,
the fix on Qwen3-8B. Runs on the Mac, drives lanes on Killarney and Nibi through the addendum's own
machinery (scripts/addendum_lane.py -> persistent_arm_replay.py, one persistent server per arm).

  python3 scripts/step8_campaign.py plan      # manifest + per-lane work lists from what is pulled locally
  python3 scripts/step8_campaign.py push      # code, prompt sets, work lists -> lane repos / lane roots
  python3 scripts/step8_campaign.py submit    # keep each lane's 3 h Slurm chain supplied
  python3 scripts/step8_campaign.py collect   # pull finished run dirs (no-clobber) + lane journals
  python3 scripts/step8_campaign.py cycle     # collect -> plan -> push -> submit -> commit + push branch
  python3 scripts/step8_campaign.py summary

Protocol per (target, drafter, dataset), confirmed with Bill 2026-10-03:
  dedicated drafter: calibration of the five rules at their 4-point grids on case_001-003 -> three l_bar targets
    at the 20/55/90th percentile of the shared span -> each rule at the grid alpha nearest each target on the full
    case set (campaign_run.pick_targets_and_alphas, unchanged), plus the pair's own lossless reference;
  standalone drafter: each rule at its loosest grid alpha + lossless, GSM8K and LiveCodeBench;
  fix (block 6): spec_casc_tok_lt 0.15 / 0.20 and spec_casc_opt_head (alpha 0.05, beta 0.15) on Qwen3-8B +
    its EAGLE-3 head, against the existing Killarney Qwen3 lossless reference (runs/addendum/nibiref).
Every run: seed 0, N_draft 6, T 1.0, top-p 1.0, the paper's budgets, --no-trace-proposals.

Run layout: runs/addendum/step8/<target>__<drafter>/<dataset>/<method>/<params>/case_NNN/seed_0/.
A full arm's item lists only the cases calibration did not run (case_004 on), so no lane reruns a case
another lane already has; its server starts at case_004.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import shlex
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import addendum_campaign as ac  # noqa: E402
from campaign_run import (  # noqa: E402
    ALPHA_GRIDS, MODEL_FAMILIES, QWEN3_ROPE_SCALING, TOKEN_BUDGETS, base_dataset, model_flags, pick_targets_and_alphas,
)

S8 = REPO / "campaign" / "addendum" / "step8"
MANIFEST = S8 / "manifest.csv"
STATE = S8 / "state.json"
LANES_DIR = S8 / "lanes"
CALIB_DIR = REPO / "campaign" / "calibration"
RUN_SUBROOT = "runs/addendum/step8"
FIVE = ac.FIVE
N_CASES = {"gsm8k": 150, "livecodebench": 90, "mtbench": 80, "aime24": 30}
CALIB_CASES = ["case_001", "case_002", "case_003"]
LOOSEST = {m: max(ALPHA_GRIDS[m]) for m in FIVE}
KP, NP = ac.KILLARNEY_PROJECT, ac.NIBI_PROJECT
HF_LOCAL = f"{KP}/hf/local"

# Killarney lanes K1-K4 are the addendum's lane copies (repo + patched venv each); K5-K8 are copies of K1 made
# for step 8. Killarney gives every job a private /tmp and stop_server.sh is job-scoped, so lanes may share a
# node (README deviation 15). Nibi A/B keep their disjoint node sets (no per-job /tmp there).
LANES: dict[str, dict] = {
    **{f"K{n}": {"host": "killarney", "account": "aip-hongyanz", "project": KP,
                 "repo": f"{KP}/lossy-token-eff" + ("" if n == 1 else f"-lane{n}"),
                 "root": f"/scratch/billxby/step8/laneK{n}", "exclude": ""} for n in range(1, 9)},
    "A": {**ac.LANES["A"], "root": "/scratch/billxby/step8/laneA"},
    "B": {**ac.LANES["B"], "root": "/scratch/billxby/step8/laneB"},
}
ACTIVE_LANES = {"killarney": ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"], "nibi": ["A", "B"]}
MAX_CHAIN, JOB_TIME, JOB_HOURS = 3, "3:00:00", 3.0
STARTUP_H = 0.08
# GPU-h per full arm, measured in the addendum (PROGRESS.md) for GPT-OSS and Qwen3 on Nibi/Killarney H100s;
# the Llama-3.1-8B-Instruct rows are taken as GPT-OSS-like (no reasoning trace), R1-Distill as Qwen3-like
ARM_H = {
    "gpt_oss_20b": {"gsm8k": 0.14, "livecodebench": 0.27, "mtbench": 0.11, "aime24": 0.22},
    "qwen3": {"gsm8k": 0.26, "livecodebench": 0.95, "mtbench": 0.23, "aime24": 0.86},
}
ARM_H["llama31"] = ARM_H["gpt_oss_20b"]
# R1-Distill measured in Block 0 (lossless + EAGLE-3, Killarney): LiveCodeBench ~53 s/case, AIME24 ~90 s/case
# (its drafter stops drafting past ~2048 positions), GSM8K ~1.2 s/case
ARM_H["r1llama"] = {"gsm8k": 0.05, "livecodebench": 1.35, "mtbench": 0.2, "aime24": 0.8}
SUFFIX = {"gpt_oss_20b": "", "qwen3": "_qwen3", "llama31": "_llama31", "r1llama": "_r1llama"}
TARGET_SLUG = {"gpt_oss_20b": "gpt-oss-20b", "qwen3": "qwen3-8b", "llama31": "llama31-8b-instruct",
               "r1llama": "r1-distill-llama-8b"}
# tables cite the canonical ids; the mirrors are README deviation 29
CANONICAL = {"RedHatAI/Llama-3.1-8B-Instruct": "meta-llama/Llama-3.1-8B-Instruct",
             "alpindale/Llama-3.2-1B-Instruct": "meta-llama/Llama-3.2-1B-Instruct"}


def maxpos(repo: str) -> str:
    """README deviation 31: the yuhuili EAGLE heads' config stops at 2048 positions."""
    return f"{HF_LOCAL}/{repo.split('/')[1]}-maxpos65536"


# README deviation 33: R1-Distill's declared tokenizer class mis-encodes every prompt under transformers 5.18; the server
# gets a copy of the same tokenizer.json declared PreTrainedTokenizerFast (remote/run_server_vllm.sh TOKENIZER)
R1_TOKENIZER = f"{HF_LOCAL}/DeepSeek-R1-Distill-Llama-8B-tokenizer-fast"
FAMILY_ENV = {"r1llama": {"TOKENIZER": R1_TOKENIZER}}
DRAFTER_FAMILY = {"eagle3": "eagle3", "eagle": "eagle1", "medusa": "medusa", "dspark": "dspark", "dflash": "dflash",
                  "draft_model": "draft_model"}
V2, V1 = "V2 accept-test-only", "V1 full patches"


def sampler_path(family: str, spec: str) -> str:
    """vLLM 0.26.0 (config/vllm.py use_v2_model_runner): dense targets run eagle/eagle3/dflash/dspark on the V2 runner,
    whose consolidated sampler is accept-test-only for cactus and spec_casc_tok; medusa and draft_model fall back to V1,
    and GPT-OSS-20B (MoE) is always V1 -- both with the full patches."""
    return V2 if family != "gpt_oss_20b" and spec in ("eagle", "eagle3", "dflash", "dspark") else V1


def pair(block: str, family: str, slug: str, drafter: str, spec: str, kind: str, datasets: list[str], host: str,
         drafter_path: str | None = None, env: dict | None = None, arms: list | None = None,
         sampler: str | None = None) -> dict:
    pid = f"{TARGET_SLUG[family]}__{slug}"
    # a compile cache per pair: two drafters of one architecture (Qwen3-0.6B / 1.7B) collided in the shared cache
    # (Block 0, 2026-10-03: illegal memory access in the drafter's graph capture after an AOT cache load)
    env = {"VLLM_CACHE_ROOT": f"/scratch/billxby/vllm_cache_step8/{pid}", **FAMILY_ENV.get(family, {}), **(env or {})}
    return {"block": block, "family": family, "slug": slug, "drafter": drafter, "drafter_path": drafter_path or drafter,
            "spec": spec, "kind": kind, "datasets": datasets, "host": host,
            "sampler": sampler or sampler_path(family, spec),
            "drafter_family": DRAFTER_FAMILY[spec], "env": env, "arms": arms, "id": pid}


R1_E3, L31_E3, L31_E1 = ("yuhuili/EAGLE3-DeepSeek-R1-Distill-LLaMA-8B", "yuhuili/EAGLE3-LLaMA3.1-Instruct-8B",
                         "yuhuili/EAGLE-LLaMA3.1-Instruct-8B")
L32_1B = "alpindale/Llama-3.2-1B-Instruct"
FIX_ARMS = [("spec_casc_tok_lt", "0.15", None), ("spec_casc_tok_lt", "0.2", None), ("spec_casc_opt_head", "0.05", "0.15")]
# Block 0(d): Qwen3-8B's second dedicated drafter = the first of these, in this order, to pass the q probe (Bill)
BLOCK3_CANDIDATES = {
    "dspark": ("deepseek-ai/dspark_qwen3_8b_block7", "dspark"),
    "dflash": ("RedHatAI/Qwen3-8B-speculator.dflash", "dflash"),
    "thinking-eagle3": ("RedHatAI/Qwen3-8B-Thinking-speculator.eagle3", "eagle3"),
}
BLOCK3_DRAFTER = "dspark"  # Block 0(d), 2026-10-03: first in Bill's order to pass the q probe (q present, 0% one-hot)
PAIRS = [
    pair("1", "r1llama", "eagle3", R1_E3, "eagle3", "dedicated", ["gsm8k", "livecodebench", "mtbench", "aime24"],
         "killarney", drafter_path=maxpos(R1_E3)),
    pair("2", "llama31", "eagle3", L31_E3, "eagle3", "dedicated", ["gsm8k", "livecodebench", "mtbench"], "killarney",
         drafter_path=maxpos(L31_E3)),
    pair("2", "llama31", "eagle1", L31_E1, "eagle", "dedicated", ["gsm8k", "livecodebench", "mtbench"], "killarney",
         drafter_path=maxpos(L31_E1)),
    pair("2", "llama31", "medusa", "nebius/MEDUSA-Llama-3.1-8B-Instruct", "medusa", "dedicated",
         ["gsm8k", "livecodebench", "mtbench"], "killarney"),
    pair("2", "llama31", "llama32-1b", L32_1B, "draft_model", "standalone", ["gsm8k", "livecodebench"], "killarney"),
    *([pair("3", "qwen3", BLOCK3_DRAFTER, *BLOCK3_CANDIDATES[BLOCK3_DRAFTER], "dedicated",
            ["gsm8k", "livecodebench", "mtbench"], "killarney")] if BLOCK3_DRAFTER else []),
    pair("3", "qwen3", "qwen3-1.7b", "Qwen/Qwen3-1.7B", "draft_model", "standalone", ["gsm8k", "livecodebench"],
         "killarney"),
    pair("4", "gpt_oss_20b", "rh-eagle3", "RedHatAI/gpt-oss-20b-speculator.eagle3", "eagle3", "dedicated",
         # on Killarney since 2026-10-03 ~20:20Z: every Nibi GPU node down or drained (README deviation 39)
         ["gsm8k", "livecodebench", "mtbench"], "killarney", env={"MENTORED_DEC_TEST_V1_ONLY": "1"}),
    pair("5", "r1llama", "llama32-1b", L32_1B, "draft_model", "standalone", ["gsm8k", "livecodebench"], "killarney"),
    pair("6", "qwen3", "eagle3-fix", MODEL_FAMILIES["qwen3"][1], "eagle3", "fix", ["gsm8k", "livecodebench"],
         "killarney", arms=FIX_ARMS),
    # Block 7 (optional; started 2026-10-04 ~14:40Z once blocks 0-6 were committed and the lanes free): P-EAGLE drafts
    # in parallel, which vLLM 0.26.0 runs on the V1 runner (V2's EagleSpeculator does not support parallel drafting)
    pair("7", "qwen3", "peagle", "RedHatAI/Qwen3-8B-speculator.peagle", "eagle3", "standalone", ["gsm8k", "livecodebench"],
         "killarney", env={"PARALLEL_DRAFTING": "true"}, sampler=V1),
]
BLOCKS_ENABLED = {"1", "2", "3", "4", "5", "6", "7"}  # plan only these (block 0 decides drafter paths and fallbacks)
DISABLED_PAIRS: dict[str, str] = {  # pair id -> reason (block 0 fallbacks)
    "llama31-8b-instruct__medusa": "block 0: no draft probabilities reach the sampler (vLLM's medusa path passes "
                                   "draft_probs None: every traced q(x) = 1.0, no draft entropy); the cascade and fuzzy "
                                   "rules need q -- dropped per the plan's Medusa fallback",
}


def cases(n: int, start: int = 1) -> list[str]:
    return [f"case_{i:03d}" for i in range(start, n + 1)]


def fmt(a) -> str:
    return f"{float(a):g}"


def params_dir(method: str, alpha: str, beta: str | None = None) -> str:
    if method == "strict":
        return "strict"
    p = f"alpha{float(alpha):g}".replace("-", "neg")
    if beta is not None:
        p += f"_beta{float(beta):g}".replace("-", "neg")
    return p


def run_dir(p: dict, ds: str, method: str, alpha: str, case: str, beta: str | None = None) -> pathlib.Path:
    return REPO / RUN_SUBROOT / p["id"] / ds / method / params_dir(method, alpha, beta) / case / "seed_0"


def run_ok(path: pathlib.Path) -> dict | None:
    try:
        data = json.loads((path / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if data.get("status") == "ok" else None


def calib_path(p: dict, base: str) -> pathlib.Path:
    return CALIB_DIR / f"{base}_{p['family']}_{p['slug']}.json"


def make_item(p: dict, base: str, method: str, alpha: str, stage: str, case_list: list[str],
              beta: str | None = None) -> dict:
    ds = base + SUFFIX[p["family"]]
    target, _, served, rope = MODEL_FAMILIES[p["family"]]
    item = {
        "id": f"s8|{p['id']}|{ds}|{method}|{alpha}" + (f"|b{beta}" if beta else "") + f"|{stage}",
        "step": f"8.{p['block']}", "condition": f"step8/{p['id']}", "dataset": ds, "method": method,
        "alpha": alpha, "seed": 0, "cases": case_list, "prompt_root": f"prompts/{ds}",
        "runs_subroot": f"{RUN_SUBROOT}/{p['id']}", "max_new_tokens": TOKEN_BUDGETS[ds],
        "model_flags": model_flags(target, p["drafter_path"], served, rope),
        "num_spec": 6, "temperature": 1.0, "top_p": 1.0, "env": {"SPEC_METHOD": p["spec"], **p["env"]},
    }
    if beta is not None:
        item["extra_flags"] = ["--spec-casc-opt-head-beta", beta]
        item["params_dir"] = params_dir(method, alpha, beta)
    return item


def item_missing(p: dict, item: dict) -> list[str]:
    beta = item.get("extra_flags", [None, None])[1] if item.get("extra_flags") else None
    base = base_dataset(item["dataset"])
    return [c for c in item["cases"] if not run_ok(run_dir(p, item["dataset"], item["method"], item["alpha"], c, beta))]


def calibrate(p: dict, base: str) -> dict | None:
    """Targets and chosen alphas once all 20 calibration arms are pulled; None while any is missing."""
    ds = base + SUFFIX[p["family"]]
    grid: dict[str, list[tuple[float, float]]] = {}
    for method in FIVE:
        pts = []
        for alpha in ALPHA_GRIDS[method]:
            lbars = []
            for case in CALIB_CASES:
                run = run_ok(run_dir(p, ds, method, fmt(alpha), case))
                if run is None:
                    return None
                lbars.append(run.get("l_bar"))
            lbars = [x for x in lbars if x is not None]
            if lbars:
                pts.append((alpha, sum(lbars) / len(lbars)))
        grid[method] = pts
    targets, chosen = pick_targets_and_alphas(grid, 3)
    out = calib_path(p, base)
    record = {
        "dataset": ds, "pair": p["id"], "target": MODEL_FAMILIES[p["family"]][0], "drafter": p["drafter"],
        "drafter_path": p["drafter_path"], "spec_method": p["spec"], "probe_cases": CALIB_CASES,
        "full_cases": cases(N_CASES[base]), "max_new_tokens": TOKEN_BUDGETS[ds],
        "alpha_grids": {m: ALPHA_GRIDS[m] for m in FIVE},
        "grid_results": {m: [{"alpha": a, "mean_l_bar": l} for a, l in pts] for m, pts in grid.items()},
        "targets_l_bar": targets, "chosen_alphas": chosen,
        "rule": "campaign_run.pick_targets_and_alphas (20/55/90th percentile of the shared span, nearest grid alpha)",
    }
    if not out.is_file() or json.loads(out.read_text(encoding="utf-8")).get("chosen_alphas") != chosen:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        ac.progress(f"step 8: calibrated {p['id']} {ds}: targets {[round(t, 3) for t in targets]}, "
                    + ", ".join(f"{m} {chosen[m]}" for m in FIVE))
    return record


def pair_items(p: dict) -> list[dict]:
    items = []
    for base in p["datasets"]:
        n = N_CASES[base]
        if p["kind"] != "fix":
            items.append(make_item(p, base, "strict", "strict", "full", cases(n)))
        if p["kind"] == "dedicated":
            for method in FIVE:
                for alpha in ALPHA_GRIDS[method]:
                    items.append(make_item(p, base, method, fmt(alpha), "calib", CALIB_CASES))
            record = calibrate(p, base)
            if record:
                for method in FIVE:
                    for alpha in record["chosen_alphas"][method]:
                        items.append(make_item(p, base, method, fmt(alpha), "full", cases(n, start=len(CALIB_CASES) + 1)))
        elif p["kind"] == "standalone":
            for method in FIVE:
                items.append(make_item(p, base, method, fmt(LOOSEST[method]), "full", cases(n)))
        elif p["kind"] == "fix":
            for method, alpha, beta in p["arms"]:
                items.append(make_item(p, base, method, alpha, "full", cases(n), beta=beta))
    return items


def est_hours(p: dict, item: dict, n_missing: int) -> float:
    base = base_dataset(item["dataset"])
    return STARTUP_H + ARM_H[p["family"]][base] * n_missing / N_CASES[base] if n_missing else 0.0


def load_state() -> dict:
    if STATE.is_file():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"assign": {}, "lanes": {lane: {"jobs": []} for lane in LANES}}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8")


STAGE_ORDER = {"calib": 0, "full": 1}


def cmd_plan(args: argparse.Namespace) -> int:
    state = load_state()
    assign: dict[str, str] = state["assign"]
    rows, per_lane = [], {lane: [] for lane in LANES}
    load = {lane: 0.0 for lane in LANES}
    planned = []
    for p in PAIRS:
        if p["block"] not in BLOCKS_ENABLED or p["id"] in DISABLED_PAIRS:
            continue
        for item in pair_items(p):
            missing = item_missing(p, item)
            planned.append((p, item, missing, est_hours(p, item, len(missing))))
    # sticky assignment: an item keeps its lane once given one (its partial runs live in that lane root)
    for p, item, missing, hours in planned:
        # an item whose pair moved cluster is reassigned (its lane root on the old cluster holds none of its runs)
        if item["id"] in assign and LANES[assign[item["id"]]]["host"] != p["host"]:
            del assign[item["id"]]
        if item["id"] in assign:
            load[assign[item["id"]]] += hours
    for p, item, missing, hours in sorted(planned, key=lambda t: -t[3]):  # LPT: longest first to least-loaded lane
        if item["id"] not in assign and missing:
            lane = min(ACTIVE_LANES[p["host"]], key=lambda l: load[l])
            assign[item["id"]] = lane
            load[lane] += hours
    for p, item, missing, hours in planned:
        lane = assign.get(item["id"], "")
        status = "done" if not missing else "pending"
        if missing and lane:
            per_lane[lane].append((p, item))
        rows.append({"block": p["block"], "pair": p["id"], "target": CANONICAL.get(MODEL_FAMILIES[p["family"]][0],
                     MODEL_FAMILIES[p["family"]][0]), "drafter": CANONICAL.get(p["drafter"], p["drafter"]),
                     "spec_method": p["spec"], "drafter_family": p["drafter_family"],
                     "sampler_path": p["sampler"], "dataset": item["dataset"],
                     "method": item["method"], "alpha": item["alpha"],
                     "beta": item["extra_flags"][1] if item.get("extra_flags") else "",
                     "stage": item["id"].rsplit("|", 1)[1], "n_cases": len(item["cases"]),
                     "n_done": len(item["cases"]) - len(missing), "status": status, "lane": lane,
                     "gpu_hours_est": f"{hours:.2f}"})
    S8.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    LANES_DIR.mkdir(parents=True, exist_ok=True)
    for lane, entries in per_lane.items():
        # calibration first (it unlocks the full arms), then by block, then the order planned
        entries.sort(key=lambda e: (STAGE_ORDER[e[1]["id"].rsplit("|", 1)[1]], e[0]["block"]))
        waiting = any(r["stage"] == "calib" and r["status"] != "done" for r in rows if r["pair"] in
                      {e[0]["id"] for e in entries}) or any(
            r["stage"] == "calib" and r["status"] != "done" and LANES.get(r["lane"], {}).get("host") == LANES[lane]["host"]
            for r in rows)
        work = {"items": [e[1] for e in entries], "hold_minutes": 30 if waiting else 0}
        (LANES_DIR / f"{lane}.json").write_text(json.dumps(work, indent=1) + "\n", encoding="utf-8")
    save_state(state)
    if not getattr(args, "quiet", False):
        print_summary(rows, load)
    return 0


def print_summary(rows: list[dict], load: dict | None = None) -> None:
    by = {}
    for r in rows:
        key = (r["block"], r["pair"])
        d = by.setdefault(key, [0, 0, 0.0])
        d[0] += r["n_done"]
        d[1] += r["n_cases"]
        d[2] += float(r["gpu_hours_est"])
    for (block, pid), (done, total, hours) in sorted(by.items()):
        print(f"block {block} {pid:40s} {done:5d}/{total:5d} runs, ~{hours:.1f} GPU-h left")
    if load:
        print("lane load (GPU-h): " + ", ".join(f"{l} {h:.1f}" for l, h in load.items() if h))


def cmd_summary(args: argparse.Namespace) -> int:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = [{**r, "n_done": int(r["n_done"]), "n_cases": int(r["n_cases"])} for r in csv.DictReader(handle)]
    print_summary(rows)
    return 0


# ------------------------------------------------------------------ push / submit / collect
PUSH_FILES = ac.PUSH_FILES + ["scripts/answer_extraction.py", "scripts/grade_gsm8k.py", "scripts/grade_livecodebench.py",
                              "scripts/grade_aime.py"]
PROMPTS = [f"prompts/{b}{s}" for s in ("_llama31", "_r1llama") for b in N_CASES]


def lanes_in_use() -> list[str]:
    hosts = {p["host"] for p in PAIRS if p["block"] in BLOCKS_ENABLED}
    return [lane for h in hosts for lane in ACTIVE_LANES[h]]


def cmd_push(args: argparse.Namespace) -> int:
    files = [f for f in PUSH_FILES if (REPO / f).is_file()]
    code = subprocess.run(["tar", "-cf", "-", *files], cwd=REPO, capture_output=True, check=True,
                          env={"COPYFILE_DISABLE": "1", "PATH": "/usr/bin:/bin"}).stdout
    prompts = subprocess.run(["tar", "-cf", "-", *[p for p in PROMPTS if (REPO / p).is_dir()]], cwd=REPO,
                             capture_output=True, check=True, env={"COPYFILE_DISABLE": "1", "PATH": "/usr/bin:/bin"}).stdout
    state = load_state()
    pushed = state.setdefault("prompts_pushed", {})
    digest = __import__("hashlib").sha256(prompts).hexdigest()
    for lane in lanes_in_use():
        info = LANES[lane]
        ac.ssh(f"cd {shlex.quote(info['repo'])} && tar -xf -", input_bytes=code, host=info["host"])
        if pushed.get(lane) != digest:
            ac.ssh(f"cd {shlex.quote(info['repo'])} && tar -xf -", input_bytes=prompts, host=info["host"], timeout=1800)
            pushed[lane] = digest
        work = (LANES_DIR / f"{lane}.json").read_bytes()
        root = shlex.quote(info["root"])
        ac.ssh(f"mkdir -p {root}/slurm && cat > {root}/work.json.tmp && mv {root}/work.json.tmp {root}/work.json",
               input_bytes=work, host=info["host"])
        print(f"pushed {len(files)} code files + work list ({len(json.loads(work)['items'])} items) to lane {lane}")
    save_state(state)
    return 0


def squeue(host: str) -> dict[str, str]:
    out = ac.ssh("bash -lc 'squeue -u billxby -h -o \"%i %T\"'", host=host, check=False, timeout=120)
    if out.returncode != 0:
        return {}
    return dict(line.split()[:2] for line in out.stdout.decode().splitlines() if line.strip())


def cmd_submit(args: argparse.Namespace) -> int:
    state = load_state()
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    live = {h: squeue(h) for h in {LANES[l]["host"] for l in lanes_in_use()}}
    for lane in lanes_in_use():
        info = LANES[lane]
        jobs = state["lanes"].setdefault(lane, {"jobs": []})["jobs"]
        for job in jobs:
            job["state"] = live[info["host"]].get(job["id"], "ENDED")
        active = [j for j in jobs if j["state"] in ("PENDING", "RUNNING", "CONFIGURING", "COMPLETING")]
        remaining = sum(float(r["gpu_hours_est"]) for r in rows if r["lane"] == lane and r["status"] != "done")
        if remaining <= 0:
            continue
        want = max(1, min(MAX_CHAIN, math.ceil(remaining / (0.9 * JOB_HOURS))))
        warm = state.get("warm", {}).get(info["host"])
        while len(active) < want:
            if active:
                dep = f"--dependency=afterany:{active[-1]['id']} "
            else:  # a lane's first job waits for its cluster's warm-up job (README deviation 35), if still known
                dep = f"--dependency=afterok:{warm} " if warm and live[info["host"]].get(warm) else ""
            cmd = (f"cd {shlex.quote(info['repo'])} && mkdir -p {info['root']}/slurm && "
                   f"LANE={lane} REPO_DIR={shlex.quote(info['repo'])} LANE_ROOT={info['root']} PROJECT_DIR={info['project']} "
                   f"sbatch --parsable --job-name=s8-{lane} --account={info['account']} "
                   + (f"--exclude={info['exclude']} " if info["exclude"] else "")
                   + f"--time={JOB_TIME} --output={info['root']}/slurm/%x-%j.out {dep}cascade/cluster/addendum_lane.sbatch")
            out = ac.ssh(f"bash -lc {shlex.quote(cmd)}", host=info["host"]).stdout.decode().strip().splitlines()[-1]
            job = {"id": out.split(";")[0].strip(), "state": "PENDING", "submitted": ac.utc_now(),
                   "dependency": active[-1]["id"] if active else ""}
            jobs.append(job)
            active.append(job)
            ac.progress(f"step 8 lane {lane}: submitted job {job['id']}" + (f" (afterany:{job['dependency']})" if job["dependency"] else "")
                        + f", ~{remaining:.1f} GPU-h assigned")
            print(f"lane {lane}: submitted {job['id']}")
    save_state(state)
    return 0


WARM_SUBROOT = "runs/addendum/step8_warmup"  # outside RUN_SUBROOT: warm-up runs are never measured or pulled


def cmd_warm(args: argparse.Namespace) -> int:
    """README deviation 35: one throwaway server per pair (lossless, case_001, 64 tokens) on the pair's own compile
    cache, so no measured arm runs on a freshly compiled server. One job per cluster; each lane's first job waits
    for it (afterok, cmd_submit)."""
    state = load_state()
    for host, lanes in ACTIVE_LANES.items():
        pairs = [p for p in PAIRS if p["host"] == host and p["block"] in BLOCKS_ENABLED and p["id"] not in DISABLED_PAIRS
                 and (not getattr(args, "only", None) or p["id"] in args.only)]
        if not pairs:
            continue
        items = []
        for p in pairs:
            item = make_item(p, p["datasets"][0], "strict", "strict", "warm", ["case_001"])
            item.update(id=f"warm|{p['id']}", runs_subroot=f"{WARM_SUBROOT}/{p['id']}", max_new_tokens=64)
            items.append(item)
        info = LANES[lanes[0]]
        root = f"/scratch/billxby/step8/warm_{host}"
        work = json.dumps({"items": items, "hold_minutes": 0}, indent=1).encode()
        ac.ssh(f"mkdir -p {root}/slurm && cat > {root}/work.json", input_bytes=work, host=host)
        cmd = (f"cd {shlex.quote(info['repo'])} && LANE=warm-{host} REPO_DIR={shlex.quote(info['repo'])} LANE_ROOT={root} "
               f"PROJECT_DIR={info['project']} sbatch --parsable --job-name=s8-warm --account={info['account']} "
               + (f"--exclude={info['exclude']} " if info["exclude"] else "")
               + f"--time=2:00:00 --output={root}/slurm/%x-%j.out cascade/cluster/addendum_lane.sbatch")
        job = ac.ssh(f"bash -lc {shlex.quote(cmd)}", host=host).stdout.decode().strip().splitlines()[-1].split(";")[0]
        state.setdefault("warm", {})[host] = job
        ac.progress(f"step 8: warm-up job {job} on {host} ({len(items)} pair caches)")
        print(f"{host}: warm-up job {job} for {[p['id'] for p in pairs]}")
    save_state(state)
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    ac.LANES_DIR = LANES_DIR  # lane journals land in campaign/addendum/step8/lanes/
    LANES_DIR.mkdir(parents=True, exist_ok=True)
    pulled = []
    for lane in lanes_in_use():
        if not ac.reachable(LANES[lane]["host"]):
            print(f"lane {lane}: unreachable")
            continue
        got = ac.pull_lane_runs(lane, LANES[lane])
        pulled += got
        if got:
            print(f"lane {lane}: pulled {len(got)} run dir(s)")
    if pulled:
        ac.progress(f"step 8: pulled {len(pulled)} run dir(s)")
    return 0


MIRROR = "/scratch/billxby/step8/mirror"   # on Nibi: graded there (the code graders cap memory with RLIMIT_AS)
GRADES = S8 / "grades.csv"                 # relpath (relative to runs/) -> verdict, read by addendum_tables.py


def cmd_grade(args: argparse.Namespace) -> int:
    """Upload not-yet-graded step-8 runs to the Nibi mirror, pull finished verdicts back, and submit one CPU
    grading job (cascade/cluster/addendum_grade.sbatch, the campaign's own graders) when there is new work."""
    import io
    import tarfile
    data = ac.ssh(f"cat {MIRROR}/grades.csv 2>/dev/null", check=False).stdout
    if data:
        GRADES.write_bytes(data)
    graded = set()
    if GRADES.is_file():
        with GRADES.open(newline="", encoding="utf-8") as handle:
            graded = {r["relpath"] for r in csv.DictReader(handle) if r.get("verdict")}
    uploaded_file = S8 / "mirror_uploaded.txt"
    uploaded = set(uploaded_file.read_text().split()) if uploaded_file.is_file() else set()
    rels = sorted(str(p.parent.relative_to(REPO / "runs")) for p in (REPO / RUN_SUBROOT).glob("*/*/*/*/case_*/seed_*/run.json"))
    rels = [r for r in rels if base_dataset(r.split("/")[3]) in ("gsm8k", "livecodebench", "aime24")]
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
    queued = ac.ssh("bash -lc 'squeue -u billxby -h -n s8-grade -o %i'", check=False).stdout.decode().split()
    pending = [r for r in uploaded | set(new) if r not in graded]
    if pending and not queued:
        repo = LANES["A"]["repo"]
        out = ac.ssh(f"bash -lc {shlex.quote(f'cd {repo} && mkdir -p {MIRROR}/slurm && MIRROR={MIRROR} REPO_DIR={repo} sbatch --parsable --job-name=s8-grade --account=def-hongyanz_cpu --output={MIRROR}/slurm/%x-%j.out cascade/cluster/addendum_grade.sbatch')}").stdout.decode().strip()
        ac.progress(f"step 8 grading: {len(new)} new run dir(s) uploaded, {len(pending)} pending, CPU job {out}")
    print(f"grading: {len(graded)} graded, {len(new)} uploaded now, {len(pending)} pending, job {'queued' if queued else 'submitted' if pending else 'none'}")
    return 0


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
    # tables and RESULTS.md regenerated from what is pulled and graded so far (never edited by hand)
    for script, arg in (("addendum_tables.py", "step8"), ("addendum_results.py", None)):
        subprocess.run([sys.executable, str(REPO / "scripts" / script), *([arg] if arg else [])], cwd=REPO,
                       capture_output=True, check=False)
    # runs/** is gitignored (the addendum's runs live on disk too); the manifest, calibration and tables are committed
    paths = ["campaign/addendum/step8", "campaign/addendum/PROGRESS.md", "campaign/calibration", "campaign/addendum/tables",
             "campaign/addendum/RESULTS.md"]
    if ac.commit(f"step 8: cycle {ac.utc_now()}", [p for p in paths if (REPO / p).exists()]):
        ac.git("push", "-q", "origin", "addendum-step8", check=False)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", choices=["plan", "push", "submit", "collect", "cycle", "summary", "warm", "grade"])
    parser.add_argument("--only", nargs="*", help="warm: only these pair ids")
    args = parser.parse_args()
    return {"plan": cmd_plan, "push": cmd_push, "submit": cmd_submit, "collect": cmd_collect, "cycle": cmd_cycle,
            "summary": cmd_summary, "warm": cmd_warm, "grade": cmd_grade}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
