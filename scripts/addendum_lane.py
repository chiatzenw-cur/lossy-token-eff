#!/usr/bin/env python3
"""One addendum lane inside one Slurm job (campaign/addendum/README.md).

A lane is one H100, one repo copy with its own .venv-vllm (the patches are
mutually exclusive on one installed file, so two concurrent jobs must never
share a venv), and one run root under $SCRATCH that only this lane writes to.
The Mac-side orchestrator (scripts/addendum_campaign.py) writes the lane's
ordered work list to <lane-root>/work.json; this driver runs it:

  loop:
    re-read work.json (the orchestrator may append items while a job runs)
    first item with missing cases in this lane's run root -> run it through
    scripts/persistent_arm_replay.py (one server per arm+seed, reused across
    that arm's cases, --no-trace-proposals), then look again

Rules this enforces (campaign/addendum/README.md "Ground rules"):
  * never --overwrite; a case counts as done when its run.json says "ok"
  * a seed_N/ directory with no run.json (job killed mid-request) or a
    non-ok run.json is MOVED to <lane-root>/quarantine/<stamp>/..., never
    deleted, before its case is retried
  * 2 GB free-disk floor checked before every arm
  * at most two attempts per item per job, so one deterministic failure
    cannot spin a whole 12 h allocation
  * <lane-root>/STOP makes the driver exit before its next item

Every attempt is journaled to <lane-root>/status.jsonl (start/end, job id,
cases missing before and ok after, exit code, elapsed seconds); the
orchestrator reads that for gpu_hours_actual and slurm_job_ids.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MIN_FREE_GB = 2
MAX_ATTEMPTS_PER_JOB = 2
ENV_WAIT_S = 30  # how long a job waits for the CVMFS software stack after a node reboot (see Lane.env_ready)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def params_dir(method: str, alpha: str) -> str:
    """Must match fresh_server_replay.method_and_params_for()."""
    if method in ("strict", "baseline"):
        return method
    return f"alpha{float(alpha):g}".replace("-", "neg")


def item_run_dir(lane_root: pathlib.Path, item: dict, case: str) -> pathlib.Path:
    return (
        lane_root / item["runs_subroot"] / item["dataset"] / item["method"]
        / params_dir(item["method"], item["alpha"]) / case / f"seed_{item['seed']}"
    )


def run_state(run_dir: pathlib.Path) -> str:
    """ok | missing | partial (dir without run.json) | error (run.json not ok)."""
    run_json = run_dir / "run.json"
    if not run_json.is_file():
        return "partial" if run_dir.exists() else "missing"
    try:
        status = json.loads(run_json.read_text(encoding="utf-8")).get("status")
    except (OSError, json.JSONDecodeError):
        status = None
    return "ok" if status == "ok" else "error"


class Lane:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.root: pathlib.Path = args.lane_root
        self.root.mkdir(parents=True, exist_ok=True)
        self.status_path = self.root / "status.jsonl"
        self.job = os.environ.get("SLURM_JOB_ID", "nojob")
        self.host = os.uname().nodename

    def journal(self, **record) -> None:
        record = {"t": utc_now(), "lane": self.args.lane, "job": self.job, "host": self.host, **record}
        with self.status_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        print(json.dumps(record), flush=True)

    def load_work(self) -> list[dict]:
        for _ in range(5):
            try:
                return json.loads(self.args.work.read_text(encoding="utf-8"))["items"]
            except (OSError, json.JSONDecodeError, KeyError) as exc:
                last = exc
                time.sleep(3)  # the orchestrator replaces work.json atomically; retry a torn read anyway
        self.journal(event="work_unreadable", error=f"{type(last).__name__}: {last}")
        return []

    def hold_minutes(self) -> float:
        """work.json's hold_minutes: how long to wait for new items once the list is exhausted."""
        try:
            return float(json.loads(self.args.work.read_text(encoding="utf-8")).get("hold_minutes") or 0)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return 0.0

    def missing_cases(self, item: dict, quarantine: bool) -> list[str]:
        missing = []
        for case in item["cases"]:
            run_dir = item_run_dir(self.root, item, case)
            state = run_state(run_dir)
            if state == "ok":
                continue
            if state in ("partial", "error") and quarantine:
                stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                dest = self.root / "quarantine" / f"{stamp}_{self.job}" / run_dir.relative_to(self.root)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(run_dir), str(dest))
                self.journal(event="quarantined", item=item["id"], case=case, state=state, to=str(dest))
            missing.append(case)
        return missing

    def disk_ok(self, item: dict) -> bool:
        for path in (self.root, REPO_ROOT):
            free_gb = shutil.disk_usage(path).free / 1024**3
            if free_gb < MIN_FREE_GB:
                self.journal(event="disk_floor", item=item["id"], path=str(path), free_gb=round(free_gb, 2))
                return False
        return True

    def command(self, item: dict, cases: list[str]) -> list[str]:
        runs_root = self.root / item["runs_subroot"]
        log_root = self.root / "logs" / item["runs_subroot"] / item["dataset"]
        cmd = [
            self.args.python, str(REPO_ROOT / "scripts" / "persistent_arm_replay.py"),
            "--arms", item["method"],
            "--cases", *cases,
            "--seeds", str(item["seed"]),
            "--prompt-root", item["prompt_root"],
            "--runs-root", str(runs_root),
            "--log-root", str(log_root),
            "--max-new-tokens", str(item["max_new_tokens"]),
            "--num-spec", str(item["num_spec"]),
            "--temperature", str(item["temperature"]),
            "--top-p", str(item["top_p"]),
            "--server-seed", str(item.get("server_seed", 0)),
            "--port", str(self.args.port),
            "--no-trace-proposals",
            *item.get("model_flags", []),
            *item.get("extra_flags", []),
        ]
        if item["method"] not in ("strict", "baseline"):
            cmd += [f"--{item['method'].replace('_', '-')}-alpha", str(item["alpha"])]
        return cmd

    def env_ready(self) -> bool:
        """Right after a node reboot /cvmfs may not be mounted yet when a job starts: `module load` then fails
        without stopping the batch script, this driver comes up on the system python, and the venv python -- a
        link into /cvmfs -- cannot be executed (ELOOP; job 5839004 on kn172, 2026-10-01). The job's private mount
        namespace (job_container/tmpfs) keeps that state for the job's life -- K1/K2's first jobs on kn169 saw
        ELOOP for 300 s while the next jobs, 2 s later, ran -- but the attempt mounts /cvmfs on the node. So wait
        only briefly, and if the modules did not load (no EBROOTCUDA) stop rather than run vLLM in a partial
        environment: the next job in the chain starts in a new namespace."""
        deadline = time.time() + ENV_WAIT_S
        while True:
            try:
                ok = subprocess.run([self.args.python, "-c", "pass"], check=False).returncode == 0
                error = "" if ok else "venv python exited nonzero"
            except OSError as exc:
                ok, error = False, str(exc)
            if ok:
                break
            if time.time() > deadline:
                self.journal(event="env_not_ready", reason=f"venv python not runnable after {ENV_WAIT_S} s: {error}")
                return False
            time.sleep(10)
        if not os.environ.get("EBROOTCUDA"):
            self.journal(event="env_not_ready", reason="module load did not take effect (no EBROOTCUDA)",
                         python=sys.executable)
            return False
        return True

    def run(self) -> int:
        self.journal(event="job_start", work=str(self.args.work))
        if not self.env_ready():
            self.journal(event="job_end", failures=1)
            return 1
        attempts: dict[str, int] = {}
        failures = 0
        idle_since = None
        while True:
            if (self.root / "STOP").exists():
                self.journal(event="stop_file")
                break
            target = None
            for item in self.load_work():
                if attempts.get(item["id"], 0) >= MAX_ATTEMPTS_PER_JOB:
                    continue
                if self.missing_cases(item, quarantine=False):
                    target = item
                    break
            if target is None:
                # the orchestrator may be about to queue the next phase (step 7): keep the GPU a while
                hold = self.hold_minutes()
                if hold > 0 and (idle_since is None or time.time() - idle_since < hold * 60):
                    if idle_since is None:
                        idle_since = time.time()
                        self.journal(event="idle_hold", minutes=hold)
                    time.sleep(60)
                    continue
                break
            if idle_since is not None:
                self.journal(event="idle_end", waited_s=round(time.time() - idle_since, 1))
                idle_since = None
            missing = self.missing_cases(target, quarantine=True)
            if not self.disk_ok(target):
                failures += 1
                break
            attempts[target["id"]] = attempts.get(target["id"], 0) + 1
            cmd = self.command(target, missing)
            env = dict(os.environ)
            env.update({k: str(v) for k, v in target.get("env", {}).items()})
            self.journal(event="item_start", item=target["id"], attempt=attempts[target["id"]],
                         missing=len(missing), of=len(target["cases"]), command=cmd)
            started = time.time()
            rc = subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=False).returncode
            elapsed = time.time() - started
            still_missing = self.missing_cases(target, quarantine=False)
            self.journal(event="item_end", item=target["id"], rc=rc, elapsed_s=round(elapsed, 1),
                         missing_before=len(missing), missing_after=len(still_missing), of=len(target["cases"]))
            if rc != 0:
                failures += 1
        self.journal(event="job_end", failures=failures)
        return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--lane-root", type=pathlib.Path, required=True)
    parser.add_argument("--work", type=pathlib.Path, default=None, help="Defaults to <lane-root>/work.json.")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--python", default=str(REPO_ROOT / ".venv-vllm" / "bin" / "python"))
    args = parser.parse_args()
    args.work = args.work or (args.lane_root / "work.json")
    return Lane(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
