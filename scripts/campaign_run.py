#!/usr/bin/env python3
"""One dataset's slice of campaign/PLAN.md: calibrate each of the 5 taxonomy
methods' alpha->l_bar curve on a small probe subset, pick 3 shared l_bar
targets, then run the full case set at each method's 3 chosen alphas.

Delegates every actual server-lifecycle/generation step to
scripts/fresh_server_replay.py (already handles fresh-server-per-measurement,
patch switching, resumable skip-if-done) -- this script only decides WHICH
(method, alpha, cases) triples to ask it to run, and reads run.json back
afterwards to make the next decision. Safe to re-run: every invocation of
fresh_server_replay.py is itself a no-op for runs that already exist, so
interrupting this script and restarting it just re-derives the same plan and
continues.

See campaign/PLAN.md for the design rationale (grids, target-selection rule,
case counts, token budgets).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PYTHON = str(REPO_ROOT / ".venv-vllm" / "bin" / "python")

# method -> (alpha grid, 4 points, anchored to campaign/PLAN.md's table)
ALPHA_GRIDS: dict[str, list[float]] = {
    "mentored_dec": [0.15, 0.35, 0.55, 0.75],
    "cactus": [0.03, 0.08, 0.18, 0.35],
    "spec_casc_opt": [-0.3, -0.1, -0.02, 0.05],
    "r_fuzzy": [0.03, 0.08, 0.15, 0.25],
    "spec_casc_tok": [0.15, 0.35, 0.55, 0.8],
}
METHODS = list(ALPHA_GRIDS.keys())

# dataset -> --max-new-tokens budget (campaign/PLAN.md's "Per-dataset token budget" table)
TOKEN_BUDGETS: dict[str, int] = {
    "gsm8k": 2048,
    "aime24": 32768,
    "humaneval": 9000,
    "livecodebench": 12000,
    "mtbench": 4096,
    "longbench_v2": 8192,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True, choices=sorted(TOKEN_BUDGETS.keys()))
    parser.add_argument("--methods", nargs="+", default=METHODS, choices=METHODS)
    parser.add_argument("--full-cases", type=int, default=12, help="Total cases in the full sweep.")
    parser.add_argument("--calib-cases", type=int, default=3, help="Leading subset of --full-cases used for calibration.")
    parser.add_argument("--num-targets", type=int, default=3)
    parser.add_argument("--runs-root", type=pathlib.Path, default=REPO_ROOT / "runs")
    parser.add_argument("--prompt-root", type=pathlib.Path, default=None, help="Defaults to prompts/<dataset>.")
    parser.add_argument("--calibration-out", type=pathlib.Path, default=None, help="Defaults to campaign/calibration/<dataset>.json.")
    parser.add_argument("--max-new-tokens", type=int, default=None, help="Overrides the dataset's default budget.")
    parser.add_argument("--port", type=int, default=30000)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def case_list(n: int) -> list[str]:
    return [f"case_{i:03d}" for i in range(1, n + 1)]


def clean_partial_runs(runs_root: pathlib.Path, dataset: str) -> int:
    """Remove any seed_N/ run directory that exists but has no run.json --
    i.e. a case that started (run_experiment_vllm.py already wrote
    config.json/request.json) and then never finished (server killed,
    process crashed, host restarted, timeout, ...).

    Load-bearing for resumability: run_experiment_vllm.py's run_one()
    refuses to write into a directory that already exists
    (`FileExistsError` unless --overwrite), and fresh_server_replay.py's own
    skip-if-done check only looks for run.json. Without this cleanup, a
    half-finished run directory left over from an interrupted process would
    make every future retry of that exact (method, alpha, case) fail the
    same way forever -- a silent permanent gap, not a visible one, since
    fresh_server_replay.py logs the failure and moves on rather than
    stopping. Confirmed reproducing this exact shape in the gsm8k smoke test
    (a `timeout 300`-killed run left `alpha0.35/case_001/seed_0/` with
    config/request/server_info.json but no run.json).
    """
    dataset_root = runs_root / dataset
    if not dataset_root.is_dir():
        return 0
    removed = 0
    for seed_dir in dataset_root.glob("*/*/*/seed_*"):
        if not seed_dir.is_dir():
            continue
        if not (seed_dir / "run.json").is_file() and any(seed_dir.iterdir()):
            print(f"cleaning up partial run dir (no run.json): {seed_dir}")
            for child in seed_dir.iterdir():
                child.unlink()
            seed_dir.rmdir()
            removed += 1
    return removed


def run_fresh_server_replay(
    *, method: str, alpha: float, cases: list[str], prompt_root: pathlib.Path,
    runs_root: pathlib.Path, log_root: pathlib.Path, max_new_tokens: int, port: int, dry_run: bool,
) -> subprocess.CompletedProcess:
    flag = f"--{method.replace('_', '-')}-alpha"
    command = [
        PYTHON, str(REPO_ROOT / "scripts" / "fresh_server_replay.py"),
        "--arms", method,
        "--cases", *cases,
        flag, f"{alpha:g}",
        "--prompt-root", str(prompt_root),
        "--runs-root", str(runs_root),
        "--log-root", str(log_root),
        "--max-new-tokens", str(max_new_tokens),
        "--port", str(port),
        "--no-trace-proposals",  # see campaign/PLAN.md's disk-budget section
    ]
    if dry_run:
        command.append("--dry-run")
    print(f"$ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=REPO_ROOT, check=False)


def alpha_dir_name(alpha: float) -> str:
    """Must match fresh_server_replay.py's method_and_params_for() exactly --
    that's what decides the run directory this script reads back from."""
    return f"alpha{alpha:g}".replace("-", "neg")


def read_l_bar(runs_root: pathlib.Path, dataset: str, method: str, alpha: float, case: str) -> float | None:
    run_json = runs_root / dataset / method / alpha_dir_name(alpha) / case / "seed_0" / "run.json"
    if not run_json.is_file():
        return None
    try:
        data = json.loads(run_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("status") != "ok":
        return None
    return data.get("l_bar")


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def pick_targets_and_alphas(
    grid_results: dict[str, list[tuple[float, float]]], num_targets: int
) -> tuple[list[float], dict[str, list[float]]]:
    """grid_results: method -> [(alpha, mean_l_bar), ...] sorted by alpha,
    only points with a real measurement. See campaign/PLAN.md's
    'Target-selection rule' for what this implements."""
    mins = {m: min(l for _, l in pts) for m, pts in grid_results.items() if pts}
    maxs = {m: max(l for _, l in pts) for m, pts in grid_results.items() if pts}
    if not mins:
        raise ValueError("no calibration data for any method -- cannot pick targets")
    lo, hi = max(mins.values()), min(maxs.values())
    if hi <= lo:  # ranges don't overlap across every method -- fall back to the global span
        lo, hi = min(mins.values()), max(maxs.values())
    fractions = [0.2, 0.55, 0.9] if num_targets == 3 else [i / (num_targets - 1) for i in range(num_targets)]
    targets = [lo + f * (hi - lo) for f in fractions[:num_targets]]

    chosen: dict[str, list[float]] = {}
    for method, pts in grid_results.items():
        if not pts:
            chosen[method] = []
            continue
        picks = [min(pts, key=lambda p: abs(p[1] - t))[0] for t in targets]
        distinct = list(dict.fromkeys(picks))
        if len(distinct) < num_targets:
            for extreme in (pts[0][0], pts[-1][0]):
                if extreme not in distinct:
                    distinct.append(extreme)
                if len(distinct) >= num_targets:
                    break
        chosen[method] = distinct[:num_targets]
    return targets, chosen


def main() -> int:
    args = parse_args()
    prompt_root = args.prompt_root or (REPO_ROOT / "prompts" / args.dataset)
    calibration_out = args.calibration_out or (REPO_ROOT / "campaign" / "calibration" / f"{args.dataset}.json")
    log_root = REPO_ROOT / "logs" / f"campaign_{args.dataset}"
    max_new_tokens = args.max_new_tokens or TOKEN_BUDGETS[args.dataset]
    probe_cases = case_list(args.calib_cases)
    full_cases = case_list(args.full_cases)

    print(f"=== campaign_run: dataset={args.dataset} methods={args.methods} "
          f"probe_cases={probe_cases} full_cases={len(full_cases)} max_new_tokens={max_new_tokens} ===", flush=True)

    if not args.dry_run:
        removed = clean_partial_runs(args.runs_root, args.dataset)
        if removed:
            print(f"cleaned up {removed} partial run dir(s) from a previous interrupted attempt", flush=True)

    # --- Stage 1: calibration grid ---
    for method in args.methods:
        for alpha in ALPHA_GRIDS[method]:
            result = run_fresh_server_replay(
                method=method, alpha=alpha, cases=probe_cases, prompt_root=prompt_root,
                runs_root=args.runs_root, log_root=log_root, max_new_tokens=max_new_tokens,
                port=args.port, dry_run=args.dry_run,
            )
            if result.returncode != 0:
                print(f"warning: calibration run failed method={method} alpha={alpha} (exit {result.returncode}), continuing", file=sys.stderr)

    if args.dry_run:
        print("dry-run: stopping before target selection (no calibration data to read)")
        return 0

    grid_results: dict[str, list[tuple[float, float]]] = {}
    for method in args.methods:
        points = []
        for alpha in ALPHA_GRIDS[method]:
            l_bars = [read_l_bar(args.runs_root, args.dataset, method, alpha, case) for case in probe_cases]
            m = mean(l_bars)
            if m is not None:
                points.append((alpha, m))
            else:
                print(f"warning: no usable l_bar for method={method} alpha={alpha} -- excluded from calibration", file=sys.stderr)
        grid_results[method] = points

    targets, chosen_alphas = pick_targets_and_alphas(grid_results, args.num_targets)
    print(f"targets (l_bar): {[round(t, 3) for t in targets]}")
    for method, alphas in chosen_alphas.items():
        print(f"  {method}: chosen alphas = {alphas}")

    calibration_out.parent.mkdir(parents=True, exist_ok=True)
    calibration_out.write_text(
        json.dumps(
            {
                "dataset": args.dataset,
                "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "probe_cases": probe_cases,
                "full_cases": full_cases,
                "max_new_tokens": max_new_tokens,
                "alpha_grids": ALPHA_GRIDS,
                "grid_results": {m: [{"alpha": a, "mean_l_bar": l} for a, l in pts] for m, pts in grid_results.items()},
                "targets_l_bar": targets,
                "chosen_alphas": chosen_alphas,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {calibration_out}")

    # --- Stage 2: full sweep at each method's chosen alphas ---
    for method in args.methods:
        for alpha in chosen_alphas.get(method, []):
            result = run_fresh_server_replay(
                method=method, alpha=alpha, cases=full_cases, prompt_root=prompt_root,
                runs_root=args.runs_root, log_root=log_root, max_new_tokens=max_new_tokens,
                port=args.port, dry_run=args.dry_run,
            )
            if result.returncode != 0:
                print(f"warning: full-sweep run failed method={method} alpha={alpha} (exit {result.returncode}), continuing", file=sys.stderr)

    print(f"=== campaign_run done: dataset={args.dataset} ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
