#!/usr/bin/env python3
"""Fill the two missing rules of the addendum's step-4.3 pair (Qwen3-8B + Qwen3-0.6B draft model) on GSM8K and
LiveCodeBench (Bill, 2026-10-06: the paper's Qwen3-0.6B column had no spec_casc_opt / r_fuzzy cells there).
spec_casc_opt 0.05 and r_fuzzy 0.25 (each rule's loosest grid alpha, as the other three cells: mentored_dec 0.75,
cactus 0.35, spec_casc_tok 0.8) with the addendum's own item definition (addendum_campaign.make_row / work_item,
condition lmdraft), into runs/addendum/lmdraft, paired by addendum_tables.py lmdraft with the same step-4.3 lossless
reference as the cells beside them. Two Killarney lanes (K1 GSM8K, K2 LiveCodeBench) with their own lane roots.

  python3 scripts/step9_lmdraft_fill.py submit | collect | grade
"""
import argparse
import io
import json
import pathlib
import shlex
import sys
import tarfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import addendum_campaign as ac  # noqa: E402
import step9_campaign as s9  # noqa: E402

ARMS = [("spec_casc_opt", "0.05"), ("r_fuzzy", "0.25")]
PLAN = {"K1": "gsm8k_qwen3", "K2": "livecodebench_qwen3"}
ROOT = "/scratch/billxby/step9/lmfill_{lane}"
MIRROR = "/scratch/billxby/step9/lmfill_mirror"
GRADES = s9.S9 / "grades_lmdraft.csv"


def items(lane: str) -> list[dict]:
    ds = PLAN[lane]
    out = []
    for method, alpha in ARMS:
        row = ac.make_row("4.3", "lmdraft", ds, method, alpha, 0)
        item = ac.work_item(row, [f"case_{i:03d}" for i in range(1, ac.N_CASES[ac.base_of(ds)] + 1)])
        item["env"] = {**item.get("env", {}), "FLASHINFER_WORKSPACE_BASE": f"/scratch/billxby/step9/flashinfer/{lane}"}
        item["extra_flags"] = ["--startup-timeout", "1200"]
        out.append(item)
    return out


def cmd_submit(args) -> int:
    for lane in PLAN:
        info, root = s9.LANES[lane], ROOT.format(lane=lane)
        work = json.dumps({"items": items(lane), "hold_minutes": 0}, indent=1).encode()
        ac.ssh(f"mkdir -p {root}/slurm && cat > {root}/work.json", input_bytes=work, host="killarney")
        cmd = (f"cd {shlex.quote(info['repo'])} && LANE=fill-{lane} REPO_DIR={shlex.quote(info['repo'])} LANE_ROOT={root} "
               f"PROJECT_DIR={info['project']} sbatch --parsable --job-name=s9-fill-{lane} --account={info['account']} "
               f"--time=3:00:00 --output={root}/slurm/%x-%j.out cascade/cluster/addendum_lane.sbatch")
        job = ac.ssh(f"bash -lc {shlex.quote(cmd)}", host="killarney").stdout.decode().strip().splitlines()[-1]
        print(f"{lane} {PLAN[lane]}: job {job}")
        ac.progress(f"step 9 lmdraft fill: {PLAN[lane]} spec_casc_opt 0.05 / r_fuzzy 0.25, Killarney job {job}")
    return 0


def cmd_collect(args) -> int:
    ac.LANES_DIR = s9.LANES_DIR
    for lane in PLAN:
        got = ac.pull_lane_runs(f"fill{lane}", {"host": "killarney", "root": ROOT.format(lane=lane)})
        print(f"{lane}: pulled {len(got)} run dir(s)")
    return 0


def cmd_grade(args) -> int:
    """Upload the filled runs to a Nibi mirror and grade them with the campaign's graders (addendum_grade.py)."""
    rels = sorted(str(p.parent.relative_to(REPO / "runs")) for m, a in ARMS for ds in PLAN.values()
                  for p in (REPO / "runs" / "addendum" / "lmdraft" / ds / m).glob("*/case_*/seed_0/run.json"))
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for rel in rels:
            for name in ("run.json", "config.json", "output.txt"):
                path = REPO / "runs" / rel / name
                if path.is_file():
                    tar.add(path, arcname=f"{rel}/{name}")
    ac.ssh(f"mkdir -p {MIRROR}/runs && cd {MIRROR}/runs && tar -xf -", input_bytes=buf.getvalue(), timeout=1800)
    repo = s9.GRADE_REPO
    cmd = (f"cd {repo} && module load StdEnv/2023 python/3.12 && unset PYTHONPATH && python3 scripts/addendum_grade.py "
           f"--runs-root {MIRROR}/runs --out {MIRROR}/grades.csv --workers 8")
    out = ac.ssh(f"bash -lc {shlex.quote(cmd)}", timeout=3600)
    print(out.stdout.decode()[-300:])
    GRADES.write_bytes(ac.ssh(f"cat {MIRROR}/grades.csv").stdout)
    print(f"{len(rels)} runs, grades -> {GRADES.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["submit", "collect", "grade"])
    a = p.parse_args()
    raise SystemExit({"submit": cmd_submit, "collect": cmd_collect, "grade": cmd_grade}[a.cmd](a))
