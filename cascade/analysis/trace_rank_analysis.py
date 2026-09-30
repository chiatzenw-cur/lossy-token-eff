#!/usr/bin/env python3
"""Where do relaxed rules commit tokens the verifier did not want -- and does
that predict length inflation? (DIRECTIONS.md D2, no GPU needed.)

Every relaxed run's proposals.jsonl (patches/relaxation_trace.py) records,
per emitted token, whether the strict rule would have accepted it
(`strict_would_accept`), whether it was emitted only because the bar was
lowered (`lossy_only_accepted`), and the drafted token's standing under the
verifier: `p`, `target_rank` (0 = the verifier's argmax) and
`target_top1_prob`. So for every lossy-only accept we can ask how far
outside the verifier's head it was.

"Outside the head at beta" reuses spec-casc-tok's own trusted-set
definition: p(x) < (1 - beta) * max_w p(w). At beta = 0.8 (tok's loosest
campaign alpha) that is p(x) < 0.2 * top1.

Per arm (dataset, method, params) this reports:
  lossy_only_per_1k     lossy-only accepts per 1000 emitted tokens
  ooh80_share           share of lossy-only accepts outside the head at beta=0.8
  ooh80_per_1k          those per 1000 emitted tokens (the exposure measure)
  rank_ge1/3/10_share   share of lossy-only accepts with verifier rank >= 1/3/10
  len_ratio             mean completion length / strict's, paired by case
  budget_hit_rate       fraction of runs that hit --max-new-tokens
  r_len_vs_ooh80        Pearson r across cases: per-case ooh80_per_1k vs per-case
                        length ratio to strict (Spearman rho alongside)
  ooh80_per_1k in stop runs / early part of budget-hit runs / late part
and a per-case CSV for anything finer.

Strict runs have no lossy-only accepts by definition; their row reports how
often *lossless* verification itself commits out-of-head tokens (accepted
rows with p < 0.2*top1), the natural baseline.

Usage:
  python3 cascade/analysis/trace_rank_analysis.py                 # old_runs/{humaneval,aime24}
  python3 cascade/analysis/trace_rank_analysis.py --runs-root runs --datasets gsm8k
Writes cascade/results/trace_rank_analysis.{md,csv} and
cascade/results/trace_rank_analysis_cases.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import re
import statistics
from collections import defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO_ROOT / "cascade" / "results"
TAXONOMY = ("strict", "mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok")
CASE_RE = re.compile(r"^case_\d{3}$")
BETAS = (0.8, 0.5)  # head widths: p(x) < (1-beta)*top1 is "outside"


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(sxx * syy)


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def spearman(xs: list[float], ys: list[float]) -> float | None:
    return pearson(ranks(xs), ranks(ys)) if len(xs) >= 3 else None


def scan_run(run_dir: pathlib.Path) -> dict | None:
    trace = run_dir / "proposals.jsonl"
    run_json = run_dir / "run.json"
    if not trace.is_file() or not run_json.is_file():
        return None
    meta = json.loads(run_json.read_text())
    if meta.get("status") != "ok":
        return None
    n_emitted = 0
    n_accept = 0
    n_lossy_only = 0
    ooh_lossy = {b: 0 for b in BETAS}
    ooh_accept = {b: 0 for b in BETAS}  # among ALL accepted rows (strict baseline uses this)
    rank_ge = {1: 0, 3: 0, 10: 0}
    lossy_ranks: list[int] = []
    ooh80_positions: list[int] = []
    with trace.open() as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            n_emitted += 1
            if not row.get("actually_accepted"):
                continue
            p, top1 = row.get("p"), row.get("target_top1_prob")
            if p is None or top1 is None:
                continue
            n_accept += 1
            for b in BETAS:
                if p < (1.0 - b) * top1:
                    ooh_accept[b] += 1
            if row.get("lossy_only_accepted"):
                n_lossy_only += 1
                rank = int(row.get("target_rank") or 0)
                lossy_ranks.append(rank)
                for k in rank_ge:
                    if rank >= k:
                        rank_ge[k] += 1
                for b in BETAS:
                    if p < (1.0 - b) * top1:
                        ooh_lossy[b] += 1
                        if b == 0.8:
                            ooh80_positions.append(int(row.get("output_position") or 0))
    return {
        "output_tokens": int(meta.get("output_tokens") or n_emitted),
        "budget_hit": meta.get("finish_reason") == "length",
        "n_emitted": n_emitted,
        "n_accept": n_accept,
        "n_lossy_only": n_lossy_only,
        "ooh_lossy": ooh_lossy,
        "ooh_accept": ooh_accept,
        "rank_ge": rank_ge,
        "lossy_ranks": lossy_ranks,
        "ooh80_positions": ooh80_positions,
    }


def per_1k(count: int, denom: int) -> float:
    return 1000.0 * count / denom if denom else 0.0


def analyse(runs_root: pathlib.Path, dataset: str, methods: tuple[str, ...]) -> tuple[list[dict], list[dict]]:
    ds_root = runs_root / dataset
    if not ds_root.is_dir():
        return [], []
    runs: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    for method_dir in sorted(ds_root.iterdir()):
        if method_dir.name not in methods:
            continue
        for params_dir in sorted(method_dir.iterdir()):
            if not params_dir.is_dir():
                continue
            for case_dir in sorted(params_dir.iterdir()):
                if not CASE_RE.match(case_dir.name):
                    continue
                scanned = scan_run(case_dir / "seed_0")
                if scanned:
                    runs[(method_dir.name, params_dir.name)][case_dir.name] = scanned
    strict = runs.get(("strict", "strict"), {})
    arm_rows: list[dict] = []
    case_rows: list[dict] = []
    for (method, params), cases in sorted(runs.items()):
        paired = sorted(set(cases) & set(strict)) if strict else []
        tot_emitted = sum(r["n_emitted"] for r in cases.values())
        tot_accept = sum(r["n_accept"] for r in cases.values())
        tot_lossy = sum(r["n_lossy_only"] for r in cases.values())
        tot_ooh80 = sum(r["ooh_lossy"][0.8] for r in cases.values())
        tot_ooh50 = sum(r["ooh_lossy"][0.5] for r in cases.values())
        tot_acc_ooh80 = sum(r["ooh_accept"][0.8] for r in cases.values())
        all_ranks = [rk for r in cases.values() for rk in r["lossy_ranks"]]
        rank_ge = {k: sum(r["rank_ge"][k] for r in cases.values()) for k in (1, 3, 10)}
        xs, ys = [], []
        stop_ooh, stop_emit = 0, 0
        early_ooh, early_emit, late_ooh, late_emit = 0, 0, 0, 0
        for case, r in cases.items():
            ooh80_rate = per_1k(r["ooh_lossy"][0.8], r["n_emitted"])
            len_ratio = r["output_tokens"] / strict[case]["output_tokens"] if case in strict and strict[case]["output_tokens"] else None
            case_rows.append({
                "dataset": dataset, "method": method, "params": params, "case": case,
                "output_tokens": r["output_tokens"], "budget_hit": r["budget_hit"],
                "len_ratio_vs_strict": round(len_ratio, 4) if len_ratio else "",
                "n_emitted": r["n_emitted"], "n_lossy_only": r["n_lossy_only"],
                "lossy_only_per_1k": round(per_1k(r["n_lossy_only"], r["n_emitted"]), 3),
                "ooh80": r["ooh_lossy"][0.8], "ooh80_per_1k": round(ooh80_rate, 3),
                "ooh50_per_1k": round(per_1k(r["ooh_lossy"][0.5], r["n_emitted"]), 3),
                "accepted_ooh80_per_1k": round(per_1k(r["ooh_accept"][0.8], r["n_emitted"]), 3),
            })
            if len_ratio is not None:
                xs.append(ooh80_rate)
                ys.append(len_ratio)
            if r["budget_hit"]:
                quarter = r["n_emitted"] // 4
                early = sum(1 for pos in r["ooh80_positions"] if pos < quarter)
                late = sum(1 for pos in r["ooh80_positions"] if pos >= r["n_emitted"] - quarter)
                early_ooh += early
                late_ooh += late
                early_emit += quarter
                late_emit += quarter
            else:
                stop_ooh += r["ooh_lossy"][0.8]
                stop_emit += r["n_emitted"]
        m_len = statistics.fmean(cases[c]["output_tokens"] for c in paired) if paired else None
        s_len = statistics.fmean(strict[c]["output_tokens"] for c in paired) if paired else None
        arm_rows.append({
            "dataset": dataset, "method": method, "params": params, "n_runs": len(cases),
            "mean_output_tokens": round(statistics.fmean(r["output_tokens"] for r in cases.values()), 1),
            "len_ratio": round(m_len / s_len, 3) if m_len and s_len else "",
            "budget_hit_rate": round(sum(r["budget_hit"] for r in cases.values()) / len(cases), 3),
            "accept_rate": round(tot_accept / tot_emitted, 3) if tot_emitted else "",
            "lossy_only_per_1k": round(per_1k(tot_lossy, tot_emitted), 2),
            "ooh80_share": round(tot_ooh80 / tot_lossy, 3) if tot_lossy else "",
            "ooh50_share": round(tot_ooh50 / tot_lossy, 3) if tot_lossy else "",
            "ooh80_per_1k": round(per_1k(tot_ooh80, tot_emitted), 2),
            "accepted_ooh80_per_1k": round(per_1k(tot_acc_ooh80, tot_emitted), 2),
            "rank_ge1_share": round(rank_ge[1] / tot_lossy, 3) if tot_lossy else "",
            "rank_ge3_share": round(rank_ge[3] / tot_lossy, 3) if tot_lossy else "",
            "rank_ge10_share": round(rank_ge[10] / tot_lossy, 3) if tot_lossy else "",
            "median_lossy_rank": statistics.median(all_ranks) if all_ranks else "",
            "r_len_vs_ooh80": round(pearson(xs, ys), 3) if pearson(xs, ys) is not None else "",
            "rho_len_vs_ooh80": round(spearman(xs, ys), 3) if spearman(xs, ys) is not None else "",
            "n_corr": len(xs),
            "ooh80_per_1k_stop_runs": round(per_1k(stop_ooh, stop_emit), 2),
            "ooh80_per_1k_budget_runs_first_quarter": round(per_1k(early_ooh, early_emit), 2) if early_emit else "",
            "ooh80_per_1k_budget_runs_last_quarter": round(per_1k(late_ooh, late_emit), 2) if late_emit else "",
        })
    return arm_rows, case_rows


def fmt(v) -> str:
    if v == "" or v is None:
        return "--"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def write_markdown(arm_rows: list[dict], path: pathlib.Path) -> None:
    lines = [
        "# Out-of-head accepts vs length inflation (trace analysis)",
        "",
        "Generated by `cascade/analysis/trace_rank_analysis.py`. A *lossy-only* accept is a "
        "token emitted only because the relaxed rule lowered the bar (strict would have "
        "rejected it). `ooh80` = that token had p(x) < 0.2 * max p under the verifier, i.e. it "
        "was outside spec-casc-tok's trusted head at alpha 0.8. Rates are per 1000 emitted "
        "tokens. `len_ratio` is paired against strict on the same cases. `r`/`rho` correlate, "
        "across cases within an arm, the per-case ooh80 rate with the per-case length ratio.",
        "",
    ]
    datasets = sorted({r["dataset"] for r in arm_rows})
    for dataset in datasets:
        lines += [
            f"## {dataset}",
            "",
            "| method | params | n | len_ratio | budget_hit | lossy-only /1k | ooh80 share | ooh80 /1k | ooh50 share | rank>=1 | rank>=3 | rank>=10 | median rank | r (rho) len vs ooh80 | ooh80/1k stop runs | budget runs: first ¼ | last ¼ | accepted ooh80 /1k (all accepts) |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|",
        ]
        for r in sorted((r for r in arm_rows if r["dataset"] == dataset), key=lambda r: (r["method"] != "strict", r["method"], r["params"])):
            corr = f"{fmt(r['r_len_vs_ooh80'])} ({fmt(r['rho_len_vs_ooh80'])}), n={r['n_corr']}"
            lines.append(
                f"| {r['method']} | {r['params']} | {r['n_runs']} | {fmt(r['len_ratio'])} | {fmt(r['budget_hit_rate'])} | "
                f"{fmt(r['lossy_only_per_1k'])} | {fmt(r['ooh80_share'])} | {fmt(r['ooh80_per_1k'])} | {fmt(r['ooh50_share'])} | "
                f"{fmt(r['rank_ge1_share'])} | {fmt(r['rank_ge3_share'])} | {fmt(r['rank_ge10_share'])} | {fmt(r['median_lossy_rank'])} | "
                f"{corr} | {fmt(r['ooh80_per_1k_stop_runs'])} | {fmt(r['ooh80_per_1k_budget_runs_first_quarter'])} | "
                f"{fmt(r['ooh80_per_1k_budget_runs_last_quarter'])} | {fmt(r['accepted_ooh80_per_1k'])} |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-root", type=pathlib.Path, default=REPO_ROOT / "old_runs")
    parser.add_argument("--datasets", nargs="+", default=["humaneval", "aime24"])
    parser.add_argument("--methods", nargs="+", default=list(TAXONOMY))
    parser.add_argument("--out-prefix", type=pathlib.Path, default=OUT_DIR / "trace_rank_analysis")
    args = parser.parse_args()

    arm_rows: list[dict] = []
    case_rows: list[dict] = []
    for dataset in args.datasets:
        a, c = analyse(args.runs_root, dataset, tuple(args.methods))
        print(f"{dataset}: {len(a)} arms, {len(c)} runs scanned", flush=True)
        arm_rows += a
        case_rows += c
    if not arm_rows:
        print("no traced runs found under", args.runs_root)
        return 1
    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{args.out_prefix}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(arm_rows[0].keys()))
        w.writeheader()
        w.writerows(arm_rows)
    with open(f"{args.out_prefix}_cases.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(case_rows[0].keys()))
        w.writeheader()
        w.writerows(case_rows)
    write_markdown(arm_rows, pathlib.Path(f"{args.out_prefix}.md"))
    print(f"wrote {args.out_prefix}.md / .csv / _cases.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
