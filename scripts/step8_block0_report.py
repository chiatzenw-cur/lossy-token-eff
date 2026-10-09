#!/usr/bin/env python3
"""Step 8 Block 0 report data (campaign/addendum/step8/GOAL.md): reads the pulled Block 0 runs
(runs/addendum/step8_block0/) and the patch / q-probe lines of the server logs on Killarney, writes

  campaign/addendum/step8/block0/checks.csv        one row per check run: status, tokens, l_bar, finish, host
  campaign/addendum/step8/block0/strict_limit.csv  (f) each rule at its strict point vs lossless (must be identical)
                                                   and at its loosest grid alpha (must differ), per sampler path
  campaign/addendum/step8/block0/v2_ab.csv         V2 port check: old (68d0a904) vs new (796e3c85) file, same arms
  campaign/addendum/step8/block0/server_log_lines.txt  the [... PATCH ...] and [Q-PROBE V2] lines, per log file

  python3 scripts/step8_block0_report.py [--no-ssh]
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import subprocess

REPO = pathlib.Path(__file__).resolve().parent.parent
B0 = REPO / "runs" / "addendum" / "step8_block0"
OUT = REPO / "campaign" / "addendum" / "step8" / "block0"
FIVE = ["mentored_dec", "cactus", "spec_casc_opt", "r_fuzzy", "spec_casc_tok"]
STRICT_POINT = {"mentored_dec": "alpha0", "cactus": "alpha0", "spec_casc_opt": "alphaneginf", "r_fuzzy": "alphaneginf",
                "spec_casc_tok": "alphaneginf"}
LOOSEST = {"mentored_dec": "alpha0.75", "cactus": "alpha0.35", "spec_casc_opt": "alpha0.05", "r_fuzzy": "alpha0.25",
           "spec_casc_tok": "alpha0.8"}
STRICT_LIMIT_CHECKS = {"f2_v2_l31_eagle3_maxpos": "V2 (Llama-3.1-8B-Instruct + EAGLE-3, 65536-position head)",
                       "f_v1_l31_llama1b": "V1 (Llama-3.1-8B-Instruct + Llama-3.2-1B, draft_model)"}


def load(run_dir: pathlib.Path) -> dict | None:
    try:
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if run.get("status") != "ok":
        return None
    run["_text"] = (run_dir / "output.txt").read_text(encoding="utf-8") if (run_dir / "output.txt").is_file() else ""
    try:
        run["_host"] = json.loads((run_dir / "config.json").read_text(encoding="utf-8")).get("host", "")
    except (OSError, ValueError):
        run["_host"] = ""
    return run


def write(path: pathlib.Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {path.relative_to(REPO)} ({len(rows)} rows)")


def checks() -> None:
    rows = []
    for rj in sorted(B0.glob("*/*/*/*/case_*/seed_0/run.json")):
        check, ds, method, params, case = rj.parts[-7:-2]
        run = load(rj.parent)
        rows.append({"check": check, "dataset": ds, "method": method, "params": params, "case": case,
                     "status": "ok" if run else "not ok", "output_tokens": run and run.get("output_tokens"),
                     "finish": run and run.get("finish_reason"), "l_bar": run and round(run.get("l_bar") or 0, 3),
                     "host": run and run.get("_host")})
    write(OUT / "checks.csv", rows)


def strict_limit() -> None:
    rows = []
    for check, path in STRICT_LIMIT_CHECKS.items():
        base = B0 / check / "gsm8k_llama31"
        strict = load(base / "strict" / "strict" / "case_001" / "seed_0")
        for m in FIVE:
            for kind, params in (("strict point", STRICT_POINT[m]), ("loosest", LOOSEST[m])):
                run = load(base / m / params / "case_001" / "seed_0")
                same = None if (run is None or strict is None) else run["_text"] == strict["_text"]
                ok = None if same is None else (same if kind == "strict point" else not same)
                rows.append({"sampler_path": path, "method": m, "setting": kind, "params": params,
                             "identical_to_lossless": same, "expected": "identical" if kind == "strict point" else "differs",
                             "pass": ok, "tokens": run and run.get("output_tokens"),
                             "tokens_lossless": strict and strict.get("output_tokens"),
                             "l_bar": run and round(run.get("l_bar") or 0, 3),
                             "l_bar_lossless": strict and round(strict.get("l_bar") or 0, 3)})
    write(OUT / "strict_limit.csv", rows)


def v2_ab(ssh: bool) -> None:
    """The V2 check's runs stay on Killarney (/scratch/billxby/step8/v2check); compare output.txt there."""
    if not ssh:
        return
    script = r'''
import json, pathlib
root = pathlib.Path("/scratch/billxby/step8/v2check")
def one(side, m, p):
    d = root / side / "runs" / "gsm8k_qwen3" / m / p / "case_001" / "seed_0"
    try:
        r = json.loads((d / "run.json").read_text())
    except Exception:
        return None
    if r.get("status") != "ok":
        return None
    return (d / "output.txt").read_text(), r.get("output_tokens"), r.get("l_bar")
arms = [("strict", "strict"), ("mentored_dec", "alpha0.75"), ("cactus", "alpha0.35"), ("spec_casc_opt", "alpha0.05"),
        ("r_fuzzy", "alpha0.25"), ("spec_casc_tok", "alpha0.8"), ("spec_casc_tok_lt", "alphaneginf"),
        ("spec_casc_tok_lt", "alpha0.15"), ("spec_casc_tok_lt", "alpha0.2"), ("spec_casc_opt_head", "alphaneginf_beta0.15"),
        ("spec_casc_opt_head", "alpha0.05_beta0.15")]
strict_new = one("new", "strict", "strict")
for m, p in arms:
    old, new = one("old", m, p), one("new", m, p)
    print(json.dumps({"method": m, "params": p, "old_ok": old is not None, "new_ok": new is not None,
                      "old_eq_new": None if old is None or new is None else old[0] == new[0],
                      "new_eq_strict_new": None if new is None or strict_new is None else new[0] == strict_new[0],
                      "tokens_old": old and old[1], "tokens_new": new and new[1],
                      "l_bar_old": old and old[2], "l_bar_new": new and new[2]}))
'''
    out = subprocess.run(["ssh", "-o", "BatchMode=yes", "killarney", "python3 -"], input=script, text=True,
                         capture_output=True, timeout=300)
    rows = [json.loads(l) for l in out.stdout.splitlines() if l.startswith("{")]
    write(OUT / "v2_ab.csv", rows)


def log_lines(ssh: bool) -> None:
    if not ssh:
        return
    cmd = ("cd /scratch/billxby/step8 && grep -r -h -o -E '\\[(Q-PROBE V2|Q-PROBE V1 trace|[A-Z-]+ PATCH[^]]*)\\][^(]*' "
           "--include='*.log' --include='*.out' --with-filename . 2>/dev/null | sort -u")
    out = subprocess.run(["ssh", "-o", "BatchMode=yes", "killarney", cmd], text=True, capture_output=True, timeout=600)
    (OUT / "server_log_lines.txt").write_text(out.stdout, encoding="utf-8")
    print(f"wrote server_log_lines.txt ({len(out.stdout.splitlines())} lines)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-ssh", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    checks()
    strict_limit()
    v2_ab(not args.no_ssh)
    log_lines(not args.no_ssh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
