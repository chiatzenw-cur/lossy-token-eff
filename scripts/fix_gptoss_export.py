#!/usr/bin/env python3
"""Block 6: re-export the GPT-OSS-20B "fix" results (head-restricted relaxation,
spec_casc_tok_lt and spec_casc_opt_head; cascade/RESULTS.md sections 2.3, 2.3b
and 2.4) into one CSV in the addendum table format:

    campaign/addendum/tables/fix__gpt-oss-20b.csv

Stdlib only; reads, never writes, the sources:
  campaign/tables/<stem>.csv    per-run records (case, seed, l_bar, output_tokens,
                                draft_rounds, finish_reason, wall_time_seconds)
  campaign/results/<stem>.csv   per-point accuracy (graded per seed, 2026-09-16 fix)
  cascade/RESULTS.md section 2.4  E6's seed-0 lossless accuracy (no CSV has it)
  cascade/results/speed_ignoring_accuracy.csv  cross-check only (3-decimal values)

Every number is computed with the definitions of scripts/addendum_tables.py
compare(): each relaxed run is paired with the strict run of the same (case, seed);
l_bar = mean per-run l_bar; lambda / rounds_ratio / time_ratio = ratio of paired
means of output_tokens / draft_rounds / wall_time_seconds; capout = finish_reason
== "length"; time_per_round_ratio = time_ratio / rounds_ratio. These are the same
paired means cascade/analysis/speed_ignoring_accuracy.py used for RESULTS.md, so
the script asserts agreement with that CSV (rounds_speedup = 1 / rounds_ratio,
len_ratio = lambda, mean_l_bar, budget-hit rates) before writing.

Left empty because the sources do not have them: bootstrap intervals (*_ci_*;
not in any source), nodes / nodes_strict / same_node* / time_ratio_same_node (the
per-run tables carry no host), accuracy for mtbench (no grader in E1P).

  python3 scripts/fix_gptoss_export.py
"""

from __future__ import annotations

import csv
import math
import pathlib
import re
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parent.parent
TABLES = REPO / "campaign" / "tables"
RESULTS = REPO / "campaign" / "results"
RESULTS_MD = REPO / "cascade" / "RESULTS.md"
SIA = REPO / "cascade" / "results" / "speed_ignoring_accuracy.csv"
OUT = REPO / "campaign" / "addendum" / "tables" / "fix__gpt-oss-20b.csv"

ADDENDUM_FIELDS = [
    "condition", "dataset", "method", "alpha", "n_pairs", "l_bar", "l_bar_strict", "mean_tokens",
    "mean_tokens_strict", "lambda", "rounds_ratio", "time_ratio", "accuracy", "accuracy_strict", "capout_rate",
    "capout_rate_strict", "time_per_round_ratio", "nodes", "nodes_strict", "same_node_pairs", "same_node",
    "lambda_ci_lo", "lambda_ci_hi", "rounds_ratio_ci_lo", "rounds_ratio_ci_hi", "time_ratio_ci_lo",
    "time_ratio_ci_hi", "time_ratio_same_node",
]
EXTRA_FIELDS = ["target", "drafter", "beta", "seeds", "n_seeds", "server", "experiment", "source"]

TARGET = "gpt-oss-20b"
DRAFTER = "nebius/EAGLE3-gpt-oss-20b"
SERVER_BASE = ("Nibi, one H100 SXM, vLLM 0.26.0 (V1 runner), persistent warm server per arm and seed "
               "(scripts/persistent_arm_replay.py)")
# Slurm jobs per experiment (cascade/JOURNAL.md 2026-09-13 .. 2026-09-16); lane = node pool
JOBS = {  # E1P resubmissions reused run.jsons completed by the failed 2026-09-14 submission (skip-if-done)
    ("E1F", "aime24"): "job 21804913 (strict and relaxed arms in this one job)",
    ("E6", "aime24"): "job 21848564 (opt_head arms; strict seed 0 is E1F job 21804913's, identical rows)",
    ("E1P", "gsm8k"): "job 21986969, may reuse runs from failed 21910960 (lane 1, nodes g1-g14)",
    ("E1P", "humaneval"): "job 21986970 + gap-fill 22068663 (tok_lt alpha 0.15), may reuse runs from failed 21910961 "
                          "(lane 1, nodes g1-g14)",
    ("E1P", "livecodebench"): "job 21986971, may reuse runs from failed 21910964 (lane 1, nodes g1-g14)",
    ("E1P", "mtbench"): "job 21988492, may reuse runs from failed 21910962 (lane 2, nodes g15-g28)",
    ("E1P", "longbench_v2"): "jobs 21988496 + refill 22068664, may reuse runs from failed 21910965 (lane 2, nodes g15-g28)",
}

# (experiment, dataset, table/results stem, RESULTS.md section, method, [(params, alpha, beta)], seeds)
TOK_LT = "spec_casc_tok_lt"
OPT_HEAD = "spec_casc_opt_head"
E1P_ALPHAS = [("alpha0.15", "0.15"), ("alpha0.2", "0.2"), ("alpha0.25", "0.25")]
SPECS = [
    ("E1F", "aime24", "aime24_fine", "2.3", TOK_LT,
     [(f"alpha{a}", a, "") for a in ("0.05", "0.1", "0.15", "0.2", "0.25")], ("0", "1", "2")),
    *[("E1P", ds, f"{ds}_proper", "2.3b", TOK_LT, [(p, a, "") for p, a in E1P_ALPHAS], ("0", "1", "2"))
      for ds in ("gsm8k", "humaneval", "livecodebench", "mtbench", "longbench_v2")],
    ("E6", "aime24", "aime24_e6", "2.4", OPT_HEAD,
     [(f"alpha{a.replace('-', 'neg')}_beta{b}", a, b) for b in ("0.15", "0.35") for a in ("-0.3", "-0.1", "-0.02", "0.05")],
     ("0",)),
]


def mean(xs: list[float]) -> float:
    return math.fsum(xs) / len(xs)


def fmt(x):
    if x is None:
        return ""
    if isinstance(x, float):
        return "" if math.isnan(x) else f"{x:.6g}"
    return x


def load_runs(stem: str) -> dict[tuple[str, str], dict[tuple[str, str], dict]]:
    """(method, params) -> (case, seed) -> run, status ok only (as speed_ignoring_accuracy.py)."""
    cells: dict = defaultdict(dict)
    for r in csv.DictReader((TABLES / f"{stem}.csv").open()):
        if r["status"] == "ok":
            cells[(r["method"], r["params"])][(r["case"], r["seed"])] = r
    return cells


def load_accuracy(stem: str) -> dict[tuple[str, str], tuple[float | None, int]]:
    """(method key, alpha) -> (accuracy, n_cases) from campaign/results/<stem>.csv."""
    out = {}
    for r in csv.DictReader((RESULTS / f"{stem}.csv").open()):
        acc = float(r["accuracy"]) if r["accuracy"] not in ("", "None") else None
        out[(r["method"], r["alpha"])] = (acc, int(r["n_cases"]))
    return out


def e6_strict_seed0() -> dict:
    """RESULTS.md 2.4: 'Lossless (seed 0): 2.22 accepted per pass, 2 runaways, 80%.'"""
    text = RESULTS_MD.read_text(encoding="utf-8")
    sec = text.split("### 2.4", 1)[1].split("\n## ", 1)[0]
    m = re.search(r"Lossless \(seed 0\): ([\d.]+) accepted per pass, (\d+) runaways, (\d+)%", sec)
    if not m:
        raise SystemExit("RESULTS.md 2.4: lossless seed-0 line not found")
    return {"l_bar": float(m.group(1)), "runaways": int(m.group(2)), "accuracy_pct": int(m.group(3))}


def load_sia() -> dict[tuple[str, str, str], dict]:
    return {(r["dataset"], r["method"], r["alpha"]): r for r in csv.DictReader(SIA.open())}


def compare(rel: dict, strict: dict) -> dict:
    keys = sorted(set(rel) & set(strict))
    R, S = [rel[k] for k in keys], [strict[k] for k in keys]
    col = lambda runs, k: [float(r[k]) for r in runs]
    Lr, Ls = mean(col(R, "output_tokens")), mean(col(S, "output_tokens"))
    Rr, Rs = mean(col(R, "draft_rounds")), mean(col(S, "draft_rounds"))
    Tr, Ts = mean(col(R, "wall_time_seconds")), mean(col(S, "wall_time_seconds"))
    out = {
        "n_pairs": len(keys),
        "l_bar": mean(col(R, "l_bar")), "l_bar_strict": mean(col(S, "l_bar")),
        "mean_tokens": Lr, "mean_tokens_strict": Ls,
        "lambda": Lr / Ls, "rounds_ratio": Rr / Rs, "time_ratio": Tr / Ts,
        "capout_rate": mean([float(r["finish_reason"] == "length") for r in R]),
        "capout_rate_strict": mean([float(s["finish_reason"] == "length") for s in S]),
        "_capouts_strict": sum(s["finish_reason"] == "length" for s in S),
        "_seeds": sorted({k[1] for k in keys}),
    }
    out["time_per_round_ratio"] = out["time_ratio"] / out["rounds_ratio"]
    return out


def check(label: str, ok: bool) -> None:
    if not ok:
        raise SystemExit(f"cross-check failed: {label}")


def main() -> int:
    sia = load_sia()
    e6_lossless = e6_strict_seed0()
    rows, sources = [], []
    for exp, ds, stem, section, method, points, seeds in SPECS:
        cells = load_runs(stem)
        acc = load_accuracy(stem)
        strict = cells[("strict", "strict")]
        strict = {k: v for k, v in strict.items() if k[1] in seeds}
        for params, alpha, beta in points:
            rel = cells[(method, params)]
            c = compare(rel, strict)
            check(f"{stem} {params}: all relaxed runs paired", c["n_pairs"] == len(rel))
            check(f"{stem} {params}: seeds {c['_seeds']} != {list(seeds)}", c["_seeds"] == list(seeds))
            # cross-check against the 3-decimal values RESULTS.md was built from
            sia_alpha = f"{float(alpha):g}" + (f" (beta{beta})" if beta else "")
            s = sia[(stem, method, sia_alpha)]
            check(f"{stem} {params} n_paired", int(s["n_paired"]) == c["n_pairs"])
            check(f"{stem} {params} mean_l_bar", round(c["l_bar"], 3) == float(s["mean_l_bar"]))
            check(f"{stem} {params} len_ratio", round(c["lambda"], 3) == float(s["len_ratio"]))
            check(f"{stem} {params} rounds_speedup", round(1 / c["rounds_ratio"], 3) == float(s["rounds_speedup"]))
            check(f"{stem} {params} wall_speedup", round(1 / c["time_ratio"], 3) == float(s["wall_speedup"]))
            check(f"{stem} {params} budget_hit_rate", round(c["capout_rate"], 3) == float(s["budget_hit_rate"]))
            # accuracy: campaign/results keys two-knob arms as <method>_beta<b>
            acc_key = (f"{method}_beta{beta}" if beta else method, alpha)
            accuracy, n_cases = acc[acc_key]
            check(f"{stem} {params} accuracy n_cases", n_cases == c["n_pairs"])
            src = [f"campaign/tables/{stem}.csv (method={method}, params={params}, seeds {','.join(seeds)}; "
                   f"strict same case+seed)",
                   f"accuracy: campaign/results/{stem}.csv (method={acc_key[0]}, alpha={alpha})"]
            if exp == "E6":
                # strict paired runs are seed 0 only; campaign/results' strict accuracy pools 3 seeds
                check("E6 strict seed-0 l_bar vs RESULTS.md 2.4", round(c["l_bar_strict"], 2) == e6_lossless["l_bar"])
                check("E6 strict seed-0 runaways vs RESULTS.md 2.4", c["_capouts_strict"] == e6_lossless["runaways"])
                accuracy_strict = e6_lossless["accuracy_pct"] / 100  # 24/30 exactly
                src.append("accuracy_strict: cascade/RESULTS.md 2.4 'Lossless (seed 0): ... 80%'")
            else:
                accuracy_strict, n_strict = acc[("strict", "strict")]
                check(f"{stem} strict accuracy n_cases", n_strict == c["n_pairs"])
                src.append(f"accuracy_strict: campaign/results/{stem}.csv (strict)")
            src.append(f"reported in cascade/RESULTS.md {section}")
            row = {k: v for k, v in c.items() if not k.startswith("_")}
            row.update({
                "condition": "fix", "dataset": ds, "method": method, "alpha": alpha,
                "accuracy": accuracy, "accuracy_strict": accuracy_strict,
                "target": TARGET, "drafter": DRAFTER, "beta": beta,
                "seeds": ",".join(seeds), "n_seeds": len(seeds),
                "server": f"{SERVER_BASE}; {JOBS[(exp, ds)]}", "experiment": exp, "source": "; ".join(src),
            })
            rows.append(row)
            sources.append((exp, ds, method, alpha, beta, src))

    fields = ADDENDUM_FIELDS + EXTRA_FIELDS
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: fmt(r.get(k)) for k in fields})
    print(f"wrote {OUT.relative_to(REPO)} ({len(rows)} rows); all cross-checks against "
          f"{SIA.relative_to(REPO)} passed")
    for exp, ds, method, alpha, beta, src in sources:
        print(f"  {exp:4s} {ds:14s} {method:20s} alpha={alpha:6s}" + (f" beta={beta}" if beta else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
