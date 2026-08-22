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
# Qwen3-8B + drafter run (2026-08-17, user request: "run the experiment with
# qwen 8b and a drafter"). Same token budgets as the GPT-OSS-20B datasets --
# same task difficulty either way -- reusing prompts/<dataset>_qwen3/ built
# by scripts/build_prompts_qwen3.py (same underlying problems, re-rendered
# through Qwen3's own chat template instead of Harmony). Kept as separate
# dataset names (not a --model-family flag on the original 6) so
# runs/results/calibration/graphs for the two model families never collide
# and both can be inspected side by side.
TOKEN_BUDGETS.update({f"{name}_qwen3": budget for name, budget in list(TOKEN_BUDGETS.items())})

# model-family -> (MODEL_PATH, DRAFT_MODEL_PATH, served-model-name,
# rope_scaling_json). Dataset names ending "_qwen3" (prompts/<name>_qwen3/
# built by scripts/build_prompts_qwen3.py) use the qwen3 triple; everything
# else (unchanged, original 6 dataset names) keeps GPT-OSS-20B, so a plain
# `--dataset gsm8k` run is exactly what it always was.
#
# Qwen3-8B's native max_position_embeddings is 40960 (its own config.json:
# rope_scaling=null) -- below every dataset's max_new_tokens + worst-case
# input added together once longbench_v2's own ~47k-token cases are in the
# mix. YaRN factor 1.6 (Qwen's own documented context-extension mechanism,
# not the "extreme caution" raw vLLM override) stretches that to 65536,
# matching GPT-OSS-20B's own MAX_MODEL_LEN exactly -- applied uniformly to
# every qwen3 dataset (not just longbench_v2) for the same reason
# MAX_MODEL_LEN itself is one fixed value across all 6 GPT-OSS datasets:
# one serving config per model family, not tuned per-dataset.
QWEN3_ROPE_SCALING = '{"rope_type":"yarn","factor":1.6,"original_max_position_embeddings":40960}'
# Drafter swapped 2026-08-20 (Tengyunw/qwen3_8b_eagle3 -> RedHatAI/Qwen3-8B-
# speculator.eagle3). With the original drafter, cactus/spec_casc_opt/
# r_fuzzy/spec_casc_tok were bit-identical to strict at every alpha tested,
# from 0.001 to 2.0 (well past their real calibration grids) -- genuinely
# flat, not noise (confirmed via repeated deterministic runs). mentored_dec
# alone stayed alpha-sensitive throughout, both before and after the
# --generation-config vllm sampling-parameter fix (kept; real and correct on
# its own, just not the explanation here). Root cause not conclusively
# isolated (draft_probs-is-None was the leading hypothesis but the vLLM
# config conditions that would force that all checked out fine on paper;
# live instrumentation to confirm directly got tangled in vLLM's
# multi-process architecture and a patch hash-safety check without a clean
# answer -- see campaign/JOURNAL.md's 2026-08-19/20 entries for the full
# trail). Empirically: swapping to RedHatAI's speculator (73k downloads,
# published by the team that builds vLLM-optimized speculators, vs.
# Tengyunw's own smaller-community upload) immediately produced real
# divergence from strict on the same case/alpha that was previously
# bit-identical -- confirmed the server actually read each distinct alpha
# value (not a threading bug) via each run's own "[CACTUS PATCH...] alpha=X"
# startup line. Trusting campaign_run.py's own calibration stage (which
# probes 3 cases per method, not just one) to find where real alpha-
# sensitivity shows up, rather than more manual single-case probing.
MODEL_FAMILIES: dict[str, tuple[str, str, str, str]] = {
    "gpt_oss_20b": ("openai/gpt-oss-20b", "nebius/EAGLE3-gpt-oss-20b", "gpt-oss-20b", ""),
    "qwen3": ("Qwen/Qwen3-8B", "RedHatAI/Qwen3-8B-speculator.eagle3", "qwen3-8b", QWEN3_ROPE_SCALING),
}


def model_family_for(dataset: str) -> tuple[str, str, str, str]:
    """(model_path, draft_model_path, served_model_name, rope_scaling_json) for this dataset name."""
    if dataset.endswith("_qwen3"):
        return MODEL_FAMILIES["qwen3"]
    return MODEL_FAMILIES["gpt_oss_20b"]


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
    parser.add_argument(
        "--skip-strict", action="store_true",
        help="Skip the lossless (`strict`) reference pass. On by default since 2026-08-15 (user request) -- pass this to opt out.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def case_list(n: int) -> list[str]:
    return [f"case_{i:03d}" for i in range(1, n + 1)]


def clean_partial_runs(runs_root: pathlib.Path, dataset: str) -> int:
    """Remove any seed_N/ run directory that exists but either has no
    run.json (a case that started -- run_experiment_vllm.py already wrote
    config.json/request.json -- and then never finished: server killed,
    process crashed, host restarted, timeout, ...) OR has a run.json whose
    status is not "ok" (the request itself completed and got a response,
    but it was an error -- e.g. an HTTP 500 from a server-side crash).

    Load-bearing for resumability: run_experiment_vllm.py's run_one()
    refuses to write into a directory that already exists
    (`FileExistsError` unless --overwrite), and fresh_server_replay.py's own
    skip-if-done check only looks for run.json EXISTING, not its status.
    Without this cleanup, either shape -- missing run.json, or a real one
    recording status="error" -- would make every future retry of that exact
    (method, alpha, case) silently skip forever, not just fail loudly once.
    Confirmed reproducing the missing-run.json shape in the gsm8k smoke test
    (a `timeout 300`-killed run left `alpha0.35/case_001/seed_0/` with
    config/request/server_info.json but no run.json); confirmed the
    status="error" shape for real on 2026-08-18 (longbench_v2_qwen3
    strict/case_007: a CUDA device-side assert crashed that one server mid-
    request, run_experiment_vllm.py's own exception handler wrote
    `{"status": "error", ...}` before re-raising, and the next dataset-wide
    rerun silently treated it as done until this function grew a status
    check).
    """
    dataset_root = runs_root / dataset
    if not dataset_root.is_dir():
        return 0
    removed = 0
    for seed_dir in dataset_root.glob("*/*/*/seed_*"):
        if not seed_dir.is_dir():
            continue
        run_json = seed_dir / "run.json"
        needs_cleanup = False
        if not run_json.is_file():
            needs_cleanup = any(seed_dir.iterdir())
        else:
            try:
                status = json.loads(run_json.read_text(encoding="utf-8")).get("status")
            except (OSError, json.JSONDecodeError):
                status = None  # unreadable run.json is as good as no run.json -- redo it
            needs_cleanup = status != "ok"
        if needs_cleanup:
            reason = "no run.json" if not run_json.is_file() else f"run.json status={status!r}"
            print(f"cleaning up partial/errored run dir ({reason}): {seed_dir}")
            for child in seed_dir.iterdir():
                child.unlink()
            seed_dir.rmdir()
            removed += 1
    return removed


def model_flags(model_path: str, draft_model_path: str, served_model_name: str, rope_scaling_json: str) -> list[str]:
    flags = [
        "--model-path", model_path,
        "--draft-model-path", draft_model_path,
        "--served-model-name", served_model_name,
    ]
    if rope_scaling_json:
        flags += ["--rope-scaling-json", rope_scaling_json]
    return flags


def run_fresh_server_replay(
    *, method: str, alpha: float, cases: list[str], prompt_root: pathlib.Path,
    runs_root: pathlib.Path, log_root: pathlib.Path, max_new_tokens: int, port: int, dry_run: bool,
    model_path: str, draft_model_path: str, served_model_name: str, rope_scaling_json: str,
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
        *model_flags(model_path, draft_model_path, served_model_name, rope_scaling_json),
        # Tracing is ON (fresh_server_replay.py's own default) -- see
        # campaign/PLAN.md's disk-budget section for why this was briefly
        # off and got turned back on.
    ]
    if dry_run:
        command.append("--dry-run")
    print(f"$ {' '.join(command)}", flush=True)
    return subprocess.run(command, cwd=REPO_ROOT, check=False)


def run_strict_reference(
    *, cases: list[str], prompt_root: pathlib.Path, runs_root: pathlib.Path,
    log_root: pathlib.Path, max_new_tokens: int, port: int, dry_run: bool,
    model_path: str, draft_model_path: str, served_model_name: str, rope_scaling_json: str,
) -> subprocess.CompletedProcess:
    """Lossless reference point (2026-08-15, user request): a single
    `--arms strict` pass over the full case set, one run per case, no alpha
    axis (fresh_server_replay.py's own `method_and_params_for()` maps
    "strict" -> runs/<dataset>/strict/strict/<case>/seed_0/). Not part of
    the alpha-sweep loop -- it's a fixed reference the 5 lossy methods'
    l̄-matched points get compared against, so it needs no calibration and
    runs once, on the full 12 cases directly (skip-if-done like every other
    fresh_server_replay.py call, so re-running a dataset that already has
    its strict reference is a no-op here)."""
    command = [
        PYTHON, str(REPO_ROOT / "scripts" / "fresh_server_replay.py"),
        "--arms", "strict",
        "--cases", *cases,
        "--prompt-root", str(prompt_root),
        "--runs-root", str(runs_root),
        "--log-root", str(log_root),
        "--max-new-tokens", str(max_new_tokens),
        "--port", str(port),
        *model_flags(model_path, draft_model_path, served_model_name, rope_scaling_json),
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
    model_path, draft_model_path, served_model_name, rope_scaling_json = model_family_for(args.dataset)

    print(f"=== campaign_run: dataset={args.dataset} methods={args.methods} "
          f"probe_cases={probe_cases} full_cases={len(full_cases)} max_new_tokens={max_new_tokens} "
          f"model={served_model_name} ({model_path} + {draft_model_path}) ===", flush=True)

    if not args.dry_run:
        removed = clean_partial_runs(args.runs_root, args.dataset)
        if removed:
            print(f"cleaned up {removed} partial run dir(s) from a previous interrupted attempt", flush=True)

    # --- Stage 0: lossless (`strict`) reference, full case set, no alpha axis ---
    if not args.skip_strict:
        result = run_strict_reference(
            cases=full_cases, prompt_root=prompt_root, runs_root=args.runs_root,
            log_root=log_root, max_new_tokens=max_new_tokens, port=args.port, dry_run=args.dry_run,
            model_path=model_path, draft_model_path=draft_model_path, served_model_name=served_model_name, rope_scaling_json=rope_scaling_json,
        )
        if result.returncode != 0:
            print(f"warning: strict reference run failed (exit {result.returncode}), continuing", file=sys.stderr)

    # --- Stage 1: calibration grid ---
    for method in args.methods:
        for alpha in ALPHA_GRIDS[method]:
            result = run_fresh_server_replay(
                method=method, alpha=alpha, cases=probe_cases, prompt_root=prompt_root,
                runs_root=args.runs_root, log_root=log_root, max_new_tokens=max_new_tokens,
                port=args.port, dry_run=args.dry_run,
                model_path=model_path, draft_model_path=draft_model_path, served_model_name=served_model_name, rope_scaling_json=rope_scaling_json,
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
                model_path=model_path, draft_model_path=draft_model_path, served_model_name=served_model_name, rope_scaling_json=rope_scaling_json,
            )
            if result.returncode != 0:
                print(f"warning: full-sweep run failed method={method} alpha={alpha} (exit {result.returncode}), continuing", file=sys.stderr)

    print(f"=== campaign_run done: dataset={args.dataset} ===", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
