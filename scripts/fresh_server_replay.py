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
    # registry -- the two future-guard variants and spec_casc_tok_force_commit
    # are the only methods here with two. Default matches each patch's own
    # missing-file default. Own flag per variant (not shared) so a sweep
    # running multiple such arms at once can use different values per arm
    # without one overwriting the other.
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
    parser.add_argument(
        "--spec-casc-tok-force-commit-threshold",
        type=int,
        default=28000,
        help="spec_casc_tok_force_commit only: cumulative token count before forcing a final-channel-open.",
    )
    parser.add_argument(
        "--spec-casc-tok-self-check-interval",
        type=int,
        default=3000,
        help="spec_casc_tok_self_check only: real tokens between periodic self-checks.",
    )
    parser.add_argument(
        "--spec-casc-tok-self-check-final-threshold",
        type=int,
        default=28000,
        help="spec_casc_tok_self_check only: a 'yes' past this cumulative token count forces final instead of pivoting.",
    )
    parser.add_argument(
        "--spec-casc-tok-free-judgment-trace-path",
        default="",
        help="spec_casc_tok_free_judgment only: file to append observation JSONL rows to. Empty = disabled (no-op).",
    )
    parser.add_argument(
        "--spec-casc-tok-free-judgment-reject-threshold",
        type=float,
        default=0.08,  # picked from real-trace resample-rate calibration, not a proof of separation --
        # see HASHES.txt's "REDESIGN 2026-08-13" entry: no transform of the per-round p_yes/p_no
        # reading separates "needs it" from "doesn't", so this design makes a false positive cheap
        # (bans only the single last real drafted token, rejection sampling resamples a fresh
        # alternative there) instead of trying to discriminate perfectly, and can safely default ON.
        help="spec_casc_tok_free_judgment only: per-round score=p_yes-p_no threshold that triggers a reject-and-resample of the last real drafted token.",
    )
    parser.add_argument(
        "--spec-casc-tok-judge-nudge-threshold",
        type=float,
        default=0.03,  # NOT rigorously calibrated -- see patches/HASHES.txt's own spec-casc-tok-judge-nudge entry
        help="spec_casc_tok_judge_nudge only: per-round score=p_true-p_false threshold that arms a nudge window.",
    )
    parser.add_argument(
        "--spec-casc-tok-judge-nudge-rv-alpha",
        type=float,
        default=0.3,  # Reflective Verification's own default (arXiv:2505.18629)
        help="spec_casc_tok_judge_nudge only: blend coefficient for the NUDGE mode's z_mix=(1-alpha)*z0+alpha*z_reflect.",
    )
    parser.add_argument(
        "--spec-casc-tok-judge-nudge-window",
        type=int,
        default=4,
        help="spec_casc_tok_judge_nudge only: fixed number of rounds to nudge for once triggered.",
    )
    parser.add_argument(
        "--spec-casc-tok-judge-nudge-trace-path",
        default="",
        help="spec_casc_tok_judge_nudge only: file to append observation JSONL rows to. Empty = disabled (no-op).",
    )
    parser.add_argument(
        "--spec-casc-tok-hsr-guard-window",
        type=int,
        default=600,
        help="spec_casc_tok_hsr_guard only: committed-token window for both the recurrence budget and the percentile self-calibration.",
    )
    parser.add_argument(
        "--spec-casc-tok-hsr-guard-budget",
        type=int,
        default=25,  # not 3 -- see patches/HASHES.txt's own hsr-guard-model-runner "fixed" entry
        help="spec_casc_tok_hsr_guard only: recurrence-crossings required within the window to trip the guard.",
    )
    parser.add_argument(
        "--spec-casc-tok-hsr-guard-percentile",
        type=float,
        default=99.9,
        help="spec_casc_tok_hsr_guard only: self-calibrated per-generation percentile threshold for a recurrence crossing.",
    )
    parser.add_argument(
        "--spec-casc-tok-hsr-guard-actuator-k",
        type=int,
        default=8,
        help="spec_casc_tok_hsr_guard only: strict-verification window length once the budget trips.",
    )
    parser.add_argument("--prompt-root", type=pathlib.Path, default=pathlib.Path("prompts/humaneval"))
    parser.add_argument(
        "--runs-root",
        type=pathlib.Path,
        default=pathlib.Path("runs"),
        help="Top-level runs directory; the benchmark name (prompt-root's own basename, "
        "e.g. 'aime24', 'humaneval') is appended automatically, giving "
        "<runs-root>/<bench>/<method>/<params>/<case>/seed_N/.",
    )
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
    # Model-family override (2026-08-17, Qwen3-8B+drafter run). Every
    # default below is GPT-OSS-20B's own pair, so a plain invocation is
    # byte-for-byte the same as before this was added. All three must move
    # together: MODEL_PATH/DRAFT_MODEL_PATH become run_server_vllm.sh's own
    # env vars (what the server actually loads), served-model-name becomes
    # BOTH the server's --served-model-name AND run_experiment_vllm.py's
    # --model (the client's request_payload["model"] -- vLLM 400s if these
    # two don't match).
    parser.add_argument("--model-path", default="openai/gpt-oss-20b", help="Target model, HF repo id or local path. Sets run_server_vllm.sh's MODEL_PATH.")
    parser.add_argument("--draft-model-path", default="nebius/EAGLE3-gpt-oss-20b", help="Speculative-decoding draft model. Sets run_server_vllm.sh's DRAFT_MODEL_PATH.")
    parser.add_argument("--served-model-name", default="gpt-oss-20b", help="Must match on both the server (--served-model-name) and the client (request's \"model\" field).")
    parser.add_argument(
        "--rope-scaling-json", default="",
        help="Raw JSON for run_server_vllm.sh's ROPE_SCALING_JSON (the value of a \"rope_scaling\" hf-override, "
        "e.g. '{\"rope_type\":\"yarn\",\"factor\":1.6,\"original_max_position_embeddings\":40960}'). "
        "Empty (default) = no override, matches every model whose native window already covers --max-new-tokens.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def alpha_for(args: argparse.Namespace, method: str) -> float:
    return getattr(args, f"{method}_alpha")


def tag_for(args: argparse.Namespace, arm: str) -> str:
    """Compact single-string display label (log filenames only, not the
    run directory -- see method_and_params_for() for that)."""
    method, params = method_and_params_for(args, arm)
    if method == params:  # strict/baseline: no separate params axis
        return method + args.tag_suffix
    camel = "".join(part.capitalize() if i else part for i, part in enumerate(method.split("_")))
    # params is e.g. "alpha0.3_budget25_pct99.9_k8" -- turn it into the same
    # compact CamelCase+suffix shape tag_for() has always produced, purely
    # for readable log filenames.
    compact = params.replace("alpha", "", 1)
    return f"{camel}{compact}" + args.tag_suffix


def method_and_params_for(args: argparse.Namespace, arm: str) -> tuple[str, str]:
    """(method, params) for the run directory: runs-root/<bench>/<method>/
    <params>/<case>/seed_N/. params always starts with alpha<value> for
    every relaxed method (the one knob every MethodSpec has), with any
    extra per-method knobs appended -- this must be the FULL set of knobs
    that actually affects the generation, not just alpha, or two genuinely
    different configs can collide under the same directory (this bit
    hsr-guard for real: its old tag only had alpha+K, not budget/
    percentile, so a mis-calibrated pilot and the corrected full sweep
    both landed under the same directory name -- see patches/HASHES.txt's
    own hsr-guard-model-runner "fixed" entry and analysis/semantic_guard/
    README.md)."""
    if arm in ("strict", "baseline"):
        return arm, arm
    alpha = alpha_for(args, arm)
    # Dots kept literal (alpha0.3, not alpha0p3): matches the params strings
    # already on disk from the runs/ reorganization (see runs/readme.md and
    # patches/HASHES.txt), so future runs land next to, not beside, the
    # historical data for the same config. "-" is still escaped since a
    # literal minus is a directory-naming footgun (e.g. -inf).
    params = f"alpha{alpha:g}".replace("-", "neg")
    if arm == "spec_casc_tok_semantic_guard_future_guard":
        params += f"_k{args.spec_casc_tok_semantic_guard_future_guard_k}"
    if arm == "spec_casc_tok_semantic_guard_future_guard_and":
        params += f"_k{args.spec_casc_tok_semantic_guard_future_guard_and_k}"
    if arm == "spec_casc_tok_force_commit":
        params += f"_t{args.spec_casc_tok_force_commit_threshold}"
    if arm == "spec_casc_tok_self_check":
        params += f"_i{args.spec_casc_tok_self_check_interval}"
    if arm == "spec_casc_tok_hsr_guard":
        params += (
            f"_budget{args.spec_casc_tok_hsr_guard_budget}"
            f"_pct{args.spec_casc_tok_hsr_guard_percentile:g}"
            f"_k{args.spec_casc_tok_hsr_guard_actuator_k}"
        )
    return arm, params


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
        #
        # mentored-dec is special-cased to its V1-only patch (same reason
        # and same file as apply.sh's own fresh-install path -- see its
        # 2026-08-20 comment): the original two-file vllm-0.26.0-mentored-
        # dec.patch's V2 hunk was written against a pristine V2, but V2 has
        # permanently carried the consolidated 5-method logic since earlier
        # that session and is never touched per-method any more, forward OR
        # reverse. Reversing the full patch here failed the same way
        # apply.sh's forward-install did (4/4 V2 hunks FAILED), blocking
        # every mentored-dec->other-method switch in an unattended sweep --
        # a real, later find, since this reversal path wasn't touched by
        # the first fix.
        if label == "mentored-dec":
            other_patch = REPO_ROOT / "patches" / "vllm-0.26.0-mentored-dec-v1only.patch"
        else:
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
    env["MODEL_PATH"] = args.model_path
    env["DRAFT_MODEL_PATH"] = args.draft_model_path
    env["SERVED_MODEL_NAME"] = args.served_model_name
    env["ROPE_SCALING_JSON"] = args.rope_scaling_json
    mode = "baseline" if arm == "baseline" else ("strict" if arm == "strict" else "lossy")
    if arm not in ("baseline", "strict"):
        env["LOSSY_RULE"] = arm
        env[METHODS[arm].env_var] = f"{alpha_for(args, arm):g}"
        if arm == "spec_casc_tok_semantic_guard_future_guard":
            env["SPEC_CASC_TOK_FUTURE_GUARD_K"] = str(args.spec_casc_tok_semantic_guard_future_guard_k)
        if arm == "spec_casc_tok_semantic_guard_future_guard_and":
            env["SPEC_CASC_TOK_FUTURE_GUARD_AND_K"] = str(args.spec_casc_tok_semantic_guard_future_guard_and_k)
        if arm == "spec_casc_tok_force_commit":
            env["SPEC_CASC_TOK_FORCE_COMMIT_THRESHOLD"] = str(args.spec_casc_tok_force_commit_threshold)
        if arm == "spec_casc_tok_self_check":
            env["SPEC_CASC_TOK_SELF_CHECK_INTERVAL"] = str(args.spec_casc_tok_self_check_interval)
            env["SPEC_CASC_TOK_SELF_CHECK_FINAL_THRESHOLD"] = str(args.spec_casc_tok_self_check_final_threshold)
        if arm == "spec_casc_tok_free_judgment":
            env["SPEC_CASC_TOK_FREE_JUDGMENT_TRACE_PATH"] = args.spec_casc_tok_free_judgment_trace_path
            env["SPEC_CASC_TOK_FREE_JUDGMENT_REJECT_THRESHOLD"] = str(args.spec_casc_tok_free_judgment_reject_threshold)
        if arm == "spec_casc_tok_judge_nudge":
            env["SPEC_CASC_TOK_JUDGE_NUDGE_THRESHOLD"] = str(args.spec_casc_tok_judge_nudge_threshold)
            env["SPEC_CASC_TOK_JUDGE_NUDGE_RV_ALPHA"] = str(args.spec_casc_tok_judge_nudge_rv_alpha)
            env["SPEC_CASC_TOK_JUDGE_NUDGE_WINDOW"] = str(args.spec_casc_tok_judge_nudge_window)
            env["SPEC_CASC_TOK_JUDGE_NUDGE_TRACE_PATH"] = args.spec_casc_tok_judge_nudge_trace_path
        if arm == "spec_casc_tok_hsr_guard":
            env["HSR_GUARD_WINDOW"] = str(args.spec_casc_tok_hsr_guard_window)
            env["HSR_GUARD_BUDGET"] = str(args.spec_casc_tok_hsr_guard_budget)
            env["HSR_GUARD_PERCENTILE"] = str(args.spec_casc_tok_hsr_guard_percentile)
            env["HSR_GUARD_ACTUATOR_K"] = str(args.spec_casc_tok_hsr_guard_actuator_k)

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
    args: argparse.Namespace, arm: str, case: str, seed: int, tag: str, method: str, params: str,
    runs_root: pathlib.Path, log_path: pathlib.Path,
) -> subprocess.CompletedProcess:
    mode = "baseline" if arm == "baseline" else ("strict" if arm == "strict" else "lossy")
    command = [
        args.python,
        str(REPO_ROOT / "scripts" / "run_experiment_vllm.py"),
        "--mode", mode,
        "--prompt-root", str(args.prompt_root),
        "--runs-root", str(runs_root),
        "--cases", case,
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
        "--assert-fresh-server",
        "--model", args.served_model_name,
        "--draft-model", args.draft_model_path,
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

    bench = args.prompt_root.name
    runs_root = REPO_ROOT / args.runs_root / bench

    plan = [
        (case, seed, arm, tag_for(args, arm), *method_and_params_for(args, arm))
        for case in args.cases
        for seed in args.seeds
        for arm in args.arms
    ]
    todo = []
    for case, seed, arm, tag, method, params in plan:
        run_json = runs_root / method / params / case / f"seed_{seed}" / "run.json"
        if run_json.is_file() and not args.overwrite:
            print(f"skip {case} seed={seed} {method}/{params}: already present ({run_json})")
            continue
        todo.append((case, seed, arm, tag, method, params))

    print(f"{len(todo)} run(s), one fresh server each")
    if args.dry_run:
        for case, seed, arm, tag, method, params in todo:
            print(f"  {case} seed={seed} arm={arm} -> {bench}/{method}/{params}")
        return 0
    if not todo:
        return 0

    if args.capture_hidden_states:
        ensure_hidden_state_capture_applied()

    results = []
    failures = 0
    for index, (case, seed, arm, tag, method, params) in enumerate(todo, start=1):
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
            run_dir = runs_root / method / params / case / f"seed_{seed}"
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
                completed = request_once(args, arm, case, seed, tag, method, params, runs_root, log_path)
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
                "method": method,
                "params": params,
                "status": status,
                "wall_time_seconds": round(elapsed, 1),
                "server_log": os.path.relpath(log_path, REPO_ROOT),
            }
        )

    manifest = runs_root / "fresh_server_replay.json"
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
