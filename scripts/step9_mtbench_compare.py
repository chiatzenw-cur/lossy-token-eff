#!/usr/bin/env python3
"""MT-Bench judge scores of the step-8 / step-9 arms against their own pair's lossless run, paired by question:
mean score (1-10; a run with no readable answer scores 1, as the addendum's step 1.9), the paired difference
arm - lossless with a 95% bootstrap interval (10,000 resamples, numpy seed 20261001), over the questions both have a
score for (judge refusals dropped pairwise). Reads step9/mtbench_judge/mtbench_judge.csv
(scripts/step9_mtbench_judge.py collect); writes step9/mtbench_judge/mtbench_vs_lossless.csv.
"""
import csv
import pathlib

import numpy as np

REPO = pathlib.Path(__file__).resolve().parent.parent
D = REPO / "campaign" / "addendum" / "step9" / "mtbench_judge"


def main() -> int:
    rows = list(csv.DictReader((D / "mtbench_judge.csv").open(newline="", encoding="utf-8")))
    cells: dict[tuple, dict[str, float]] = {}
    for r in rows:
        if r["score"] in ("", None):
            continue
        cells.setdefault((r["target"], r["method"], r["alpha"]), {})[r["case"]] = float(r["score"])
    rng = np.random.default_rng(20261001)
    out = []
    for (pair, method, alpha), cell in sorted(cells.items()):
        if method == "strict":
            continue
        base = cells.get((pair, "strict", "strict"), {})
        cases = sorted(set(cell) & set(base))
        a = np.array([cell[c] for c in cases])
        b = np.array([base[c] for c in cases])
        d = a - b
        boot = d[rng.integers(0, len(d), size=(10000, len(d)))].mean(axis=1)
        out.append({"pair": pair, "method": method, "alpha": alpha, "n_pairs": len(cases),
                    "score": round(float(a.mean()), 3), "score_lossless": round(float(b.mean()), 3),
                    "diff": round(float(d.mean()), 3), "diff_ci_lo": round(float(np.percentile(boot, 2.5)), 3),
                    "diff_ci_hi": round(float(np.percentile(boot, 97.5)), 3)})
    with (D / "mtbench_vs_lossless.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(out)
    for r in out:
        flag = " *" if r["diff_ci_hi"] < 0 or r["diff_ci_lo"] > 0 else ""
        print(f"{r['pair']:34s} {r['method']:13s} {r['alpha']:>6s} {r['score']:5.2f} vs {r['score_lossless']:5.2f} "
              f"diff {r['diff']:+.2f} [{r['diff_ci_lo']:+.2f}, {r['diff_ci_hi']:+.2f}]{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
