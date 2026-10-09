#!/usr/bin/env python3
"""Step 9 Block 0 (campaign/addendum/step9/BLOCK0.md): the 2-case lossless smoke runs of every (pair, dataset) block,
graded with the campaign's own graders (answer segment, extraction method, verdict), plus the run's length, finish
reason, l_bar and the server's node. Reads runs/addendum/step9_block0/<cluster>/<pair>/... (pulled by
scripts/step9_campaign.py collect); writes campaign/addendum/step9/block0/smoke.csv and prints a table.

HumanEval candidates are executed by grade_humaneval.execute (RLIMIT_AS works on Linux only: run this where the
code runs, or pass --no-exec to report extraction alone).

  python3 scripts/step9_block0.py [--no-exec]
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import grade_aime  # noqa: E402
import grade_humaneval  # noqa: E402
import grade_longbench  # noqa: E402
import step9_campaign as s9  # noqa: E402
from campaign_run import base_dataset  # noqa: E402

OUT = s9.S9 / "block0" / "smoke.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-exec", action="store_true", help="HumanEval: extraction only")
    args = parser.parse_args()
    rows = []
    for block, pid, base in s9.BLOCKS:
        item = s9.smoke_item(block)
        sub = item["runs_subroot"].rsplit("/", 1)[0]
        for case in s9.SMOKE_CASES:
            run_dir = s9.run_dir(pid, item["dataset"], "strict", "strict", case, sub)
            run = s9.s8.run_ok(run_dir)
            if run is None:
                continue
            config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
            text = (run_dir / "output.txt").read_text(encoding="utf-8", errors="replace")
            prompts = REPO / "prompts" / item["dataset"]
            if base == "aime24":
                answer, how = grade_aime.extract_answer(text)
                verdict = (grade_aime.grade(run_dir, prompts) or {}).get("verdict")
            elif base == "longbench_v2":
                answer, how = grade_longbench.extract_answer(text)
                verdict = (grade_longbench.grade(run_dir, prompts) or {}).get("verdict")
            else:
                code, how = grade_humaneval.extract_candidate(text)
                answer = f"{len(code.splitlines())} lines" if code else None
                if args.no_exec:
                    verdict = "extracted" if code else "no_answer"
                else:
                    verdict = (grade_humaneval.grade(run_dir, prompts, 10.0, 1024) or {}).get("verdict")
            rows.append({
                "block": block, "cluster": s9.block_host(block), "pair": pid, "dataset": item["dataset"], "case": case,
                "output_tokens": run.get("output_tokens"), "finish_reason": run.get("finish_reason"),
                "l_bar": f"{run.get('l_bar'):.3f}", "wall_s": f"{run.get('wall_time_seconds', 0):.1f}",
                "host": config.get("host", ""), "answer_segment": how, "answer": answer, "verdict": verdict,
                "draft_model": config.get("draft_model", ""),
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        fields = list(rows[0]) if rows else ["block"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        print(f"{r['block']:3s} {r['cluster']:9s} {r['dataset']:22s} {r['case']} {r['output_tokens']:>6} tok "
              f"{r['finish_reason']:6s} l_bar {r['l_bar']} {r['host']:6s} {r['answer_segment']:24s} "
              f"{str(r['answer'])[:12]:12s} {r['verdict']}")
    print(f"wrote {OUT.relative_to(REPO)} ({len(rows)} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
