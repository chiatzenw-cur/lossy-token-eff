#!/usr/bin/env python3
"""FROZEN evaluator for the autoguard autoresearch loop.

This file is the equivalent of Karpathy's autoresearch `prepare.py`: it is
NOT edited by the loop. It installs the current `patches/autoguard.py`,
runs the fixed evaluation set through the frozen fresh-server replay
harness, grades it, and emits a single scalar score plus a metrics record.

The ONLY thing the loop edits is `patches/autoguard.py::decide()`.

Objective (lower is better):
    score = mean completion length (output tokens) over the eval set,
            for the spec_casc_tok_autoguard arm.

Hard constraint (an eval that violates it is a FAILURE, not a candidate):
    accuracy >= baseline_accuracy - ACC_TOLERANCE_CASES / n_cases

Other failure conditions (mirroring autoresearch's ">10 min = failure"):
    * `patches/autoguard.py` fails `apply.sh spec-casc-tok-autoguard`
      (syntax error, broken import, failing plumbing test)
    * any eval run errors
    * total eval wall time exceeds --max-eval-seconds

Run:
    .venv-vllm/bin/python autoresearch/evaluate.py            # score the current autoguard.py
    .venv-vllm/bin/python autoresearch/evaluate.py --baseline # (re)collect the spec_casc_tok baseline
    .venv-vllm/bin/python autoresearch/evaluate.py --dry-run  # print the plan, run nothing
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import shutil
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from grade_aime import grade  # noqa: E402  (frozen grader, authoritative)
from fresh_server_replay import ensure_patch_applied  # noqa: E402  (frozen; auto-switches patches, runs apply.sh + the plumbing test)

# ---- frozen configuration ---------------------------------------------------
PROMPT_ROOT = REPO / "prompts" / "aime24"
RUNS_ROOT = REPO / "autoresearch" / "runs"          # separate from the campaign's runs/
LOG_ROOT = REPO / "autoresearch" / "logs"
METRICS_PATH = REPO / "autoresearch" / "metrics.json"
EVAL_CASES = [f"case_{i:03d}" for i in range(1, 9)]  # first 8 AIME24 cases
MAX_NEW_TOKENS = 32768
ALPHA = 0.3                                          # spec_casc_tok's own alpha, fixed
BASELINE_ARM = "spec_casc_tok"
GUARD_ARM = "spec_casc_tok_autoguard"
ACC_TOLERANCE_CASES = 1                              # guard may lose at most this many cases vs baseline
PY = str(REPO / ".venv-vllm" / "bin" / "python")

# model-runner patches that add per-round overhead / their own knob effects;
# reversed to pristine before an autoguard eval so the measurement is clean.
STATEFUL_MODEL_RUNNER_LABELS = {
    "hsr-guard-model-runner", "jn-model-runner",
    "rv-model-runner", "free-judgment-model-runner",
}


@dataclasses.dataclass
class ArmResult:
    arm: str
    n: int
    n_ok: int
    n_correct: int
    n_no_answer: int
    n_hit_cap: int
    mean_completion_tokens: float
    mean_l_bar: float
    per_case: list[dict]

    @property
    def accuracy(self) -> float:
        return self.n_correct / self.n if self.n else 0.0


def _venv_pkg() -> pathlib.Path:
    out = subprocess.run(
        [PY, "-c", "import pathlib, vllm; print(pathlib.Path(vllm.__file__).parent)"],
        capture_output=True, text=True, check=True,
    )
    return pathlib.Path(out.stdout.strip())


def _hash(path: pathlib.Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""


def _hashes_manifest() -> dict[str, str]:
    manifest: dict[str, str] = {}
    for line in (REPO / "patches" / "HASHES.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        h, _, label = line.partition("  ")
        if label:
            manifest[h] = label.strip()
    return manifest


def ensure_clean_model_runner() -> str | None:
    """Reverse a stateful *-model-runner patch to pristine if one is live.
    Returns the label reversed, or None."""
    pkg = _venv_pkg()
    gmr = pkg / "v1" / "worker" / "gpu_model_runner.py"
    label = _hashes_manifest().get(_hash(gmr))
    if label in STATEFUL_MODEL_RUNNER_LABELS:
        patch = REPO / "patches" / f"vllm-0.26.0-{label}.patch"
        r = subprocess.run(
            ["patch", "-p1", "-R", "-d", str(pkg.parent)],
            input=patch.read_text(), capture_output=True, text=True,
        )
        if r.returncode != 0:
            raise SystemExit(f"could not reverse {label} to pristine:\n{r.stdout}\n{r.stderr}")
        return label
    return None


def install_autoguard() -> None:
    """Copy the current patches/autoguard.py into the venv and ensure the
    spec-casc-tok-autoguard patch is the live one (auto-switching from
    whatever else is installed). ensure_patch_applied runs apply.sh, which
    re-copies autoguard.py and runs the plumbing test. Raises on failure."""
    src = REPO / "patches" / "autoguard.py"
    if not src.is_file():
        raise SystemExit("patches/autoguard.py is missing")
    shutil.copyfile(src, _venv_pkg() / "v1" / "sample" / "autoguard.py")
    try:
        ensure_patch_applied("spec_casc_tok_autoguard")
    except RuntimeError as exc:
        raise SystemExit(
            "patches/autoguard.py does not pass `apply.sh spec-casc-tok-autoguard` "
            f"(syntax error, bad import, or failing plumbing test):\n{exc}"
        )


def replay(arm: str, cases: list[str], timeout: float | None) -> None:
    cmd = [
        PY, str(REPO / "scripts" / "fresh_server_replay.py"),
        "--arms", arm,
        "--cases", *cases,
        "--prompt-root", str(PROMPT_ROOT),
        "--runs-root", str(RUNS_ROOT),
        "--log-root", str(LOG_ROOT),
        "--max-new-tokens", str(MAX_NEW_TOKENS),
    ]
    if arm == GUARD_ARM:
        cmd += ["--spec-casc-tok-autoguard-alpha", str(ALPHA)]
    elif arm == BASELINE_ARM:
        cmd += ["--spec-casc-tok-alpha", str(ALPHA)]
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO, check=False, timeout=timeout)


def collect(arm: str, cases: list[str]) -> ArmResult:
    method_dir = RUNS_ROOT / "aime24" / arm
    per_case: list[dict] = []
    for case in cases:
        hits = sorted(method_dir.glob(f"*/{case}/seed_*"))
        row = grade(hits[-1], PROMPT_ROOT) if hits else None
        per_case.append({"case": case, **(row or {"verdict": "missing", "output_tokens": None})})
    graded = [r for r in per_case if r["verdict"] != "missing"]
    toks = [r["output_tokens"] for r in graded if r.get("output_tokens") is not None]
    lbars = [r["l_bar"] for r in graded if r.get("l_bar") is not None]
    return ArmResult(
        arm=arm,
        n=len(cases),
        n_ok=len(graded),
        n_correct=sum(r["verdict"] == "correct" for r in graded),
        n_no_answer=sum(r["verdict"] == "no_answer" for r in graded),
        n_hit_cap=sum(bool(r.get("hit_cap")) for r in graded),
        mean_completion_tokens=sum(toks) / len(toks) if toks else float("nan"),
        mean_l_bar=sum(lbars) / len(lbars) if lbars else float("nan"),
        per_case=per_case,
    )


def guard_fire_rate(cases: list[str]) -> dict:
    """Best-effort: fraction of drafted tokens the guard forced strict on,
    read from proposals.jsonl (field token_marker_guard_active)."""
    method_dir = RUNS_ROOT / "aime24" / GUARD_ARM
    active = total = 0
    for case in cases:
        for trace in method_dir.glob(f"*/{case}/seed_*/proposals.jsonl"):
            for line in trace.read_text().splitlines():
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if "token_marker_guard_active" not in rec:
                    continue
                total += 1
                if rec["token_marker_guard_active"]:
                    active += 1
    return {"guarded_tokens": active, "traced_tokens": total,
            "guard_fire_rate": (active / total) if total else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", action="store_true", help=f"(re)collect the {BASELINE_ARM} baseline, then exit")
    ap.add_argument("--cases", nargs="+", default=EVAL_CASES)
    ap.add_argument("--max-eval-seconds", type=float, default=3600.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print(f"eval set : {', '.join(args.cases)}  ({len(args.cases)} AIME24 cases)")
        print(f"arm      : {GUARD_ARM}  vs baseline {BASELINE_ARM}  (alpha={ALPHA}, max_new_tokens={MAX_NEW_TOKENS})")
        print(f"runs     : {RUNS_ROOT}/aime24/<arm>/...")
        print(f"objective: minimise mean completion tokens; accuracy floor = baseline - {ACC_TOLERANCE_CASES}/{len(args.cases)}")
        print(f"budget   : {args.max_eval_seconds:.0f}s wall for the guard arm")
        return 0

    reversed_label = ensure_clean_model_runner()
    if reversed_label:
        print(f"note: reversed stale {reversed_label} to pristine for a clean measurement")

    if args.baseline:
        replay(BASELINE_ARM, args.cases, timeout=None)
        base = collect(BASELINE_ARM, args.cases)
        (REPO / "autoresearch" / "baseline.json").write_text(json.dumps(dataclasses.asdict(base), indent=2) + "\n")
        print(f"baseline: {base.n_correct}/{base.n} correct, mean completion {base.mean_completion_tokens:.0f} tokens")
        return 0

    baseline_path = REPO / "autoresearch" / "baseline.json"
    if not baseline_path.is_file():
        raise SystemExit("no autoresearch/baseline.json -- run `evaluate.py --baseline` once first")
    base = ArmResult(**{k: v for k, v in json.loads(baseline_path.read_text()).items()})

    failure: str | None = None
    t0 = time.time()
    try:
        install_autoguard()
    except SystemExit as exc:
        failure = str(exc)

    guard: ArmResult | None = None
    if failure is None:
        # The guard arm is rewritten every iteration -- clear its prior run
        # dirs so fresh_server_replay's skip-if-done does not keep stale
        # results. The baseline arm is left cached.
        shutil.rmtree(RUNS_ROOT / "aime24" / GUARD_ARM, ignore_errors=True)
        try:
            replay(GUARD_ARM, args.cases, timeout=args.max_eval_seconds)
        except subprocess.TimeoutExpired:
            failure = f"eval exceeded --max-eval-seconds ({args.max_eval_seconds:.0f}s)"
        guard = collect(GUARD_ARM, args.cases)
        if guard.n_ok < guard.n:
            failure = failure or f"{guard.n - guard.n_ok}/{guard.n} eval runs did not produce a graded result"
        acc_floor = base.accuracy - ACC_TOLERANCE_CASES / guard.n
        if guard.accuracy < acc_floor - 1e-9:
            failure = failure or (
                f"accuracy {guard.accuracy:.3f} below floor {acc_floor:.3f} "
                f"(baseline {base.accuracy:.3f} - {ACC_TOLERANCE_CASES}/{guard.n})"
            )

    elapsed = time.time() - t0
    score = guard.mean_completion_tokens if guard else float("inf")
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "score": score,                       # mean completion tokens, lower is better
        "failure": failure is not None,
        "failure_reason": failure,
        "improved_vs_baseline": bool(guard and not failure and score < base.mean_completion_tokens),
        "eval_wall_seconds": round(elapsed, 1),
        "objective": "min mean completion tokens s.t. accuracy >= baseline - "
                     f"{ACC_TOLERANCE_CASES}/{len(args.cases)}",
        "eval_cases": args.cases,
        "alpha": ALPHA,
        "baseline": dataclasses.asdict(base),
        "guard": dataclasses.asdict(guard) if guard else None,
        "delta_completion_tokens": (score - base.mean_completion_tokens) if guard else None,
        "delta_accuracy_cases": (guard.n_correct - base.n_correct) if guard else None,
        **(guard_fire_rate(args.cases) if guard else {}),
    }
    METRICS_PATH.write_text(json.dumps(record, indent=2) + "\n")

    tag = "FAILURE" if record["failure"] else ("IMPROVED" if record["improved_vs_baseline"] else "no improvement")
    print(f"\n[{tag}] score={score:.0f} tok  (baseline {base.mean_completion_tokens:.0f})  "
          f"acc {guard.accuracy:.3f} vs {base.accuracy:.3f}" if guard else f"\n[{tag}]")
    if failure:
        print(f"  reason: {failure}")
    print(f"  wrote {METRICS_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
