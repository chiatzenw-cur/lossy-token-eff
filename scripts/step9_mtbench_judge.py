#!/usr/bin/env python3
"""MT-Bench judge for the step-8 and step-9 MT-Bench arms (Bill, 2026-10-06: "please grade all MT-bench"):
scripts/addendum_mtbench_judge.py unchanged -- FastChat single-answer prompts (turn 1), claude-fable-5-1 at effort
medium on the Message Batches API, the same rating parse and summaries -- pointed at the step-8 / step-9 run trees.

  python3 scripts/step9_mtbench_judge.py plan      # runs to judge, cost estimate; no API call
  python3 scripts/step9_mtbench_judge.py submit    # one batch
  python3 scripts/step9_mtbench_judge.py collect   # wait, parse, write campaign/addendum/step9/mtbench_judge/*.csv

Only the arms that enter the tables are judged: lossless and each (rule, alpha) of the pair's step8__ / step9__ table
(calibration-only alphas, 3 cases each, are not). The answer a reader sees: GPT-OSS = Harmony final channel; Qwen3
and R1-Distill = text outside <think> (R1's prompt opens <think>, the judge's own splitter handles an unopened one);
Llama-3.1 = the whole completion (it does not reason in tags). `target` in the outputs is the pair id, so arms of two
pairs never merge.
"""

from __future__ import annotations

import csv
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import addendum_mtbench_judge as aj  # noqa: E402

WT = REPO.parent  # .claude/worktrees: the step-8 and step-9 run trees live in their own worktrees (runs/ is gitignored)
TREES = {"step8": WT / "addendum-step8" / "runs", "step9": WT / "addendum-step9" / "runs"}
TABLES = REPO / "campaign" / "addendum" / "tables"
FAMILY_OF = {"mtbench": "gpt-oss-20b", "mtbench_qwen3": "qwen3-8b", "mtbench_llama31": "llama31",
             "mtbench_r1llama": "r1llama"}

aj.OUT = REPO / "campaign" / "addendum" / "step9" / "mtbench_judge"
aj.STATE = aj.OUT / "batches.json"
aj.DIRECT_CACHE = aj.OUT / "direct.jsonl"


def table_arms() -> dict[tuple[str, str], set[tuple[str, str]]]:
    """(step, pair) -> {(method, alpha)} of the MT-Bench rows in tables/step{8,9}__<pair>.csv, plus strict."""
    arms: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for step in ("step8", "step9"):
        for path in sorted(TABLES.glob(f"{step}__*.csv")):
            pair = path.stem.split("__", 1)[1]
            with path.open(newline="", encoding="utf-8") as handle:
                for r in csv.DictReader(handle):
                    if r["dataset"].startswith("mtbench") and not r.get("beta"):
                        arms.setdefault((step, pair), {("strict", "strict")}).add((r["method"], f"{float(r['alpha']):g}"))
    return arms


def answer_text(text: str, family: str) -> str:
    if family == "gpt-oss-20b":
        return aj.answer_text(text, "gpt-oss-20b")
    if family == "llama31":
        return aj.SPECIAL.sub("", text).strip()
    return aj.answer_text(text, "qwen3-8b")  # Qwen3 and R1-Distill: outside <think>


def collect_runs(seeds=None) -> list[dict]:
    prompts, by_text, refs = aj.load_judge_data()
    arms = table_arms()
    runs = []
    for (step, pair), wanted in sorted(arms.items()):
        root = TREES[step]
        for ds_dir in sorted((root / "addendum" / step / pair).glob("mtbench*")):
            ds, family = ds_dir.name, FAMILY_OF[ds_dir.name]
            for run_json in sorted(ds_dir.glob("*/*/case_*/seed_0/run.json")):
                run_dir = run_json.parent
                case, params, method = run_dir.parent.name, run_dir.parent.parent.name, run_dir.parent.parent.parent.name
                alpha = "strict" if method == "strict" else f"{float(params.removeprefix('alpha').replace('neg', '-')):g}"
                if (method, alpha) not in wanted or "_" in params:
                    continue
                run = json.loads(run_json.read_text(encoding="utf-8"))
                if run.get("status") != "ok":
                    continue
                case_dir = REPO / "prompts" / ds / case
                question = json.loads((case_dir / "source.json").read_text(encoding="utf-8"))["problem"]
                category = json.loads((case_dir / "metadata.json").read_text(encoding="utf-8"))["category"]
                q = by_text.get(question.strip())
                if q is None:  # the same case_007 typo as the addendum (see addendum_mtbench_judge.collect_runs)
                    import difflib
                    best = max(by_text, key=lambda t: difflib.SequenceMatcher(None, t, question.strip()).ratio())
                    if difflib.SequenceMatcher(None, best, question.strip()).ratio() < 0.95:
                        raise SystemExit(f"no FastChat question matches {ds}/{case}")
                    q = by_text[best]
                answer = answer_text((run_dir / "output.txt").read_text(encoding="utf-8", errors="replace"), family)
                version = "single-math-v1" if category in aj.NEED_REF_CATS else "single-v1"
                fields = {"question": question, "answer": answer}
                if version == "single-math-v1":
                    fields["ref_answer_1"] = refs[q["question_id"]]
                runs.append({
                    "relpath": str(run_dir.relative_to(root)), "target": pair, "method": method, "alpha": alpha,
                    "case": case, "seed": "0", "category": category, "question_id": q["question_id"],
                    "prompt_version": version, "answer_chars": len(answer), "finish_reason": run.get("finish_reason"),
                    "system": prompts[version]["system_prompt"],
                    "user": prompts[version]["prompt_template"].format(**fields),
                })
    return runs


aj.collect_runs = collect_runs

if __name__ == "__main__":
    aj.OUT.mkdir(parents=True, exist_ok=True)
    raise SystemExit(aj.main())
