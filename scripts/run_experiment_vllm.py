#!/usr/bin/env python3
"""Run and archive one generation against vLLM's OpenAI-compatible API.

Ported from lossy-spec-decode-repetition/scripts/run_experiment_vllm.py and
generalised from 3 hardcoded methods to 5 via scripts/lossy_methods.py's
registry -- see that module's docstring for why. Same artifact contract
(config.json/request.json/response.json/output.txt/run.json/server_info.json
under runs_root/<case>/seed_<N>/<tag>/), so scripts/grade_humaneval.py and
scripts/grade_aime.py work unchanged.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import sysconfig
import time
import urllib.error
import urllib.request
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lossy_methods import METHODS, parse_alpha_from_log_line  # noqa: E402

DEFAULT_PROMPT_ROOT = pathlib.Path("prompts/humaneval")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("baseline", "strict", "lossy"))
    parser.add_argument(
        "--lossy-method",
        choices=(*METHODS.keys(), "synthetic_acceptance"),
        default=None,
        help="Required in lossy mode. Must match the server's LOSSY_RULE.",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        help="Required for every --lossy-method except synthetic_acceptance. See scripts/lossy_methods.py.",
    )
    parser.add_argument(
        "--synthetic-acceptance-length",
        type=float,
        default=None,
        help="Required for --lossy-method synthetic_acceptance; must match SYNTH_LEN.",
    )
    parser.add_argument("--tag", help="Display/config.json label; defaults to a name built from the arm. No longer used for the output directory (see --method-dir/--params-dir).")
    parser.add_argument("--method-dir", help="Output directory's <method> level; defaults to args.mode/args.lossy_method. Callers with extra per-method knobs beyond alpha (e.g. K, budget) should pass this explicitly together with --params-dir so the directory fully identifies the config.")
    parser.add_argument("--params-dir", help="Output directory's <params> level; defaults to alpha<value> (or the mode name for strict/baseline). Paired with --method-dir.")
    parser.add_argument("--server-url", default="http://127.0.0.1:30000")
    parser.add_argument("--prompt-root", type=pathlib.Path, default=DEFAULT_PROMPT_ROOT)
    parser.add_argument("--cases", nargs="+", default=None)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0])
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=9000)
    parser.add_argument("--timeout", type=float, default=3600.0)
    parser.add_argument("--runs-root", type=pathlib.Path, default=pathlib.Path("runs"))
    parser.add_argument("--model", default="gpt-oss-20b", help="Served model name.")
    parser.add_argument("--draft-model", default="nebius/EAGLE3-gpt-oss-20b")
    parser.add_argument(
        "--assert-fresh-server",
        action="store_true",
        help=(
            "Fail unless the server has served nothing yet. Output depends on how "
            "many requests preceded it on the same engine, so an arm comparison is "
            "only clean if both sides sit at the same position -- which one request "
            "per server makes trivially true."
        ),
    )
    parser.add_argument(
        "--server-log",
        type=pathlib.Path,
        default=None,
        help=(
            "Server stdout/stderr log. The patched sampler announces the alpha it "
            "loaded there; recording that line is the only proof that does not "
            "depend on the file still holding the same value."
        ),
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def write_json(path: pathlib.Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def http_json(url: str, *, payload: dict[str, Any] | None, timeout: float) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def spec_counters(base_url: str) -> dict[str, float]:
    """Cumulative speculative-decode counters from /metrics.

    vLLM reports these per engine, not per request, so a request's own counts
    come from differencing a snapshot taken either side of it. Valid only while
    requests are issued one at a time.
    """
    wanted = {
        "vllm:spec_decode_num_draft_tokens_total": "draft_tokens",
        "vllm:spec_decode_num_accepted_tokens_total": "accepted_tokens",
        "vllm:spec_decode_num_drafts_total": "drafts",
    }
    out: dict[str, float] = {}
    try:
        request = urllib.request.Request(f"{base_url.rstrip('/')}/metrics")
        text = urllib.request.urlopen(request, timeout=30).read().decode("utf-8")
    except Exception:
        return out
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        for metric, key in wanted.items():
            if line.startswith(metric):
                try:
                    out[key] = float(line.rsplit(" ", 1)[1])
                except (ValueError, IndexError):
                    pass
    return out


def acceptance_stats(before: dict[str, float], after: dict[str, float]) -> dict[str, Any]:
    """Per-request acceptance, from the counter delta.

    l_bar is mean accepted DRAFT tokens per verification round, so the mean
    accepted length including the always-kept bonus token is l_bar + 1.
    """
    drafted = after.get("draft_tokens", 0.0) - before.get("draft_tokens", 0.0)
    accepted = after.get("accepted_tokens", 0.0) - before.get("accepted_tokens", 0.0)
    drafts = after.get("drafts", 0.0) - before.get("drafts", 0.0)
    stats: dict[str, Any] = {
        "draft_tokens": drafted or None,
        "accepted_tokens": accepted or None,
        "draft_rounds": drafts or None,
        "draft_acceptance_rate": (accepted / drafted) if drafted else None,
        "l_bar": (accepted / drafts) if drafts else None,
    }
    stats["mean_accept_length"] = (stats["l_bar"] + 1) if stats["l_bar"] is not None else None
    return stats


def server_info(base_url: str) -> dict[str, Any]:
    """vLLM has no /get_server_info; record what the OpenAI surface exposes."""
    info: dict[str, Any] = {}
    for name, path in (("models", "/v1/models"), ("version", "/version")):
        try:
            info[name] = http_json(f"{base_url.rstrip('/')}{path}", payload=None, timeout=30)
        except Exception as exc:
            info[name] = {"unavailable": f"{type(exc).__name__}: {exc}"}
    return info


def engine_totals(base_url: str) -> dict[str, float]:
    """Cumulative work counters, used only to tell a fresh engine from a used one."""
    wanted = (
        "vllm:prompt_tokens_total",
        "vllm:generation_tokens_total",
        "vllm:request_success_total",
        "vllm:spec_decode_num_drafts_total",
    )
    out: dict[str, float] = {}
    try:
        request = urllib.request.Request(f"{base_url.rstrip('/')}/metrics")
        text = urllib.request.urlopen(request, timeout=30).read().decode("utf-8")
    except Exception:
        return out
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        for metric in wanted:
            if line.startswith(metric):
                try:
                    out[metric] = out.get(metric, 0.0) + float(line.rsplit(" ", 1)[1])
                except (ValueError, IndexError):
                    pass
    return out


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_dirty() -> bool | None:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True, stderr=subprocess.DEVNULL
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return bool(out.strip())


def sha256_of(path: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def load_hashes_manifest() -> dict[str, str]:
    """sha256 -> label, from patches/HASHES.txt. Single source of truth,
    shared with patches/apply.sh, instead of duplicating hashes in this file
    the way the sibling repo's PATCHED_FILES/*_PATCHED_FILES dicts did.

    Keyed by hash, not by label: the manifest reuses the label "upstream" for
    BOTH files' pristine hashes (they're different files with different
    content, so different hashes, but the same meaning), so a label-keyed
    dict would silently let the second "upstream" line overwrite the first.
    Hashes don't collide across files, so this direction is unambiguous.
    """
    manifest_path = pathlib.Path(__file__).resolve().parent.parent / "patches" / "HASHES.txt"
    out: dict[str, str] = {}
    try:
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                out[parts[0]] = parts[1]
    except OSError:
        pass
    return out


def vllm_install_info() -> dict[str, Any]:
    """Version and verifier hashes of the vLLM this interpreter would import.

    Read off disk rather than by importing vLLM: this is the client process and
    importing it costs ~10s per invocation, which the one-server-per-case driver
    pays once per case. Only meaningful when the runner shares a filesystem with
    the server, which is the supported single-box setup.
    """
    info: dict[str, Any] = {"version": None, "commit_id": None, "site_packages": None}
    try:
        purelib = pathlib.Path(sysconfig.get_paths()["purelib"])
    except Exception:
        return info
    info["site_packages"] = str(purelib)
    version_py = purelib / "vllm" / "_version.py"
    try:
        text = version_py.read_text(encoding="utf-8")
    except OSError:
        return info
    for key, pattern in (
        ("version", r"__version__ = version = '([^']+)'"),
        ("commit_id", r"__commit_id__ = commit_id = '([^']+)'"),
    ):
        match = re.search(pattern, text)
        if match:
            info[key] = match.group(1)

    hash_to_label = load_hashes_manifest()
    v1_rel = "vllm/v1/sample/rejection_sampler.py"
    v2_rel = "vllm/v1/worker/gpu/spec_decode/rejection_sampler_utils.py"
    v1_hash = sha256_of(purelib / v1_rel)
    v2_hash = sha256_of(purelib / v2_rel)
    info["v1_sha256"] = v1_hash
    info["v2_sha256"] = v2_hash
    v1_label = hash_to_label.get(v1_hash) if v1_hash else None
    v2_label = hash_to_label.get(v2_hash) if v2_hash else None
    info["v1_label"] = v1_label
    info["v2_label"] = v2_label
    patches_applied: dict[str, bool] = {}
    for name, spec in METHODS.items():
        v1_ok = v1_label == spec.hashes_label
        v2_ok = (v2_label == spec.hashes_label) if spec.touches_v2 else (v2_label == "upstream")
        patches_applied[name] = v1_ok and v2_ok
    info["patch_applied"] = patches_applied
    info["v1_is_pristine"] = v1_label == "upstream"
    return info


def alpha_in_force(method: str) -> dict[str, Any]:
    """The alpha the patched sampler would load, read from its own channel.

    The server writes this file before starting and the sampler reads it at
    import, so agreement between it and --alpha is what makes a run directory
    self-describing.
    """
    spec = METHODS[method]
    record: dict[str, Any] = {"path": str(spec.alpha_file), "value": None}
    try:
        record["value"] = float(spec.alpha_file.read_text().strip())
        record["mtime_utc"] = dt.datetime.fromtimestamp(
            spec.alpha_file.stat().st_mtime, dt.timezone.utc
        ).isoformat()
    except (OSError, ValueError) as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    return record


def server_log_alpha(method: str, path: pathlib.Path | None) -> dict[str, Any] | None:
    """The alpha the sampler actually announced, scraped from the server log.

    The file check above can only say what the file held when the client
    looked; this says what the engine loaded at import, which is the value
    that ran.
    """
    if path is None:
        return None
    spec = METHODS[method]
    record: dict[str, Any] = {"path": str(path), "lines": [], "alphas": []}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record
    for line in text.splitlines():
        if spec.log_prefix not in line:
            continue
        record["lines"].append(line.strip())
        value = parse_alpha_from_log_line(line)
        if value is not None:
            record["alphas"].append(value)
    record["distinct_alphas"] = sorted(set(record["alphas"]))
    return record


def selected_cases(prompt_root: pathlib.Path) -> list[str]:
    index_path = prompt_root / "candidate_index.jsonl"
    selected: list[str] = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("selected_for_pilot", True):
            selected.append(str(item["case"]))
    if not selected:
        raise ValueError(f"No cases in {index_path}")
    return selected


def safe_tag(args: argparse.Namespace) -> str:
    if args.tag:
        tag = args.tag
    elif args.mode != "lossy":
        tag = args.mode
    elif args.lossy_method == "synthetic_acceptance":
        tag = f"synthetic{args.synthetic_acceptance_length:g}".replace(".", "p")
    else:
        camel = "".join(
            part.capitalize() if i else part
            for i, part in enumerate(args.lossy_method.split("_"))
        )
        tag = f"{camel}{args.alpha:g}".replace(".", "p").replace("-", "neg")
    # "." allowed: tag is metadata/log-filename only now (not a path
    # component -- see --method-dir/--params-dir), and callers such as
    # fresh_server_replay.py's tag_for() pass explicit --tag values with a
    # literal decimal point (e.g. "specCascTok0.31") to match its own
    # dot-preserving params convention.
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if not tag or any(ch not in allowed for ch in tag):
        raise ValueError(f"Unsafe tag: {tag!r}")
    return tag


def safe_method_and_params(args: argparse.Namespace) -> tuple[str, str]:
    """(method, params) for the output directory: runs_root/<method>/<params>/
    <case>/seed_<N>/. Explicit --method-dir/--params-dir win (needed for
    methods with extra knobs beyond alpha -- K, budget, threshold, interval
    -- that this script has no other way to know about, since those are set
    via /tmp knob files or env vars by the caller, not CLI args here);
    otherwise derived the same way safe_tag() derives its own single string,
    just split into two levels instead of one."""
    if args.method_dir and args.params_dir:
        method, params = args.method_dir, args.params_dir
    elif args.mode != "lossy":
        method, params = args.mode, args.mode
    elif args.lossy_method == "synthetic_acceptance":
        method = "synthetic_acceptance"
        params = f"length{args.synthetic_acceptance_length:g}".replace(".", "p")
    else:
        method = args.lossy_method
        params = f"alpha{args.alpha:g}".replace(".", "p").replace("-", "neg")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    for value, label in ((method, "method"), (params, "params")):
        if not value or any(ch not in allowed for ch in value):
            raise ValueError(f"Unsafe {label}: {value!r}")
    return method, params


def validate_args(args: argparse.Namespace) -> None:
    if args.temperature <= 0:
        raise ValueError(
            "temperature must be > 0: at temperature 0 the verifier takes a greedy path and the "
            "probabilistic acceptance rule under test is not exercised"
        )
    if args.max_new_tokens < 1:
        raise ValueError("--max-new-tokens must be positive")

    if args.mode == "lossy":
        if args.lossy_method is None:
            raise ValueError(f"lossy mode requires --lossy-method {{{','.join(METHODS)},synthetic_acceptance}}")
        if args.lossy_method == "synthetic_acceptance":
            if args.synthetic_acceptance_length is None:
                raise ValueError("--lossy-method synthetic_acceptance requires --synthetic-acceptance-length")
            if args.alpha is not None:
                raise ValueError("--alpha is not used by --lossy-method synthetic_acceptance")
        else:
            if args.synthetic_acceptance_length is not None:
                raise ValueError(f"--synthetic-acceptance-length is not used by --lossy-method {args.lossy_method}")
            if args.alpha is None:
                raise ValueError(f"--lossy-method {args.lossy_method} requires --alpha")
            METHODS[args.lossy_method].validate_alpha(args.alpha)
    else:
        if args.alpha is not None:
            raise ValueError("--alpha is only valid with --mode lossy")
        if args.synthetic_acceptance_length is not None:
            raise ValueError("--synthetic-acceptance-length is only valid with --mode lossy")
        if args.lossy_method is not None:
            raise ValueError("--lossy-method is only valid with --mode lossy")


def alpha_matches(got: float, expected: float, tol: float = 1e-9) -> bool:
    """True iff got and expected are the same alpha. Handles +/-inf (several
    methods use -inf as their strict point) via exact equality -- inf-inf is
    nan, so a plain abs-difference check would wrongly reject a correct
    -inf-vs--inf match."""
    if got == expected:
        return True  # exact match; also correctly handles +inf==+inf, -inf==-inf
    if got != got or expected != expected:  # either is nan
        return False
    return abs(got - expected) <= tol


def acceptance_rule_record(args: argparse.Namespace) -> dict[str, Any]:
    """Everything needed to identify the acceptance rule from the artifact alone.

    Also fails the run when the alpha the server loaded disagrees with the
    one requested for the ACTIVE method -- including the strict arm, which
    must be running with every method's knob at its own strict value. An arm
    mislabelled here is invisible afterwards: that is how a 'strict' run
    directory in the sibling repo ended up holding lossy output once already.
    """
    record: dict[str, Any] = {
        "mode": args.mode,
        "lossy_method": args.lossy_method,
        "lossy_parameters": {},
    }

    if args.mode == "lossy" and args.lossy_method != "synthetic_acceptance":
        method = args.lossy_method
        spec = METHODS[method]
        alpha = args.alpha
        record["lossy_parameters"] = {"alpha": alpha}
        record["acceptance_rule"] = spec.acceptance_rule(alpha)
        record["taxonomy"] = spec.taxonomy

        in_force = alpha_in_force(method)
        record[f"{method}_alpha_in_force"] = in_force
        announced = server_log_alpha(method, args.server_log)
        if announced is not None:
            record[f"{method}_alpha_announced_by_server"] = announced

        got = in_force["value"]
        if got is None:
            raise ValueError(
                f"expected {method} alpha {alpha:g} but {spec.alpha_file} is unreadable "
                f"({in_force.get('error')}). Start the server with remote/run_server_vllm.sh, "
                "which writes it for every mode."
            )
        if not alpha_matches(got, alpha):
            raise ValueError(
                f"server loaded {method} alpha {got:g}, run was invoked for {alpha:g}. "
                "Refusing to write a mislabelled run directory."
            )
        if announced is not None and announced.get("distinct_alphas"):
            if any(not alpha_matches(a, alpha) for a in announced["distinct_alphas"]):
                raise ValueError(
                    f"server log {args.server_log} announces {method} alpha(s) "
                    f"{announced['distinct_alphas']}, run was invoked for {alpha:g}"
                )
    elif args.mode == "lossy":
        record["lossy_parameters"] = {"synthetic_acceptance_length": args.synthetic_acceptance_length}
        record["acceptance_rule"] = (
            f"synthetic: accept at a prescribed rate for mean length "
            f"{args.synthetic_acceptance_length:g}, ignoring p and q"
        )
    else:
        record["acceptance_rule"] = "accept iff p(x) / q(x) >= u"

    # Every OTHER method's knob must sit at ITS OWN strict value regardless of
    # which arm is active -- remote/run_server_vllm.sh writes all five for
    # every mode for exactly this reason. Checked here, not just trusted,
    # because a leftover value from an earlier run silently turning a
    # "strict" run into a partially-relaxed one is invisible without this.
    active = args.lossy_method if (args.mode == "lossy" and args.lossy_method != "synthetic_acceptance") else None
    for name, spec in METHODS.items():
        if name == active:
            continue
        other = alpha_in_force(name)
        record.setdefault("other_methods_neutral", {})[name] = other
        got = other["value"]
        if got is not None and not alpha_matches(got, spec.strict_alpha):
            raise ValueError(
                f"{name}'s knob is {got:g}, not its strict value {spec.strict_alpha:g}, while "
                f"running mode={args.mode} lossy_method={args.lossy_method}. A stale value from an "
                f"earlier lossy run may have leaked into this one -- refusing to write a run "
                f"directory that could be silently mislabelled."
            )
    return record


def run_one(
    args: argparse.Namespace,
    case: str,
    seed: int,
    tag: str,
    method: str,
    params: str,
    info: dict[str, Any],
    provenance: dict[str, Any],
    ordinal: int,
) -> dict[str, Any]:
    case_dir = args.prompt_root / case
    prompt_path = case_dir / "rendered_prompt.txt"
    metadata_path = case_dir / "metadata.json"
    if not prompt_path.is_file() or not metadata_path.is_file():
        raise FileNotFoundError(f"Incomplete prompt case: {case_dir}")

    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    # runs_root/<method>/<params>/<case>/seed_<N>/ -- not runs_root/<case>/
    # seed_<N>/<tag>/ (the old, now-abandoned flat layout: too many
    # scattered campaign directories and a single "tag" string that could
    # under-specify a method's real config, e.g. hsr-guard's own budget/
    # percentile knobs weren't in its tag, so two genuinely different
    # configs collided under one directory name). The prompt itself is
    # NOT copied into the run directory -- prompts/<bench>/<case>/
    # rendered_prompt.txt is already the canonical, single copy.
    output_dir = args.runs_root / method / params / case / f"seed_{seed}"
    if output_dir.exists() and not args.overwrite:
        raise FileExistsError(f"Refusing to overwrite {output_dir}; pass --overwrite to replace files")
    output_dir.mkdir(parents=True, exist_ok=True)

    request_payload = {
        "model": args.model,
        "prompt": prompt,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_new_tokens,
        "seed": seed,
        "repetition_penalty": 1.0,
        # The archived prompts are already rendered Harmony text carrying their own
        # special tokens; letting the tokenizer add more would change the input.
        "add_special_tokens": False,
        "skip_special_tokens": False,
        "spaces_between_special_tokens": False,
        "stream": False,
    }

    config = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "backend": "vllm",
        "tag": tag,
        **provenance["acceptance"],
        "model": args.model,
        "draft_model": None if args.mode == "baseline" else args.draft_model,
        "seed": seed,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_new_tokens": args.max_new_tokens,
        "input_tokens_archived": prompt_metadata.get("input_tokens"),
        "prompt_case": case,
        "prompt_source_id": prompt_metadata.get("source_id"),
        "reference_answer": prompt_metadata.get("reference_answer"),
        "endpoint": f"{args.server_url.rstrip('/')}/v1/completions",
        # Request position on this engine. Output depends on it, so a
        # comparison is only clean between runs that share it; the
        # fresh-server driver pins it to 1 on every arm.
        "server_request_ordinal": ordinal,
        "fresh_server_asserted": args.assert_fresh_server,
        "engine_totals_before_first_request": provenance["engine_totals_at_start"],
        "vllm": provenance["vllm"],
        "git_commit": provenance["git_commit"],
        "git_dirty": provenance["git_dirty"],
        "command": provenance["command"],
    }
    write_json(output_dir / "config.json", config)
    write_json(output_dir / "request.json", request_payload)
    write_json(output_dir / "server_info.json", info)
    # No prompt.txt: prompts/<bench>/<case>/rendered_prompt.txt (read above)
    # is already the single canonical copy; request.json's own "prompt"
    # field carries the exact text actually sent, for anyone who needs it
    # inline without cross-referencing the prompt root.

    counters_before = spec_counters(args.server_url)
    started = time.perf_counter()
    try:
        response = http_json(
            f"{args.server_url.rstrip('/')}/v1/completions",
            payload=request_payload,
            timeout=args.timeout,
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        elapsed = time.perf_counter() - started
        write_json(
            output_dir / "run.json",
            {"status": "error", "error": f"{type(exc).__name__}: {exc}", "wall_time_seconds": elapsed},
        )
        raise
    elapsed = time.perf_counter() - started
    spec = acceptance_stats(counters_before, spec_counters(args.server_url))

    write_json(output_dir / "response.json", response)
    choices = response.get("choices") or [{}]
    choice = choices[0] if isinstance(choices[0], dict) else {}
    output_text = choice.get("text", "")
    usage = response.get("usage") or {}
    finish_reason = choice.get("finish_reason")
    (output_dir / "output.txt").write_text(str(output_text), encoding="utf-8")

    run_record = {
        "status": "ok",
        "backend": "vllm",
        "wall_time_seconds": elapsed,
        "server_request_ordinal": ordinal,
        "input_tokens": usage.get("prompt_tokens", prompt_metadata.get("input_tokens")),
        "output_tokens": usage.get("completion_tokens"),
        "finish_reason": finish_reason,
        "eos_reached": finish_reason == "stop",
        "reached_max_new_tokens": finish_reason == "length",
        "usage": usage,
        # Harmony channels: a degenerate loop lives in `analysis` and never
        # reaches `final`, so length has to be attributed per channel or a
        # truncated run reads as rambling.
        "analysis_chars": len(str(output_text).split("<|channel|>final")[0]),
        "final_chars": (
            len(str(output_text).split("<|channel|>final<|message|>")[-1])
            if "<|channel|>final" in str(output_text)
            else 0
        ),
        "reached_final_channel": "<|channel|>final" in str(output_text),
        **spec,
    }
    L = run_record["output_tokens"]
    l_bar = run_record.get("l_bar")
    run_record["L_over_l_bar"] = (L / l_bar) if (L and l_bar) else None
    write_json(output_dir / "run.json", run_record)
    print(
        f"{case} seed={seed} mode={tag}: L={L} finish={finish_reason} "
        f"l_bar={l_bar if l_bar is None else round(l_bar, 3)} "
        f"L/l_bar={run_record['L_over_l_bar'] if run_record['L_over_l_bar'] is None else round(run_record['L_over_l_bar'], 1)} "
        f"final_ch={run_record['reached_final_channel']} wall={elapsed:.2f}s",
        flush=True,
    )
    return run_record


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        tag = safe_tag(args)
        method, params = safe_method_and_params(args)
        cases = args.cases or selected_cases(args.prompt_root)
        unknown = [case for case in cases if not (args.prompt_root / case).is_dir()]
        if unknown:
            raise ValueError(f"Unknown cases under {args.prompt_root}: {', '.join(unknown)}")
        acceptance = acceptance_rule_record(args)
        totals = engine_totals(args.server_url)
        if args.assert_fresh_server:
            if not totals:
                raise ValueError(
                    f"cannot verify a fresh server: no usable counters at {args.server_url}/metrics"
                )
            used = {name: value for name, value in totals.items() if value > 0}
            if used:
                raise ValueError(
                    f"server has already served requests ({used}); --assert-fresh-server "
                    "requires an engine that has done no work yet"
                )
            if len(cases) * len(args.seeds) > 1:
                raise ValueError(
                    "--assert-fresh-server takes exactly one case and one seed: the guarantee "
                    "is one request per engine, and only the first request is at ordinal 1"
                )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    provenance = {
        "acceptance": acceptance,
        "engine_totals_at_start": totals or None,
        "vllm": vllm_install_info(),
        "git_commit": git_commit(),
        "git_dirty": git_dirty(),
        "command": sys.argv,
    }
    if args.mode == "lossy" and args.lossy_method != "synthetic_acceptance":
        if not provenance["vllm"]["patch_applied"].get(args.lossy_method):
            print(
                f"configuration error: the {args.lossy_method} patch is not applied to "
                f"{provenance['vllm'].get('site_packages')}; run "
                f"bash patches/apply.sh {args.lossy_method.replace('_', '-')}",
                file=sys.stderr,
            )
            return 2
    elif args.mode != "lossy" and provenance["vllm"].get("v1_label") is None:
        # Strict/baseline mode does NOT require pristine vLLM: every patch's
        # kernel is bit-identical to pristine's at its own strict alpha (see
        # STRICT_TRACE_CARRIER in scripts/lossy_methods.py), and running
        # strict through a patch is how a trace gets captured at all --
        # pristine vLLM has no tracer hook. What's actually required is that
        # SOME known state is installed (pristine, or any of the five
        # patches) and every method's own knob sits at its own strict value
        # -- the latter is checked unconditionally in acceptance_rule_record
        # above (other_methods_neutral), not just here. An UNKNOWN hash
        # (v1_label is None) means neither pristine nor any recorded patch,
        # which this refuses rather than guessing what's actually running.
        print(
            f"configuration error: {provenance['vllm'].get('site_packages')}'s rejection_sampler.py "
            f"matches no known state (sha256 {provenance['vllm'].get('v1_sha256')}) -- neither pristine "
            "nor any patch in patches/HASHES.txt. Reinstall vLLM 0.26.0 fresh or re-apply a patch.",
            file=sys.stderr,
        )
        return 2

    info = server_info(args.server_url)
    failures = 0
    ordinal = 0
    for case in cases:
        for seed in args.seeds:
            ordinal += 1
            try:
                run_one(args, case, seed, tag, method, params, info, provenance, ordinal)
            except Exception as exc:
                failures += 1
                print(f"{case} seed={seed} failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
