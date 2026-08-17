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
import importlib
import json
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Accuracy grading (2026-08-16, user request: "we should also produce score
# accuracy of final result graph"). One grade_*.py per dataset, same
# run-directory-walking convention (grade(run_dir, prompt_root) ->
# {..., "verdict": ...}), imported directly rather than shelled out to --
# matches scripts/summarize_arms.py's existing pattern of importing
# grade_aime/grade_humaneval rather than reinventing the run-tree walk.
# mtbench has no grader (needs an LLM-judge; no infra exists yet, and
# building one costs extra GPU time on the single GPU the live campaign is
# still using) -- simply absent from this dict, and grade_accuracy() below
# no-ops cleanly for any dataset not listed here.
#
# livecodebench's grade() takes one extra required arg (test_cases_by_qid,
# loaded from prompts/livecodebench/test_cases.json -- see
# scripts/grade_livecodebench.py's own docstring for how those 12 rows
# were fetched and why it's public_test_cases only); "kwargs" is a
# zero-arg callable here instead of a static dict so that lookup can
# happen lazily, only for datasets that need it.
GRADERS: dict[str, dict] = {
    "gsm8k": {"module": "grade_gsm8k", "correct_verdicts": {"correct"}, "kwargs": {}},
    "aime24": {"module": "grade_aime", "correct_verdicts": {"correct"}, "kwargs": {}},
    "humaneval": {"module": "grade_humaneval", "correct_verdicts": {"passed"}, "kwargs": {"timeout": 10.0, "memory_limit_mb": 1024}},
    "longbench_v2": {"module": "grade_longbench", "correct_verdicts": {"correct"}, "kwargs": {}},
    "livecodebench": {
        "module": "grade_livecodebench", "correct_verdicts": {"passed"},
        "kwargs": lambda module: {
            "test_cases_by_qid": module.load_test_cases(REPO_ROOT / "prompts" / "livecodebench" / "test_cases.json"),
            "timeout": 10.0, "memory_limit_mb": 1024,
        },
    },
}

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

# Lossless reference point (2026-08-15, user request): a single (not swept)
# `strict` arm, plotted separately from the 5 categorical method lines --
# it's a reference the methods are compared against, not a peer category,
# so it deliberately does NOT take a 6th slot in the categorical palette
# (dataviz skill: fixed categorical order, never extended ad hoc). Neutral
# ink color (matches this script's own axis-text color, not a hue used
# anywhere in METHOD_STYLE), a distinct marker, and light dashed guide
# lines to both axes so it reads as "the line to beat," not a 6th series.
STRICT_STYLE: dict = {"color": "#3a3a37", "marker": "X", "label": "lossless (strict)"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--runs-root", type=pathlib.Path, default=REPO_ROOT / "runs")
    parser.add_argument("--calibration-json", type=pathlib.Path, default=None)
    parser.add_argument("--tables-out", type=pathlib.Path, default=None)
    parser.add_argument("--results-out", type=pathlib.Path, default=None)
    parser.add_argument("--graph-out", type=pathlib.Path, default=None)
    parser.add_argument("--accuracy-graph-out", type=pathlib.Path, default=None)
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


def grade_accuracy(runs_root: pathlib.Path, dataset: str) -> dict[tuple[str, str, str], bool]:
    """(method, params, case) -> True/False (correct/not), for every run
    grade()-able for this dataset. Empty dict, not an error, for any
    dataset without a grader in GRADERS -- callers treat that as "no
    accuracy data yet," not a failure."""
    # "gsm8k_qwen3" grades with the same rules as "gsm8k" -- answer_extraction.py
    # (2026-08-17) already handles both Harmony's final-channel marker and
    # Qwen3's </think> convention inside the shared final_segment() step, so
    # every grade_*.py module works unmodified against either model family.
    # Only the GRADERS lookup key needs the family suffix stripped; prompt_root/
    # dataset_root below stay on the FULL dataset name (prompts/gsm8k_qwen3,
    # runs/gsm8k_qwen3 are real, separate directories from the gpt-oss ones).
    base_dataset = dataset.removesuffix("_qwen3")
    spec = GRADERS.get(base_dataset)
    if spec is None:
        return {}
    module = importlib.import_module(spec["module"])
    prompt_root = REPO_ROOT / "prompts" / dataset
    dataset_root = runs_root / dataset
    kwargs = spec["kwargs"](module) if callable(spec["kwargs"]) else spec["kwargs"]
    out: dict[tuple[str, str, str], bool] = {}
    for run_json in sorted(dataset_root.glob("*/*/*/seed_*/run.json")):
        run_dir = run_json.parent
        row = module.grade(run_dir, prompt_root, **kwargs)
        if row is None:
            continue
        method, params, case = row["method"], row["params"], row["case"]
        out[(method, params, case)] = row["verdict"] in spec["correct_verdicts"]
    return out


def main() -> int:
    args = parse_args()
    calibration_json = args.calibration_json or (REPO_ROOT / "campaign" / "calibration" / f"{args.dataset}.json")
    tables_out = args.tables_out or (REPO_ROOT / "campaign" / "tables" / f"{args.dataset}.csv")
    results_out = args.results_out or (REPO_ROOT / "campaign" / "results" / f"{args.dataset}.csv")
    graph_out = args.graph_out or (REPO_ROOT / "campaign" / "graphs" / f"{args.dataset}.png")
    accuracy_graph_out = args.accuracy_graph_out or (REPO_ROOT / "campaign" / "graphs" / f"{args.dataset}_accuracy.png")

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

    # Accuracy (2026-08-16, user request): empty dict for any dataset
    # without a grader in GRADERS -- accuracy_of() then returns None for
    # every point, and downstream code (results.csv column, 2nd graph)
    # degrades to "no accuracy data yet" rather than erroring.
    accuracy_map = grade_accuracy(args.runs_root, args.dataset)

    def accuracy_of(cases: list[dict]) -> float | None:
        if not accuracy_map:
            return None
        verdicts = [accuracy_map[(c["method"], c["params"], c["case"])] for c in cases if (c["method"], c["params"], c["case"]) in accuracy_map]
        return mean([1.0 if v else 0.0 for v in verdicts]) if verdicts else None

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
                    "accuracy": accuracy_of(cases),
                }
            )

    # Lossless reference: no alpha axis (method_and_params_for() maps
    # "strict" -> params "strict" too), no calibration/chosen_alphas entry
    # -- just every ok "strict" run.json found for this dataset, aggregated
    # into a single row.
    strict_cases = [r for r in all_rows if r["method"] == "strict" and r["status"] == "ok"]
    if strict_cases:
        result_rows.append(
            {
                "dataset": args.dataset,
                "method": "strict",
                "alpha": "strict",
                "n_cases": len(strict_cases),
                "mean_l_bar": mean([c["l_bar"] for c in strict_cases]),
                "mean_completion_length": mean([c["output_tokens"] for c in strict_cases]),
                "accuracy": accuracy_of(strict_cases),
            }
        )

    write_csv(results_out, result_rows, ["dataset", "method", "alpha", "n_cases", "mean_l_bar", "mean_completion_length", "accuracy"])
    print(f"wrote {results_out} ({len(result_rows)} rows)")
    if not accuracy_map:
        print(f"  (no grader registered for {args.dataset} yet -- accuracy column left blank; see GRADERS in this script)")

    # --- 3. the graph(s) -- shared renderer, x=mean l̄ always, y swaps
    # between completion length and accuracy (2 separate PNGs, never a
    # dual-axis chart on one figure -- dataviz skill's "one axis" rule) ---
    render_graph(
        result_rows, y_field="mean_completion_length", y_label="mean completion length (tokens)",
        title=f"{args.dataset}: completion length vs. mean accepted length", out_path=graph_out,
        y_is_fraction=False,
    )
    if accuracy_map:
        render_graph(
            result_rows, y_field="accuracy", y_label="accuracy",
            title=f"{args.dataset}: accuracy vs. mean accepted length", out_path=accuracy_graph_out,
            y_is_fraction=True,
        )
    else:
        print(f"  no grader registered for {args.dataset} yet -- accuracy graph not written")
    return 0


def render_graph(
    result_rows: list[dict], *, y_field: str, y_label: str, title: str, out_path: pathlib.Path, y_is_fraction: bool,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    ax.set_facecolor("#fcfcfb")
    fig.patch.set_facecolor("#fcfcfb")
    any_plotted = False
    # Vertical offsets cycle by method index so end-labels don't collide
    # when several methods land on the same (coarsely-quantized, n=12
    # cases) accuracy value -- fixed (6, 4) for every label was fine on the
    # completion-length graph but garbled into overlapping text on
    # low-case-count accuracy graphs (see campaign/JOURNAL.md).
    label_offsets = [(6, 4), (6, -14), (6, 16), (6, -24)]
    for idx, method in enumerate(METHOD_ORDER):
        style = METHOD_STYLE[method]
        points = sorted(
            ((r["mean_l_bar"], r[y_field]) for r in result_rows if r["method"] == method and r["mean_l_bar"] is not None and r[y_field] is not None),
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
            style["label"], (xs[-1], ys[-1]), textcoords="offset points", xytext=label_offsets[idx % len(label_offsets)],
            fontsize=9, color="#0b0b0b",
        )
    strict_row = next((r for r in result_rows if r["method"] == "strict"), None)
    if strict_row and strict_row["mean_l_bar"] is not None and strict_row[y_field] is not None:
        any_plotted = True
        sx, sy = strict_row["mean_l_bar"], strict_row[y_field]
        # Guide lines to both axes, drawn first so the marker sits on top --
        # reads as "the reference to compare against," not a 6th line.
        ax.axhline(sy, color="#c3c2b7", linewidth=0.8, linestyle=":", zorder=1)
        ax.axvline(sx, color="#c3c2b7", linewidth=0.8, linestyle=":", zorder=1)
        ax.scatter(
            [sx], [sy], color=STRICT_STYLE["color"], marker=STRICT_STYLE["marker"],
            s=130, linewidths=1.6, zorder=5, label=STRICT_STYLE["label"],
        )
        ax.annotate(
            STRICT_STYLE["label"], (sx, sy), textcoords="offset points", xytext=(8, -12),
            fontsize=9, color="#0b0b0b",
        )

    if not any_plotted:
        print(f"  no complete (method, alpha) points yet for {y_field} -- {out_path.name} not written")
        plt.close(fig)
        return

    ax.set_xlabel("mean accepted length (l̄)", color="#0b0b0b")
    ax.set_ylabel(y_label, color="#0b0b0b")
    ax.set_title(title, color="#0b0b0b")
    if y_is_fraction:
        ax.set_ylim(-0.02, 1.02)
        ax.yaxis.set_major_formatter(lambda v, _pos: f"{v:.0%}")
    ax.grid(True, color="#e5e4df", linewidth=0.7)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#c3c2b7")
    ax.tick_params(colors="#52514e")
    ax.legend(frameon=False, labelcolor="#0b0b0b")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    raise SystemExit(main())
