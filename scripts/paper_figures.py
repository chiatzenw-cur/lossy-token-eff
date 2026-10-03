#!/usr/bin/env python3
"""Build the six paper result figures (figures/*.png) from campaign data.

Three plot types x two target models, each a 3x2 grid of dataset panels:

  figures/<target>_completion_length.png   y = mean completion length (tokens)
  figures/<target>_verifier_rounds.png     y = mean verifier rounds (target forward passes)
  figures/<target>_accuracy.png            y = accuracy, fixed 0-100%

with <target> in {gpt_oss_20b, qwen3_8b}.  Layout, series encoding and
data sources follow figures/figures-spec.md.

Data sources
  * campaign/results/<stem>.csv  -- mean_l_bar, mean_completion_length,
    accuracy per (method, alpha), plus the strict row.  <stem> is the
    dataset for GPT-OSS-20B and <dataset>_qwen3 for Qwen3-8B.
  * runs/<stem>/<method>/<alpha dir>/case_*/seed_*/run.json -- `draft_rounds`
    (= verifier rounds, see cascade/METRICS.md), averaged over status=="ok"
    runs.  The run tree is gitignored, so pass --runs-root if it lives
    elsewhere; every value read is also cached in figures/points.csv and
    reused when the run tree is absent, so the PNGs are reproducible from
    tracked files alone.

Why this script exists (2026-09-24): the first version of these figures
joined each method's sweep points in file order, which is calibration
order, not sorted order, so several curves doubled back on themselves.
Here every curve is sorted by mean accepted length before drawing, and
the script fails loudly if any curve would still not be x-monotone.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import MultipleLocator, PercentFormatter  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
FIGURES_DIR = REPO_ROOT / "figures"
POINTS_CACHE = FIGURES_DIR / "points.csv"

TARGETS = {
    "gpt_oss_20b": {"title": "GPT-OSS-20B", "suffix": ""},
    "qwen3_8b": {"title": "Qwen3-8B", "suffix": "_qwen3"},
}
# Fixed panel order: row 1, row 2, row 3.
DATASETS = [
    ("gsm8k", "GSM8K"), ("aime24", "AIME24"),
    ("humaneval", "HumanEval"), ("livecodebench", "LiveCodeBench"),
    ("mtbench", "MT-Bench"), ("longbench_v2", "LongBench-v2"),
]
# Legend is 3 columns x 2 rows, filled column-major by matplotlib, so this
# handle order renders as   mentored_dec | spec_casc_opt | spec_casc_tok
#                           cactus       | r_fuzzy       | lossless (strict)
METHOD_STYLE: dict[str, dict] = {
    "mentored_dec":  {"color": "#1f77b4", "marker": "o", "markersize": 5.0, "linewidth": 1.8, "label": "mentored_dec"},
    "cactus":        {"color": "#d62728", "marker": "s", "markersize": 4.6, "linewidth": 1.8, "label": "cactus"},
    "spec_casc_opt": {"color": "#2ca02c", "marker": "^", "markersize": 5.4, "linewidth": 1.8, "label": "spec_casc_opt"},
    "r_fuzzy":       {"color": "#ff7f0e", "marker": "D", "markersize": 4.4, "linewidth": 1.8, "label": "r_fuzzy"},
    "spec_casc_tok": {"color": "#9467bd", "marker": "*", "markersize": 5.6, "linewidth": 1.2, "label": "spec_casc_tok"},
}
METHOD_ORDER = list(METHOD_STYLE)
STRICT_STYLE = {"color": "#222222", "marker": "x", "markersize": 9.0, "markeredgewidth": 1.8, "label": "lossless (strict)"}

PLOTS = [
    ("completion_length", "mean_completion_length", "mean completion length (tokens)"),
    ("verifier_rounds", "mean_verifier_rounds", "mean verifier rounds\n(target forward passes)"),
    ("accuracy", "accuracy", "accuracy"),
]
POINT_FIELDS = ["target", "dataset", "stem", "method", "alpha", "n_cases", "mean_l_bar",
                "mean_completion_length", "mean_verifier_rounds", "accuracy"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs-root", type=pathlib.Path, default=REPO_ROOT / "runs",
                   help="root of the run tree (runs/<stem>/<method>/<params>/case_*/seed_*/run.json)")
    p.add_argument("--out-dir", type=pathlib.Path, default=FIGURES_DIR)
    p.add_argument("--dpi", type=int, default=300)
    return p.parse_args()


def alpha_dir_name(alpha: float) -> str:
    return f"alpha{alpha:g}".replace("-", "neg")


def to_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def load_cache() -> dict[tuple[str, str, str], float]:
    """(stem, method, alpha-string) -> cached mean_verifier_rounds."""
    if not POINTS_CACHE.exists():
        return {}
    cached: dict[tuple[str, str, str], float] = {}
    with POINTS_CACHE.open() as fh:
        for row in csv.DictReader(fh):
            rounds = to_float(row.get("mean_verifier_rounds"))
            if rounds is not None:
                cached[(row["stem"], row["method"], row["alpha"])] = rounds
    return cached


def mean_rounds(runs_root: pathlib.Path, stem: str, method: str, params: str) -> tuple[int, float | None]:
    values: list[float] = []
    for run_json in runs_root.glob(f"{stem}/{method}/{params}/case_*/seed_*/run.json"):
        with run_json.open() as fh:
            run = json.load(fh)
        if run.get("status") == "ok" and run.get("draft_rounds") is not None:
            values.append(float(run["draft_rounds"]))
    return len(values), (statistics.fmean(values) if values else None)


def load_points(runs_root: pathlib.Path, cache: dict) -> list[dict]:
    """One dict per plotted point (five methods x their alphas, plus strict), all targets and datasets."""
    points: list[dict] = []
    missing_rounds: list[str] = []
    for target, tmeta in TARGETS.items():
        for dataset, _label in DATASETS:
            stem = f"{dataset}{tmeta['suffix']}"
            csv_path = REPO_ROOT / "campaign" / "results" / f"{stem}.csv"
            if not csv_path.exists():
                sys.exit(f"missing {csv_path}")
            with csv_path.open() as fh:
                rows = list(csv.DictReader(fh))
            for row in rows:
                method = row["method"]
                if method not in METHOD_ORDER and method != "strict":
                    continue
                params = "strict" if method == "strict" else alpha_dir_name(float(row["alpha"]))
                n_runs, rounds = mean_rounds(runs_root, stem, method, params)
                if rounds is None:
                    rounds = cache.get((stem, method, row["alpha"]))
                    if rounds is None:
                        missing_rounds.append(f"{stem}/{method}/{params}")
                elif n_runs != int(row["n_cases"]):
                    print(f"  warning: {stem}/{method}/{params}: {n_runs} ok runs with draft_rounds "
                          f"vs n_cases={row['n_cases']} in {csv_path.name}", file=sys.stderr)
                points.append({
                    "target": target, "dataset": dataset, "stem": stem, "method": method, "alpha": row["alpha"],
                    "n_cases": int(row["n_cases"]), "mean_l_bar": float(row["mean_l_bar"]),
                    "mean_completion_length": to_float(row["mean_completion_length"]),
                    "mean_verifier_rounds": rounds, "accuracy": to_float(row["accuracy"]),
                })
    if missing_rounds:
        print("  warning: no run.json and no cached rounds for: " + ", ".join(missing_rounds), file=sys.stderr)
    return points


def write_cache(points: list[dict]) -> None:
    POINTS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with POINTS_CACHE.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=POINT_FIELDS)
        writer.writeheader()
        for p in points:
            writer.writerow({k: ("" if p[k] is None else p[k]) for k in POINT_FIELDS})


def x_range(points: list[dict], target: str) -> tuple[float, float]:
    xs = [p["mean_l_bar"] for p in points if p["target"] == target]
    lo, hi = min(xs), max(xs)
    pad = 0.07 * (hi - lo)
    return lo - pad, hi + pad


def style_axes(ax: plt.Axes, xlim: tuple[float, float]) -> None:
    ax.set_xlim(*xlim)
    ax.xaxis.set_major_locator(MultipleLocator(0.5))
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(which="both", direction="in", top=True, right=True, bottom=True, left=True, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color("#444444")
        spine.set_linewidth(0.8)


def render_figure(points: list[dict], target: str, plot_key: str, y_field: str, y_label: str,
                  xlim: tuple[float, float], out_path: pathlib.Path, dpi: int) -> None:
    tmeta = TARGETS[target]
    # 2070 x 2100 px at dpi 300.
    fig, axes = plt.subplots(3, 2, figsize=(6.9, 7.0), dpi=dpi, facecolor="white")
    fig.suptitle(tmeta["title"], fontsize=12, fontweight="bold", y=0.985)
    handles = [
        Line2D([], [], color=s["color"], marker=s["marker"], markersize=s["markersize"] + 1,
               linewidth=s["linewidth"], label=s["label"])
        for s in METHOD_STYLE.values()
    ] + [Line2D([], [], color=STRICT_STYLE["color"], marker=STRICT_STYLE["marker"], markersize=STRICT_STYLE["markersize"],
                markeredgewidth=STRICT_STYLE["markeredgewidth"], linestyle="none", label=STRICT_STYLE["label"])]

    for (dataset, label), ax in zip(DATASETS, axes.flat):
        ax.set_title(label, fontsize=9, fontweight="bold", pad=4)
        style_axes(ax, xlim)
        panel = [p for p in points if p["target"] == target and p["dataset"] == dataset]
        drawable = [p for p in panel if p[y_field] is not None]
        if not drawable:
            # e.g. MT-Bench accuracy: axes drawn, grey centred text, no data.
            ax.text(0.5, 0.5, "no grader", transform=ax.transAxes, ha="center", va="center",
                    fontsize=9, color="#888888")
        for method in METHOD_ORDER:
            s = METHOD_STYLE[method]
            # Sorted by mean accepted length -- the fix for the doubling-back curves.
            pts = sorted((p["mean_l_bar"], p[y_field]) for p in drawable if p["method"] == method)
            if not pts:
                continue
            xs, ys = zip(*pts)
            assert all(a <= b for a, b in zip(xs, xs[1:])), f"{target}/{dataset}/{method}: x not monotone {xs}"
            ax.plot(xs, ys, color=s["color"], marker=s["marker"], markersize=s["markersize"],
                    linewidth=s["linewidth"], linestyle="-", zorder=3)
        strict = next((p for p in drawable if p["method"] == "strict"), None)
        if strict is not None:
            ax.plot([strict["mean_l_bar"]], [strict[y_field]], color=STRICT_STYLE["color"], marker=STRICT_STYLE["marker"],
                    markersize=STRICT_STYLE["markersize"], markeredgewidth=STRICT_STYLE["markeredgewidth"],
                    linestyle="none", zorder=4)
        if y_field == "accuracy":
            ax.set_ylim(0, 1)
            ax.yaxis.set_major_locator(MultipleLocator(0.25))
            ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
        else:
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)
            ax.margins(y=0.08)

    for ax in axes[-1]:
        ax.set_xlabel("mean accepted length ℓ̄", fontsize=8)
    for ax in axes.flat:
        ax.set_ylabel(y_label, fontsize=7.5)

    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=7.5, frameon=False,
               bbox_to_anchor=(0.5, 0.0), columnspacing=1.8, handlelength=2.4)
    fig.subplots_adjust(left=0.11, right=0.975, top=0.92, bottom=0.115, hspace=0.42, wspace=0.34)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, facecolor="white")
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> int:
    args = parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.formatter.limits": (-7, 9), "axes.formatter.useoffset": False})
    cache = load_cache()
    points = load_points(args.runs_root, cache)
    write_cache(points)
    print(f"wrote {POINTS_CACHE} ({len(points)} points)")
    # Report where mean accepted length is not monotone in alpha -- the
    # spec's stated reason for the zigzags; worth knowing either way.
    for target in TARGETS:
        for dataset, _ in DATASETS:
            for method in METHOD_ORDER:
                seq = sorted((float(p["alpha"]), p["mean_l_bar"]) for p in points
                             if p["target"] == target and p["dataset"] == dataset and p["method"] == method)
                lbars = [x for _, x in seq]
                if lbars != sorted(lbars):
                    print(f"  note: {target}/{dataset}/{method}: l_bar not monotone in alpha: {seq}")
    for target in TARGETS:
        xlim = x_range(points, target)
        print(f"{target}: shared x-range {xlim[0]:.2f} to {xlim[1]:.2f}")
        for plot_key, y_field, y_label in PLOTS:
            render_figure(points, target, plot_key, y_field, y_label, xlim,
                          args.out_dir / f"{target}_{plot_key}.png", args.dpi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
