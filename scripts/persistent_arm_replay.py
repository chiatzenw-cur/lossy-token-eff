#!/usr/bin/env python3
"""Replay cases with one server kept alive per (arm, seed) -- restarted only
when the arm (method+alpha) or seed changes, not per case.

This is a DELIBERATE, EXPLICITLY-REQUESTED deviation from
scripts/fresh_server_replay.py's fresh-per-measurement policy (see that
script's own docstring, and remote/ENVIRONMENT.md's "Fresh server per
measurement -- not optional" section, for why that policy exists: request
ordinal position on a warm engine measurably changes output length --
continuous batching + RNG state carry over between requests -- and that
confound previously flipped a real 9/10 vs 6/10 accuracy comparison into a
tie once isolated).

User (2026-08-26) explicitly chose to accept that risk in exchange for
speed at the campaign's now-much-larger scope, after: (1) being shown the
sibling-repo evidence and a live re-measurement on this exact box quantifying
it (aime24 GPT-OSS: mean 72.7s generation vs 103.5s restart overhead per
request, stdev 2.8s -- a real, stable cost, not noise); (2) declining an
offered ~1h direct verification of the ordinal effect on this setup;
(3) learning that a TRUE single-server-for-everything isn't mechanically
possible without new engineering (method/alpha are read from environment
variables at server-process startup, not per-request -- see
fresh_server_replay.py's start_server()), and choosing "one server per arm,
reused across its cases" as the feasible ceiling instead.

What this means for the data it produces: every run.json written this way
still carries its own honest `server_request_ordinal` (from
run_experiment_vllm.py's own provenance -- ordinal 1 for an arm's first
case, 2+ for every case after it on the same engine). That field is what
distinguishes this data from scripts/fresh_server_replay.py's output --
check it before treating a get-more-cases pass done this way as directly
comparable to an ordinal-1-only dataset. Not asserted or enforced here;
recorded for whoever analyses it later to see.

Mechanically: for each arm, for each seed, start ONE server, hand
run_experiment_vllm.py the FULL list of that arm's still-missing cases in
one process (no --assert-fresh-server -- multiple cases per engine is the
whole point here), then stop the server. Restarts happen only on an
arm/seed boundary.

Tracing (--trace-proposals) and hidden-state capture are refused outright:
both resolve their destination file once per *process*, and multiple cases
sharing one process here would either collide into one file or silently
overwrite -- pass --no-trace-proposals (fresh_server_replay.py's own
default for anything at this scale anyway; see aime24_extend_collect.sh).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import fresh_server_replay as fsr  # noqa: E402
from lossy_methods import METHODS  # noqa: E402

REPO_ROOT = fsr.REPO_ROOT


def request_many(
    args, arm: str, cases: list[str], seed: int, tag: str, method: str, params: str,
    runs_root: pathlib.Path, log_path: pathlib.Path,
) -> subprocess.CompletedProcess:
    """Like fresh_server_replay.request_once, but hands run_experiment_vllm.py
    every case for this arm+seed in one process (no --assert-fresh-server)."""
    mode = "baseline" if arm == "baseline" else ("strict" if arm == "strict" else "lossy")
    command = [
        args.python,
        str(REPO_ROOT / "scripts" / "run_experiment_vllm.py"),
        "--mode", mode,
        "--prompt-root", str(args.prompt_root),
        "--runs-root", str(runs_root),
        "--cases", *cases,
        "--seeds", str(seed),
        "--tag", tag,
        "--method-dir", method,
        "--params-dir", params,
        "--temperature", str(args.temperature),
        "--top-p", str(args.top_p),
        "--max-new-tokens", str(args.max_new_tokens),
        "--timeout", str(args.request_timeout),
        "--server-url", f"http://127.0.0.1:{args.port}",
        "--server-log", str(log_path),
        "--model", args.served_model_name,
        "--draft-model", args.draft_model_path,
    ]
    if arm not in ("baseline", "strict"):
        command += ["--lossy-method", arm, "--alpha", f"{fsr.alpha_for(args, arm):g}"]
    if args.overwrite:
        command.append("--overwrite")
    return subprocess.run(command, cwd=REPO_ROOT, check=False)


def main() -> int:
    args = fsr.parse_args()
    if args.trace_proposals:
        print(
            "persistent_arm_replay.py requires --no-trace-proposals: tracing resolves its "
            "destination once per server process, and this script runs many cases per "
            "process -- their proposals would collide into one file. Pass --no-trace-proposals.",
            file=sys.stderr,
        )
        return 2
    if args.capture_hidden_states:
        print(
            "persistent_arm_replay.py does not support --capture-hidden-states (same "
            "one-destination-per-process issue as tracing).",
            file=sys.stderr,
        )
        return 2

    unknown = [case for case in args.cases if not (REPO_ROOT / args.prompt_root / case).is_dir()]
    if unknown:
        print(f"unknown cases under {args.prompt_root}: {', '.join(unknown)}", file=sys.stderr)
        return 2

    bench = args.prompt_root.name
    runs_root = REPO_ROOT / args.runs_root / bench

    # Group by (arm, seed): one server serves every still-missing case for
    # that pair. Order matches args.arms / args.seeds as given.
    groups = []
    for arm in args.arms:
        method, params = fsr.method_and_params_for(args, arm)
        for seed in args.seeds:
            missing = [
                case for case in args.cases
                if args.overwrite
                or not (runs_root / method / params / case / f"seed_{seed}" / "run.json").is_file()
            ]
            if missing:
                groups.append((arm, method, params, seed, missing))

    total_cases = sum(len(g[4]) for g in groups)
    print(f"{len(groups)} server(s) (one per arm/seed), {total_cases} case(s) total")
    if args.dry_run:
        for arm, method, params, seed, missing in groups:
            print(f"  arm={arm} seed={seed} -> {bench}/{method}/{params}: {len(missing)} case(s): {' '.join(missing)}")
        return 0
    if not groups:
        return 0

    results = []
    failures = 0
    for index, (arm, method, params, seed, missing) in enumerate(groups, start=1):
        tag = fsr.tag_for(args, arm) + (f"_seed{seed}" if seed != args.server_seed else "")
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = REPO_ROOT / args.log_root / f"{tag}_batch_{stamp}.log"
        print(
            f"\n[{index}/{len(groups)}] arm={arm} seed={seed} -> {len(missing)} case(s), one server -> {log_path}",
            flush=True,
        )
        started = time.perf_counter()
        status = "ok"
        process = None
        try:
            fsr.stop_server()
            fsr.set_trace_destination(None)
            fsr.set_hidden_state_destination(None)
            process = fsr.start_server(args, arm, log_path)
            try:
                completed = request_many(args, arm, missing, seed, tag, method, params, runs_root, log_path)
                if completed.returncode != 0:
                    status = f"request(s) failed (exit {completed.returncode})"
                    failures += 1
            finally:
                fsr.stop_server()
                if process is not None and process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except (RuntimeError, OSError) as exc:
            status = f"{type(exc).__name__}: {exc}"
            failures += 1
            print(status, file=sys.stderr)
            fsr.stop_server()
        elapsed = time.perf_counter() - started
        print(f"[{index}/{len(groups)}] {status} in {elapsed:.0f}s for {len(missing)} case(s)", flush=True)
        results.append(
            {
                "arm": arm,
                "seed": seed,
                "method": method,
                "params": params,
                "cases": missing,
                "status": status,
                "wall_time_seconds": round(elapsed, 1),
                "server_log": os.path.relpath(log_path, REPO_ROOT),
            }
        )

    manifest = runs_root / "persistent_arm_replay.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    previous = []
    if manifest.is_file():
        try:
            previous = json.loads(manifest.read_text(encoding="utf-8")).get("batches", [])
        except (OSError, json.JSONDecodeError):
            previous = []
    previous.append(
        {
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "arms": args.arms,
            "alphas": {name: fsr.alpha_for(args, name) for name in METHODS},
            "command": sys.argv,
            "groups": results,
        }
    )
    manifest.write_text(json.dumps({"batches": previous}, indent=2) + "\n", encoding="utf-8")
    ok_groups = len(results) - failures
    print(f"\nwrote {manifest}; {ok_groups}/{len(results)} group(s) ok, {total_cases} case(s) attempted")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
