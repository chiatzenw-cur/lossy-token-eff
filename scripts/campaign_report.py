#!/usr/bin/env python3
"""Build the per-dataset deliverables from campaign/PLAN.md's run tree:

  1. campaign/tables/<dataset>.csv       every run.json found, one row per
                                          (method, alpha, case) -- the
                                          "table on run metrics per case"
  2. campaign/results/<dataset>.csv      aggregated (method, alpha) points
                                          restricted to campaign/calibration/
                                          <dataset>.json's chosen_alphas --
                                          what the graph actually plots
  3. campaign/graphs/<dataset>.png       x=mean l_bar, y=mean completion
                                          length, one line per method

Safe to re-run at any point mid-campaign: reads whatever run.json files
exist right now, so a mid-campaign call just reports partial progress
(fewer points per line) rather than failing.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# campaign/PLAN.md's fixed method order + the dataviz skill's validated
# categorical palette (references/palette.md, slots 1-5, fixed order -- never
# cycled/reassigned). Colour alone isn't a safe identity channel past 3
# series on the skill's own all-pairs gate, so each method also gets a
# distinct marker + linestyle as secondary encoding, and lines are
# end-labelled directly (not legend-only).
METHOD_STYLE: dict[str, dict] = {
    "mentored_dec":  {"color": "#2a78d6", "marker": "o", "linestyle": "-",  "label": "mentored_dec"},
    "cactus":        {"color": "#eb6834", "marker": "s", "linestyle": "--", "label": "cactus"},
    "spec_casc_opt": {"color": "#1baf7a", "marker": "^", "linestyle": "-.", "label": "spec_casc_opt"},
    "r_fuzzy":       {"color": "#eda100", "marker": "D", "linestyle": ":",  "label": "r_fuzzy"},
    "spec_casc_tok": {"color": "#e87ba4", "marker": "*", "linestyle": "-",  "label": "spec_casc_tok"},
}
METHOD_ORDER = list(METHOD_STYLE.keys())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--runs-root", type=pathlib.Path, default=REPO_ROOT / "runs")
    parser.add_argument("--calibration-json", type=pathlib.Path, default=None)
    parser.add_argument("--tables-out", type=pathlib.Path, default=None)
    parser.add_argument("--results-out", type=pathlib.Path, default=None)
    parser.add_argument("--graph-out", type=pathlib.Path, default=None)
    return parser.parse_args()


def alpha_dir_name(alpha: float) -> str:
    return f"alpha{alpha:g}".replace("-", "neg")


def load_all_runs(runs_root: pathlib.Path, dataset: str) -> list[dict]:
    """One row per run.json under runs_root/dataset/<method>/<params>/<case>/seed_N/."""
    rows = []
    dataset_root = runs_root / dataset
    if not dataset_root.is_dir():
        return rows
    for run_json in sorted(dataset_root.glob("*/*/*/seed_*/run.json")):
        seed_dir = run_json.parent
        case = seed_dir.parent.name
        params = seed_dir.parent.parent.name
        method = seed_dir.parent.parent.parent.name
        try:
            data = json.loads(run_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        rows.append(
            {
                "dataset": dataset,
                "method": method,
                "params": params,
                "case": case,
                "seed": seed_dir.name.replace("seed_", ""),
                "status": data.get("status"),
                "l_bar": data.get("l_bar"),
                "mean_accept_length": data.get("mean_accept_length"),
                "output_tokens": data.get("output_tokens"),
                "draft_rounds": data.get("draft_rounds"),
                "draft_acceptance_rate": data.get("draft_acceptance_rate"),
                "finish_reason": data.get("finish_reason"),
                "reached_final_channel": data.get("reached_final_channel"),
                "wall_time_seconds": data.get("wall_time_seconds"),
            }
        )
    return rows


def write_csv(path: pathlib.Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def main() -> int:
    args = parse_args()
    calibration_json = args.calibration_json or (REPO_ROOT / "campaign" / "calibration" / f"{args.dataset}.json")
    tables_out = args.tables_out or (REPO_ROOT / "campaign" / "tables" / f"{args.dataset}.csv")
    results_out = args.results_out or (REPO_ROOT / "campaign" / "results" / f"{args.dataset}.csv")
    graph_out = args.graph_out or (REPO_ROOT / "campaign" / "graphs" / f"{args.dataset}.png")

    # --- 1. per-case table: every run found, calibration + full sweep alike ---
    all_rows = load_all_runs(args.runs_root, args.dataset)
    if not all_rows:
        print(f"no runs found yet under {args.runs_root / args.dataset}")
        return 0
    write_csv(tables_out, all_rows, list(all_rows[0].keys()))
    print(f"wrote {tables_out} ({len(all_rows)} rows)")

    # --- 2. aggregated (method, alpha) points, restricted to the chosen targets ---
    if not calibration_json.is_file():
        print(f"no calibration file at {calibration_json} yet -- skipping results/graph")
        return 0
    calibration = json.loads(calibration_json.read_text(encoding="utf-8"))
    chosen_alphas: dict[str, list[float]] = calibration.get("chosen_alphas", {})

    by_method_alpha: dict[tuple[str, float], list[dict]] = {}
    for row in all_rows:
        if row["status"] != "ok" or row["method"] not in chosen_alphas:
            continue
        for alpha in chosen_alphas[row["method"]]:
            if row["params"] == alpha_dir_name(alpha):
                by_method_alpha.setdefault((row["method"], alpha), []).append(row)

    result_rows = []
    for method in METHOD_ORDER:
        for alpha in chosen_alphas.get(method, []):
            cases = by_method_alpha.get((method, alpha), [])
            result_rows.append(
                {
                    "dataset": args.dataset,
                    "method": method,
                    "alpha": alpha,
                    "n_cases": len(cases),
                    "mean_l_bar": mean([c["l_bar"] for c in cases]),
                    "mean_completion_length": mean([c["output_tokens"] for c in cases]),
                }
            )
    write_csv(results_out, result_rows, ["dataset", "method", "alpha", "n_cases", "mean_l_bar", "mean_completion_length"])
    print(f"wrote {results_out} ({len(result_rows)} rows)")

    # --- 3. the graph ---
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.set_facecolor("#fcfcfb")
    fig.patch.set_facecolor("#fcfcfb")
    any_plotted = False
    for method in METHOD_ORDER:
        style = METHOD_STYLE[method]
        points = sorted(
            ((r["mean_l_bar"], r["mean_completion_length"]) for r in result_rows if r["method"] == method and r["mean_l_bar"] is not None and r["mean_completion_length"] is not None),
        )
        if len(points) < 1:
            continue
        any_plotted = True
        xs, ys = zip(*points)
        ax.plot(
            xs, ys, color=style["color"], marker=style["marker"], linestyle=style["linestyle"],
            linewidth=2, markersize=9, label=style["label"], markeredgecolor="white", markeredgewidth=0.6,
        )
        # direct end-label -- not legend-only, per the dataviz skill's rule
        # that identity is never color-alone past 3 categorical series.
        ax.annotate(
            style["label"], (xs[-1], ys[-1]), textcoords="offset points", xytext=(6, 4),
            fontsize=9, color="#0b0b0b",
        )
    if not any_plotted:
        print("no complete (method, alpha) points yet -- graph not written")
        plt.close(fig)
        return 0

    ax.set_xlabel("mean accepted length (l̄)", color="#0b0b0b")
    ax.set_ylabel("mean completion length (tokens)", color="#0b0b0b")
    ax.set_title(f"{args.dataset}: completion length vs. mean accepted length", color="#0b0b0b")
    ax.grid(True, color="#e5e4df", linewidth=0.7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#c3c2b7")
    ax.tick_params(colors="#52514e")
    ax.legend(frameon=False, labelcolor="#0b0b0b")
    fig.tight_layout()
    graph_out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(graph_out, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"wrote {graph_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
