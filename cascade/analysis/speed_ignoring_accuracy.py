#!/usr/bin/env python3
"""Length-corrected speed of every (method, alpha) point, ignoring accuracy.

Answers the question from the 2026-09 group meeting: "forget accuracy -- is
there any setting that actually speeds up end-to-end output, without the
output being obvious garbage?" campaign/FINDINGS.md's speed table is the
*mean accepted length* ratio (l̄ speedup), which is only the per-round gain.
This script uses what campaign/tables/<dataset>.csv already records per case
to compute the end-to-end quantities instead:

  rounds_speedup = strict mean verifier rounds / method mean verifier rounds
                   (paired over the cases both arms ran; one round = one
                   target forward pass, so this IS the length-corrected
                   speedup of Xia et al. Eq. 4 up to the drafter-cost term)
  wall_speedup   = strict mean wall_time_seconds / method mean wall_time_seconds
                   (actual measured generation time on the H100 box, batch 1)
  len_ratio      = method mean completion length / strict mean completion length
  lc_speedup     = ((l̄_method+1)/(l̄_strict+1)) / len_ratio   -- Eq. 4 rebuilt
                   from l̄ and length, as a cross-check on rounds_speedup

"Garbage" is measured, not eyeballed: budget_hit_rate is the fraction of
cases whose finish_reason is "length" (the generation ran into
--max-new-tokens, which is what repetition loops and rambling look like in
these tables), and no_final_rate (GPT-OSS only) is the fraction that never
opened the Harmony final channel. A point is flagged clean when its
budget_hit_rate is within +5 percentage points of strict's own on that
dataset. Accuracy is joined from campaign/results/<dataset>.csv for context
only -- it does not enter the ranking.

Caveat carried over from campaign/JOURNAL.md: the 50->150 case extensions
ran with scripts/persistent_arm_replay.py (one warm server per arm), so
per-case wall times and lengths for ordinal>1 requests carry the documented
warm-engine confound. Rounds and lengths are still what the model produced;
treat wall_speedup as the noisier of the two speed columns.

Usage (stdlib only, runs anywhere):
  python3 cascade/analysis/speed_ignoring_accuracy.py
Writes cascade/results/speed_ignoring_accuracy.{csv,md}.
"""

from __future__ import annotations

import csv
import glob
import os
import pathlib
import statistics
from collections import defaultdict

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TABLES = REPO_ROOT / "campaign" / "tables"
RESULTS = REPO_ROOT / "campaign" / "results"
OUT_DIR = REPO_ROOT / "cascade" / "results"
CLEAN_TOLERANCE = 0.05  # absolute, on budget_hit_rate vs strict
MIN_FULL_FRACTION = 0.5  # a point counts as "full sweep" if it paired with >= half of strict's cases

METHOD_ORDER = ["strict", "mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok"]


def params_to_alpha(params: str) -> float | None:
    """'alpha0.35' -> 0.35, 'alphaneg0.3' -> -0.3; guard variants carry extra
    knobs after the alpha ('alpha0.3_budget10_pct90_k8'), only the leading
    alpha is parsed."""
    if params == "strict":
        return None
    head = params.split("_", 1)[0]
    return float(head.replace("alpha", "", 1).replace("neg", "-"))


def params_label(params: str) -> str:
    if params == "strict":
        return ""
    alpha = params_to_alpha(params)
    extra = params.split("_", 1)[1] if "_" in params else ""
    return f"{alpha:g}" + (f" ({extra})" if extra else "")


def load_accuracy(dataset: str) -> dict[tuple[str, float | None], float | None]:
    path = RESULTS / f"{dataset}.csv"
    table: dict[tuple[str, float | None], float | None] = {}
    if not path.is_file():
        return table
    for row in csv.DictReader(path.open()):
        alpha = None if row["alpha"] == "strict" else float(row["alpha"])
        acc = row.get("accuracy", "")
        table[(row["method"], alpha)] = float(acc) if acc not in ("", "None") else None
    return table


def fmean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def analyse_dataset(path: pathlib.Path) -> list[dict]:
    dataset = path.stem
    rows = [r for r in csv.DictReader(path.open()) if r["status"] == "ok"]
    # keyed by (case, seed): multi-seed sweeps pair each run with strict's
    # run of the same problem AND seed, instead of collapsing to one seed
    by_arm: dict[tuple[str, str], dict[tuple[str, str], dict]] = defaultdict(dict)
    for r in rows:
        by_arm[(r["method"], r["params"])][(r["case"], r.get("seed", "0"))] = r
    strict = by_arm.get(("strict", "strict"))
    if not strict:
        print(f"{dataset}: no strict rows, skipped")
        return []
    accuracy = load_accuracy(dataset)
    is_gpt_oss = not dataset.endswith("_qwen3")

    out: list[dict] = []
    for (method, params), cases in by_arm.items():
        paired = sorted(set(cases) & set(strict))
        if not paired:
            continue
        m_rounds = fmean([float(cases[c]["draft_rounds"]) for c in paired])
        s_rounds = fmean([float(strict[c]["draft_rounds"]) for c in paired])
        m_len = fmean([float(cases[c]["output_tokens"]) for c in paired])
        s_len = fmean([float(strict[c]["output_tokens"]) for c in paired])
        m_wall = fmean([float(cases[c]["wall_time_seconds"]) for c in paired])
        s_wall = fmean([float(strict[c]["wall_time_seconds"]) for c in paired])
        m_lbar = fmean([float(cases[c]["l_bar"]) for c in paired])
        s_lbar = fmean([float(strict[c]["l_bar"]) for c in paired])
        budget_hit = fmean([1.0 if cases[c]["finish_reason"] == "length" else 0.0 for c in paired])
        s_budget_hit = fmean([1.0 if strict[c]["finish_reason"] == "length" else 0.0 for c in paired])
        no_final = (
            fmean([1.0 if cases[c]["reached_final_channel"] != "True" else 0.0 for c in paired])
            if is_gpt_oss else None
        )
        len_ratio = m_len / s_len
        rounds_speedup = s_rounds / m_rounds
        wall_speedup = s_wall / m_wall if m_wall else None
        lc_speedup = ((m_lbar + 1.0) / (s_lbar + 1.0)) / len_ratio
        alpha = params_to_alpha(params)
        # two-knob methods are keyed in campaign/results as "<method>_<extra>"
        # (e.g. spec_casc_opt_head_beta0.8) by campaign_report.py
        extra = params.split("_", 1)[1] if "_" in params else ""
        acc = accuracy.get((f"{method}_{extra}", alpha)) if extra else accuracy.get((method, alpha))
        out.append({
            "dataset": dataset,
            "method": method,
            "alpha": params_label(params),
            "n_paired": len(paired),
            "n_strict": len(strict),
            # calibration-only grid points ran on 3 probe cases; the full
            # sweep ran every case. Headline tables only rank full points.
            "full": len(paired) >= MIN_FULL_FRACTION * len(strict),
            "mean_l_bar": round(m_lbar, 3),
            "len_ratio": round(len_ratio, 3),
            "rounds_speedup": round(rounds_speedup, 3),
            "lc_speedup": round(lc_speedup, 3),
            "wall_speedup": round(wall_speedup, 3) if wall_speedup else "",
            "budget_hit_rate": round(budget_hit, 3),
            "strict_budget_hit_rate": round(s_budget_hit, 3),
            "no_final_rate": "" if no_final is None else round(no_final, 3),
            "clean": budget_hit <= s_budget_hit + CLEAN_TOLERANCE,
            "accuracy": acc,
            "strict_accuracy": accuracy.get(("strict", None)),
        })
    return out


def method_rank(method: str) -> int:
    return METHOD_ORDER.index(method) if method in METHOD_ORDER else len(METHOD_ORDER)


def fmt(value, digits=2) -> str:
    if value is None or value == "":
        return "--"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_markdown(all_rows: list[dict], path: pathlib.Path) -> None:
    lines = [
        "# Length-corrected speed, ignoring accuracy",
        "",
        "Generated by `cascade/analysis/speed_ignoring_accuracy.py` from "
        "`campaign/tables/*.csv` (paired against `strict` on the same cases). "
        "`rounds_speedup` = strict rounds / method rounds, the end-to-end proxy; "
        "`len_ratio` > 1 means longer completions than lossless; `budget_hit` is the "
        "fraction of cases that ran into `--max-new-tokens`; `clean` means budget_hit "
        f"is within +{CLEAN_TOLERANCE:.0%} of strict's own rate. Accuracy is context only.",
        "",
        "Only full-sweep points (paired with at least half of strict's cases) are ranked in "
        "the two headline tables; 3-case calibration probes are listed in the per-dataset "
        "tables with their `n` for completeness but are too noisy to rank.",
        "",
        "## Best clean point per dataset (max rounds_speedup among clean full-sweep points)",
        "",
        "| dataset | method | alpha | n | rounds_speedup | wall_speedup | len_ratio | l̄ | budget_hit (strict) | accuracy (strict) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    datasets = sorted({r["dataset"] for r in all_rows}, key=lambda d: (d.endswith("_qwen3"), d))
    for dataset in datasets:
        candidates = [
            r for r in all_rows
            if r["dataset"] == dataset and r["method"] != "strict" and r["clean"] and r["full"]
        ]
        if not candidates:
            lines.append(f"| {dataset} | (no clean lossy point) | | | | | | | | |")
            continue
        best = max(candidates, key=lambda r: r["rounds_speedup"])
        lines.append(
            f"| {dataset} | {best['method']} | {best['alpha']} | {best['n_paired']} | {fmt(best['rounds_speedup'])} | "
            f"{fmt(best['wall_speedup'])} | {fmt(best['len_ratio'])} | {fmt(best['mean_l_bar'])} | "
            f"{fmt(best['budget_hit_rate'])} ({fmt(best['strict_budget_hit_rate'])}) | "
            f"{fmt(best['accuracy'])} ({fmt(best['strict_accuracy'])}) |"
        )

    lines += [
        "",
        "## Best full-sweep point per dataset with NO garbage filter (max rounds_speedup)",
        "",
        "| dataset | method | alpha | n | rounds_speedup | len_ratio | budget_hit (strict) | accuracy (strict) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for dataset in datasets:
        candidates = [r for r in all_rows if r["dataset"] == dataset and r["method"] != "strict" and r["full"]]
        if not candidates:
            continue
        best = max(candidates, key=lambda r: r["rounds_speedup"])
        lines.append(
            f"| {dataset} | {best['method']} | {best['alpha']} | {best['n_paired']} | {fmt(best['rounds_speedup'])} | "
            f"{fmt(best['len_ratio'])} | {fmt(best['budget_hit_rate'])} ({fmt(best['strict_budget_hit_rate'])}) | "
            f"{fmt(best['accuracy'])} ({fmt(best['strict_accuracy'])}) |"
        )

    lines += [
        "",
        "## Speculative cascades only (both variants, every full-sweep alpha)",
        "",
        "| dataset | method | alpha | n | l̄ | rounds_speedup | lc_speedup | wall_speedup | len_ratio | budget_hit (strict) | clean | accuracy (strict) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for dataset in datasets:
        for r in sorted(
            (r for r in all_rows if r["dataset"] == dataset and r["method"].startswith("spec_casc") and r["full"]),
            key=lambda r: (r["method"], float(r["alpha"].split(" ")[0])),
        ):
            lines.append(
                f"| {dataset} | {r['method']} | {r['alpha']} | {r['n_paired']} | {fmt(r['mean_l_bar'])} | {fmt(r['rounds_speedup'])} | "
                f"{fmt(r['lc_speedup'])} | {fmt(r['wall_speedup'])} | {fmt(r['len_ratio'])} | "
                f"{fmt(r['budget_hit_rate'])} ({fmt(r['strict_budget_hit_rate'])}) | {fmt(r['clean'])} | "
                f"{fmt(r['accuracy'])} ({fmt(r['strict_accuracy'])}) |"
            )

    lines += ["", "## Every point, per dataset (sorted by rounds_speedup)", ""]
    for dataset in datasets:
        lines += [
            f"### {dataset}",
            "",
            "| method | alpha | n | l̄ | rounds_speedup | lc_speedup | wall_speedup | len_ratio | budget_hit | no_final | clean | accuracy |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
        ]
        rows = sorted(
            (r for r in all_rows if r["dataset"] == dataset),
            key=lambda r: (-r["rounds_speedup"], method_rank(r["method"])),
        )
        for r in rows:
            lines.append(
                f"| {r['method']} | {r['alpha'] or 'strict'} | {r['n_paired']} | {fmt(r['mean_l_bar'])} | "
                f"{fmt(r['rounds_speedup'])} | {fmt(r['lc_speedup'])} | {fmt(r['wall_speedup'])} | {fmt(r['len_ratio'])} | "
                f"{fmt(r['budget_hit_rate'])} | {fmt(r['no_final_rate'])} | {fmt(r['clean'])} | {fmt(r['accuracy'])} |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    all_rows: list[dict] = []
    for path in sorted(glob.glob(str(TABLES / "*.csv"))):
        all_rows.extend(analyse_dataset(pathlib.Path(path)))
    if not all_rows:
        print("no data found under", TABLES)
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "speed_ignoring_accuracy.csv"
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
        writer.writeheader()
        writer.writerows(all_rows)
    md_path = OUT_DIR / "speed_ignoring_accuracy.md"
    write_markdown(all_rows, md_path)
    print(f"wrote {os.path.relpath(csv_path, REPO_ROOT)} ({len(all_rows)} rows) and {os.path.relpath(md_path, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
