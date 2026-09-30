#!/usr/bin/env python3
"""Hardware dependence of the time measurements (campaign/addendum/README.md, found in step 2).

The campaign's seed-0 runs ran on the old box (H100 PCIe); the addendum's seeds 1-2 on Nibi (H100
SXM). lambda and the rounds ratio agree across machines; the time ratio does not. This script writes
the evidence to campaign/addendum/analysis/:

  seed_shift.csv            per metric (lambda, rounds ratio, time ratio): mean seed-1 - seed-0,
                            seed-2 - seed-0 and seed-2 - seed-1 differences over the GPT-OSS cells
                            with seeds 0-2 complete, cells where the Nibi seed is lower, win/loss flips
  hardware_tpr_ratio.csv    per cell and seed: time-per-round ratio relaxed / strict (mean of per-run
                            wall_time_seconds / draft_rounds over paired cases)
  hardware_tpr_model.csv    per machine and dataset: OLS of per-run time per round on tokens per round
                            (l_bar + 1), strict + loosest arms: intercept c0, slope c1, R^2

  python3 scripts/addendum_hardware.py
"""

from __future__ import annotations

import csv
import statistics as st
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import addendum_tables as t  # noqa: E402

OUT = t.ADD / "analysis"
DATASETS = ("gsm8k", "humaneval", "mtbench", "livecodebench", "aime24", "longbench_v2")
MACHINE = {0: "old box (H100 PCIe)", 1: "Nibi (H100 SXM)", 2: "Nibi (H100 SXM)"}


def write(name: str, rows: list[dict]) -> None:
    t.write_csv(OUT / name, rows)


def main() -> int:
    tpr_rows, shift_input = [], []
    for ds in DATASETS:
        for m in t.FIVE:
            a = t.loosest(ds, m)
            per_seed = {}
            for s in (0, 1, 2):
                R, S = t.load_cell(ds, m, a, s), t.load_cell(ds, "strict", "strict", s)
                cases = sorted(set(R) & set(S))
                if len(cases) < t.N_CASES[ds]:
                    continue
                tpr = lambda runs: st.mean(runs[c]["wall_time_seconds"] / runs[c]["draft_rounds"] for c in cases)
                c = t.compare(R, S)
                per_seed[s] = {"tpr_ratio": tpr(R) / tpr(S), **c}
                tpr_rows.append({"target": "gpt-oss-20b", "dataset": ds, "method": m, "alpha": a, "seed": s,
                                 "machine": MACHINE[s], "n_pairs": len(cases), "time_per_round_ratio": tpr(R) / tpr(S),
                                 "lambda": c["lambda"], "rounds_ratio": c["rounds_ratio"], "time_ratio": c["time_ratio"]})
            if all(s in per_seed for s in (0, 1, 2)):
                shift_input.append((ds, m, per_seed))
    write("hardware_tpr_ratio.csv", tpr_rows)

    shift = []
    for metric in ("lambda", "rounds_ratio", "time_ratio", "tpr_ratio"):
        d10 = [p[1][metric] - p[0][metric] for _, _, p in shift_input]
        d20 = [p[2][metric] - p[0][metric] for _, _, p in shift_input]
        d21 = [p[2][metric] - p[1][metric] for _, _, p in shift_input]
        row = {"metric": metric, "n_cells": len(shift_input),
               "mean_s1_minus_s0": st.mean(d10), "mean_s2_minus_s0": st.mean(d20), "mean_s2_minus_s1": st.mean(d21),
               "cells_s1_below_s0": sum(x < 0 for x in d10), "cells_s2_below_s0": sum(x < 0 for x in d20),
               "mean_s0": st.mean(p[0][metric] for _, _, p in shift_input),
               "mean_s1": st.mean(p[1][metric] for _, _, p in shift_input),
               "mean_s2": st.mean(p[2][metric] for _, _, p in shift_input)}
        if metric in ("rounds_ratio", "time_ratio"):
            row["cells_win_loss_flip_across_seeds"] = sum(
                len({p[s][metric] < 1 for s in (0, 1, 2)}) > 1 for _, _, p in shift_input)
        shift.append(row)
    write("seed_shift.csv", shift)

    model = []
    for label, seeds in (("old box (H100 PCIe), seed 0", (0,)), ("Nibi (H100 SXM), seeds 1-2", (1, 2))):
        for ds in DATASETS:
            x, y = [], []
            for m in ["strict", *t.FIVE]:
                a = "strict" if m == "strict" else t.loosest(ds, m)
                for s in seeds:
                    for r in t.load_cell(ds, m, a, s).values():
                        if r["draft_rounds"] and r["l_bar"] is not None:
                            x.append(r["l_bar"] + 1)
                            y.append(r["wall_time_seconds"] / r["draft_rounds"])
            if len(x) < 20:
                continue
            x, y = np.array(x), np.array(y)
            c1, c0 = np.polyfit(x, y, 1)
            r2 = 1 - ((y - (c0 + c1 * x)) ** 2).sum() / ((y - y.mean()) ** 2).sum()
            model.append({"machine": label, "dataset": ds, "n_runs": len(x), "c0_ms": 1000 * c0,
                          "c1_ms_per_token": 1000 * c1, "c1_over_c0": c1 / c0, "r2": r2,
                          "mean_time_per_round_ms": 1000 * y.mean()})
    write("hardware_tpr_model.csv", model)

    readme = OUT / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    lines = {
        "seed_shift.csv": "GPT-OSS cells with seeds 0-2 complete (step 2): mean differences between seeds of lambda, "
        "rounds ratio, time ratio and time-per-round ratio; seed 0 ran on the old box (H100 PCIe), seeds 1-2 on Nibi "
        "(H100 SXM); win/loss flips = cells whose ratio is on both sides of 1 across the three seeds. "
        "(scripts/addendum_hardware.py)",
        "hardware_tpr_ratio.csv": "per GPT-OSS loosest cell and seed: time-per-round ratio relaxed / strict (mean of "
        "per-run wall_time_seconds / draft_rounds over paired cases), with lambda, rounds and time ratios. "
        "(scripts/addendum_hardware.py)",
        "hardware_tpr_model.csv": "per machine and dataset: OLS of per-run time per round (s) on tokens per round "
        "(l_bar + 1) over strict + loosest-arm runs; c0 = fixed cost per round, c1 = cost per emitted token. "
        "(scripts/addendum_hardware.py)",
    }
    for name, desc in lines.items():
        entry = f"- `{name}`: {desc}"
        if f"- `{name}`:" not in text:
            text = text.rstrip("\n") + "\n" + entry + "\n"
    readme.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
