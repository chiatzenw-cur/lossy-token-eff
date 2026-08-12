#!/usr/bin/env python3
"""Replay cases with one freshly started server per (arm, case, seed).

Ported from lossy-spec-decode-repetition/scripts/fresh_server_replay.py,
generalised from 3 arms to 6 (strict + 5 relaxed methods, all via
scripts/lossy_methods.py's registry) plus baseline. See that script's own
docstring for why fresh-per-measurement is the policy, not an optimisation
detail: request position on a warm engine measurably changes output length
(the sibling repo's case_001: 1,711 tokens as a server's first request vs
2,485 as its second, same prompt, same seed).

Seed is fixed, not left to default randomness -- --seeds defaults to a
single value (0) and --server-seed likewise, so a re-run of the same plan
reproduces the same requests. This is what "replicable" means here: the
*prompts and requests* are deterministic; the *output* is not guaranteed
bit-identical across restarts (GPU kernel nondeterminism is real and
untouched by this), but nothing about which case/seed/arm ran is left to
chance.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lossy_methods import METHODS, STRICT_TRACE_CARRIER, TRACE_PATH_FILE  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ARMS = ("baseline", "strict", *METHODS.keys())

# Mirrors patches/hidden_state_trace.py's own _DEST_FILE exactly (uid-scoped,
# same /tmp naming convention as every other knob file here) -- not imported
# from there directly, since that module is meant to run inside vLLM's own
# process (imports torch at module scope) and has no reason to be imported
# by this orchestration script too.
HIDDEN_STATE_TRACE_PATH_FILE = pathlib.Path(f"/tmp/lossy-token-eff-hidden-state-trace-{os.getuid()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--arms",
        nargs="+",
        default=["strict", *METHODS.keys()],
        choices=ARMS,
        help="Arms to replay. Each (arm, case, seed) gets its own server.",
    )
    parser.add_argument("--cases", nargs="+", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0], help="Fixed by default (single seed=0) for replicability.")
    for name, spec in METHODS.items():
        parser.add_argument(
            f"--{name.replace('_', '-')}-alpha",
            type=float,
            default=spec.default_alpha,
            help=f"{spec.taxonomy['family']}. Domain: {spec.alpha_domain}.",
        )
    # One-off second knob, not part of the generic MethodSpec (single-knob)
    # registry -- the two future-guard variants are the only methods here with
    # two. Default matches each patch's own missing-file default. Own flag
    # per variant (not shared) so a sweep running both arms at once can use
    # different K per arm without one overwriting the other.
    parser.add_argument(
        "--spec-casc-tok-semantic-guard-future-guard-k",
        type=int,
        default=8,
        help="spec_casc_tok_semantic_guard_future_guard only: length of the strict window after an accepted marker.",
    )
    parser.add_argument(
        "--spec-casc-tok-semantic-guard-future-guard-and-k",
        type=int,
        default=8,
        help="spec_casc_tok_semantic_guard_future_guard_and only: length of the AND-combined window after an accepted marker.",
    )
    parser.add_argument("--prompt-root", type=pathlib.Path, default=pathlib.Path("prompts/humaneval"))
    parser.add_argument("--runs-root", type=pathlib.Path, default=pathlib.Path("runs/humaneval_fresh"))
    parser.add_argument("--log-root", type=pathlib.Path, default=pathlib.Path("logs/humaneval_fresh"))
    parser.add_argument("--tag-suffix", default="", help="Appended to the default per-arm tag.")
    parser.add_argument("--temperature", type=float, default=1.0, help="Fixed, not 0: draft_sample_method=probabilistic needs a real distribution to sample from.")
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=9000)
    parser.add_argument("--server-seed", type=int, default=0, help="vLLM's own --seed. Fixed for replicability.")
    parser.add_argument("--num-spec", type=int, default=6, help="EAGLE3 draft length (NUM_SPEC).")
    parser.add_argument("--port", type=int, default=30000)
    parser.add_argument("--startup-timeout", type=float, default=1800.0)
    parser.add_argument("--request-timeout", type=float, default=7200.0)
    parser.add_argument(
        "--python",
        default=str(REPO_ROOT / ".venv-vllm" / "bin" / "python"),
        help="Interpreter for both the server and the request client.",
    )
    parser.add_argument(
        "--trace-proposals",
        dest="trace_proposals",
        action="store_true",
        default=True,
        help="Record every proposal token to <run dir>/proposals.jsonl. On by default. Observation only.",
    )
    parser.add_argument("--no-trace-proposals", dest="trace_proposals", action="store_false")
    parser.add_argument(
        "--capture-hidden-states",
        action="store_true",
        help=(
            "Also capture target hidden states per round to <run dir>/hidden_states.bin "
            "(patches/hidden_state_trace.py). Off by default -- real per-request storage, "
            "meant for short diagnostic runs, not full sweeps. Applies "
            "patches/apply_hidden_state_capture.sh automatically if not already installed."
        ),
    )
    parser.add_argument("--overwrite", action="store_true", help="Redo runs that already exist.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def alpha_for(args: argparse.Namespace, method: str) -> float:
    return getattr(args, f"{method}_alpha")


def tag_for(args: argparse.Namespace, arm: str) -> str:
    if arm in ("strict", "baseline"):
        base = arm
    else:
        spec = METHODS[arm]
        camel = "".join(part.capitalize() if i else part for i, part in enumerate(arm.split("_")))
        base = f"{camel}{alpha_for(args, arm):g}".replace(".", "p").replace("-", "neg")
        if arm == "spec_casc_tok_semantic_guard_future_guard":
            # K into the tag too, not just alpha -- run directories from
            # different K sweeps must not collide under the same tag.
            base += f"k{args.spec_casc_tok_semantic_guard_future_guard_k}"
        if arm == "spec_casc_tok_semantic_guard_future_guard_and":
            base += f"k{args.spec_casc_tok_semantic_guard_future_guard_and_k}"
    return base + args.tag_suffix


def stop_server() -> None:
    subprocess.run(
        ["bash", str(REPO_ROOT / "remote" / "stop_server.sh")],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def health_ok(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as response:
            return response.status == 200
    except Exception:
        return False


def set_trace_destination(path: pathlib.Path | None) -> None:
    """Tell the patched sampler where to write its proposal trace.

    A file, not an environment variable: EngineCore is spawned with a
    sanitised environment, so env vars never reach the sampler. Must be set
    before the server starts, because the tracer resolves it at import.
    """
    if path is None:
        TRACE_PATH_FILE.write_text("", encoding="utf-8")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        TRACE_PATH_FILE.write_text(str(path), encoding="utf-8")


def set_hidden_state_destination(path: pathlib.Path | None) -> None:
    """Same idea as set_trace_destination, for patches/hidden_state_trace.py's
    own destination knob -- a separate file so hidden-state capture can be
    toggled independently of scalar proposal tracing."""
    if path is None:
        HIDDEN_STATE_TRACE_PATH_FILE.write_text("", encoding="utf-8")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        HIDDEN_STATE_TRACE_PATH_FILE.write_text(str(path), encoding="utf-8")


def ensure_hidden_state_capture_applied() -> None:
    """Idempotent: patches/apply_hidden_state_capture.sh already no-ops if
    already installed (hash match), same as ensure_patch_applied's per-method
    equivalent. Independent of which method's rejection_sampler.py patch is
    installed -- touches a different file entirely."""
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "patches" / "apply_hidden_state_capture.sh")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"patches/apply_hidden_state_capture.sh failed (exit {result.returncode}):\n"
            f"{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
        )


def _installed_v1_label() -> str | None:
    """Which patch (if any) vllm/v1/sample/rejection_sampler.py currently
    matches, by sha256 against patches/HASHES.txt. None means neither
    pristine nor any known patch."""
    from run_experiment_vllm import load_hashes_manifest, sha256_of  # local import: avoids a cycle at module load

    purelib = pathlib.Path(args_python_purelib())
    v1_hash = sha256_of(purelib / "vllm" / "v1" / "sample" / "rejection_sampler.py")
    if v1_hash is None:
        return None
    return load_hashes_manifest().get(v1_hash)


def args_python_purelib() -> str:
    """site-packages of the venv's own interpreter (not this driver's), since
    that's what the server actually imports from."""
    out = subprocess.run(
        [str(REPO_ROOT / ".venv-vllm" / "bin" / "python"), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def ensure_patch_applied(method: str) -> None:
    """Apply the patch this arm needs, switching automatically if a
    DIFFERENT patch is currently installed.

    patches/apply.sh deliberately refuses to auto-switch (a human running it
    by hand should have to notice and reverse the wrong patch explicitly),
    but an unattended multi-arm sweep needs exactly that automation -- the
    whole point of the sweep is visiting every method in turn on the same
    mutually-exclusive file. Reversal uses the same `patch -p1 -R` apply.sh
    itself suggests in its refusal message, not a different mechanism.
    """
    label = _installed_v1_label()
    hashes_label = METHODS[method].hashes_label
    if label != hashes_label and label is not None and label != "upstream":
        # A different patch is installed; reverse it first via the label's
        # own patch file (label == the method name apply.sh/HASHES.txt use).
        other_patch = REPO_ROOT / "patches" / f"vllm-0.26.0-{label}.patch"
        sp = pathlib.Path(args_python_purelib())
        reverse = subprocess.run(
            ["patch", "-p1", "-R", "-d", str(sp)],
            input=other_patch.read_text(encoding="utf-8"),
            capture_output=True,
            text=True,
        )
        if reverse.returncode != 0:
            raise RuntimeError(
                f"failed to reverse {label} patch before applying {method}:\n"
                f"{reverse.stdout[-2000:]}\n{reverse.stderr[-2000:]}"
            )

    result = subprocess.run(
        ["bash", str(REPO_ROOT / "patches" / "apply.sh"), method.replace("_", "-")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"patches/apply.sh {method.replace('_', '-')} failed (exit {result.returncode}):\n"
            f"{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
        )


def start_server(args: argparse.Namespace, arm: str, log_path: pathlib.Path):
    """Start one server and wait for it to serve. Returns the Popen handle."""
    # baseline needs no draft model at all, so no patched kernel is ever
    # exercised -- whatever is currently installed is irrelevant, and no
    # patch is applied for it. Every other arm -- including "strict" -- runs
    # through a patched kernel: pristine vLLM has no tracer hook at all, so
    # "strict" specifically needs STRICT_TRACE_CARRIER applied at its own
    # strict alpha to get a trace (see scripts/lossy_methods.py).
    if arm != "baseline":
        ensure_patch_applied(arm if arm not in ("strict",) else STRICT_TRACE_CARRIER)

    env = dict(os.environ)
    env["PYTHON"] = args.python
    env["PORT"] = str(args.port)
    env["SEED"] = str(args.server_seed)
    env["NUM_SPEC"] = str(args.num_spec)
    mode = "baseline" if arm == "baseline" else ("strict" if arm == "strict" else "lossy")
    if arm not in ("baseline", "strict"):
        env["LOSSY_RULE"] = arm
        env[METHODS[arm].env_var] = f"{alpha_for(args, arm):g}"
        if arm == "spec_casc_tok_semantic_guard_future_guard":
            env["SPEC_CASC_TOK_FUTURE_GUARD_K"] = str(args.spec_casc_tok_semantic_guard_future_guard_k)
        if arm == "spec_casc_tok_semantic_guard_future_guard_and":
            env["SPEC_CASC_TOK_FUTURE_GUARD_AND_K"] = str(args.spec_casc_tok_semantic_guard_future_guard_and_k)

    log_path.parent.mkdir(parents=True, exist_ok=True)
    handle = log_path.open("w", encoding="utf-8")
    # New process group: the server spawns EngineCore children, and
    # stop_server.sh is the thing that knows how to clear the GPU, so this
    # handle is only used for liveness and for a last-resort kill.
    process = subprocess.Popen(
        ["bash", str(REPO_ROOT / "remote" / "run_server_vllm.sh"), mode],
        cwd=REPO_ROOT,
        env=env,
        stdout=handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    deadline = time.time() + args.startup_timeout
    while time.time() < deadline:
        if health_ok(args.port):
            return process
        if process.poll() is not None:
            handle.close()
            tail = "\n".join(log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-25:])
            raise RuntimeError(f"server exited with code {process.returncode} during startup:\n{tail}")
        time.sleep(2.0)
    handle.close()
    raise RuntimeError(f"server did not become healthy within {args.startup_timeout:.0f}s; see {log_path}")


def request_once(
    args: argparse.Namespace, arm: str, case: str, seed: int, tag: str, log_path: pathlib.Path
) -> subprocess.CompletedProcess:
    mode = "baseline" if arm == "baseline" else ("strict" if arm == "strict" else "lossy")
    command = [
        args.python,
        str(REPO_ROOT / "scripts" / "run_experiment_vllm.py"),
        "--mode", mode,
        "--prompt-root", str(args.prompt_root),
        "--runs-root", str(args.runs_root),
        "--cases", case,
        "--seeds", str(seed),
        "--tag", tag,
        "--temperature", str(args.temperature),
        "--top-p", str(args.top_p),
        "--max-new-tokens", str(args.max_new_tokens),
        "--timeout", str(args.request_timeout),
        "--server-url", f"http://127.0.0.1:{args.port}",
        "--server-log", str(log_path),
        "--assert-fresh-server",
    ]
    if arm not in ("baseline", "strict"):
        command += ["--lossy-method", arm, "--alpha", f"{alpha_for(args, arm):g}"]
    if args.overwrite:
        command.append("--overwrite")
    return subprocess.run(command, cwd=REPO_ROOT, check=False)


def main() -> int:
    args = parse_args()
    unknown = [case for case in args.cases if not (REPO_ROOT / args.prompt_root / case).is_dir()]
    if unknown:
        print(f"unknown cases under {args.prompt_root}: {', '.join(unknown)}", file=sys.stderr)
        return 2

    plan = [
        (case, seed, arm, tag_for(args, arm))
        for case in args.cases
        for seed in args.seeds
        for arm in args.arms
    ]
    todo = []
    for case, seed, arm, tag in plan:
        run_json = REPO_ROOT / args.runs_root / case / f"seed_{seed}" / tag / "run.json"
        if run_json.is_file() and not args.overwrite:
            print(f"skip {case} seed={seed} {tag}: already present ({run_json})")
            continue
        todo.append((case, seed, arm, tag))

    print(f"{len(todo)} run(s), one fresh server each")
    if args.dry_run:
        for case, seed, arm, tag in todo:
            print(f"  {case} seed={seed} arm={arm} tag={tag}")
        return 0
    if not todo:
        return 0

    if args.capture_hidden_states:
        ensure_hidden_state_capture_applied()

    results = []
    failures = 0
    for index, (case, seed, arm, tag) in enumerate(todo, start=1):
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        log_path = REPO_ROOT / args.log_root / f"{tag}_{case}_seed{seed}_{stamp}.log"
        print(f"\n[{index}/{len(todo)}] {case} seed={seed} arm={arm} -> {log_path}", flush=True)
        started = time.perf_counter()
        status = "ok"
        process = None
        try:
            stop_server()
            # Set before start_server: the tracer resolves its destination at
            # import, inside EngineCore. Staged outside the run directory --
            # run_experiment_vllm.py refuses to write into a directory that
            # already exists, so creating the trace there first would trip
            # its overwrite guard. Moved into the run directory afterwards.
            run_dir = REPO_ROOT / args.runs_root / case / f"seed_{seed}" / tag
            trace_stage = (
                REPO_ROOT / args.log_root / f"{tag}_{case}_seed{seed}_proposals.jsonl"
                if args.trace_proposals
                else None
            )
            set_trace_destination(trace_stage)
            hidden_state_stage = (
                REPO_ROOT / args.log_root / f"{tag}_{case}_seed{seed}_hidden_states.bin"
                if args.capture_hidden_states
                else None
            )
            set_hidden_state_destination(hidden_state_stage)
            process = start_server(args, arm, log_path)
            try:
                completed = request_once(args, arm, case, seed, tag, log_path)
                if completed.returncode != 0:
                    status = f"request failed (exit {completed.returncode})"
                    failures += 1
            finally:
                stop_server()
                if process is not None and process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                if trace_stage is not None and trace_stage.is_file():
                    if run_dir.is_dir():
                        trace_stage.replace(run_dir / "proposals.jsonl")
                    else:
                        print(f"  warning: run dir missing, trace left at {trace_stage}", file=sys.stderr)
                if hidden_state_stage is not None and hidden_state_stage.is_file():
                    if run_dir.is_dir():
                        hidden_state_stage.replace(run_dir / "hidden_states.bin")
                    else:
                        print(f"  warning: run dir missing, hidden states left at {hidden_state_stage}", file=sys.stderr)
        except (RuntimeError, OSError) as exc:
            status = f"{type(exc).__name__}: {exc}"
            failures += 1
            print(status, file=sys.stderr)
            stop_server()
        finally_trace = None
        try:
            set_trace_destination(None)
            set_hidden_state_destination(None)
        except OSError as exc:  # non-fatal: only affects the next run's tracing
            finally_trace = str(exc)
        elapsed = time.perf_counter() - started
        print(f"[{index}/{len(todo)}] {status} in {elapsed:.0f}s", flush=True)
        if finally_trace:
            print(f"  warning: could not clear trace destination: {finally_trace}", file=sys.stderr)
        results.append(
            {
                "case": case,
                "seed": seed,
                "arm": arm,
                "tag": tag,
                "status": status,
                "wall_time_seconds": round(elapsed, 1),
                "server_log": os.path.relpath(log_path, REPO_ROOT),
            }
        )

    manifest = REPO_ROOT / args.runs_root / "fresh_server_replay.json"
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
            "alphas": {name: alpha_for(args, name) for name in METHODS},
            "command": sys.argv,
            "runs": results,
        }
    )
    manifest.write_text(json.dumps({"batches": previous}, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {manifest}; {len(results) - failures}/{len(results)} ok")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
